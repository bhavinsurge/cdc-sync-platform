from __future__ import annotations

import json
import logging
import time
from typing import Any
from uuid import uuid4

from confluent_kafka import Consumer, KafkaException, Producer

from app.cdc.helpers import backoff_ms, should_retry
from app.core.config import get_settings
from app.db.session import control_conn, dest_conn

logger = logging.getLogger(__name__)


def _already_applied(pipeline_id: str, idempotency_key: str) -> bool:
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM applied_keys
                WHERE pipeline_id = %s AND idempotency_key = %s
                """,
                (pipeline_id, idempotency_key),
            )
            return cur.fetchone() is not None


def _mark_applied(pipeline_id: str, idempotency_key: str) -> None:
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO applied_keys (pipeline_id, idempotency_key)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (pipeline_id, idempotency_key),
            )


def _update_event_status(event_id: str, status: str, error: str | None = None) -> None:
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE events_log
                SET status = %s, error = COALESCE(%s, error)
                WHERE event_id = %s
                """,
                (status, error, event_id),
            )


def _update_sync(pipeline_id: str, lsn: str | None, lag_ms: int) -> None:
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sync_state (
                  pipeline_id, last_lsn, last_event_at, lag_ms, consumer_status, updated_at
                ) VALUES (%s, %s, now(), %s, 'running', now())
                ON CONFLICT (pipeline_id) DO UPDATE SET
                  last_lsn = COALESCE(EXCLUDED.last_lsn, sync_state.last_lsn),
                  last_event_at = now(),
                  lag_ms = EXCLUDED.lag_ms,
                  consumer_status = 'running',
                  updated_at = now()
                """,
                (pipeline_id, lsn, lag_ms),
            )


def apply_event(event: dict[str, Any], dest_schema: str, dest_table: str) -> None:
    op = event["op"]
    after = event.get("after") or {}
    before = event.get("before") or {}
    row = after if op != "d" else before
    if not row or "id" not in row:
        raise ValueError("Change event missing primary key id")

    fq = f'"{dest_schema}"."{dest_table}"'
    with dest_conn() as conn:
        with conn.cursor() as cur:
            if op == "d":
                cur.execute(f"DELETE FROM {fq} WHERE id = %s", (row["id"],))
                return
            cur.execute(
                f"""
                INSERT INTO {fq} (id, customer_email, amount_cents, status, updated_at)
                VALUES (%(id)s, %(customer_email)s, %(amount_cents)s, %(status)s, COALESCE(%(updated_at)s::timestamptz, now()))
                ON CONFLICT (id) DO UPDATE SET
                  customer_email = EXCLUDED.customer_email,
                  amount_cents = EXCLUDED.amount_cents,
                  status = EXCLUDED.status,
                  updated_at = EXCLUDED.updated_at
                """,
                {
                    "id": row["id"],
                    "customer_email": row.get("customer_email"),
                    "amount_cents": row.get("amount_cents"),
                    "status": row.get("status", "pending"),
                    "updated_at": row.get("updated_at"),
                },
            )


def send_to_dlq(event: dict[str, Any], error: str, attempts: int) -> None:
    settings = get_settings()
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dlq_entries (id, pipeline_id, event_id, payload, error, attempts, status)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s, 'open')
                """,
                (
                    str(uuid4()),
                    event["pipeline_id"],
                    event["event_id"],
                    json.dumps(event),
                    error,
                    attempts,
                ),
            )
    _update_event_status(event["event_id"], "dlq", error)
    try:
        p = Producer({"bootstrap.servers": settings.kafka_bootstrap})
        p.produce(settings.kafka_dlq_topic, value=json.dumps({"event": event, "error": error}).encode())
        p.flush(5)
    except Exception:
        logger.exception("Failed to publish DLQ kafka message")


def process_event(event: dict[str, Any], max_retries: int | None = None) -> str:
    """Apply one event. Returns 'applied' | 'duplicate' | 'dlq'."""
    settings = get_settings()
    retries = max_retries if max_retries is not None else settings.max_retries
    pipeline_id = event["pipeline_id"]
    key = event["idempotency_key"]

    if _already_applied(pipeline_id, key):
        return "duplicate"

    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT dest_schema, dest_table, max_retries FROM pipelines WHERE id = %s",
                (pipeline_id,),
            )
            pipe = cur.fetchone()
    if not pipe:
        raise ValueError(f"Unknown pipeline {pipeline_id}")

    retries = min(retries, pipe["max_retries"])
    last_error = "unknown"
    for attempt in range(retries + 1):
        try:
            apply_event(event, pipe["dest_schema"], pipe["dest_table"])
            _mark_applied(pipeline_id, key)
            _update_event_status(event["event_id"], "applied")
            lag = max(0, int(time.time() * 1000) - int(event.get("ts_ms") or time.time() * 1000))
            _update_sync(pipeline_id, event.get("lsn"), lag)
            return "applied"
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Apply attempt %s failed: %s", attempt + 1, last_error)
            if should_retry(attempt + 1, retries):
                time.sleep(backoff_ms(attempt) / 1000.0)
            else:
                break

    send_to_dlq(event, last_error, retries + 1)
    return "dlq"


def run_consumer_loop(stop_flag: dict[str, bool] | None = None) -> None:
    settings = get_settings()
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap,
            "group.id": settings.kafka_consumer_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([settings.kafka_topic])
    logger.info("CDC consumer subscribed to %s", settings.kafka_topic)
    try:
        while True:
            if stop_flag and stop_flag.get("stop"):
                break
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            try:
                event = json.loads(msg.value().decode("utf-8"))
                result = process_event(event)
                logger.info("Processed %s → %s", event.get("event_id"), result)
                consumer.commit(asynchronous=False)
            except Exception:
                logger.exception("Consumer failed on message")
                # commit anyway after DLQ path inside process_event; if parse fails, skip
                try:
                    consumer.commit(asynchronous=False)
                except Exception:
                    pass
    finally:
        consumer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_consumer_loop()

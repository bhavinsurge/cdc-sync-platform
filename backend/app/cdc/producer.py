from __future__ import annotations

import json
import logging
import time
from typing import Any
from uuid import UUID, uuid4

from confluent_kafka import Producer

from app.cdc.helpers import build_change_event, parse_test_decoding_change
from app.core.config import get_settings
from app.db.session import control_conn, source_conn

logger = logging.getLogger(__name__)


def ensure_slot(slot: str) -> None:
    with source_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_replication_slots WHERE slot_name = %s",
                (slot,),
            )
            if cur.fetchone():
                return
            cur.execute(
                "SELECT * FROM pg_create_logical_replication_slot(%s, 'test_decoding')",
                (slot,),
            )
            logger.info("Created replication slot %s", slot)


def _active_pipeline() -> dict[str, Any] | None:
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, source_schema, source_table, topic, status, max_retries
                FROM pipelines
                WHERE status = 'running'
                ORDER BY created_at
                LIMIT 1
                """
            )
            return cur.fetchone()


def _log_event(event: dict[str, Any], status: str = "published") -> None:
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events_log (
                  id, pipeline_id, event_id, idempotency_key, op, payload, status, lsn
                ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (
                    str(uuid4()),
                    event["pipeline_id"],
                    event["event_id"],
                    event["idempotency_key"],
                    event["op"],
                    json.dumps(event),
                    status,
                    event.get("lsn"),
                ),
            )
            cur.execute(
                """
                INSERT INTO sync_state (pipeline_id, last_lsn, last_event_at, lag_ms, producer_status, updated_at)
                VALUES (%s, %s, now(), 0, 'running', now())
                ON CONFLICT (pipeline_id) DO UPDATE SET
                  last_lsn = EXCLUDED.last_lsn,
                  last_event_at = EXCLUDED.last_event_at,
                  producer_status = 'running',
                  updated_at = now()
                """,
                (event["pipeline_id"], event.get("lsn")),
            )
            cur.execute(
                """
                INSERT INTO pipeline_offsets (pipeline_id, producer_lsn, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (pipeline_id) DO UPDATE SET
                  producer_lsn = EXCLUDED.producer_lsn,
                  updated_at = now()
                """,
                (event["pipeline_id"], event.get("lsn")),
            )


def poll_once(producer: Producer) -> int:
    settings = get_settings()
    pipeline = _active_pipeline()
    if not pipeline:
        return 0

    emitted = 0
    with source_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT lsn::text AS lsn, xid::text AS xid, data
                FROM pg_logical_slot_get_changes(%s, NULL, NULL)
                """,
                (settings.replication_slot,),
            )
            rows = cur.fetchall()

    pending_before: dict[str, dict[str, Any]] = {}
    for row in rows:
        data = row["data"]
        if data.startswith("BEGIN") or data.startswith("COMMIT"):
            continue
        parsed = parse_test_decoding_change(data)
        if not parsed:
            continue
        if (
            parsed.schema != pipeline["source_schema"]
            or parsed.table != pipeline["source_table"]
        ):
            continue

        before = None
        after = None
        if parsed.op == "d":
            before = parsed.values
        elif parsed.op == "c":
            after = parsed.values
        else:
            # test_decoding UPDATE shows new values only; treat as after
            after = parsed.values
            before = pending_before.get(str(parsed.values.get("id")))

        event = build_change_event(
            pipeline_id=str(pipeline["id"]),
            schema=parsed.schema,
            table=parsed.table,
            op=parsed.op,
            before=before,
            after=after,
            lsn=row["lsn"],
            ts_ms=int(time.time() * 1000),
        )
        topic = pipeline["topic"]
        producer.produce(
            topic,
            key=str((after or before or {}).get("id", event["event_id"])),
            value=json.dumps(event).encode("utf-8"),
        )
        _log_event(event, status="published")
        emitted += 1

    if emitted:
        producer.flush(5)
    return emitted


def run_producer_loop(stop_flag: dict[str, bool] | None = None) -> None:
    settings = get_settings()
    ensure_slot(settings.replication_slot)
    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap})
    logger.info("CDC producer started (slot=%s)", settings.replication_slot)
    while True:
        if stop_flag and stop_flag.get("stop"):
            break
        try:
            n = poll_once(producer)
            if n:
                logger.info("Published %s change event(s)", n)
        except Exception:
            logger.exception("Producer poll failed")
            with control_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE sync_state SET producer_status = 'error', updated_at = now()
                        WHERE pipeline_id IN (SELECT id FROM pipelines WHERE status = 'running')
                        """
                    )
        time.sleep(settings.cdc_poll_interval_ms / 1000.0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_producer_loop()

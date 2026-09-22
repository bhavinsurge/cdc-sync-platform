"""Integration: source insert → CDC poll → consumer apply → dest row.

Requires Docker Compose infra. Skips unless rivercdc_* databases are reachable
and current control DB name starts with rivercdc_.
"""

from __future__ import annotations

import json
import os
import time
import uuid

import psycopg
import pytest
from confluent_kafka import Producer

# Ensure backend on path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.cdc.consumer import process_event
from app.cdc.helpers import build_change_event
from app.cdc.producer import ensure_slot, poll_once
from app.core.config import get_settings

SOURCE = os.getenv(
    "SOURCE_DATABASE_URL",
    "postgresql://rivercdc:rivercdc_dev_password@localhost:5436/rivercdc_source",
)
DEST = os.getenv(
    "DEST_DATABASE_URL",
    "postgresql://rivercdc:rivercdc_dev_password@localhost:5437/rivercdc_dest",
)
CONTROL = os.getenv(
    "CONTROL_DATABASE_URL",
    "postgresql://rivercdc:rivercdc_dev_password@localhost:5437/rivercdc_control",
)


def _db_name(url: str) -> str:
    return url.rsplit("/", 1)[-1].split("?")[0]


def _reachable() -> bool:
    try:
        for url in (SOURCE, DEST, CONTROL):
            if not _db_name(url).startswith("rivercdc_"):
                return False
            with psycopg.connect(url, connect_timeout=3) as conn:
                row = conn.execute("SELECT current_database() AS d").fetchone()
                assert row[0].startswith("rivercdc_")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="rivercdc docker DBs not reachable")


def test_direct_apply_idempotent():
    """Unit-style integration of consumer apply without Kafka."""
    with psycopg.connect(CONTROL) as conn:
        pipe = conn.execute("SELECT id FROM pipelines WHERE name = 'orders-sync'").fetchone()
        assert pipe, "seed pipeline missing — run scripts/seed.py"
        pipeline_id = str(pipe[0])

    order_id = str(uuid.uuid4())
    event = build_change_event(
        pipeline_id=pipeline_id,
        schema="shop",
        table="orders",
        op="c",
        before=None,
        after={
            "id": order_id,
            "customer_email": "integ@example.com",
            "amount_cents": 999,
            "status": "pending",
        },
        lsn="0/ABCDEF",
        ts_ms=int(time.time() * 1000),
    )
    assert process_event(event) == "applied"
    assert process_event(event) == "duplicate"

    with psycopg.connect(DEST) as conn:
        row = conn.execute(
            "SELECT customer_email, amount_cents FROM shop.orders WHERE id = %s",
            (order_id,),
        ).fetchone()
        assert row is not None
        assert row[0] == "integ@example.com"
        assert row[1] == 999


def test_producer_poll_publishes_and_consumer_applies(monkeypatch):
    settings = get_settings()
    ensure_slot(settings.replication_slot)

    order_id = str(uuid.uuid4())
    with psycopg.connect(SOURCE) as conn:
        conn.execute(
            """
            INSERT INTO shop.orders (id, customer_email, amount_cents, status)
            VALUES (%s, %s, %s, %s)
            """,
            (order_id, "kafka@example.com", 4242, "pending"),
        )
        conn.commit()

    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap})
    # Drain any prior changes then get ours
    deadline = time.time() + 15
    found = False
    while time.time() < deadline:
        n = poll_once(producer)
        with psycopg.connect(DEST) as conn:
            # Prefer applying via process from events_log
            pass
        with psycopg.connect(CONTROL) as conn:
            row = conn.execute(
                """
                SELECT payload FROM events_log
                WHERE payload::text LIKE %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (f"%{order_id}%",),
            ).fetchone()
            if row:
                payload = row[0]
                if isinstance(payload, str):
                    payload = json.loads(payload)
                process_event(payload)
                found = True
                break
        time.sleep(0.5)

    assert found, "CDC producer did not capture source insert"

    with psycopg.connect(DEST) as conn:
        row = conn.execute(
            "SELECT amount_cents FROM shop.orders WHERE id = %s",
            (order_id,),
        ).fetchone()
        assert row is not None
        assert int(row[0]) == 4242

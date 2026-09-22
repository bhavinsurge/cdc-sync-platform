#!/usr/bin/env python3
"""Seed RiverCDC control plane + sample source rows. Only touches rivercdc_* DBs."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import bcrypt
import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONTROL_URL = "postgresql://rivercdc:rivercdc_dev_password@localhost:5437/rivercdc_control"
SOURCE_URL = "postgresql://rivercdc:rivercdc_dev_password@localhost:5436/rivercdc_source"
DEST_URL = "postgresql://rivercdc:rivercdc_dev_password@localhost:5437/rivercdc_dest"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def assert_safe(url: str) -> None:
    name = url.rsplit("/", 1)[-1].split("?")[0]
    if not name.startswith("rivercdc_"):
        raise SystemExit(f"Refusing unsafe db: {name}")


def seed() -> None:
    for u in (CONTROL_URL, SOURCE_URL, DEST_URL):
        assert_safe(u)

    pipeline_id = str(uuid4())
    admin_id = str(uuid4())

    with psycopg.connect(CONTROL_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", ("admin@rivercdc.local",))
            existing = cur.fetchone()
            if not existing:
                cur.execute(
                    """
                    INSERT INTO users (id, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, 'ADMIN')
                    """,
                    (
                        admin_id,
                        "admin@rivercdc.local",
                        _hash("Password123!"),
                        "River Admin",
                    ),
                )
                print("Created admin@rivercdc.local")
            else:
                # Ensure demo password works after bcrypt backend changes
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE email = %s",
                    (_hash("Password123!"), "admin@rivercdc.local"),
                )
                print("Admin user already exists (password refreshed)")

            cur.execute("SELECT id FROM pipelines WHERE name = %s", ("orders-sync",))
            prow = cur.fetchone()
            if not prow:
                cur.execute(
                    """
                    INSERT INTO pipelines (
                      id, name, source_schema, source_table, topic,
                      dest_schema, dest_table, status, max_retries
                    ) VALUES (%s, 'orders-sync', 'shop', 'orders', 'rivercdc.shop.orders',
                              'shop', 'orders', 'running', 3)
                    """,
                    (pipeline_id,),
                )
                cur.execute(
                    "INSERT INTO sync_state (pipeline_id, producer_status, consumer_status) VALUES (%s, 'idle', 'idle')",
                    (pipeline_id,),
                )
                cur.execute(
                    "INSERT INTO pipeline_offsets (pipeline_id) VALUES (%s)",
                    (pipeline_id,),
                )
                print(f"Created pipeline orders-sync ({pipeline_id})")
            else:
                pipeline_id = str(prow[0])
                print(f"Pipeline exists ({pipeline_id})")
        conn.commit()

    sample_id = "11111111-1111-1111-1111-111111111111"
    with psycopg.connect(SOURCE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM shop.orders WHERE id = %s", (sample_id,))
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO shop.orders (id, customer_email, amount_cents, status)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (sample_id, "alice@example.com", 2599, "pending"),
                )
                print("Inserted sample source order")
            else:
                print("Sample source order exists")
        conn.commit()

    print("Seed complete.")


if __name__ == "__main__":
    seed()

#!/usr/bin/env python3
"""Apply control-plane migrations to rivercdc_control databases only."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg

SAFE_PREFIX = "rivercdc_"
MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "app" / "db" / "migrations"


def assert_safe_db(url: str) -> str:
    # Extract dbname
    name = url.rsplit("/", 1)[-1].split("?")[0]
    if not name.startswith(SAFE_PREFIX):
        raise SystemExit(f"Refusing to migrate unsafe database name: {name}")
    return name


def migrate(url: str) -> None:
    db = assert_safe_db(url)
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        raise SystemExit("No migration files found")
    print(f"Migrating {db} with {len(sql_files)} file(s)...")
    with psycopg.connect(url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              filename TEXT PRIMARY KEY,
              applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.commit()
        for path in sql_files:
            row = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE filename = %s",
                (path.name,),
            ).fetchone()
            if row:
                print(f"  skip {path.name}")
                continue
            sql = path.read_text()
            conn.execute(sql)
            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (path.name,),
            )
            conn.commit()
            print(f"  applied {path.name}")
    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default="postgresql://rivercdc:rivercdc_dev_password@localhost:5437/rivercdc_control",
    )
    args = parser.parse_args()
    migrate(args.url)


if __name__ == "__main__":
    main()

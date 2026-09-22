from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings


def _connect(url: str) -> psycopg.Connection:
    return psycopg.connect(url, row_factory=dict_row)


@contextmanager
def control_conn() -> Generator[psycopg.Connection, None, None]:
    conn = _connect(get_settings().control_database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def source_conn() -> Generator[psycopg.Connection, None, None]:
    conn = _connect(get_settings().source_database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def dest_conn() -> Generator[psycopg.Connection, None, None]:
    conn = _connect(get_settings().dest_database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

"""Pure helpers for CDC: idempotency, LSN ordering, test_decoding parse, retry."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class ParsedChange:
    schema: str
    table: str
    op: str  # c | u | d
    values: dict[str, Any]


_ROW_RE = re.compile(
    r"^table (?P<schema>\w+)\.(?P<table>\w+): (?P<op>INSERT|UPDATE|DELETE): (?P<body>.*)$"
)


def compare_lsn(a: str | None, b: str | None) -> int:
    """Compare PostgreSQL LSNs. Return -1, 0, 1."""
    if a is None and b is None:
        return 0
    if a is None:
        return -1
    if b is None:
        return 1

    def parts(lsn: str) -> tuple[int, int]:
        left, right = lsn.split("/")
        return int(left, 16), int(right, 16)

    pa, pb = parts(a), parts(b)
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0


def make_idempotency_key(
    pipeline_id: str,
    schema: str,
    table: str,
    pk: str,
    lsn: str,
    op: str,
) -> str:
    return f"{pipeline_id}:{schema}.{table}:{pk}:{lsn}:{op}"


def should_retry(attempt: int, max_retries: int) -> bool:
    return attempt < max_retries


def backoff_ms(attempt: int, base_ms: int = 200, cap_ms: int = 5000) -> int:
    delay = base_ms * (2**attempt)
    return min(delay, cap_ms)


def _coerce(typename: str, raw: str | None) -> Any:
    if raw is None:
        return None
    t = typename.lower()
    if t in {"integer", "int4", "int8", "bigint", "smallint"}:
        return int(raw)
    if t in {"bool", "boolean"}:
        return raw in {"t", "true", "1"}
    return raw


def parse_test_decoding_change(line: str) -> ParsedChange | None:
    """Parse a single test_decoding change line into a structured op."""
    line = line.strip()
    m = _ROW_RE.match(line)
    if not m:
        return None
    op_map = {"INSERT": "c", "UPDATE": "u", "DELETE": "d"}
    op = op_map[m.group("op")]
    values: dict[str, Any] = {}
    # Matches: name[type]:null | name[type]:'quoted' | name[type]:bare
    for fm in re.finditer(
        r"(\w+)\[([^\]]+)\]:(null|'([^']*)'|([^\s]+))",
        m.group("body"),
    ):
        name, typename = fm.group(1), fm.group(2)
        if fm.group(3) == "null":
            values[name] = None
        elif fm.group(4) is not None:
            values[name] = _coerce(typename, fm.group(4))
        else:
            values[name] = _coerce(typename, fm.group(5))
    return ParsedChange(
        schema=m.group("schema"),
        table=m.group("table"),
        op=op,
        values=values,
    )


def new_event_id() -> str:
    return str(uuid.uuid4())


def build_change_event(
    *,
    pipeline_id: str,
    schema: str,
    table: str,
    op: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    lsn: str,
    ts_ms: int,
    database: str = "rivercdc_source",
) -> dict[str, Any]:
    pk_source = after or before or {}
    pk = str(pk_source.get("id", "unknown"))
    event_id = new_event_id()
    idem = make_idempotency_key(pipeline_id, schema, table, pk, lsn, op)
    return {
        "event_id": event_id,
        "idempotency_key": idem,
        "pipeline_id": pipeline_id,
        "source": {"database": database, "schema": schema, "table": table},
        "op": op,
        "before": before,
        "after": after,
        "lsn": lsn,
        "ts_ms": ts_ms,
    }

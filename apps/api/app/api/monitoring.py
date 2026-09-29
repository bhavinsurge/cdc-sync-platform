import json
from typing import Annotated, Any
from uuid import uuid4

from confluent_kafka import Producer
from fastapi import APIRouter, Depends, Query

from app.api.deps import err, get_current_user, ok, require_operator
from app.cdc.consumer import process_event
from app.core.config import get_settings
from app.db.session import control_conn

router = APIRouter(prefix="/api", tags=["monitoring"])


def _ser(row: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif k in {"id", "pipeline_id", "event_id"} and v is not None:
            out[k] = str(v)
        elif isinstance(v, dict):
            out[k] = v
        else:
            out[k] = v
    return out


@router.get("/health")
def health():
    return ok({"status": "ok", "service": "rivercdc-api"})


@router.get("/events")
def list_events(
    _: Annotated[dict[str, Any], Depends(get_current_user)],
    pipeline_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
):
    with control_conn() as conn:
        with conn.cursor() as cur:
            if pipeline_id:
                cur.execute(
                    """
                    SELECT * FROM events_log
                    WHERE pipeline_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (pipeline_id, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM events_log
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            rows = cur.fetchall()
    return ok([_ser(r) for r in rows])


@router.get("/sync/lag")
def sync_lag(_: Annotated[dict[str, Any], Depends(get_current_user)]):
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.*, p.name AS pipeline_name
                FROM sync_state s
                JOIN pipelines p ON p.id = s.pipeline_id
                ORDER BY p.name
                """
            )
            rows = cur.fetchall()
    return ok([_ser(r) for r in rows])


@router.get("/dlq")
def list_dlq(
    _: Annotated[dict[str, Any], Depends(get_current_user)],
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
):
    with control_conn() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    """
                    SELECT * FROM dlq_entries
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (status, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM dlq_entries
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            rows = cur.fetchall()
    return ok([_ser(r) for r in rows])


@router.post("/dlq/{dlq_id}/replay")
def replay_dlq(
    dlq_id: str,
    _: Annotated[dict[str, Any], Depends(require_operator)],
):
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM dlq_entries WHERE id = %s", (dlq_id,))
            entry = cur.fetchone()
    if not entry:
        err("NOT_FOUND", "DLQ entry not found", status_code=404)
    if entry["status"] != "open":
        err("INVALID_STATE", "Only open DLQ entries can be replayed")

    payload = entry["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)

    # New idempotency attempt: keep same key so duplicate-safe if already applied;
    # if not applied, process_event will apply.
    result = process_event(payload)

    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE dlq_entries
                SET status = 'replayed', updated_at = now()
                WHERE id = %s
                """,
                (dlq_id,),
            )

    # Also re-publish for streaming visibility
    settings = get_settings()
    try:
        p = Producer({"bootstrap.servers": settings.kafka_bootstrap})
        p.produce(settings.kafka_topic, value=json.dumps(payload).encode("utf-8"))
        p.flush(5)
    except Exception:
        pass

    return ok({"dlq_id": dlq_id, "result": result})


@router.post("/dlq/{dlq_id}/discard")
def discard_dlq(
    dlq_id: str,
    _: Annotated[dict[str, Any], Depends(require_operator)],
):
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE dlq_entries
                SET status = 'discarded', updated_at = now()
                WHERE id = %s AND status = 'open'
                RETURNING id
                """,
                (dlq_id,),
            )
            row = cur.fetchone()
    if not row:
        err("NOT_FOUND", "Open DLQ entry not found", status_code=404)
    return ok({"discarded": True, "id": dlq_id})


@router.post("/events/{event_id}/replay")
def replay_event(
    event_id: str,
    _: Annotated[dict[str, Any], Depends(require_operator)],
):
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM events_log WHERE event_id = %s", (event_id,))
            row = cur.fetchone()
    if not row:
        err("NOT_FOUND", "Event not found", status_code=404)
    payload = row["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)

    # Mint a new idempotency key suffix for forced replay by cloning event
    cloned = dict(payload)
    cloned["event_id"] = str(uuid4())
    cloned["idempotency_key"] = f"{payload['idempotency_key']}:replay:{cloned['event_id'][:8]}"

    settings = get_settings()
    p = Producer({"bootstrap.servers": settings.kafka_bootstrap})
    p.produce(settings.kafka_topic, value=json.dumps(cloned).encode("utf-8"))
    p.flush(5)

    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events_log (
                  id, pipeline_id, event_id, idempotency_key, op, payload, status, lsn
                ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, 'published', %s)
                """,
                (
                    str(uuid4()),
                    cloned["pipeline_id"],
                    cloned["event_id"],
                    cloned["idempotency_key"],
                    cloned["op"],
                    json.dumps(cloned),
                    cloned.get("lsn"),
                ),
            )
    return ok({"replayed_event_id": cloned["event_id"]})

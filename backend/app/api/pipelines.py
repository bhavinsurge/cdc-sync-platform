from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.api.deps import err, get_current_user, ok, require_admin, require_operator
from app.db.session import control_conn
from app.models.schemas import PipelineIn, PipelinePatch

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])


def _serialize(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for k, v in out.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif k == "id":
            out[k] = str(v)
    return out


@router.get("")
def list_pipelines(_: Annotated[dict[str, Any], Depends(get_current_user)]):
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM pipelines ORDER BY created_at")
            rows = cur.fetchall()
    return ok([_serialize(r) for r in rows])


@router.get("/{pipeline_id}")
def get_pipeline(pipeline_id: str, _: Annotated[dict[str, Any], Depends(get_current_user)]):
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM pipelines WHERE id = %s", (pipeline_id,))
            row = cur.fetchone()
    if not row:
        err("NOT_FOUND", "Pipeline not found", status_code=404)
    return ok(_serialize(row))


@router.post("")
def create_pipeline(
    body: PipelineIn,
    _: Annotated[dict[str, Any], Depends(require_operator)],
):
    pid = str(uuid4())
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pipelines (
                  id, name, source_schema, source_table, topic, dest_schema, dest_table, max_retries
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    pid,
                    body.name,
                    body.source_schema,
                    body.source_table,
                    body.topic,
                    body.dest_schema,
                    body.dest_table,
                    body.max_retries,
                ),
            )
            row = cur.fetchone()
            cur.execute(
                """
                INSERT INTO sync_state (pipeline_id, producer_status, consumer_status)
                VALUES (%s, 'idle', 'idle')
                ON CONFLICT DO NOTHING
                """,
                (pid,),
            )
            cur.execute(
                """
                INSERT INTO pipeline_offsets (pipeline_id) VALUES (%s)
                ON CONFLICT DO NOTHING
                """,
                (pid,),
            )
    return ok(_serialize(row))


@router.patch("/{pipeline_id}")
def patch_pipeline(
    pipeline_id: str,
    body: PipelinePatch,
    _: Annotated[dict[str, Any], Depends(require_operator)],
):
    fields = []
    values: list[Any] = []
    if body.status is not None:
        fields.append("status = %s")
        values.append(body.status)
    if body.max_retries is not None:
        fields.append("max_retries = %s")
        values.append(body.max_retries)
    if body.name is not None:
        fields.append("name = %s")
        values.append(body.name)
    if not fields:
        err("NO_CHANGES", "No fields to update")
    fields.append("updated_at = now()")
    values.append(pipeline_id)
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE pipelines SET {', '.join(fields)} WHERE id = %s RETURNING *",
                values,
            )
            row = cur.fetchone()
    if not row:
        err("NOT_FOUND", "Pipeline not found", status_code=404)
    return ok(_serialize(row))


@router.delete("/{pipeline_id}")
def delete_pipeline(
    pipeline_id: str,
    _: Annotated[dict[str, Any], Depends(require_admin)],
):
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM pipelines WHERE id = %s RETURNING id", (pipeline_id,))
            row = cur.fetchone()
    if not row:
        err("NOT_FOUND", "Pipeline not found", status_code=404)
    return ok({"deleted": True, "id": pipeline_id})

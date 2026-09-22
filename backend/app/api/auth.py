from datetime import datetime, timedelta, timezone
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Cookie, Depends, Response

from app.api.deps import err, get_current_user, ok
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token_value,
    hash_password,
    hash_token,
    verify_password,
    verify_token_hash,
)
from app.db.session import control_conn
from app.models.schemas import LoginIn, RegisterIn

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "full_name": row["full_name"],
        "role": row["role"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def _set_refresh_cookie(response: Response, raw: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="river_refresh",
        value=raw,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_days * 86400,
        path="/api/auth",
    )


@router.post("/register")
def register(body: RegisterIn):
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE email = %s", (body.email.lower(),))
            if cur.fetchone():
                err("EMAIL_TAKEN", "Email already registered", status_code=409)
            user_id = str(uuid4())
            cur.execute("SELECT COUNT(*) AS c FROM users")
            count = cur.fetchone()["c"]
            role = "ADMIN" if count == 0 else "VIEWER"
            cur.execute(
                """
                INSERT INTO users (id, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, email, full_name, role, created_at
                """,
                (user_id, body.email.lower(), hash_password(body.password), body.full_name, role),
            )
            user = cur.fetchone()
    return ok(_user_out(user))


@router.post("/login")
def login(body: LoginIn, response: Response):
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, full_name, role, password_hash, created_at
                FROM users WHERE email = %s
                """,
                (body.email.lower(),),
            )
            user = cur.fetchone()
            if not user or not verify_password(body.password, user["password_hash"]):
                err("INVALID_CREDENTIALS", "Invalid email or password", status_code=401)
            raw_refresh = create_refresh_token_value()
            cur.execute(
                """
                INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    str(user["id"]),
                    hash_token(raw_refresh),
                    datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_days),
                ),
            )
    access = create_access_token(str(user["id"]), user["role"])
    _set_refresh_cookie(response, raw_refresh)
    return ok({"access_token": access, "token_type": "bearer", "user": _user_out(user)})


@router.post("/logout")
def logout(
    response: Response,
    river_refresh: Annotated[str | None, Cookie()] = None,
):
    if river_refresh:
        with control_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, token_hash FROM refresh_tokens WHERE revoked_at IS NULL")
                for row in cur.fetchall():
                    if verify_token_hash(river_refresh, row["token_hash"]):
                        cur.execute(
                            "UPDATE refresh_tokens SET revoked_at = now() WHERE id = %s",
                            (str(row["id"]),),
                        )
                        break
    response.delete_cookie("river_refresh", path="/api/auth")
    return ok({"logged_out": True})


@router.post("/refresh")
def refresh(
    response: Response,
    river_refresh: Annotated[str | None, Cookie()] = None,
):
    if not river_refresh:
        err("NO_REFRESH", "Missing refresh token", status_code=401)
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rt.id, rt.token_hash, rt.expires_at, rt.revoked_at,
                       u.id AS user_id, u.email, u.full_name, u.role, u.created_at
                FROM refresh_tokens rt
                JOIN users u ON u.id = rt.user_id
                WHERE rt.revoked_at IS NULL
                """
            )
            matched = None
            for row in cur.fetchall():
                if verify_token_hash(river_refresh, row["token_hash"]):
                    matched = row
                    break
            if not matched:
                err("INVALID_REFRESH", "Invalid refresh token", status_code=401)
            if matched["expires_at"] < datetime.now(timezone.utc):
                err("EXPIRED_REFRESH", "Refresh token expired", status_code=401)
            cur.execute(
                "UPDATE refresh_tokens SET revoked_at = now() WHERE id = %s",
                (str(matched["id"]),),
            )
            raw_refresh = create_refresh_token_value()
            cur.execute(
                """
                INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    str(matched["user_id"]),
                    hash_token(raw_refresh),
                    datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_days),
                ),
            )
            user = {
                "id": matched["user_id"],
                "email": matched["email"],
                "full_name": matched["full_name"],
                "role": matched["role"],
                "created_at": matched["created_at"],
            }
    access = create_access_token(str(user["id"]), user["role"])
    _set_refresh_cookie(response, raw_refresh)
    return ok({"access_token": access, "token_type": "bearer", "user": _user_out(user)})


@router.get("/me")
def me(user: Annotated[dict[str, Any], Depends(get_current_user)]):
    return ok(_user_out(user))

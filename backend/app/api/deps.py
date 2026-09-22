from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status

from app.core.security import decode_access_token
from app.db.session import control_conn

ROLE_RANK = {"VIEWER": 1, "OPERATOR": 2, "ADMIN": 3}


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized") from exc

    user_id = payload.get("sub")
    with control_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, full_name, role, created_at FROM users WHERE id = %s",
                (user_id,),
            )
            user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user


def require_roles(*roles: str):
    minimum = min(ROLE_RANK[r] for r in roles)

    def _dep(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
        if ROLE_RANK.get(user["role"], 0) < minimum and user["role"] not in roles:
            # Allow if user has equal or higher rank than the lowest requested role
            if ROLE_RANK.get(user["role"], 0) < minimum:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep


def require_operator(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
    if ROLE_RANK.get(user["role"], 0) < ROLE_RANK["OPERATOR"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user


def require_admin(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user


def ok(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data}


def err(code: str, message: str, details: Any = None, status_code: int = 400) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message, "details": details}},
    )

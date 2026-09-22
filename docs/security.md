# RiverCDC — Security

## Authentication

- Passwords hashed with bcrypt
- Short-lived JWT access tokens (15m)
- Rotating refresh tokens stored hashed in DB; httpOnly cookie `river_refresh`
- Logout revokes refresh token

## Authorization

Roles: `ADMIN` | `OPERATOR` | `VIEWER`

- VIEWER: read pipelines, events, DLQ, lag
- OPERATOR: mutate pipelines (create/update), replay/discard DLQ
- ADMIN: delete pipelines + all operator capabilities

Enforced in FastAPI dependencies.

## Transport & headers

- Local HTTP only (no paid TLS terminator required)
- CORS limited to UI origin `http://localhost:3007`
- Security headers on Next.js middleware where applicable
- Zod/Pydantic validation on all inputs

## Secrets

- `JWT_SECRET`, DB passwords, Kafka bootstrap in `.env` (not committed)
- Demo credentials documented in README only

## Data safety

- Scripts only touch `rivercdc_*` databases
- No cascade drops of unknown DBs
- Idempotency prevents duplicate destination writes from token replay storms

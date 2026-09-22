# RiverCDC — API Design

Base URL: `http://localhost:8007`

Envelope:

```json
{ "success": true, "data": {} }
```

```json
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "...", "details": null } }
```

## Auth

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/auth/register` | Register (admin seed preferred) |
| POST | `/api/auth/login` | Login → access JWT + refresh cookie |
| POST | `/api/auth/logout` | Clear refresh |
| POST | `/api/auth/refresh` | Rotate tokens |
| GET | `/api/auth/me` | Current user |

## Pipelines

| Method | Path | Roles |
| --- | --- | --- |
| GET | `/api/pipelines` | any |
| GET | `/api/pipelines/{id}` | any |
| POST | `/api/pipelines` | ADMIN, OPERATOR |
| PATCH | `/api/pipelines/{id}` | ADMIN, OPERATOR |
| DELETE | `/api/pipelines/{id}` | ADMIN |

## Events & monitoring

| Method | Path | Roles |
| --- | --- | --- |
| GET | `/api/events` | any (`pipeline_id`, `limit`, `cursor`) |
| GET | `/api/sync/lag` | any |
| GET | `/api/health` | public |

## DLQ & replay

| Method | Path | Roles |
| --- | --- | --- |
| GET | `/api/dlq` | any |
| POST | `/api/dlq/{id}/replay` | ADMIN, OPERATOR |
| POST | `/api/dlq/{id}/discard` | ADMIN, OPERATOR |
| POST | `/api/events/{event_id}/replay` | ADMIN, OPERATOR |

## Auth header

`Authorization: Bearer <access_token>`

Cookies: `river_refresh` (httpOnly)

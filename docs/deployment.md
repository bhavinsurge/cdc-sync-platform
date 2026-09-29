# RiverCDC — Deployment

## Local (primary)

1. `yarn infra:up`
2. `yarn python:install && yarn db:migrate && yarn db:seed`
3. Start `yarn api:dev`, `yarn producer:dev`, `yarn consumer:dev`, `yarn web:dev` (or `yarn dev`)

See root README for exact commands.

## Components

| Component | Deploy target |
| --- | --- |
| Next.js UI (`apps/web`) | Vercel-ready / Node host |
| FastAPI (`apps/api`) | Any Python host / container |
| Producer / consumer | Separate process or container per runtime |
| Postgres ×2 | Docker / managed PG with logical decoding on source |
| Kafka | Docker KRaft / local broker |

## Free/local only

No paid SaaS. For demos keep Compose on a single machine.

## Health

- `GET http://localhost:8007/api/health`
- UI `http://localhost:3007`

## Environment

Copy `apps/api/.env.example` → `apps/api/.env` and `apps/web/.env.example` → `apps/web/.env.local`.

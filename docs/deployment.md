# RiverCDC — Deployment

## Local (primary)

1. `docker compose up -d`
2. Backend migrations + seed
3. Start producer, consumer, FastAPI, Next.js

See root README for exact commands.

## Components

| Component | Deploy target |
| --- | --- |
| Next.js UI | Vercel-ready / Node host |
| FastAPI + workers | Any Python host / container |
| Postgres ×2 | Docker / managed PG with logical decoding on source |
| Kafka | Docker KRaft / local broker |

## Free/local only

No paid SaaS. For demos keep Compose on a single machine.

## Health

- `GET http://localhost:8007/api/health`
- UI `http://localhost:3007`

## Environment

Copy `.env.example` → `.env` for backend and frontend.

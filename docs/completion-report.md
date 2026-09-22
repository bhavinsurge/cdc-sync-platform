# Project 3 Completion Report

```text
Project: RiverCDC — CDC Sync Platform
Status: COMPLETE — completion gate passed

Architecture: Custom Python CDC (PostgreSQL logical decoding via test_decoding +
  pg_logical_slot_get_changes) → Kafka (KRaft) → Python consumer → destination PG;
  FastAPI control plane; Next.js monitoring UI
Database: Source PG :5436 (rivercdc_source), Dest PG :5437 (rivercdc_dest + rivercdc_control)
Backend: FastAPI auth/pipelines/events/DLQ/replay; CDC producer + consumer workers
Frontend: RiverCDC UI (Fraunces + Source Sans 3, slate + river-blue)

Major features:
- Capture INSERT/UPDATE/DELETE from shop.orders via logical replication slot
- Kafka topic rivercdc.shop.orders + DLQ topic rivercdc.dlq
- Idempotent destination apply via applied_keys (pipeline_id, idempotency_key)
- Retry with exponential backoff; exhausted attempts → DLQ table (+ Kafka DLQ)
- Replay APIs for DLQ entries and events
- JWT access + rotating refresh cookie (river_refresh); roles ADMIN/OPERATOR/VIEWER
- Monitoring UI: overview lag, pipelines, events, DLQ actions

Architecture choice vs Debezium:
- Chose custom Python logical decoding (not Debezium/Kafka Connect) for a lighter
  local stack and explicit control over event schema, idempotency, DLQ, and
  control-plane monitoring while still using real PostgreSQL WAL logical decoding.

Authentication: bcrypt passwords + JWT access (15m) + hashed refresh tokens
Authorization: OPERATOR+ for pipeline mutate / DLQ replay; ADMIN for pipeline delete

Testing: Unit 5/5, Integration 2/2, E2E 1/1 passed; frontend lint + typecheck + build OK
Live verification: source INSERT appeared on destination within ~3s

Security: CORS to UI origin; input validation; secrets in .env; only rivercdc_* DBs touched
Deployment: Docker Compose for PG×2 + Kafka KRaft + Redis; app processes on host

Known limitations:
- Demo focuses on single table shop.orders with UUID PK
- test_decoding UPDATE lines expose new values primarily (limited before-image)
- At-least-once delivery; exactly-once approximated via idempotent writes
- Single-partition topic for ordering simplicity
- Local HTTP only

Important engineering decisions:
- Isolated ports 3007/8007/5436/5437/19092/6382 to avoid Project 1–2 / Grafana conflicts
- Control plane on destination host DB rivercdc_control
- Safety guards refuse migrations/seeds unless DB name starts with rivercdc_
- Polling logical slot (get_changes) avoids custom Postgres plugins (wal2json)

Files created: under 03-cdc-sync-platform/ (docs, docker, backend, frontend)

How to run locally:
  cd 03-cdc-sync-platform
  cp backend/.env.example backend/.env
  cp frontend/.env.example frontend/.env.local
  docker compose up -d
  cd backend && python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  python scripts/migrate.py && python scripts/seed.py
  uvicorn app.main:app --host 0.0.0.0 --port 8007 --app-dir .
  python -m app.cdc.producer   # separate terminal
  python -m app.cdc.consumer   # separate terminal
  cd ../frontend && npm install && npm run dev   # http://localhost:3007

Demo login: admin@rivercdc.local / Password123!

How to run tests:
  cd backend && pytest tests/unit -q && pytest tests/integration -q
  cd frontend && npm run lint && npm run typecheck && npm run build && npm run test:e2e

How to deploy:
  See docs/deployment.md — free/local Compose + host processes; no paid SaaS.
```

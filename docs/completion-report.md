# Project 3 Completion Report

```text
Project: RiverCDC — CDC Sync Platform
Status: COMPLETE — monorepo architecture aligned to portfolio standard

Architecture: Yarn Workspaces + Turborepo monorepo
  apps/web (Next.js frontend) → /api rewrite → apps/api (FastAPI)
  apps/producer + apps/consumer (independent CDC runtimes)
  infrastructure/ (source/dest Postgres, Kafka KRaft, Redis)
  Custom Python CDC (test_decoding + pg_logical_slot_get_changes) → Kafka → apply

Database: Source PG :5436 (rivercdc_source), Dest PG :5437 (rivercdc_dest + rivercdc_control)
Backend: FastAPI (Python justified for CDC) — NestJS not used
Frontend: Next.js dashboard only (no Route Handlers as backend)

Major features:
- Capture INSERT/UPDATE/DELETE from shop.orders via logical replication slot
- Kafka topic rivercdc.shop.orders + DLQ topic rivercdc.dlq
- Idempotent destination apply via applied_keys (pipeline_id, idempotency_key)
- Retry with exponential backoff; exhausted attempts → DLQ table (+ Kafka DLQ)
- Replay APIs for DLQ entries and events
- JWT access + rotating refresh cookie; roles ADMIN/OPERATOR/VIEWER
- Monitoring UI: overview lag, pipelines, events, DLQ actions

How to run locally:
  cd 03-cdc-sync-platform
  cp apps/api/.env.example apps/api/.env
  cp apps/web/.env.example apps/web/.env.local
  yarn install && yarn python:install
  yarn infra:up
  yarn db:migrate && yarn db:seed
  yarn api:dev / yarn producer:dev / yarn consumer:dev / yarn web:dev

Demo login: admin@rivercdc.local / Password123!

How to run tests:
  yarn test
  yarn build && yarn lint && yarn typecheck
  yarn test:e2e

How to deploy:
  See docs/deployment.md — free/local Compose + host processes; no paid SaaS.
```

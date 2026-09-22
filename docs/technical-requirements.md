# RiverCDC — Technical Requirements

## Stack

| Layer | Choice |
| --- | --- |
| UI | Next.js (App Router) + TypeScript + Tailwind |
| Control plane API | Python 3.12 + FastAPI |
| CDC producer | Python logical replication client (`psycopg` + `test_decoding`) |
| Messaging | Apache Kafka (KRaft, Docker) |
| Source DB | PostgreSQL 16 (`wal_level=logical`) |
| Destination DB | PostgreSQL 16 (mirror + control plane schema) |
| Cache (optional) | Redis 7 |
| Auth | JWT access + bcrypt passwords |
| Tests | pytest (unit/integration), Playwright (e2e) |

## Ports (host)

| Service | Port |
| --- | --- |
| Next.js UI | 3007 |
| FastAPI | 8007 |
| Source Postgres | 5436 |
| Destination Postgres | 5437 |
| Kafka (external) | 19092 |
| Redis | 6382 |

## Functional Requirements

- FR1: Capture INSERT/UPDATE/DELETE on published source tables
- FR2: Emit JSON change events to Kafka with idempotency key
- FR3: Consumer applies changes upsert/delete with key-based idempotency
- FR4: Persist event log, offsets, sync state, DLQ entries
- FR5: Retry failed applies up to N times; then DLQ
- FR6: Replay API re-publishes DLQ or selected events
- FR7: JWT-protected control plane; role-aware UI

## Non-Functional

- Local-only, free tooling
- Deterministic Docker names: `rivercdc_*`
- Never drop unknown databases
- At-least-once delivery; destination writes idempotent
- Producer and consumer restartable without data loss (slot + offsets)

## Architecture Choice

**Custom Python logical replication CDC** (not Debezium):

- Uses built-in `test_decoding` plugin (no custom Postgres image plugins)
- Explicit control over event schema, retries, and monitoring tables
- Lighter Docker footprint than Kafka Connect + Debezium Connect

## Constraints

- Single partition topics for demo ordering simplicity
- Source tables must have a primary key
- Control plane lives on destination Postgres (`rivercdc_control`)

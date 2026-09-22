# RiverCDC — Product Requirements

## Overview

RiverCDC is a local-first Change Data Capture (CDC) sync platform that streams PostgreSQL source mutations through Kafka to a destination database, with monitoring, retries, dead-letter handling, and replay.

## Problem Statement

Teams need reliable near-real-time replication of operational data without paid SaaS CDC products. Portfolio demonstration of event-driven architecture, ordering, idempotency, and failure recovery.

## Goals

- Capture INSERT / UPDATE / DELETE from a PostgreSQL source
- Publish typed change events to Kafka
- Apply changes to a destination PostgreSQL mirror with idempotency
- Provide a control-plane API and monitoring UI for pipelines, events, lag, DLQ, and replay
- Run entirely on free local tooling (Docker + Python + Next.js)

## Non-Goals

- Multi-region / multi-tenant SaaS
- Paid cloud brokers or managed Debezium
- Schema evolution tooling beyond documented limitations
- Exactly-once across every failure mode (at-least-once + idempotent apply)

## Personas

| Persona | Needs |
| --- | --- |
| Operator | Create pipelines, watch lag, replay DLQ |
| Viewer | Read-only dashboards and event history |
| Admin | User management, pipeline delete, full control |

## Core Features

1. Pipeline configuration (source table → Kafka topic → destination table)
2. CDC capture via PostgreSQL logical replication (`test_decoding`)
3. Kafka publish + consumer apply with idempotency keys
4. Retry with backoff; dead-letter queue (DLQ) after max attempts
5. Event log + lag metrics in the UI
6. Replay from DLQ or by event id
7. JWT authentication for UI/API

## Success Criteria

- Insert/update/delete on source appears on destination within a few seconds
- Duplicate Kafka deliveries do not corrupt destination rows
- Failed applies land in DLQ and can be replayed
- Unit, integration, and e2e smoke tests pass
- Completion gate verification (install → migrate → seed → lint/typecheck → tests → build → start)

## Demo Scenario

1. Login as admin
2. View seeded `orders` pipeline (running)
3. Insert a row into source `orders`
4. See event in UI; destination row matches
5. Force a failure → DLQ → replay → success

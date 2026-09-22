# RiverCDC — Architecture

## High-Level

```mermaid
flowchart LR
  Src[(Source PG :5436)] -->|logical decoding| Producer[CDC Producer]
  Producer -->|change events| Kafka[Kafka :19092]
  Kafka --> Consumer[CDC Consumer]
  Consumer --> Dest[(Dest PG :5437)]
  UI[Next.js :3007] --> API[FastAPI :8007]
  API --> Dest
  API --> Kafka
  Producer --> Dest
  Consumer --> Dest
```

## Components

### Source PostgreSQL
- `wal_level=logical`, publication `rivercdc_pub`
- Sample schema `shop.orders`
- Replication slot `rivercdc_slot` consumed by producer

### CDC Producer
- Connects with replication protocol
- Decodes `test_decoding` messages → normalized `ChangeEvent`
- Publishes to Kafka topic `rivercdc.shop.orders`
- Updates producer offset / lag metrics in control plane

### Kafka
- KRaft single-node broker
- Topics: change stream + DLQ topic `rivercdc.dlq`

### CDC Consumer
- Reads Kafka messages
- Applies INSERT/UPDATE/DELETE to destination mirror
- Idempotency via `(pipeline_id, idempotency_key)` unique constraint
- On failure: retry → DLQ table + optional DLQ topic
- Updates sync state / consumed offsets

### FastAPI Control Plane
- Auth, pipelines, events, DLQ, lag, replay
- Reads/writes control tables on dest Postgres

### Next.js UI
- Login, dashboard (lag), pipelines, events, DLQ actions

## Event Schema

```json
{
  "event_id": "uuid",
  "idempotency_key": "pipeline:table:pk:lsn:op",
  "pipeline_id": "uuid",
  "source": { "database": "rivercdc_source", "schema": "shop", "table": "orders" },
  "op": "c|u|d",
  "before": {},
  "after": {},
  "lsn": "0/16B3748",
  "ts_ms": 1710000000000
}
```

## Ordering & Idempotency

- Single-partition topic preserves LSN order per table stream
- Consumer commits Kafka offset only after successful apply (or DLQ write)
- Duplicate events skipped when idempotency key already applied

## Failure Recovery

1. Transient apply error → exponential backoff retry (in-process + redelivery)
2. Exhausted retries → DLQ row; consumer continues
3. Operator replay → re-publish to main topic or direct apply
4. Producer crash → resumes from replication slot LSN

## Why not Debezium?

Debezium + Kafka Connect is valid but heavier for a local portfolio stack (extra Connect worker, connector configs, image versions). Custom Python decoding keeps the learning surface on event schema, idempotency, DLQ, and control plane while still using real PostgreSQL logical replication.

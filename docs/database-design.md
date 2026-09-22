# RiverCDC — Database Design

## Databases

| Host port | Database | Purpose |
| --- | --- | --- |
| 5436 | `rivercdc_source` | Source operational data |
| 5437 | `rivercdc_dest` | Destination mirror |
| 5437 | `rivercdc_control` | Control plane (pipelines, events, DLQ, users) |
| 5436 | `rivercdc_source_test` | Integration test source (optional) |
| 5437 | `rivercdc_control_test` | Integration test control |

Safety: only create/drop databases prefixed `rivercdc_`.

## Source schema (`shop`)

```sql
CREATE TABLE shop.orders (
  id UUID PRIMARY KEY,
  customer_email TEXT NOT NULL,
  amount_cents INT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Publication: `CREATE PUBLICATION rivercdc_pub FOR TABLE shop.orders;`

## Destination mirror

Same structure under `shop.orders` on `rivercdc_dest`.

## Control plane tables (`rivercdc_control`)

| Table | Purpose |
| --- | --- |
| `users` | Auth users + roles |
| `refresh_tokens` | Rotating refresh tokens |
| `pipelines` | Pipeline config |
| `pipeline_offsets` | Producer/consumer LSN & Kafka offsets |
| `events_log` | Captured/applied events |
| `dlq_entries` | Dead-letter records |
| `sync_state` | Lag / last success / status |
| `applied_keys` | Idempotency registry |

### Key columns

**pipelines**: id, name, source_schema, source_table, topic, dest_schema, dest_table, status, max_retries, created_at

**events_log**: id, pipeline_id, event_id, idempotency_key, op, payload jsonb, status, lsn, created_at

**dlq_entries**: id, pipeline_id, event_id, payload jsonb, error, attempts, status (open/replayed/discarded), created_at

**applied_keys**: pipeline_id, idempotency_key, applied_at (UNIQUE)

**sync_state**: pipeline_id PK, last_lsn, last_event_at, lag_ms, producer_status, consumer_status, updated_at

## Indexes

- `events_log (pipeline_id, created_at DESC)`
- `dlq_entries (status, created_at DESC)`
- `applied_keys (pipeline_id, idempotency_key)` UNIQUE
- `users (email)` UNIQUE

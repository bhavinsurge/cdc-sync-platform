# RiverCDC — Testing Strategy

## Layers

### Unit (pytest)
- Idempotency key generation
- Ordering / LSN compare helpers
- Change-event parsing from `test_decoding` sample lines
- Retry/backoff decision helpers

### Integration (pytest)
- Requires Docker Postgres + Kafka up
- Insert into source → wait → assert destination row
- Duplicate apply skipped via `applied_keys`
- Refuse to run unless `current_database()` is a `rivercdc_*_test` or configured test DSN

### E2E smoke (Playwright)
- Login page loads
- Dashboard reachable after login
- Pipelines list shows seeded pipeline

## Commands

```bash
yarn test                                    # API unit + integration via turbo
yarn workspace @rivercdc/api test            # pytest directly
yarn test:e2e                                # Playwright (API + web)
yarn build && yarn lint && yarn typecheck
```

## Coverage focus

Event-driven correctness over UI chrome: capture → Kafka → apply → DLQ/replay.

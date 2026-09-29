# @rivercdc/consumer

Independent CDC consumer runtime. Applies Kafka change events to the destination database with idempotency, retries, and DLQ handling.

Shares Python application code with `@rivercdc/api` (`apps/api/app/cdc/consumer.py`).

```bash
yarn workspace @rivercdc/api python:install
yarn workspace @rivercdc/consumer dev
```

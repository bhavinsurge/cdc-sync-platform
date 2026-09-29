# @rivercdc/producer

Independent CDC producer runtime. Captures PostgreSQL logical decoding changes and publishes to Kafka.

Shares Python application code with `@rivercdc/api` (`apps/api/app/cdc/producer.py`) so event schemas, config, and DB access stay consistent.

```bash
yarn workspace @rivercdc/api python:install
yarn workspace @rivercdc/producer dev
```

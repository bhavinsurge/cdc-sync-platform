# RiverCDC — Development Plan

## Phases

1. **Docs & Compose** — ports, DBs, Kafka KRaft, Redis optional
2. **Schema** — source sample, dest mirror, control plane migrations
3. **CDC producer** — logical decoding → Kafka
4. **CDC consumer** — apply + idempotency + DLQ
5. **FastAPI** — auth, pipelines, events, lag, replay
6. **Next.js UI** — slate + river-blue monitoring dashboard
7. **Tests** — unit / integration / e2e
8. **Verification gate** — install → migrate → seed → lint → tests → build → start
9. **Completion report + git commits**

## Definition of done

Completion gate passes; `docs/completion-report.md` written; README runnable by a stranger.

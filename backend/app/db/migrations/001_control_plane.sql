-- RiverCDC control plane schema
-- Safe: only applied to rivercdc_control / rivercdc_control_test

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('ADMIN', 'OPERATOR', 'VIEWER')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);

CREATE TABLE IF NOT EXISTS pipelines (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  source_schema TEXT NOT NULL,
  source_table TEXT NOT NULL,
  topic TEXT NOT NULL,
  dest_schema TEXT NOT NULL,
  dest_table TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'paused', 'error')),
  max_retries INT NOT NULL DEFAULT 3,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pipeline_offsets (
  pipeline_id UUID PRIMARY KEY REFERENCES pipelines(id) ON DELETE CASCADE,
  producer_lsn TEXT,
  consumer_kafka_offset BIGINT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events_log (
  id UUID PRIMARY KEY,
  pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
  event_id UUID NOT NULL UNIQUE,
  idempotency_key TEXT NOT NULL,
  op TEXT NOT NULL CHECK (op IN ('c', 'u', 'd')),
  payload JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'captured'
    CHECK (status IN ('captured', 'published', 'applied', 'failed', 'dlq')),
  lsn TEXT,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_pipeline_created ON events_log(pipeline_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_idempotency ON events_log(idempotency_key);

CREATE TABLE IF NOT EXISTS dlq_entries (
  id UUID PRIMARY KEY,
  pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
  event_id UUID NOT NULL,
  payload JSONB NOT NULL,
  error TEXT NOT NULL,
  attempts INT NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'replayed', 'discarded')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dlq_status_created ON dlq_entries(status, created_at DESC);

CREATE TABLE IF NOT EXISTS applied_keys (
  pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
  idempotency_key TEXT NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (pipeline_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS sync_state (
  pipeline_id UUID PRIMARY KEY REFERENCES pipelines(id) ON DELETE CASCADE,
  last_lsn TEXT,
  last_event_at TIMESTAMPTZ,
  lag_ms BIGINT NOT NULL DEFAULT 0,
  producer_status TEXT NOT NULL DEFAULT 'idle',
  consumer_status TEXT NOT NULL DEFAULT 'idle',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

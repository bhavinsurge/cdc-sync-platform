-- RiverCDC source database initialization
-- Only creates rivercdc_* databases.

CREATE DATABASE rivercdc_source_test;

\c rivercdc_source

CREATE SCHEMA IF NOT EXISTS shop;

CREATE TABLE IF NOT EXISTS shop.orders (
  id UUID PRIMARY KEY,
  customer_email TEXT NOT NULL,
  amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
  status TEXT NOT NULL DEFAULT 'pending',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE PUBLICATION rivercdc_pub FOR TABLE shop.orders;

-- Replication role (same user for local demo)
ALTER USER rivercdc WITH REPLICATION;

\c rivercdc_source_test

CREATE SCHEMA IF NOT EXISTS shop;

CREATE TABLE IF NOT EXISTS shop.orders (
  id UUID PRIMARY KEY,
  customer_email TEXT NOT NULL,
  amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
  status TEXT NOT NULL DEFAULT 'pending',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE PUBLICATION rivercdc_pub FOR TABLE shop.orders;
ALTER USER rivercdc WITH REPLICATION;

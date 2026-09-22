-- RiverCDC destination + control plane initialization
-- Only creates rivercdc_* databases.

CREATE DATABASE rivercdc_control;
CREATE DATABASE rivercdc_control_test;
CREATE DATABASE rivercdc_dest_test;

\c rivercdc_dest

CREATE SCHEMA IF NOT EXISTS shop;

CREATE TABLE IF NOT EXISTS shop.orders (
  id UUID PRIMARY KEY,
  customer_email TEXT NOT NULL,
  amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
  status TEXT NOT NULL DEFAULT 'pending',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

\c rivercdc_dest_test

CREATE SCHEMA IF NOT EXISTS shop;

CREATE TABLE IF NOT EXISTS shop.orders (
  id UUID PRIMARY KEY,
  customer_email TEXT NOT NULL,
  amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
  status TEXT NOT NULL DEFAULT 'pending',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

# RiverCDC packages

RiverCDC uses PostgreSQL with SQL migrations in `apps/api/app/db/migrations/` (control plane + destination schema) rather than Prisma.

Python shared libraries live under `apps/api/app/` and are consumed by the independently runnable `api`, `producer`, and `consumer` workspaces. A separate `packages/*` TypeScript/Prisma package is not required for this project.

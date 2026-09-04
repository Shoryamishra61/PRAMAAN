# ADR-003 — Durable SQLite Job State Instead of In-Memory-Only Background Work

**Status:** Accepted

## Context
Webhook handlers should acknowledge quickly, but acknowledging before durable work state exists can lose work if the process crashes. FastAPI in-process background tasks alone are not durable.

## Decision
After signature validation and deduplication, ingestion atomically records the event/case and a durable `jobs` row before returning 2xx. A lightweight worker claims jobs, records attempts, and resumes pending/stale work after restart.

SQLite WAL is used for the local Buildathon implementation with short transactions and one connection per request/task. No enterprise throughput claim is made.

## Consequences
- restart/replay behavior can be tested;
- no Redis/Celery/Kafka requirement;
- production migration to a durable external queue remains possible if scale requires it.

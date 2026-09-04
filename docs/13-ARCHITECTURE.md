# 13 — Architecture Specification

## Architecture objective
Maximize correctness, inspectability, restart safety, and local reproducibility with minimal infrastructure.

## Logical architecture

```text
Razorpay-compatible signed webhook replay
        |
        v
FastAPI Ingestion
  - raw-body HMAC
  - x-razorpay-event-id dedupe
  - validate event name
        |
        v
SQLite transaction
  - ingest_event
  - dispute_case
  - durable job
        |
        v
2xx ACK (<5s requirement)
        |
        v
Durable Worker
  |--> structured deterministic checks
  |--> load synthetic merchant evidence
  |--> semantic extraction adapter
  |--> local quote grounding
  |--> deterministic cross-source verifier
  |--> decision policy
        |
        v
SQLite findings/decision/audit
        |
        +--> React analyst UI
        +--> evaluation artifact writer
```

## Why a durable jobs table
Original reports relied on FastAPI `BackgroundTasks`. That can lose acknowledged work if the process dies.

MVP instead persists a job in the same transaction as event consumption. A worker:
- polls/claims pending jobs;
- marks `processing`;
- uses a lease/heartbeat or stale-job timeout;
- resumes stale jobs after restart;
- records attempts/failure class.

This delivers queue durability without Redis/Celery.

## Deployment topology

### Local/dev
- one FastAPI process;
- one worker loop/process;
- one SQLite DB;
- one React dev server or static bundle.

### Demo
Prefer one command:
`make demo`
which:
- validates config;
- initializes DB;
- seeds fixtures if empty;
- starts API/worker/UI;
- enables `OFFLINE_DEMO_MODE=1` only when explicitly selected.

## SQLite rules
- WAL mode;
- foreign keys ON;
- busy timeout configured;
- one connection per request/task, not global shared connection;
- short transactions;
- unique constraints for idempotency;
- no `BEGIN EXCLUSIVE` around routine operations.

SQLite is appropriate for the hackathon/local system, not claimed as a high-volume production datastore.

## Webhook durability transaction
Within one DB transaction:
1. insert ingest event keyed by `razorpay_event_id`;
2. create/update case skeleton;
3. insert processing job;
4. commit;
5. return 2xx.

Duplicate insert conflict:
- load existing event;
- return 2xx idempotently;
- no duplicate job.

## Event ordering
Razorpay warns webhooks may arrive out of order. [SRC-RZP-03]

Design:
- store every documented event with its event/received timestamps;
- do not overwrite newer state solely because an older event arrived;
- for MVP, `payment.dispute.created` drives creation;
- later events are history/observability unless a tested state reducer handles them.

Do not simply discard late events without logging.

## Semantic boundary
Only normalized synthetic text crosses into model adapter.
The model never sees:
- DB connection;
- webhook secret;
- API keys beyond provider runtime;
- action endpoints.

## Offline demo mode
Offline cache contains previously computed structured extraction results indexed by case/doc/config hash.

Requirements:
- UI shows `Offline replay`;
- results use same schema/grounding validation;
- no claim that live inference occurred.

## Cache
Persistent extraction cache table is preferred over process-memory cache so restart behavior is stable.

Key:
`sha256(document_hash + extractor_config_hash + schema_version)`

## Optional audit hash chain
If built:
- audit event canonical JSON;
- previous hash;
- current hash;
- verifier CLI/UI.
Limitations documented in security spec.

## Rejected architecture
- Kafka/RabbitMQ: no demonstrated need.
- Celery/Redis: durable SQLite jobs sufficient for MVP.
- vector database: no retrieval use case.
- microservices: increases failure surface.
- Kubernetes: no deployment need.
- OCR/PDF parser: removed from MVP evidence contract.
- agent framework: no agentic task.

## Production migration notes
If this became real:
- PostgreSQL/managed durable queue;
- enterprise identity/tenant isolation;
- object storage and malware/CDR pipeline;
- secrets manager;
- DLP/privacy program;
- metrics/tracing platform;
- provider SLA/redundancy;
- audited reason-rule governance.
These are roadmap disclosures, not hackathon implementation requirements.

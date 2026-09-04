# CONCURRENCY, IDEMPOTENCY & TRANSACTION AUDIT

**Auditor Role**: Senior Distributed Systems & Database Reliability Engineer  
**Standard**: High-Concurrency Financial Transaction Integrity Standard  
**Date**: September 2026  
**Repository**: `dispute-integrity-gate-spec`  

---

## 1. Concurrency Architecture & SQLite WAL Model

CARVE-FECL utilizes SQLite configured in Write-Ahead Logging mode (`PRAGMA journal_mode = WAL`) as its primary durable state engine.

### Database Pragma Configuration
Configured in `backend/app/database.py:connect_database`:
```python
connection.execute("PRAGMA foreign_keys = ON")
connection.execute("PRAGMA busy_timeout = 5000")
connection.execute("PRAGMA journal_mode = WAL")
```
- **WAL Mode**: Allows concurrent readers while a single writer holds the write lock, eliminating read-write contention.
- **Busy Timeout = 5000ms**: When multiple workers attempt write operations simultaneously, threads do not immediately fail with `sqlite3.OperationalError: database is locked`; they back off and retry for up to 5 seconds.
- **Foreign Keys = ON**: Enforces referential integrity at the database engine level; orphan records cannot be written.

---

## 2. Idempotency at the Database Layer

Application-level `if` statements (check-then-act) are notoriously vulnerable to race conditions under concurrent execution. CARVE-FECL enforces idempotency using **database-level unique constraints**:

### 1. Webhook Deduplication
- **Constraint**: `CREATE TABLE ingest_events (razorpay_event_id TEXT PRIMARY KEY, ...);`
- **Execution**: In `backend/app/ingestion.py`, insertion occurs inside an explicit transaction (`BEGIN IMMEDIATE`).
- **Concurrent Double-Delivery Behavior**:
  - Thread 1 and Thread 2 receive the identical `razorpay_event_id` simultaneously.
  - Thread 1 acquires the immediate write lock and inserts the row.
  - Thread 2 waits on the busy timeout. When Thread 1 commits, Thread 2 encounters `sqlite3.IntegrityError`.
  - Thread 2 catches the integrity error, executes `connection.rollback()`, queries the existing case ID, and returns HTTP 202 with `duplicate=True`.
  - **Verdict**: Zero race condition; exactly one case and one job are created.

### 2. Reprocess Job Deduplication
- **Header**: `Idempotency-Key` passed in `POST /api/v1/cases/{case_id}/reprocess`.
- **Implementation**: In `backend/app/case_actions.py:queue_reprocess`:
  ```python
  suffix = _idempotent_suffix(case_id, normalized_key) if normalized_key else uuid4().hex
  job_id = f"job_reprocess_{suffix}"
  ```
  If a client retries the reprocess call with the same idempotency key, `SELECT id FROM jobs WHERE id = ?` immediately detects the existing job and returns `QueuedReprocess(job_id=job_id, case_id=case_id)` without duplicating background tasks.

---

## 3. Worker Lease Management & Split-Brain Prevention

When multiple worker processes or threads poll the durable `jobs` table, two workers must never process the same case concurrently, nor should a crashed worker leave a job permanently locked.

### Lease Claiming Algorithm
Implemented in `backend/app/jobs.py:claim_next_job`:
```sql
BEGIN IMMEDIATE;
SELECT id, case_id, job_type, attempt_count
FROM jobs
WHERE (
    status IN ('PENDING', 'RETRYABLE_ERROR') AND available_at <= :now
) OR (
    status = 'PROCESSING' AND lease_until IS NOT NULL AND lease_until <= :now
)
ORDER BY available_at, created_at, id
LIMIT 1;

UPDATE jobs
SET status = 'PROCESSING', attempt_count = :attempt_count + 1,
    lease_until = :lease_until, updated_at = :now
WHERE id = :claimed_id;
COMMIT;
```

### Safety Properties Guaranteed
1. **Mutual Exclusion**: `BEGIN IMMEDIATE` guarantees that no two workers can read and claim the same job simultaneously.
2. **Crash Recovery**: If a worker node crashes mid-inference, `lease_until` expires after 30 seconds. A surviving worker automatically reclaims the stale job.
3. **Bounded Retries**: If a transient error occurs, `fail_job()` increments `attempt_count`. Once `attempt_count >= max_attempts` (default 3), the job transitions permanently to `FAILED`, preventing infinite retry loops.

---

## 4. Out-of-Order Event Handling

Payment network events frequently arrive out of order (e.g., `payment.dispute.under_review` arriving before `payment.dispute.created`, or a dispute updated event arriving after an analyst inspection).

### Ordering Guards
- **Timestamp Monotonicity**: Case updates update `updated_at` with strict UTC ISO timestamps.
- **Workflow State Precedence**: Once a case enters `READY_FOR_CONTEST` or `READY_WITH_OVERRIDE`, subsequent passive webhook events do not silently reset the workflow status to `REVIEW_PENDING`.
- **Audit Logging**: Every event is preserved in `ingest_events` regardless of arrival order, ensuring full historical forensics.

---

## 5. Concurrency Test Coverage

Tested in the following automated test suites:
- `backend/tests/test_jobs.py`: Tests concurrent worker claiming, lease expiry, and bounded retry behavior.
- `backend/tests/test_webhook_replay.py`: Tests duplicate webhook delivery and payload hash integrity.
- `backend/tests/test_case_actions.py`: Tests idempotent reprocess calls and override race conditions.

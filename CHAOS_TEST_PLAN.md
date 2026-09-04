# PRAMAAN / CARVE-FECL — CHAOS & FAULT INJECTION TEST PLAN

> **Test Suite**: `backend/tests/chaos/test_chaos_fault_injection.py`  
> **Core Safety Invariant**: *Technical failure must never silently become CONTEST_READY.*

---

## 1. Fault Injection Points & Expected Degradation

The chaos testing framework simulates failures across the complete dispute processing lifecycle:

```text
 Inbound Event
      │
 [1]  ▼ (Crash before DB insert) ──► Client retries; zero state persisted
 Ingest Transaction
      │
 [2]  ▼ (Crash after DB commit, before ACK) ──► Retried webhook processed idempotently
 Queue / Worker Lease
      │
 [3]  ▼ (Worker stalls past lease_until) ──► Lease expires; Worker B recovers job safely
 Extractor / SMT Solver
      │
 [4]  ▼ (LLM or Z3 solver times out) ──► Fails closed to REVIEW (F_MODEL_UNAVAILABLE)
 Verification
      │
 [5]  ▼ (Malformed extraction schema) ──► Fails closed to REVIEW (F_EXTRACTION_MALFORMED)
 Gate Decision Write
      │
 [6]  ▼ (Disk / SQLite lock error) ──► Transaction rolled back; retry scheduled
```

---

## 2. Tested Failure Scenarios

### 1. Extractor & SMT Solver Timeout
- **Injection**: Extractor delays execution past configured deadline (`timeout_seconds=0.05`).
- **Assertion**: Pipeline catches `TimeoutError`, logs structured failure event, and yields:
  $$\text{Status} = \text{REVIEW}, \quad \text{Finding} = \text{F\_MODEL\_UNAVAILABLE}$$
- **Safety Invariant**: Under no circumstance does a timeout result in `PASS` or automated submission.

### 2. Extractor Crash & Exception Handling
- **Injection**: Semantic model raises unhandled internal errors (`TransientExtractorError`).
- **Assertion**: Bounded retry executes up to `max_attempts=2`. On final exhaustion, system yields `GateStatus.REVIEW`.

### 3. Checkpoint & Release Freeze Tampering
- **Injection**: Mutating a single byte in `release_freeze.json` (altering `code_bundle_sha256` or config digest).
- **Assertion**: `verify_release_freeze` detects the alteration and raises `ReleaseFreezeError`. Engine refuses to evaluate holdout data on uncertified code.

### 4. Circuit Breaker State Machine
- **Transitions**:
  ```text
  [AUTOMATION_ENABLED] ──(Review Capacity >= 90% or Risk >= 80%)──► [DEGRADED]
                                                                        │
                                                             (Risk >= 100%)
                                                                        │
                                                                        ▼
                                                                  [REVIEW_ONLY]
  ```
- **Injection**: Heavy review volume (460 reviews) pushes review capacity utilization $\ge 90\% \implies$ transition to `DEGRADED`. Excessive high-risk passes (410 passes) consume $100\%$ daily risk budget $\implies$ transition to `REVIEW_ONLY`.

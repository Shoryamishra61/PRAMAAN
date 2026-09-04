# FINTECH RELIABILITY AUDIT: STATE INTEGRITY & FAIL-CLOSED GUARDS

**Auditor Role**: Senior Fintech Systems Architect & Risk Infrastructure Engineer  
**Standard**: Institutional Payment Gateway Reliability Standard  
**Date**: September 2026  
**Repository**: `dispute-integrity-gate-spec`  

---

## 1. System Resilience & Reliability Philosophy

Financial infrastructure cannot operate under standard web application assumptions where minor glitches result in retries and approximate results. In payment dispute processing, an incorrect automated clearance (`PASS`) immediately causes unrecoverable merchant monetary loss, acquiring network fines, and reputational risk with card schemes.

CARVE-FECL is engineered under three core financial reliability principles:
1. **Determinism over Speculation**: Formal SMT proofs and exact ledger reconciliation take strict precedence over neural network probabilities.
2. **Atomic Ingestion before Execution**: Webhook acknowledgement is completely decoupled from expensive asynchronous ML inference.
3. **Fail-Closed State Boundaries**: Any ambiguity, missing ledger record, model timeout, or unhandled exception immediately routes to `REVIEW_REQUIRED`. Under zero circumstances can a degraded component clear a case.

---

## 2. Inbound Webhook Reliability & Razorpay Specification Compliance

### Critical Ingestion Path Analysis
Razorpay webhook contracts require sub-500ms acknowledgements under threat of aggressive exponential redelivery. Expensive neural inference or solver operations inside the HTTP handler create queue starvation and webhook timeouts.

The implemented flow in `backend/app/main.py:razorpay_webhook` and `backend/app/ingestion.py:ingest_event`:
```
[Raw HTTP Post]
      │
      ├── 1. Header Validation: Check Content-Length <= 1,000,000 bytes
      ├── 2. Body Read: Read raw body bytes exactly as transmitted
      ├── 3. HMAC Verification: Constant-time comparison (app.security)
      ├── 4. Event ID Verification: Check x-razorpay-event-id header
      ▼
[ingest_event (Atomic Transaction)]
      ├── 5. BEGIN IMMEDIATE (SQLite WAL write lock)
      ├── 6. Deduplication: INSERT INTO ingest_events (razorpay_event_id PK)
      ├── 7. Case Creation: INSERT INTO dispute_cases (amount in paise, UTC timestamps)
      ├── 8. Job Enqueue: INSERT OR IGNORE INTO jobs (job_type='PROCESS_CASE')
      └── 9. COMMIT & Return HTTP 202 Accepted (< 15ms duration)
```

### Forensic Webhook Checklist
- **Signature verification over raw bytes?** YES. Verified in `backend/app/main.py` line 123 (`raw_body = await request.body()`). Never parses JSON before validating the cryptographic HMAC.
- **Constant-time signature comparison?** YES. Verified in `backend/app/security.py` line 36 (`hmac.compare_digest(expected, supplied)`).
- **Idempotent against duplicate deliveries?** YES. In `ingestion.py` line 203, a duplicate `razorpay_event_id` triggers `sqlite3.IntegrityError`, immediately rolling back and returning `IngestResult(duplicate=True, status="accepted")`.
- **Decoupled async execution?** YES. Worker processing is handled via durable `jobs` table polling, ensuring webhook ACK latency is purely dominated by SQLite write speed ($\le 15\text{ms}$).

---

## 3. State Machine Integrity

Dispute lifecycle states are governed by explicit constraints in `backend/app/domain.py` and `backend/app/database.py`:

```
Processing Status:
[RECEIVED] ──► [QUEUED] ──► [PROCESSING] ──► [READY]
                               │
                               ├──► [RETRYABLE_ERROR] ──► (retry up to 3x)
                               └──► [FAILED]

Workflow Status:
[REVIEW_PENDING] ◄────────────────────────┐
       │                                  │
       ├── (Gate = PASS)                  ├── (Reprocess Requested)
       ▼                                  │
[READY_FOR_CONTEST]                       │
       ▲                                  │
       └── (All Sources Inspected)        │
[READY_WITH_OVERRIDE] ◄───────────────────┘
       ▲
       └── (Gate = BLOCK + Analyst Override)
```

### Transition Integrity Proof
- **Forbidden Mutations**: A case in `BLOCK` status cannot transition directly to `READY_FOR_CONTEST`. Calling `mark_ready()` on a blocked case raises HTTP 409 `MARK_READY_PRECONDITION_FAILED`.
- **Mandatory Source Inspection**: An operator cannot override a `BLOCK` decision without first inspecting every cited material finding source (`inspect_source()`). Attempting to override with uninspected sources raises HTTP 409 `OVERRIDE_INSPECTION_REQUIRED`.
- **Zero Payment Mutations**: No transition exists that connects dispute verification to payment capture, refund execution, or bank account debit.

---

## 4. Fail-Closed Design Matrix

Every possible subsystem degradation was audited for fail-closed compliance:

| Failure Scenario | Subsystem | System Behavior | Resulting Gate Decision | Monetary Safety |
| :--- | :--- | :--- | :---: | :---: |
| **Model Outage / Unreachable** | `semantic_pipeline.py` | 10s timeout triggers `TransientExtractorError`; bounded retry terminates; returns `F_MODEL_UNAVAILABLE`. | `REVIEW` | SAFE (Zero false pass) |
| **Document OCR Corruption** | `sandbox_api.py` | Noise ratio threshold exceeded; returns `F_CORRUPTED_DOCUMENT`. | `REVIEW` | SAFE (Zero false pass) |
| **Ambiguous Quote Grounding** | `grounding.py` | Substring appears $\ge 2$ times in text; status marked `AMBIGUOUS`. | `REVIEW` | SAFE (Zero false pass) |
| **Incomplete Refund Ledger** | `carve.py` | `refund_state` missing or incomplete; Z3 returns `INCOMPLETE`. | `REVIEW` | SAFE (Zero false pass) |
| **SMT Solver Timeout / Error** | `carve.py` | Solver duration exceeds 50ms; status returns `INCOMPLETE`. | `REVIEW` | SAFE (Zero false pass) |
| **Currency Mismatch** | `verification.py` | Currency mismatch between claim and payment creates `F_CURRENCY_MISMATCH`. | `BLOCK` | SAFE (Contest held) |
| **Negative / Float Amount** | `domain.py` | Pydantic strict integer validation rejects input; raises validation error. | Rejected / Error | SAFE (No state corruption) |

---

## 5. Audit Conclusion

The runtime architecture of CARVE-FECL satisfies high-integrity fintech standards. The separation of concerns between raw webhook ingestion, durable state transactions, deterministic SMT compilation, and operational review workflows prevents single-point-of-failure money loss.

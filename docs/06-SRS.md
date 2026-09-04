# 06 — Software Requirements Specification (SRS)

## 1. System boundary

Dispute Integrity Gate is a local/sandbox merchant-side service. It receives Razorpay-compatible dispute events and synthetic merchant evidence. It does not act as issuer, acquirer, card scheme, or Razorpay.

## 2. Runtime components
- FastAPI API service;
- durable SQLite database in WAL mode;
- durable job worker;
- semantic extraction adapter;
- deterministic verification engine;
- React/TypeScript analyst UI;
- benchmark/evaluation CLI;
- optional offline inference cache.

## 3. Processing states

Separate system processing state from gate decision.

`RECEIVED → VALIDATED → QUEUED → PROCESSING → READY`

Exceptional:
- `RETRYABLE_ERROR`
- `FAILED`

Gate decision exists only when evaluable:
- `PASS`
- `REVIEW`
- `BLOCK`

A technical failure must not be encoded as BLOCK.

## 4. SRS requirements

### SRS-001 Configuration
All secrets/config supplied by environment variables. `.env.example` contains placeholders only.

### SRS-002 Webhook endpoint
`POST /api/v1/webhooks/razorpay`
- read raw bytes once;
- verify `X-Razorpay-Signature`;
- read `x-razorpay-event-id`;
- reject missing/invalid signature;
- persist event + job atomically;
- duplicate event ID returns safe 2xx without duplicate logical processing;
- successful durable consume returns 2xx within 5 seconds.

### SRS-003 Event types
MVP processes `payment.dispute.created`.
Other documented dispute events may be persisted for observability but do not need full business handling.

### SRS-004 Raw payload preservation
Store body SHA-256 and sanitized structured fields. Raw body storage is optional in synthetic demo; never log full raw body.

### SRS-005 Case adapter
Extract documented dispute fields when present. Unknown fields are preserved/ignored safely; payload validation must tolerate forward-compatible extra fields.

### SRS-006 Evidence source contract
MVP evidence is synthetic `text/plain` and `application/json`.
No PDF/OCR requirement.

### SRS-007 Semantic extractor
Input:
- document ID/type;
- normalized text;
- allowed claim types.

Output:
- typed claims;
- exact source quote;
- normalized attributes;
- no decision status.

### SRS-008 Grounding validator
For each model quote:
- exact substring search in canonical normalized text;
- exactly one match required for decision eligibility;
- if zero/multiple matches, mark `UNGROUNDED/AMBIGUOUS` and route case to REVIEW.

If normalization changes content, preserve a deterministic mapping or use the same canonical text for model and UI.

### SRS-009 Financial values
Integer minor units only. No float storage/calculation.

### SRS-010 Timestamps
UTC-aware timestamps internally. Raw epoch retained.

### SRS-011 Verification engine
Consumes trusted structured facts + grounded claims and emits typed findings.

### SRS-012 Decision policy
Consumes findings and verification completeness; emits PASS/REVIEW/BLOCK using `docs/12-DECISION-POLICY.md`.

### SRS-013 No network action
No code path may call Razorpay contest/accept/refund/payment write endpoints in MVP.

### SRS-014 Local workflow action
`Mark ready for contest` updates only local workflow state and must be explicitly labeled.

### SRS-015 Override
BLOCK override requires:
- conflict source A inspected;
- conflict source B inspected;
- structured reason code;
- optional note;
- audit event.

No arbitrary character threshold.

### SRS-016 Durable jobs
Job records persist before webhook ACK. Worker claims jobs with transactional status changes and resumes stale/pending jobs on restart.

### SRS-017 Retries
Only retry transient semantic-provider failures. Bound attempts. Permanent schema/grounding failures produce REVIEW, not infinite retries.

### SRS-018 Evaluation isolation
Dev evaluation and holdout evaluation are distinct CLI commands. Holdout command requires explicit flag and verifies manifest hash.

### SRS-019 Result artifact
Every evaluation run writes immutable-by-convention versioned JSON:
- system/config version;
- dataset version;
- case predictions;
- metrics;
- timestamp;
- model/prompt identifiers.

UI loads this artifact; never computes made-up metrics client-side.

### SRS-020 Offline demo
Offline output cache is generated from valid extractor schemas and versioned. The UI displays `Offline replay` badge.

### SRS-021 Logging
Structured logs:
- correlation ID;
- event/case/job IDs;
- module;
- action;
- latency if measured;
- failure class.
No raw evidence, secrets, full prompts, PAN/email/phone.

### SRS-022 Audit trail
Append-only application API. Database user/app path provides no update/delete endpoint for audit records.

### SRS-023 Hash chain (optional)
If implemented: canonical serialization + previous hash + current record hash + verifier. Documentation states threat model limitations.

### SRS-024 Health
Endpoints expose app/DB/worker status, not secrets/model credentials.

### SRS-025 Local semantic-model ablation
A reproducible training command uses only the benchmark DEV split and produces:
- a versioned local model artifact;
- grouped out-of-fold precision/recall/F1;
- the identical regex-baseline comparator;
- training/config/dataset digests;
- a promotion decision derived from predeclared criteria.

The training and inference implementation must not import or read the frozen holdout path.

### SRS-026 Bounded retrieval-augmented guidance
The AI lab may retrieve only from a versioned, allowlisted local corpus derived from canonical repository documents. Every result includes source path, section, and exact excerpt. Retrieval output:
- is advisory and visibly non-authoritative;
- cannot add or alter a finding, gate state, money value, timestamp, ID, or workflow state;
- makes no network call;
- uses no vector database;
- never invents a card-network rule.

### SRS-027 Ephemeral interactive evaluation
`POST /api/v1/sandbox/evaluate` accepts only bounded plain-text synthetic communication, a raw
reason code, exact-decimal INR strings, refund-ledger completeness, and an allowlisted local refund
state. The backend converts money to integer minor units, runs the selected offline regex extractor,
grounds exact source spans, and invokes the existing deterministic verifier and gate policy. The
response includes explicit boundary flags proving no external API call, persistence, frozen-holdout
access, or Razorpay write. Request payloads do not enter the case database or evaluation artifacts.
An allowlisted `model_outage` simulation raises the same typed transient extraction failure used by
the pipeline and must produce REVIEW with `F_MODEL_UNAVAILABLE`. Contradictory processed/not-
processed statements are unsupported semantic input and must produce REVIEW, never PASS or BLOCK.
Money with more than two decimal places must fail schema validation before a decision is created.

### SRS-028 Reproducible semantic research harness

The repository shall provide a versioned experiment runner that constructs sentence-level labels
from exact ground-truth quotes, preserves scenario-family groups, evaluates deterministic and learned
candidates on identical examples, cross-fits calibration/selection where applicable, records
robustness/OOD slices, measures latency and model size, and saves immutable-by-convention JSON
artifacts with configuration and content hashes. The runner must refuse accidental development-time
holdout access and must never change runtime selection merely because an experiment completed.

## 5. Error taxonomy
- `INGEST_SIGNATURE_INVALID`
- `INGEST_EVENT_ID_MISSING`
- `INGEST_PAYLOAD_INVALID`
- `JOB_TRANSIENT_PROVIDER_ERROR`
- `JOB_PERMANENT_SCHEMA_ERROR`
- `EXTRACTION_UNGROUNDED`
- `EVIDENCE_UNSUPPORTED`
- `STRUCTURED_STATE_INCOMPLETE`
- `DECISION_REVIEW_REQUIRED`
- `SYSTEM_INTERNAL_ERROR`

Material evidence findings use separate `F_*` reason codes.

## 6. Explicit production gaps
- local single-node SQLite;
- synthetic merchant data;
- demo operator identity, not production authentication;
- no real tenant isolation;
- no production DLP;
- no card-network outcome validation;
- no production availability/SLO claim.
- interactive sandbox inputs are synthetic and ephemeral, not authenticated production evidence.

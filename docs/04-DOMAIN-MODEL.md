# 04 — Domain Model

## Razorpay dispute facts used by the MVP

Documented dispute entity fields include:
- `id`
- `payment_id`
- `amount`
- `currency`
- `amount_deducted`
- `reason_code`
- `respond_by`
- `status`
- `phase`
- `created_at`
- `evidence` [SRC-RZP-08]

Documented dispute statuses include `open`, `under_review`, `won`, `lost`, `closed`. [SRC-RZP-08]

Documented dispute phases include `fraud`, `retrieval`, `chargeback`, `pre_arbitration`, `arbitration`. [SRC-RZP-04]

Documented events include:
- `payment.dispute.created`
- `payment.dispute.won`
- `payment.dispute.lost`
- `payment.dispute.closed`
- `payment.dispute.under_review`
- `payment.dispute.action_required` [SRC-RZP-02]

## Local domain entities

### DisputeCase
Canonical local aggregate:
- local case ID;
- Razorpay dispute ID;
- raw reason code;
- local reason profile ID;
- payment ID;
- disputed amount/currency;
- respond-by timestamp;
- Razorpay status/phase;
- processing state;
- current gate decision.

### PaymentSnapshot
Trusted demo record:
- payment ID;
- captured amount/currency;
- captured timestamp;
- refund summary.

### RefundRecord
- refund ID;
- payment ID;
- amount/currency;
- status: `created|pending|processed|failed|cancelled` (local fixture taxonomy);
- created timestamp;
- processed/settled timestamp if known;
- reference/ARN if fixture includes it.

Do not imply these local statuses are Razorpay Refund API statuses unless explicitly mapped.

### EvidenceDocument
- document ID;
- case ID;
- source type;
- media type;
- normalized text;
- SHA-256 of original/normalized bytes as appropriate;
- source system label;
- captured/event time if known;
- ingestion time.

### GroundedClaim
- claim ID;
- document ID;
- allowlisted claim type;
- subject;
- raw value;
- normalized value fields;
- exact source quote;
- deterministic `span_start`, `span_end`;
- extraction model/prompt version;
- grounding status.

### Finding
- finding ID;
- case ID;
- rule code;
- severity;
- decision effect;
- structured evidence refs;
- grounded claim refs;
- explanation template ID.

### GateDecision
- `PASS|REVIEW|BLOCK`;
- reason codes;
- evaluation timestamp;
- engine version;
- source-state version.

### ReviewEvent
Operator-side workflow action:
- evidence inspected;
- repair requested;
- local hold overridden;
- override reason;
- operator demo identity;
- timestamp.

### IngestEvent
Raw webhook metadata:
- `x-razorpay-event-id`;
- event name;
- body hash;
- received time;
- processing status.

### Job
Durable async processing record.

## Reason profile: refund_not_processed_v1

This is a **local profile**, not a claim that Razorpay's raw reason code has this literal value.

Supported resolver inputs:
- customer communication;
- refund ledger;
- payment snapshot;
- optional refund policy.

Supported findings:
- `F_REFUND_CLAIM_NO_LEDGER_MATCH`
- `F_REFUND_AMOUNT_MISMATCH`
- `F_REFUND_CURRENCY_MISMATCH`
- `F_REFUND_REFERENCE_PAYMENT_MISMATCH`
- `F_REFUND_FINAL_STATUS_CONFLICT`
- `F_EVIDENCE_RECOMMENDED_MISSING`
- `F_SOURCE_UNGROUNDED`
- `F_SOURCE_UNSUPPORTED`
- `F_MODEL_UNAVAILABLE`
- `F_STRUCTURED_STATE_INCOMPLETE`

## Important domain correction

**Visa 13.6 = Credit Not Processed. Visa 13.7 = Cancelled Merchandise/Services.** [SRC-RZP-06, SRC-VISA-01]

Therefore shipping-after-cancellation is not a default 13.6 “hard invariant.” Shipping/cancellation context may matter in some cases, but it is not the core MVP conflict.

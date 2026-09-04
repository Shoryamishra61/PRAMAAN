# 14 — API Contracts

All examples are **local application APIs**, except the inbound Razorpay-compatible webhook shape.

## API-001 POST /api/v1/webhooks/razorpay

Headers:
- `X-Razorpay-Signature`: required; case-insensitive HTTP header handling.
- `x-razorpay-event-id`: required for idempotency per Razorpay docs. [SRC-RZP-03]

Body:
Razorpay event JSON. MVP accepts `event == "payment.dispute.created"` for processing.

Behavior:
1. raw-body HMAC verify;
2. parse JSON;
3. validate event;
4. persist event/job atomically;
5. return 2xx.

Response:
```json
{
  "status": "accepted",
  "event_id": "evt_or_header_value",
  "case_id": "case_...",
  "correlation_id": "corr_..."
}
```

Do not guarantee 202 specifically; any successful 2xx is valid. Use 200/202 consistently in implementation.

## API-002 GET /api/v1/cases

Query:
- `gate_status`
- `processing_status`
- `limit`
- `cursor`

Response:
```json
{
  "items": [
    {
      "case_id": "case_001",
      "dispute_id": "disp_...",
      "payment_id": "pay_...",
      "amount_minor": 250000,
      "currency": "INR",
      "respond_by": "2026-09-01T12:00:00Z",
      "raw_reason_code": "raw_value_from_payload",
      "reason_profile": "refund_not_processed_v1",
      "processing_status": "READY",
      "gate_status": "BLOCK",
      "primary_reason_code": "F_REFUND_CLAIM_NO_LEDGER_MATCH"
    }
  ],
  "next_cursor": null
}
```

## API-003 GET /api/v1/cases/{case_id}

Returns:
- normalized dispute/payment/refund snapshots;
- evidence document metadata/text for synthetic demo;
- grounded claims;
- findings;
- current gate decision;
- local workflow state;
- relevant audit events.

Never include secrets/provider raw responses.

## API-004 POST /api/v1/cases/{case_id}/reprocess

Purpose:
re-evaluate after evidence repair.

Requires:
- local demo operator identity;
- idempotency key optional local header.

Returns queued job.

## API-005 POST /api/v1/cases/{case_id}/inspect

Records that the operator inspected a decision-relevant source.

Body:
```json
{
  "source_ref": "claim_123",
  "document_id": "doc_1"
}
```

This is used for BLOCK override evidence-directed forcing.

## API-006 POST /api/v1/cases/{case_id}/override

Preconditions:
- current gate status BLOCK;
- all required conflict sources inspected;
- valid structured reason.

Body:
```json
{
  "reason": "SOURCE_DATA_ERROR",
  "note": "Optional concise explanation"
}
```

Allowed reasons:
- `SOURCE_DATA_ERROR`
- `EVIDENCE_REPAIRED_OUTSIDE_APP`
- `KNOWN_BUSINESS_EXCEPTION`
- `DISAGREE_WITH_RULE`
- `OTHER`

For OTHER, non-empty note required.

Effect:
- append audit/review event;
- set local workflow state `READY_WITH_OVERRIDE`;
- **do not change historical gate decision**;
- **do not call Razorpay**.

## API-007 POST /api/v1/cases/{case_id}/mark-ready

Preconditions:
- gate PASS, or workflow `READY_WITH_OVERRIDE`.

Effect:
local workflow state only:
`READY_FOR_CONTEST`.

Response includes:
```json
{
  "network_write_performed": false
}
```

## API-008 GET /api/v1/evaluation/latest

Loads newest saved evaluation artifact.

Must return:
- synthetic warning;
- dataset/config IDs;
- metrics;
- counts;
- baseline comparison;
- artifact hash.

If no final artifact:
```json
{"status":"NOT_YET_MEASURED"}
```

## API-009 GET /api/v1/health

Returns:
- app status;
- DB status;
- worker status;
- configured inference mode (`live|offline|disabled`);
- no secrets.

## API-010 GET /api/v1/ai-lab/cases/{case_id}

Runs the offline experimental AI lab only over an existing local case evidence document.

Returns:
- lab boundary and promotion status;
- local model/version/config identifiers;
- exact nominated source quotations;
- present feature contributions without probability;
- regex comparator result;
- grouped DEV metric artifact summary;
- retrieval-augmented guidance with exact local citations.

The endpoint accepts no arbitrary upload or free-text prompt, performs no external request, and cannot mutate case, audit, decision, or workflow state.

## API-011 POST /api/v1/sandbox/evaluate

Runs one user-supplied synthetic refund-integrity example through the real local regex extraction,
exact grounding, deterministic verification, and gate path. This is an ephemeral product sandbox,
not signed webhook ingestion and not an evaluation-dataset runner.

Request fields:
- `raw_reason_code`: non-empty string, maximum 128 characters, preserved verbatim;
- `payment_amount_inr`: exact decimal string converted server-side to integer paise;
- `customer_communication`: plain text, 1–10,000 characters;
- `refund_ledger_complete`: boolean;
- `refund_status`: `none|created|pending|processed|failed|cancelled`;
- `refund_amount_inr`: exact decimal string required for any non-`none` refund state;
- `simulation`: optional `none|model_outage`; this is a controlled local fault-injection switch,
  not a provider call or arbitrary prompt.

Response fields include:
- stable request digest and ephemeral run ID;
- preserved raw reason code and fixed `refund_not_processed_v1` profile;
- semantic status and typed claims with exact quote/span/grounding/normalization;
- deterministic findings and PASS/REVIEW/BLOCK;
- normalized payment/refund state in integer minor units;
- closed boundary flags: local/offline, synthetic, ephemeral, not persisted, holdout not accessed,
  no external API call, and no Razorpay write.

Unknown fields, floats, invalid money strings, blank text, and refund-state/amount inconsistencies
return FastAPI's schema-validation 422 response. The endpoint never returns model confidence or a
chargeback-win probability.

## API-012 GET /api/v1/ai-research

Returns the generated `ai-research-study-v1` grouped-DEV artifact and its SHA-256 digest for the
interactive `/ai` research lab. The endpoint rejects an artifact that claims holdout access or an
unknown artifact version. It performs no model inference, recomputation, mutation, or external
request. Model scores are labeled research scores, never customer-facing confidence or gate input.

Contradictory communication and `model_outage` produce REVIEW with explicit finding codes. A
verified full-refund amount mismatch produces BLOCK. Prompt-like instructions remain untrusted
source text and cannot set the gate status.

## Error contract
```json
{
  "error": {
    "code": "EXTRACTION_UNGROUNDED",
    "message": "Evidence claim could not be grounded safely.",
    "correlation_id": "corr_..."
  }
}
```

## Razorpay write APIs
Razorpay documents:
- `POST /v1/disputes/:id/accept`
- `PATCH /v1/disputes/:id/contest` [SRC-RZP-04, SRC-RZP-05]

They are context/reference only. MVP contains no client method invoking them.

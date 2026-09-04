# Implementation Plan

## Strategy
Build evidence in this order: **domain truth → deterministic verifier → grounded extraction → end-to-end case → evaluation → UI → hardening → pitch**.

## Phase 0 — Repository skeleton
Deliver:
- backend/frontend/test directories
- configuration loader
- SQLite migration/init
- Makefile or task runner
- CI baseline

Exit: fresh clone runs a health endpoint and test suite.

## Phase 1 — Domain + deterministic vertical slice
Implement:
- dispute/payment/refund/evidence schema
- reason profile `refund_not_processed_v1`
- deterministic evidence-state checks
- gate reason codes
- PASS/REVIEW/BLOCK policy
- seeded PASS/REVIEW/BLOCK fixtures

Exit: no AI; three cases are classified correctly and explanations are deterministic.

## Phase 2 — Razorpay-compatible ingestion
Implement:
- `payment.dispute.created` sample payload adapter
- raw-body HMAC verification
- `x-razorpay-event-id` idempotency
- event persistence + durable job record
- 2xx response under 5 seconds
- replay tests

Exit: signed webhook replay creates one case/job even when delivered repeatedly.

## Phase 3 — Grounded semantic extraction
Implement:
- `SemanticExtractor` interface
- provider adapter
- strict claim schema
- exact quotation return
- deterministic span resolver
- REVIEW fallback on schema/grounding/provider failure
- regex baseline extractor

Exit: representative communications produce grounded typed refund claims.

## Phase 4 — Cross-source integrity engine
Implement:
- grounded communication claim ↔ structured refund ledger checks
- amount/status/date comparisons
- materiality/severity policy
- evidence-gap REVIEW rules
- reason explanation payloads

Exit: semantic claim is useful without a second LLM decision stage.

## Phase 5 — Benchmark/evaluation
Implement/freeze benchmark v1:
- 120 dev cases from development scenario families
- 60 holdout cases from unseen scenario families
- manifest + hashes
- regex baseline
- single-shot LLM baseline (optional if cost/time permits)
- proposed extractor + deterministic verifier
- result artifact schema
- precision/recall/F1 + operational false-PASS/false-BLOCK/review rate
- bootstrap interval with explicit small-synthetic-dataset caveat

Exit: dev evaluation works; holdout is run only at final evaluation checkpoint.

## Phase 6 — Analyst UI
Implement:
- queue
- case workspace
- evidence viewer + grounded highlight
- conflict card
- REVIEW recovery checklist
- BLOCK local hold + structured override
- evaluation page reading result artifacts
- responsive and keyboard-safe behavior

Exit: 2-minute golden demo.

## Phase 7 — Security/reliability
Implement:
- safe logging
- prompt-injection tests
- process-restart job recovery
- audit events
- optional tamper-evident hash chain
- dependency scan and negative tests

## Phase 8 — Submission hardening
Run:
- fresh clone
- complete test suite
- final holdout once config is frozen
- generate `results/final/*`
- README from actual results
- record real failure narrative
- rehearse hostile panel questions.

Do not start optional NLI, PDF/OCR, auth, live Razorpay write actions, or multi-reason-code work until Phase 8 is green.

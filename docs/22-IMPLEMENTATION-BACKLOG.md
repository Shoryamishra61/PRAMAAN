# 22 — Implementation Backlog by Dependency

## Epic E1 — Domain core
- E1.1 Pydantic/domain models
- E1.2 SQLite migrations
- E1.3 `refund_not_processed_v1` reason profile
- E1.4 deterministic verifier
- E1.5 decision policy
- E1.6 three smoke cases

Gate: PASS/REVIEW/BLOCK works without AI.

## Epic E2 — Razorpay-compatible ingest
- E2.1 raw-byte HMAC
- E2.2 event-name parser
- E2.3 `x-razorpay-event-id` unique persistence
- E2.4 case adapter
- E2.5 durable job write
- E2.6 duplicate/restart tests

Gate: signed replay → durable case/job within 5s.

## Epic E3 — Semantic extraction
- E3.1 canonical text normalization
- E3.2 extractor protocol
- E3.3 strict schema
- E3.4 provider adapter
- E3.5 exact quote grounder
- E3.6 offline replay
- E3.7 cache
- E3.8 failure → REVIEW

Gate: no ungrounded claim can affect decision.

## Epic E4 — Integrity resolver
- E4.1 communication claim ↔ refund ledger lookup
- E4.2 amount/currency/payment mismatch
- E4.3 final vs pending logic
- E4.4 explanation templates
- E4.5 evidence completeness

Gate: main BLOCK case is deterministic after grounded claim extraction.

## Epic E5 — Benchmark/evaluation
- E5.1 generator
- E5.2 hard negatives
- E5.3 DEV/HOLDOUT family partition
- E5.4 freeze manifests
- E5.5 regex baseline
- E5.6 proposed evaluator
- E5.7 metrics + artifacts
- E5.8 cost sensitivity

Gate: no hard-coded dashboard metric.

## Epic E6 — UI
- E6.1 queue
- E6.2 workspace
- E6.3 evidence viewer
- E6.4 finding card
- E6.5 REVIEW panel
- E6.6 BLOCK override
- E6.7 evaluation
- E6.8 audit
- E6.9 accessibility

## Epic E7 — reliability/security
- E7.1 safe logs
- E7.2 provider outage
- E7.3 worker restart
- E7.4 injection tests
- E7.5 secret checks
- E7.6 optional hash chain

## Epic E8 — submission
- E8.1 final holdout
- E8.2 error analysis
- E8.3 README generated from results
- E8.4 failure narrative
- E8.5 demo fixtures
- E8.6 video/panel script

## Cut order if deadline pressure
Cut in this order:
1. optional hash chain;
2. audit dashboard polish;
3. human study;
4. single-shot LLM baseline;
5. optional NLI experiment;
6. live model demo (keep offline replay + verified evaluation).

Never cut:
- deterministic core;
- grounding;
- held-out evaluation;
- safe REVIEW fallback;
- main evidence comparison UI.

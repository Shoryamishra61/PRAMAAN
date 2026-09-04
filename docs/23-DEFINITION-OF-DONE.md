# 23 — Definition of Done & Release Checklist

## Feature DoD
A feature is done only when:
- requirement ID exists;
- implementation exists;
- happy-path test exists;
- relevant failure test exists;
- traceability row exists;
- docs/copy match actual behavior.

## System DoD

### Domain
- [x] `refund_not_processed_v1` is the only evaluated reason family.
- [x] Visa 13.6/13.7 language is correct.
- [x] Raw reason code preserved.

### Ingestion
- [x] correct Razorpay event name.
- [x] raw HMAC validation.
- [x] event ID idempotency.
- [x] durable job before ACK.
- [x] response measured <5s locally.

### Decision
- [x] no direct network action.
- [x] PASS/REVIEW/BLOCK canonical semantics.
- [x] no technical error becomes BLOCK.
- [x] model outage becomes REVIEW.
- [x] grounded claim required for semantic BLOCK.

### Evaluation
- [x] benchmark version frozen.
- [x] family-level holdout.
- [x] baseline implemented.
- [x] final metrics computed and saved.
- [x] UI uses artifact.
- [x] no unmeasured claims.
- [x] synthetic limitation prominent.

### UX
- [x] exact source navigation works.
- [x] BLOCK comparison readable.
- [x] structured override works.
- [x] no 50-character ritual.
- [x] keyboard golden path.
- [x] status not color-only.

### Security/reliability
- [x] credential-pattern scan clean; no Git-history claim because Git metadata is unavailable.
- [x] prompt injection cannot cause action.
- [x] worker restart recovery.
- [x] logs contain no raw evidence.
- [x] parameterized SQL.
- [x] optional audit chain described accurately as unimplemented/tamper-evident, not immutable.

### Submission
- [x] isolated clean-source setup/full-gate/demo reproduced; no Git-clone provenance claimed.
- [x] package hygiene and secret scan clean; public repository state is not claimed because this workspace has no Git metadata.
- [x] README working-vs-mocked.
- [x] genuine failure story.
- [x] 2-minute demo stable offline.
- [x] 5-minute pitch has regression-validated 05:00 allocation; no recorded video claimed.
- [x] panel script/guardrails do not overclaim competitors, data, legal status, or ROI.

## Stop-ship defects
- fabricated metric;
- wrong Razorpay event;
- auto contest/accept;
- holdout leakage;
- model failure → PASS;
- source claim not groundable;
- README says “production-grade/PCI compliant/immutable” without proof;
- Visa 13.6 mislabeled;
- hard-coded evaluation card not sourced from artifact.

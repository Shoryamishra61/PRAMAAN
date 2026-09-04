# 12 — Decision Policy & Deterministic Invariants

## Policy philosophy
The model extracts language. Code decides whether evidence is sufficiently grounded and whether structured facts conflict.

## Signal classes

### A. Technical validity signals
- webhook authenticated;
- event ID present/unique;
- schemas valid;
- money/timestamps parse;
- source records accessible.

Failure here is an ingestion/processing error or REVIEW—not an evidence BLOCK.

### B. Evidence completeness signals
Razorpay publishes suggested evidence categories for refund-not-processed disputes. Missing suggested evidence produces REVIEW in v1. [SRC-RZP-06]

### C. Hard structured invariants
Only objective relations:
- amount > 0;
- refund amount ≥ 0;
- refund amount not greater than payment amount unless fixture explicitly models an exceptional adjustment;
- currencies must match for direct money comparison;
- refund payment_id must match case payment_id;
- duplicate IDs handled deterministically;
- timestamps are valid/UTC-aware before comparison.

### D. Grounded semantic-to-structured conflicts
May cause BLOCK when:
1. the semantic claim is allowlisted;
2. exact source quote is uniquely grounded;
3. structured resolver source is marked complete/trusted in demo;
4. conflict rule is objective;
5. conflict is material for refund-not-processed evidence.

## Decision precedence

### REVIEW first for unverifiability
If the system lacks enough trustworthy information to establish a material conflict:
- REVIEW.

### BLOCK for verified material conflict
If a material conflict is deterministically established:
- BLOCK.

### PASS otherwise
Only if required-to-evaluate inputs are present and all supported checks complete.

This avoids “deterministic error = BLOCK” confusion.

## Core policy rules

### POL-001 Scope
Unsupported reason family → REVIEW `OUT_OF_SCOPE`.

### POL-002 Ledger completeness
If refund ledger snapshot is not explicitly marked complete for the relevant payment/window → REVIEW.

### POL-003 Evidence communication absent
If customer communication needed to evaluate claim-based conflicts is absent → REVIEW.

### POL-004 Grounding
Any decision-relevant semantic claim not uniquely grounded → REVIEW.

### POL-005 Claimed processed refund / no match
If grounded communication asserts refund **was processed**, ledger is complete, and no corresponding refund exists → BLOCK.

### POL-006 Full amount mismatch
If grounded communication asserts a processed/approved full refund amount X and final processed refund total is Y != X → BLOCK if states are final; otherwise REVIEW.

### POL-007 Currency mismatch
If grounded processed/approved refund claim includes currency and matching final refund uses incompatible currency → BLOCK.

### POL-008 Wrong payment linkage
If final refund evidence references another payment ID than dispute payment → BLOCK.

### POL-009 Pending refund
If a matching refund is pending/created but not final at snapshot → REVIEW; do not say contradiction.

### POL-010 Promise vs processing
A future promise (“we will refund”) plus no current refund is **not automatically a contradiction** until the stated commitment window has unambiguously elapsed and complete state is available. If timing cannot be safely resolved → REVIEW.

### POL-011 Customer assertion vs merchant state
A customer saying “you never refunded me” while ledger says refund processed is not automatically a BLOCK against the merchant packet; it is a disputed claim requiring contextual review. Default REVIEW unless reason profile defines a verified resolver.

### POL-012 Policy interpretation
Conflicts involving prose policy interpretation default REVIEW unless converted to explicit structured merchant policy rules with verified applicability.

## Gate output
```json
{
  "status": "BLOCK",
  "primary_reason_code": "F_REFUND_CLAIM_NO_LEDGER_MATCH",
  "findings": ["..."],
  "scope": "refund_not_processed_v1",
  "disclaimer": "Local evidence integrity hold; not a dispute outcome prediction."
}
```

## Override
Override does not erase finding. It creates:
- original BLOCK;
- operator inspected sources;
- override reason;
- local readiness transition.

History remains visible.

## Deadlines
`respond_by` is used for queue urgency only.
Deadline proximity never relaxes safety or changes conflict logic.

No hardcoded 24h threshold is necessary; UI may calculate configurable urgency bands.

## Cost sensitivity
Decision threshold magic numbers are removed because default policy has no probabilistic threshold. Future probabilistic classifier threshold requires explicit validation.

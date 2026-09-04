# 10 — Data, Ontology & Synthetic Benchmark Specification

## Objective
Provide a reproducible, non-leaky benchmark sufficient to satisfy Track 02's held-out precision/recall requirement while being explicit that synthetic data does not establish production prevalence or chargeback outcomes.

## Dataset v1

**ID:** `DIG-RNP-SYN-v1`

Recommended:
- 180 case bundles total;
- 120 DEV;
- 60 HOLDOUT;
- class-balanced for diagnostic clarity, not prevalence.

### Split by scenario family, not date
Original reports proposed a chronological split with synthetic August dates. That creates no genuine distribution shift if generation logic is otherwise identical.

Instead:
- DEV uses one set of scenario templates, phrasing patterns and combinations;
- HOLDOUT uses unseen scenario families/templates, lexical structures and distractor layouts.

The holdout manifest is frozen before prompt/config finalization.

## Case bundle structure

```text
case/
  manifest.json
  razorpay_event.json
  payment_snapshot.json
  refunds.json
  evidence/
    customer_communication.txt
    refund_policy.txt?       # optional
  ground_truth/
    claims.json
    findings.json
    gate_label.json
```

`ground_truth/` is never provided to runtime system.

## Ground-truth design

Because the benchmark is synthetic, generation code knows the truth. To avoid trivial circularity:
- runtime detector cannot read generator metadata;
- scenario template IDs are hidden from runtime;
- holdout scenario families differ structurally from dev families;
- exact text variants and distractors are generated independently of detector rules;
- manually inspect a sample from every family before freezing;
- challenge cases include cases where obvious keywords appear but do **not** imply a conflict.

## Claim ontology
Allowlisted:
- refund_requested
- refund_promised
- refund_approved
- refund_claimed_processed
- refund_denied
- refund_amount
- refund_timing_commitment
- return_claimed
- return_not_received_claim
- policy_condition_reference

Ground truth includes:
- exact quote;
- start/end;
- normalized values where unambiguous.

## Gate label generation

### PASS families
Examples:
- communication says refund processed; matching processed refund exists;
- communication says refund denied; ledger has no refund and policy evidence is consistent;
- customer requested refund but merchant never promised/processed it; no unsupported conflict within profile.

### REVIEW families
Examples:
- refund ledger export marked incomplete;
- source quote ambiguous/duplicated;
- unsupported language;
- policy text requires interpretation;
- refund pending at snapshot;
- recommended evidence absent;
- customer communication missing.

### BLOCK families
Only grounded material conflicts:
- claimed-processed refund with complete ledger no-match;
- full-refund processed claim vs final partial refund;
- refund currency mismatch;
- refund linked to different payment;
- final refund status contradicts grounded “processed” claim.

Do not generate BLOCK merely from “shipping after cancellation.”

## Hard negatives
Required:
- “We will review your refund” ≠ refund promised/processed;
- “Refund request received” ≠ refund approved;
- customer claims refund “should have been processed” but merchant did not say it was;
- mention of ₹2,500 in invoice unrelated to refund;
- partial refund explicitly communicated as partial;
- multiple refunds summing to promised full amount;
- refund processed after email but before dispute snapshot;
- negation: “we have not processed a refund.”

## Adversarial/OOD cases
Include:
- prompt injection text;
- malformed model-target phrasing;
- repeated identical quote causing span ambiguity;
- non-English text → REVIEW in v1;
- extremely long irrelevant boilerplate;
- contradictory statements within one communication;
- missing structured ledger;
- duplicate webhook.

## Dataset versioning
Commit:
- generator version;
- seed;
- scenario-family list;
- `manifest.sha256`;
- holdout case hashes.

Any change to holdout content/label = new dataset version and invalidates old final metrics.

## Freeze process
1. generate v1;
2. run schema checks;
3. manually inspect representative cases;
4. fix generator if needed;
5. regenerate;
6. write final manifests;
7. record SHA-256;
8. set `FROZEN=true`;
9. coding agent may not read ground-truth holdout during development.

## Limitations to publish
- synthetic language and ledger patterns;
- balanced class distribution;
- no issuer decision outcomes;
- no production merchant prevalence;
- no proof of chargeback win-rate lift;
- LLM provider behavior can change unless model/version pinned.

## Optional challenge set
If time permits, manually author 15–20 challenge cases without using generator templates. Keep separate from dev; report results separately because sample is small.

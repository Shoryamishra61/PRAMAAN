# FECL-Bench v4 — Certified Sequential Evidence Verification protocol

Status: preregistered before benchmark generation and all v4 model fitting  
Date: 2026-09-01  
Authority: research-only until frozen gates pass; deterministic product policy remains authoritative

## Hypotheses

- H1: learned grounded semantic relations improve unseen-language slices over literal extraction.
- H2: explicit relational XGBoost outperforms semantic-only classification on exact financial
  boundaries.
- H3: formal proof compilation reduces unsafe false PASS and produces faithful contradiction
  certificates without learned overrides.
- H4: calibration-only selective control trades coverage for lower value-weighted false-PASS risk.
- H5: cost-aware acquisition resolves more REVIEW cases per evidence cost than static acquisition.
- H6: a learned acquisition policy is unnecessary unless it improves over the strongest non-learned
  policy without increasing false-PASS value.

## Dataset

Dataset ID: `DIG-FECL-BENCH-v4`. All records are synthetic and do not represent production prevalence.

| Split | Cases | Pair groups | Purpose |
|---|---:|---:|---|
| TRAIN | 1,200 | 600 | fit supervised models |
| DEV | 320 | 160 | architecture, hyperparameters, acquisition selection |
| CALIBRATION | 320 | 160 | probability calibration, CRC threshold, OOD reference |
| TEST | 480 | 240 | one frozen final evaluation |
| OOD | 160 | n/a | safety rejection; no forced in-distribution financial label |

Every in-distribution record contains the complete hidden truth plus an initial partial evidence
view. Counterfactual pair members remain in one split and differ in one financially causal fact.

### Split isolation

- TRAIN families: `formal_email`, `support_chat`, `portal_note`, `refund_ops`, `hinglish_basic`.
- DEV families: `indirect_narrative`, `passive_record`, `indian_english_ops`.
- CALIBRATION families: `terse_reconciliation`, `conditional_promise`.
- TEST families: `hinglish_unseen`, `cross_document`, `temporal_implicit`, `ocr_holdout`,
  `relation_composition`.
- Entity prefixes, pair IDs and template-family IDs are split-specific.
- Template IDs and family IDs may not cross splits.
- No TEST/OOD read is permitted by training, DEV tournament, calibration or freeze preparation.

### Required phenomena

Explicit/implicit refund claims, Hinglish, negation, one-rupee boundaries, partial and cumulative
refunds, currency, wrong RRN, wrong ARN/UTR, refund reference, refund-parent payment, matching amount
for the wrong order, chronology, not-yet-due and overdue promises, stale state, source disagreement,
policy exceptions, irrelevant matching documents, duplication, OCR corruption, inert prompt
injection, unseen relation composition and missing evidence.

### Sequential contract

Each case records authoritative state, full evidence inventory, initial visible evidence, hidden
evidence, fixed acquisition costs, atomic claims, relations, exact spans, hard constraints, known MCC
for contradictory cases, and an oracle evidence trajectory. Acquisitions never mutate authoritative
history; they reveal an existing synthetic artifact.

## Candidate ladder

| Level | System | Question |
|---:|---|---|
| 0 | literal deterministic rules | how far exact extraction/checks go |
| 1 | word+character TF-IDF logistic | whether shallow language generalizes |
| 2 | pinned transformer semantic classifier | whether semantics alone solves FECL |
| 3 | deterministic relational XGBoost | strength of explicit financial boundaries |
| 4 | grounded transformer relations + XGBoost | incremental unseen-language lift |
| 5 | frozen ESRAN v3 reference | whether prior graph hypothesis transfers |
| 6 | best semantic/structured model + proof compiler | value of formal contradiction authority |
| 7 | level 6 + CRC/selective controller | risk/coverage tradeoff |
| 8 | CARVE + selected acquisition policy | sequential evidence efficiency |

The ESRAN row is a historical frozen reference and cannot be retrained or directly merged with v4
metrics. If a reproducible v4 adapter cannot apply it without changing the architecture, report it
as `HISTORICAL_NOT_COMPARABLE`.

## Fixed model policy

- Generator/model seed: `20260911`; stochastic seeds `20260911`–`20260915` where used.
- TF-IDF: word 1–2 grams plus character 3–5 grams; class-weighted logistic regression.
- Transformer: pinned `sentence-transformers/all-MiniLM-L6-v2`, revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; frozen embedding plus supervised logistic head.
- XGBoost: maximum depth 3, 240 estimators, learning rate 0.04, subsample 0.85, column sample 0.9,
  one thread, false-PASS class weight selected on DEV from `{2,4,8}`.
- Numeric/identifier/date parsing and arithmetic remain deterministic.
- Z3 tracked constraints and deletion-minimized unsat cores implement formal MCCs.
- No LLM and no unrestricted retrieval participates in evaluation.

## Costs and definitions

All money values are synthetic INR. `₹ false-PASS exposure` is the sum of disputed values for
contradictory cases incorrectly passed; it is not observed merchant loss or savings.

- False-PASS cost: full synthetic disputed value, capped at ₹50,000 for risk calibration.
- False-BLOCK cost proxy: `min(₹500, 0.05 × disputed value)`.
- REVIEW cost proxy: ₹100 per unresolved case.
- Evidence acquisition costs: authenticated entity fetch 1, reference fetch 2, local record 4,
  customer communication 12, refund confirmation 16, bank statement 25, policy 6.

Expected Merchant Loss is the sum of those preregistered synthetic proxies plus acquisition cost.

## Metrics

Precision, recall, F1, macro-F1, PR-AUC, confusion counts, false-PASS count/rate/exposure,
false-BLOCK count/rate/cost, autonomous coverage, REVIEW rate, expected loss, Brier, NLL, ECE,
risk-coverage, relation micro/macro F1, exact-span grounding, MCC exact/node/fact F1,
counterfactual-repair accuracy, OOD REVIEW rate and OOD false PASS.

Sequential metrics: acquisitions/resolved case, acquisition cost, fraction of initial REVIEW cases
resolved, decision-risk reduction per acquisition, total cost and trajectory exact match. Report
latency, serialized model bytes and peak resident memory where measurable.

Statistics use 2,000 counterfactual-pair bootstrap resamples, exact paired McNemar tests, five-seed
mean/standard deviation for stochastic candidates and Holm correction across the preregistered
primary comparisons. Intervals describe only this synthetic generator.

## DEV and CALIBRATION rules

DEV may choose class weight, probability calibration family, acquisition policy and nonfinancial
hyperparameters. CALIBRATION fits probability calibration, CRC PASS threshold, Mondrian diagnostic
strata and OOD distance threshold. CALIBRATION cannot select architecture. TEST cannot select
anything.

## Promotion gates

1. **Semantic lift:** transformer relation macro-F1 exceeds TF-IDF relation macro-F1 by at least
   `0.02` on DEV and exact-span grounding is at least `0.98`.
2. **Hybrid lift:** semantic-relation XGBoost exceeds deterministic XGBoost by `0.02` F1 on the
   predefined semantic-shift DEV slice or reduces false-PASS exposure by 10% at no lower coverage.
3. **Formal proof:** zero hard-invariant overrides; MCC exact match at least `0.95`; solver failures
   all REVIEW.
4. **Risk control:** CALIBRATION selects a threshold satisfying corrected empirical normalized risk
   `<=0.025`; TEST reports empirical risk and at least `0.35` autonomous coverage. No TEST guarantee.
5. **Acquisition:** selected policy reduces initial REVIEW rate by at least 20% and has lower total
   synthetic cost than immediate REVIEW and acquire-all without increasing false-PASS exposure.
6. **Learned policy:** retained only if total cost is at least 5% lower than the best simple policy
   across three or more seeds with no false-PASS exposure increase.
7. **OOD:** at least 95% OOD routes to REVIEW and OOD false PASS is zero.
8. **Final CARVE:** false-PASS exposure is at most 80% of the strongest static comparator at matched
   or higher autonomous coverage; every artifact/hash/prediction is saved.

A failed component is rejected. Final CARVE may therefore be proof compiler + XGBoost + CRC + a
simple acquisition policy. No architecture name creates an exception.

## Freeze and one-shot TEST

Before TEST, hash protocol, method, generator, runner, manifest, TRAIN/DEV/CALIBRATION/TEST/OOD,
feature schema, model files, calibration artifact and DEV results into `fecl-v4-freeze.json`.
The TEST command requires explicit confirmation, verifies every hash, refuses an existing receipt,
then writes `fecl-v4-test-receipt.json` and the TEST result. Any invalidating bug creates v4.1; it
does not silently overwrite v4.


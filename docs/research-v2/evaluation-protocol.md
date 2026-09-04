# Evaluation protocol

## Pre-registration

- **DESIGN DECISION:** Before each experiment, save hypothesis, data version/hash, split manifest, candidate config, seeds, metrics, cost assumptions, promotion/kill gates and maximum tuning budget.
- **DESIGN DECISION:** The frozen v1 holdout remains archival evidence and is never used to tune research-v2.

## Evaluation ladder

1. **DESIGN DECISION:** unit: schema, exact offsets, minor-unit money, UTC time, ID matching.
2. **DESIGN DECISION:** component DEV: grouped OOF extraction/relation metrics.
3. **DESIGN DECISION:** case DEV: end-to-end findings and decisions through deterministic policy.
4. **DESIGN DECISION:** stress/OOD: adversarial language, missing/duplicated evidence, malformed input, prompt injection and outage.
5. **DESIGN DECISION:** frozen holdout: one final run after all configs and thresholds freeze.
6. **DESIGN DECISION:** shadow replay: historical point-in-time cases with no user-visible authority.

## Metrics

- **DESIGN DECISION:** claim/span: precision, recall, F1, exact match, overlap F1, unique-grounding rate.
- **DESIGN DECISION:** relation/case: macro-F1, PR-AUC where meaningful, confusion matrix, false PASS, false BLOCK and REVIEW coverage.
- **DESIGN DECISION:** uncertainty: Brier, NLL, ECE with sensitivity, risk-coverage/AURC, empirical conformal coverage and critical-risk bound when valid.
- **DESIGN DECISION:** finance: expected loss under a disclosed cost grid and break-even sensitivity.
- **DESIGN DECISION:** systems: p50/p95/p99 warm and cold latency, peak memory, artifact/model size and cost per case.

## Statistics

- **DESIGN DECISION:** paired bootstrap by case/group for metric and expected-loss deltas with 95% intervals.
- **DESIGN DECISION:** report prevalence and confusion counts beside rates.
- **DESIGN DECISION:** use multiple seeds for learned training; report median and worst seed.
- **DESIGN DECISION:** compare thresholds over a predeclared grid and show stability, not a single optimum.
- **DESIGN DECISION:** when sample size is too small for a useful bound, label the result `UNDERPOWERED`.

## Robustness slices

- **DESIGN DECISION:** unseen template/merchant, later time, non-native English, amount/reference/time qualification, negation, approval-vs-completion, partial/full, duplicated quote, long evidence, incomplete ledger, contradictory documents, prompt injection, malformed encoding and model outage.

## Artifact contract

- **DESIGN DECISION:** Every run saves config, environment lock, hashes, per-case predictions, exact spans, component outputs, curves, confusion counts, latency samples, errors and promotion result.
- **DESIGN DECISION:** The `/evaluation` and `/ai` surfaces load only these generated artifacts; missing artifacts render `NOT RUN`, never default metrics.


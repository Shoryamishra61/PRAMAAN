# Risk-control study

## Decision loss

- **ASSUMPTION:** Let `C_FPASS` be the cost of allowing an internally invalid packet, `C_FBLOCK` the cost of delaying a valid packet, and `C_REVIEW` the analyst cost of abstention.

```text
ExpectedLoss = C_FPASS * false_PASS
             + C_FBLOCK * false_BLOCK
             + C_REVIEW * REVIEW
```

- **DESIGN DECISION:** Cost values are scenario inputs shown separately; no rupee savings claim is made without merchant data.
- **DESIGN DECISION:** `C_FPASS > C_REVIEW` and `C_FBLOCK > C_REVIEW` are plausible but remain assumptions until merchant research quantifies them.

## Layered controller

1. **DESIGN DECISION:** schema/grounding/completeness guard: invalid or ambiguous input -> REVIEW.
2. **DESIGN DECISION:** OOD guard: unfamiliar language, document type or representation -> REVIEW.
3. **DESIGN DECISION:** disagreement guard: material model disagreement -> REVIEW.
4. **DESIGN DECISION:** calibrated selector: accept a learned claim only at a predeclared operating point.
5. **DESIGN DECISION:** deterministic policy: grounded material conflict with complete authoritative state -> BLOCK; unresolved uncertainty -> REVIEW; otherwise PASS.

## Techniques and validity

- **RESEARCH RESULT:** Temperature/Platt/isotonic scaling can improve probability calibration on suitable validation data, but the v1 study showed ECE improvement can accompany worse Brier, NLL and risk-coverage.
- **RESEARCH RESULT:** SelectiveNet formalizes joint prediction/rejection and risk-coverage, but its reported results do not create a guarantee for this dataset.
- **RESEARCH RESULT:** CRC controls expected monotone loss under its sampling/exchangeability conditions and an untouched calibration procedure; distribution shift and adaptive calibration invalidate naive claims.
- **RESEARCH RESULT:** Energy scoring is a comparative OOD method for classifier logits; nearest-distance OOD on 16 constructed v1 cases is only a diagnostic.

## Required plots

- **DESIGN DECISION:** PR and cost curves by threshold.
- **DESIGN DECISION:** reliability diagram plus Brier, NLL and ECE with bin sensitivity.
- **DESIGN DECISION:** risk-coverage curves for all errors, false PASS and false BLOCK separately.
- **DESIGN DECISION:** Pareto frontier over precision, recall, coverage, review load, expected loss, latency and cost.
- **DESIGN DECISION:** OOD ROC/PR plus in-domain false-reject rate.

## Promotion rule

- **DESIGN DECISION:** A controller is promoted only if its selected operating point is fixed before holdout, its critical-error upper uncertainty bound satisfies the business limit, and its coverage is operationally useful.
- **DESIGN DECISION:** Otherwise the UI must say `EMPIRICAL ABSTENTION ONLY — NO FORMAL RISK GUARANTEE`.


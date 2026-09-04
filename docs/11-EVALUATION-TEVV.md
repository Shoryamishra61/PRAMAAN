# 11 — Evaluation & TEVV Specification

## Evaluation question

Does grounded semantic extraction plus deterministic cross-source verification detect material refund-evidence conflicts better than a strong simple baseline, while safely abstaining when verification is incomplete?

## Unit of evaluation
A **case bundle**, not a document.

## Primary Track 02 metrics

### Material-conflict precision
Among cases the system BLOCKs for a material conflict, how many are ground-truth BLOCK cases?

### Material-conflict recall
Among ground-truth BLOCK cases, how many did the system correctly BLOCK?

### F1
Harmonic mean of the above.

Report numerator/denominator counts beside percentages.

## Operational gate metrics
- `false_pass_block_cases`: true BLOCK predicted PASS;
- `false_block_nonblock_cases`: true PASS/REVIEW predicted BLOCK;
- `review_rate`;
- `auto_decision_coverage = PASS + BLOCK / total`;
- 3-class macro-F1 as secondary summary;
- confusion matrix.

Avoid calling these nonstandard rates FPR/FNR without defining them.

## Claim extraction metrics
- claim-type micro/macro precision/recall/F1;
- exact grounding rate;
- normalized amount/reference/date correctness.

## Baselines

### B0 — Strong deterministic/regex baseline
- structured amount/currency/refund checks;
- exact keyword/regex patterns for refund status;
- same decision policy.

### B1 — Proposed
- grounded model extractor;
- same deterministic resolver/policy.

### B2 — Single-shot LLM judge (optional research baseline)
- receives same supported case input;
- outputs case label;
- never used in product.

This baseline can show why grounding/decomposition matters, but must not be intentionally weakened.

## Ablations
Run on DEV:
- remove grounding validation;
- remove semantic extraction (B0);
- optional NLI enabled/disabled;
- remove evidence completeness → quantify unsafe effect.

Holdout ablations only if predeclared before final run.

## False-positive cost

Razorpay requires honest false-positive cost. Do not invent a universal fee.

Use a **parameterized sensitivity analysis**:
- `C_false_block`: opportunity cost of unnecessarily holding/escalating a clean case;
- `C_false_pass`: cost proxy for allowing a materially inconsistent case through;
- `C_review`: analyst review cost.

Show:
`TotalCost = n_false_pass*C_false_pass + n_false_block*C_false_block + n_review*C_review`

Provide 3 clearly labeled illustrative parameter sets:
- review-cheap;
- balanced;
- false-pass-expensive.

Do not claim real INR savings unless real merchant cost inputs are supplied.

## Confidence/uncertainty reporting
With a 60-case synthetic holdout, report:
- exact counts;
- bootstrap confidence intervals for F1 if implemented;
- explicit caveat that intervals reflect this synthetic sample, not production population.

Do not publish a fabricated `±0.04`.

## Final evaluation protocol
1. freeze code commit;
2. freeze prompt/schema/model config;
3. verify holdout manifest hash;
4. run final holdout command once for submission result;
5. save per-case predictions;
6. compute metrics from predictions;
7. generate UI artifact;
8. manually inspect all errors;
9. do not retune after seeing holdout without creating a new benchmark/version.

If a bug invalidates the run, document the bug, fix it, version the evaluation, and disclose rerun rationale.

## Slice analysis
Report at minimum:
- claimed processed refund/no ledger;
- partial/full amount;
- negation/hard negative;
- missing evidence;
- provider/grounding failure;
- prompt injection;
- unsupported/OOD.

Slices with tiny N show counts, not sweeping percentages.

## Human-factors TEVV
Optional and formative.

If performed:
- use incorrect and correct system findings;
- compare warning-only vs evidence-inspection override;
- measure final correct decision and decision time;
- report participant N and task construction;
- do not generalize small convenience sample.

NASA-TLX may be collected but is optional and should not displace product validation.

## Evaluation dashboard rules
Dashboard is read-only from result artifacts.
Must show:
- synthetic dataset badge;
- dataset/version/hash;
- model/prompt/config;
- run timestamp/commit;
- metrics + counts;
- confusion matrix;
- error slices;
- baseline delta;
- parameterized cost table.

No hard-coded “savings”.

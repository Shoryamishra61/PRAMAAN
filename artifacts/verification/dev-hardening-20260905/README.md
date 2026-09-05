# DEV hardening evidence — 2026-09-05

These runs use the 120-case synthetic development split. They are debugging evidence, not a
new held-out result. The frozen August artifact and HOLDOUT data remain unchanged.

| Gate metric | Before repairs | After repairs |
| --- | ---: | ---: |
| BLOCK precision | 40/50 (0.8) | 40/40 (1.0) |
| BLOCK recall | 40/40 (1.0) | 40/40 (1.0) |
| False BLOCK / false PASS | 10 / 0 | 0 / 0 |
| REVIEW | 40/120 | 40/120 |

Before: `dev-hardening-20260905-revision.json`. After: `dev-refund-repair-20260905-final.json`.
Each result has a SHA-256 sidecar and per-case predictions. Do not substitute DEV numbers for
the historical HOLDOUT figures on the submission. Use the committed source revision with the
artifact SHA-256 sidecars when reproducing these results.

Two of the false BLOCKs came from sentence segmentation truncating decimal amounts. Eight
came from the aggregate-refund equality branch falling through to "no ledger match". Repairs
preserve exact source quotes and do not let aggregate totals satisfy a specific refund reference.
Malformed grouping, negative values, and unsupported precision remain unresolved.

Gate labels all match after repair, but extraction still emits 16 extra refund-amount claims
against this dataset's annotations (precision 56/72). This distinction must remain visible.
False-positive cost here is an illustrative unit-weighted scenario, not rupees or observed
merchant savings; zero DEV false BLOCK cost does not estimate deployment cost.

`local-semantic-eval.json` is a separate 5-fold scenario-family-grouped communication
classification experiment. Candidate precision 0.813953, recall 0.972222, F1 0.886076;
TP 70, FP 16, FN 2, TN 32. The regex comparator scores 1.0 on this protocol. Candidate remains
NOT_PROMOTED. `local-semantic.joblib` is its local trusted training output, not an upload format.
The PyTorch smoke test independently exercises forward/backward, optimizer update, checkpoint
save/load and exact reload predictions; it does not establish semantic generalization.

Reproduce from the repository root (DEV only):

```powershell
.venv/Scripts/python.exe scripts/evaluate_benchmark.py --dataset data/benchmark/v1 --split dev --run-id local-recheck --code-commit YOUR_REVISION --output artifacts/local-recheck
.venv/Scripts/python.exe scripts/train_local_semantic_model.py --model-output artifacts/local-recheck/candidate.joblib --eval-output artifacts/local-recheck/candidate-eval.json
.venv/Scripts/python.exe -m pytest backend/tests/test_regex_baseline.py backend/tests/test_verification.py backend/tests/ml/test_data_split_integrity.py
```

Historical `research/final_results.json` is explicitly mixed/unverified and is not submission
evidence. Its synthetic projection generators were removed. Do not describe the retired
quant-risk endpoint or the historical random-feature training smoke as an empirical result.

# FECL v2 neuro-symbolic relation model card

## Status

`RESEARCH_WINNER_NOT_DEPLOYED`. The product runtime remains `regex-baseline-v1`.

## Architecture

Pinned MiniLM semantic-state representation, a train-only semantic-state classifier, typed relation
edges to authoritative status, deterministic amount/currency equality features, and a calibrated
logistic relation head. The model never performs money arithmetic or final PASS/REVIEW/BLOCK policy.

## Frozen synthetic test

- Precision: 0.679245
- Recall: 0.750000
- F1: 0.712871
- PR-AUC: 0.830339
- False PASS: 48
- False BLOCK: 68
- Expected illustrative loss/case: 4.010417

## Safety and limitations

Only grounded semantic-state features may be learned. Missing/ambiguous/OOD/model failure routes to
REVIEW. Platt scaling worsened Brier/ECE under wording-family shift. Hinglish-holdout remains the
weakest slice. No real merchant validation exists; deployment is prohibited.

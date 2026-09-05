# PRAMAAN / CARVE-FECL claim audit

**Status:** current implementation boundary
**Rule:** code and generated artifacts outrank presentation copy.

| Claim | Executable evidence | Defensible status |
|---|---|---|
| PRAMAAN accepts bounded synthetic evidence and returns PASS, REVIEW, or BLOCK | `backend/app/sandbox_api.py`, `backend/app/case_pipeline.py`, API tests | Implemented locally |
| Money is parsed and compared in integer minor units | `backend/app/grounding.py`, `backend/app/verification.py`, money properties | Implemented for supported paths |
| Semantic output is exact-quote grounded and cannot own the gate decision | `backend/app/extraction.py`, `backend/app/grounding.py`, `backend/app/decision.py` | Implemented |
| The interactive sandbox executes Z3 | Sandbox certificate names `DETERMINISTIC_COMPILER`; it does not call `app.carve` | **False; removed from UI copy** |
| CARVE-FECL cross-checks supported research invariants with Z3 | `backend/app/carve.py`, proof and differential tests | Implemented in the research path; bounded timeout/unknown fails closed |
| A typed evidence graph is required in the active product | No active graph runtime or measured product lift exists | **Not implemented and not claimed** |
| A workflow framework improves correctness or measurements | The retired graph was a linear set of mostly no-op nodes | **No measured value; removed** |
| Learned candidates improve the production gate | Generated artifacts reject learned runtime promotion | **Not established; models remain research-only** |
| Calibration or a model probability is customer confidence | No such validation exists | **Prohibited interpretation** |
| Counterfactual evidence repair proves merchant outcome lift | The UI reruns one local synthetic evidence edit | **Demonstration only; no outcome claim** |
| The product performs Razorpay contest, accept, refund, or payment writes | Static and integration guards reject those paths | **Prohibited and absent** |
| Synthetic benchmark metrics generalize to production merchants | Dataset is balanced, generated, and template-derived | **Not established** |

## Current authority chain

```text
bounded input
  -> typed normalization
  -> replaceable claim nomination
  -> exact source grounding
  -> authoritative structured-state checks
  -> deterministic PASS / REVIEW / BLOCK policy
  -> human-owned local workflow
```

PRAMAAN is the product. CARVE-FECL is the research engine. A technical failure, missing evidence,
invalid timestamp, stale worker lease, model/version mismatch, or undecided solver result cannot be
presented as `CONTEST_READY`.

## Evidence limits

- Saved benchmark and model results are synthetic artifact evidence, not live merchant evidence.
- UI elapsed time is one observed local browser-to-API run, not a throughput benchmark or SLA.
- Automated accessibility patterns are not a WCAG certification.
- Visual QA requires a real browser capture; source and jsdom checks do not replace it.

## 2026-09-05 hardening findings

- Browser ingestion previously inferred payment amounts from customer prose, silently replaced same-name files and truncated combined communication. The shared parser now retains files and exact text, validates structured request bundles, isolates read/CSV/JSON failures and blocks verification while input errors remain.
- The UI previously fabricated certificate identifiers and presented unitless acquisition cost as INR. It now displays only returned certificate fields, and labels fixture repairs as simulations.
- The legacy quant-risk endpoint served typed-in hypothesis/economic results and invented utilization. It now returns 410 rather than presenting those values as measurements.
- The removed `training/run_all.py` wrote `TRAINING_COMPLETE_AND_FROZEN` without optimizer work. Its historical manifest is not a training receipt. A runnable test now checks actual gradients, changed weights, parameter count and checkpoint reload equality.
- `training/falsification_smoke_test.py` uses hash-seeded random text vectors and positional numeric features. Its historical results can demonstrate optimizer execution, not pretrained semantic understanding or graph-learning lift. They are excluded from the judge-facing evidence recommendation.
- The August frozen baseline artifact remains unchanged. Current detector bytes differ from that freeze; its precision/recall describe that saved revision only.


### DEV regression repairs (2026-09-05)

A fresh DEV run exposed ten false BLOCKs. Two came from decimal sentence splitting; eight
came from aggregate refund equality falling through to a missing-match finding. Focused tests
and a fresh DEV run now establish zero false BLOCKs on those same 120 development cases,
with 40 REVIEWs. This is repair evidence on observed DEV failures, not a new generalization
claim. Unsupported monetary precision and malformed grouping remain unresolved; an aggregate
cannot satisfy a specific unmatched refund reference. The saved historical HOLDOUT is unchanged.

The current UI explicitly identifies saved evaluation metrics as historical baseline evidence.
The canonical release receipt records that no rendered browser validation was available.

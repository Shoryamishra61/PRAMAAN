# ML system architecture

## Offline research path

```text
versioned case snapshots
 -> consent/de-identification gate
 -> label + adjudication store
 -> split manifest generator
 -> feature/span/graph builders
 -> baseline and candidate runners
 -> calibration/risk-control fitting
 -> case-level replay
 -> immutable-by-convention experiment artifact
 -> promotion review
 -> signed model/config bundle
```

- **DESIGN DECISION:** Dataset, label, feature, code, model, calibration and policy versions are independent lineage dimensions.
- **DESIGN DECISION:** MLflow-style local artifacts are sufficient for the hackathon; a hosted MLflow/W&B/Langfuse service is added only when multiple users/runs require coordination.
- **DESIGN DECISION:** Typed Python functions sequence evidence -> extraction -> grounding -> reconciliation -> uncertainty -> review; an orchestration framework adds no measured value here.
- **DESIGN DECISION:** RAG is limited to versioned, exact-citation policy guidance and cannot alter claims/findings/decisions.
- **DESIGN DECISION:** MCP is a future connector boundary only if an authenticated merchant ledger/document system benefits from standardized tools.

## Online inference path

```text
canonical snapshot
 -> deterministic feature view
 -> exact sentence/span candidates
 -> extractor / relation candidate
 -> local offset verifier
 -> OOD + ensemble disagreement
 -> calibrated selection policy
 -> deterministic financial verifier
 -> policy engine
 -> versioned trace + decision
```

## Feature lineage

- **DESIGN DECISION:** Deterministic features: ledger completeness, refund state, amount/reference/time equality, reason profile and evidence inventory.
- **DESIGN DECISION:** Semantic features: span representation, allowlisted claim probabilities, relation logits and evidence mask.
- **DESIGN DECISION:** Temporal features: event-time differences and ordering computed from authoritative timestamps.
- **DESIGN DECISION:** Graph features: typed degree/path/relation summaries computed without using the target label.
- **DESIGN DECISION:** Every feature definition declares `available_at`, source field, transform version and null semantics.

## Registry and promotion

- **DESIGN DECISION:** Model card stores training data/split hashes, intended use, excluded use, metrics/slices, calibration version, OOD set, latency/size, dependencies and rollback target.
- **DESIGN DECISION:** Candidate stages: `EXPERIMENT -> REJECTED | RESEARCH_ONLY -> SHADOW -> CANARY -> ACTIVE -> RETIRED`.
- **DESIGN DECISION:** Activation requires research and risk owner approval, all gates green, signed artifact digest and tested rollback.
- **DESIGN DECISION:** A model can nominate claims only; authority is a separately versioned policy capability.

## Drift and feedback

- **DESIGN DECISION:** Monitor input language/template drift, embedding distance, prediction/disagreement rates, REVIEW load, span grounding, critical errors and label delay.
- **DESIGN DECISION:** Outcome feedback is point-in-time joined after maturity; no current outcome enters historical features.
- **DESIGN DECISION:** Drift alert triggers investigation/shadow evaluation, not automatic retraining or threshold changes.

## Failure recovery

- **DESIGN DECISION:** Model timeout/schema error -> typed transient/permanent failure -> bounded retry -> REVIEW.
- **DESIGN DECISION:** Registry/config digest mismatch -> fail closed and retain prior active model.
- **DESIGN DECISION:** Corrupt feature materialization -> quarantine snapshot and replay after correction.
- **DESIGN DECISION:** Rollback restores the previous bundle while keeping new traces for audit.

## Experiment tracing schema

- **DESIGN DECISION:** Run trace includes `run_id`, hypothesis, parent baseline, data/split/code hashes, package/model revisions, parameters, seeds, start/end, hardware, metrics, curves, per-case predictions, errors, cost, reviewer and promotion outcome.
- **DESIGN DECISION:** Inference trace includes node timings and hashes, but raw evidence and prompts are excluded from general logs.

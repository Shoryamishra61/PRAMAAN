# 21 — Risk, Assumption & Decision Ledger

## Active assumptions

### A-001 Merchant source access
Assumption: a merchant can export/support access to refund ledger and customer communication.
MVP: synthetic fixtures.
Risk: production integration may be the real bottleneck.

### A-002 Source completeness flag
BLOCK rules rely on a structured source being marked complete for the relevant scope.
MVP fixture provides this.
Risk: real exports may be stale/incomplete → REVIEW.

### A-003 Semantic extraction utility
Hypothesis: a model extractor improves material-conflict recall over a strong regex baseline.
Validation: benchmark.

### A-004 Operational value
Hypothesis: preventing unsupported/inconsistent submissions has merchant value.
Primary support: Razorpay evidence guidance and `action_required` event.
Not proven: real loss-rate reduction.

### A-005 Competition deadline
Operational deadline 5 Sep 2026 from contemporaneous secondary sources; official landing page verified during research did not expose it. Submit early.

## Major risks

| Risk | Severity | Mitigation |
|---|---|---|
| Synthetic benchmark too toy-like | High | hard negatives, unseen family holdout, full disclosure |
| Product problem prevalence unproven | High | pitch as bounded hypothesis/control point, not quantified crisis |
| Competitor differentiation overstated | High | public-doc wording only |
| LLM extraction adds no lift | High | baseline + remove AI complexity if not useful |
| False BLOCK from semantics | High | exact grounding + complete trusted resolver + REVIEW otherwise |
| Demo provider outage | Medium | visible offline replay |
| Scope creep | High | AGENTS/MoSCoW |
| UI friction hurts usability | Medium | structured evidence inspection, no arbitrary text hurdle |
| Webhook processing lost | Medium | durable jobs table |
| “security” claims overreach | High | threat-model precise language |
| Holdout leakage | High | family split + hashes + explicit runner |
| Reason-code mismatch | High | preserve raw code, local profile separate |
| Timeline too short | High | build deterministic golden path before AI/UI polish |

## Decisions

### D-001 Track 02 retained
Reason: direct official verifier category + held-out metrics.

### D-002 Product narrowed to Refund/Credit Not Processed
Reason: direct Razorpay evidence guidance; natural structured+unstructured join.

### D-003 Primary product profile is local, not raw reason-code mapping
Reason: avoid assuming API `reason_code` literal.

### D-004 One AI stage by default
Reason: simpler, safer, more explainable; NLI becomes optional ablation.

### D-005 No model confidence threshold
Reason: LLM confidence/temperature claims in prior reports were invalid.

### D-006 Missing suggested evidence → REVIEW
Reason: Razorpay page calls items “Suggested Documents”; do not invent mandatory checklist semantics.

### D-007 No direct Razorpay write in MVP
Reason: defense-only, safer demo, preserves verifier identity.

### D-008 180-case benchmark recommendation
Reason: 60-case holdout provides more honest per-class counts than prior N=30, still manageable synthetically. No claim of production statistical representativeness.

### D-009 Family-level split
Reason: synthetic timestamp split is not OOD.

### D-010 Durable SQLite job queue
Reason: stronger restart semantics than acknowledged in-memory BackgroundTasks without adding broker.

### D-011 Plaintext/JSON evidence only
Reason: core thesis does not require OCR/PDF parser; security/complexity reduction.

### D-012 Structured override
Reason: evidence-directed cognitive forcing is more meaningful than a 50-character hurdle.

### D-013 Track 03 contamination excluded
A supplied Hybrid Recovery Orchestrator specification belongs to Track 03 and is non-authoritative for this repository. No retry-orchestration, UPI failure-code, payday scheduling, or recovery-agent logic may enter the Track 02 build without a deliberate product pivot.

### D-014 Sentence-level tournament replaces the old whole-document challenger
Reason: the old classifier was trained on whole communications but served sentence by sentence.
The v2 study uses scenario-family-grouped sentence predictions, exact model revisions, generated
curves, conformal/selective diagnostics, and a separately frozen final holdout.

### D-015 Learned extractors remain rejected
On grouped DEV, rules achieved precision/recall/F1 `0.9722/1.0000/0.9859`. TF-IDF, MiniLM,
their fixed ensemble, and XGBoost did not strictly improve the pre-registered precision, recall,
and F1 gates. XGBoost tied the rules baseline only by copying it: its largest mean absolute
TreeSHAP feature was `regex_nomination`, and the paired bootstrap F1 delta was exactly zero.

On frozen holdout, TF-IDF improved F1 (`0.8889` vs rules `0.4000`) and MiniLM improved F1
(`0.8421`) by recovering unseen processed-claim phrasing, but precision fell to `0.8000` and
`0.7273`. A post-hoc, non-tuning audit found unique grounding rates of `0.6000` and `0.6364`,
20 false PASS outcomes for each, and 5 false BLOCK outcomes for MiniLM. Runtime selection therefore
remains `regex-baseline-v1`; the learned models are research evidence, not deployment authority.

### D-016 NLI retained experimentally, not integrated
The pinned MiniLM NLI cross-encoder improved F1 from `0.5714` to `0.7500` at precision `1.0000`
on a 20-pair synthetic test set. It still missed amount, reference, and temporal contradictions.
The sample is too small and synthetic for a gate path, so the candidate appears only in `/ai`.

### D-017 No leaked meta-risk model, cosmetic RAG, MCP, or LoRA
The current synthetic final-gate labels are generated from deterministic reconciliation features;
training XGBoost to reproduce them would be target leakage. RAG remains exact-citation guidance,
MCP remains a future typed integration boundary, and LoRA/token classification was rejected as
data/compute-ineligible after frozen embeddings failed the safety-preserving lift gate.

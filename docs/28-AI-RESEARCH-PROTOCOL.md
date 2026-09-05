# 28 — AI Research Protocol

Status: expanded and re-registered before any v2 frozen-holdout run  
Date: 2026-09-01  
Scope: semantic evidence processing only; deterministic financial reconciliation remains fixed

## Research question

Can a learned semantic component improve exact, grounded refund-claim extraction or contradiction
detection over strong deterministic baselines on unseen phrasing families, while preserving
precision, calibration, abstention behavior, auditability, and local deployment feasibility?

## Hypotheses

- **H1 — contextual extraction:** sentence-level contextual representations improve recall on
  paraphrased processed-refund claims that the regex baseline misses, without reducing material-
  claim precision.
- **H2 — relational contradiction:** a sentence-pair NLI model detects semantically contradictory
  processed/not-processed statements beyond literal polarity patterns.
- **H3 — selective prediction:** calibration plus an explicit reject option reduces error among
  accepted semantic predictions relative to raw maximum-probability selection.
- **H4 — OOD handling:** embedding-distance or energy-like scores separate unsupported language,
  instruction-like evidence, malformed fragments, and unrelated commerce text from in-domain
  refund claims better than raw classifier probability.
- **H5 — learned meta-risk:** a tree ensemble over detector-visible structured and semantic
  features improves case-level gate prediction over logistic regression, but is deployable only if
  it also beats the deterministic reconciler on false-PASS and false-BLOCK cost.
- **H6 — hard negatives and ensembles:** explicit instruction/neutral hard negatives or disagreement
  ensembles improve precision without sacrificing recall; otherwise they are rejected.

## Fixed authority boundary

All candidates may only nominate an allowlisted claim type and an exact source sentence. Local code
must recover offsets, parse money/references, reconcile the ledger, and produce PASS/REVIEW/BLOCK.
No experiment may use model output for arithmetic, identifiers, timestamps, source completeness,
or final policy. Abstention, OOD, invalid schema, and ungrounded output route to REVIEW.

## Candidate matrix

| ID | Method | Purpose | Deployment status before experiment |
|---|---|---|---|
| B0 | Existing regex extractor | Strong non-AI baseline | Selected runtime |
| B1 | Sentence-level word+character TF-IDF logistic regression | Correct the prior train/serve granularity mismatch | Research candidate |
| B2 | Frozen MiniLM sentence embedding + class-weighted logistic head | Test contextual transfer with low compute | Research candidate |
| B3 | NLI cross-encoder over exact sentence pairs | Contradiction-only ablation | Research candidate |
| B4 | Constrained local instruction model extraction | GenAI feasibility comparator | Run only if pinned local inference fits compute and schema/grounding gates |
| B5 | Fine-tuned encoder or SetFit | Lightweight learned representation | Run only if B2 shows a residual, data-supported gap and training is reproducible |
| B6 | XGBoost over frozen semantic + detector-visible features | Nonlinear meta-risk challenger with native TreeSHAP | Research candidate; never financial authority |
| B7 | Rules/TF-IDF/embedding stack | Disagreement and hard-negative ablation | Research candidate |
| B8 | Logistic regression over the same B6 features | Classical meta-risk comparator | Research candidate |

Candidates B4/B5 are not mandatory executions when credentials, compute, or sample size make the
result scientifically invalid. Their exclusion must be recorded with evidence, not hidden.

## Data and split discipline

1. Existing `DIG-RNP-SYN-v1/dev` is available for development and grouped cross-validation.
2. Exact claim quotes create sentence-level labels; case/scenario family remains the grouping unit.
3. A versioned semantic challenge set uses disjoint template families for contradiction, negation,
   temporal language, partial/full language, prompt injection, unrelated commerce text, malformed
   fragments, and unsupported language.
4. Thresholds and calibration parameters are selected only from inner calibration groups.
5. The frozen v1 holdout remains unread until the candidate set, code, model revisions, thresholds,
   and promotion rule are frozen. Any post-holdout retuning requires a new benchmark version.
6. The freeze binds the protocol, runner, DEV artifact, challenge set, model revisions, feature
   schema, and holdout manifest hashes. The first freeze was invalidated before holdout access when
   the tournament scope expanded; it is not evidence for the final run.

## Metrics

Claim extraction:
- precision, recall, F1 with exact counts;
- exact-quote grounding rate;
- amount/reference normalization accuracy where applicable;
- case-level downstream false PASS and false BLOCK under the unchanged verifier.

Contradiction detection:
- precision, recall, F1 and confusion matrix;
- literal-pattern baseline delta;
- separate negation, temporal, coreference, and prompt-injection slices.

Calibration and selection:
- Brier score;
- expected calibration error with five equal-width bins and non-empty-bin counts;
- negative log loss;
- risk–coverage points and area under the risk–coverage curve;
- selective risk at 50%, 70%, 80%, 90%, and 100% coverage;
- OOD AUROC and FPR at 95% TPR where sample counts permit.
- grouped cross-conformal 90% prediction-set coverage, singleton rate, and abstention rate;
- paired bootstrap 95% intervals for headline F1 deltas, labeled descriptive on synthetic data.

Meta-risk:
- macro F1 and three-way confusion matrix;
- false-PASS and false-BLOCK counts and configured cost-weighted utility;
- native XGBoost TreeSHAP contributions over learned features only;
- comparison to multinomial logistic regression and the deterministic reconciler.

Latency and footprint:
- cold model load, warm p50/p95 inference, serialized artifact/model bytes, and peak process memory
  when measurable on the reference machine.

## Ablations

- whole-document versus sentence-level training;
- word features only, character features only, and combined TF-IDF;
- frozen embeddings with and without the logistic relational head;
- raw probability versus calibrated probability;
- probability-only selection versus probability plus OOD rejection;
- ordinary versus hard-negative-weighted training;
- individual candidates versus fixed, untuned mean/disagreement ensembles;
- logistic versus XGBoost on an identical feature schema;
- literal contradiction rules versus NLI;
- exact-grounding gate removed only as an offline safety ablation, never a product candidate.

## Promotion gates

A learned extractor may replace B0 only if all conditions hold on the pre-registered final split:

1. material-claim precision is at least B0 precision;
2. recall increases by at least 5 percentage points and F1 strictly improves;
3. exact grounding is 100% for accepted predictions;
4. no increase in downstream false BLOCK count;
5. selective risk at 80% coverage is no worse than B0;
6. unsupported/OOD inputs abstain at least 95% of the time;
7. added warm p95 latency is below 250 ms on the reference machine, or the slower path is explicitly
   confined to asynchronous REVIEW assistance;
8. all artifacts, model revisions, hashes, and per-example predictions are saved.

An NLI stage is retained only if it improves contradiction F1 by at least 5 points at precision
greater than or equal to the literal baseline and does not create a new direct gate path.

The meta-risk model is rejected unless it strictly improves cost-weighted error over both logistic
regression and the deterministic reconciler without any increase in false PASS. TreeSHAP is an
explanation of the fitted tree score, never causal evidence. An ensemble is retained only if it
clears the same extractor gates as a standalone candidate.

## Execution and tracing

The research runner uses ordinary typed Python functions in an explicit sequence. Generated JSON
artifacts record dataset/model revisions, seeds, configuration, calibration, latency, predictions,
abstention behavior, and promotion outcomes. No orchestration framework, agent, tool loop,
credential, payment write path, or model-owned decision is required.

RAG remains a bounded exact-citation comparator until a measured retrieval ablation shows lift.
MCP is documented as a future typed integration boundary only; no connector is introduced without
an authenticated data source and an evaluation-backed failure it solves.

## Statistical reporting

Report paired prediction deltas and exact counts. Use stratified bootstrap confidence intervals only
as descriptive uncertainty over the synthetic sample; never present them as production-population
guarantees. With small slices, show counts and examples instead of unstable percentages.

## Known validity threats

- synthetic template language may favor both rules and pretrained encoders;
- class balance is diagnostic, not production prevalence;
- public NLI datasets do not establish financial-domain validity;
- a frozen pretrained model can change if the Hub revision is not pinned;
- the current Hugging Face account is non-Pro and read-only for repositories, so managed TRL Jobs
  cannot persist a fine-tuned model during this run;
- the reference Python environment has CPU-only PyTorch despite an installed laptop GPU.
- the synthetic corpus is too small for a scientifically credible LoRA/QLoRA or token-classifier
  fine-tune; those candidates must be marked data/compute-ineligible unless a new versioned corpus
  is created before holdout access.

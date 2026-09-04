# Dispute Integrity Gate: a grounded semantic model tournament

## Abstract

We tested whether learned semantic models can improve refund-processed claim extraction and
contradiction detection without taking authority from deterministic financial reconciliation. The
study compared regex, word/character TF-IDF, frozen MiniLM embeddings, a fixed ensemble, XGBoost
stacking with a hard-negative ablation, and a pinned NLI cross-encoder. All extraction candidates
operated on exact source sentences under scenario-family-grouped evaluation. No learned extractor
cleared the pre-registered deployment gate. A cross-encoder improved synthetic contradiction F1,
but failed important relational slices and remains offline research only.

## Research question and boundary

Can learned semantics recover unseen phrasing that rules miss while preserving material-claim
precision, unique grounding, safe abstention, latency, and downstream false-PASS/false-BLOCK cost?

Models may nominate an allowlisted typed claim and exact quote. They never own money arithmetic,
refund identifiers, timestamps, ledger completeness, state transitions, or PASS/REVIEW/BLOCK.
LangGraph sequences the research nodes; deterministic code supplies the financial decision.

## Dataset and protocol

- Extraction DEV: 533 sentence decisions, 70 positives, 15 scenario families, synthetic.
- Extraction HOLDOUT: 100 sentence decisions, 40 positives, 6 unseen families, frozen before the
  final run.
- Contradiction challenge: 12 calibration and 20 test pairs across negation, amount, reference,
  temporal, coreference, neutral, prompt-injection, and unrelated slices.
- Five-fold `GroupKFold` by scenario family; no sentence from a family crosses train/evaluation.
- Fixed seed `20260901`; threshold `0.5` except NLI threshold selected on its separate calibration
  partition.
- Exact model revisions, package versions, feature schema, per-example scores, curves, traces, and
  hashes are saved in the generated artifacts.

Sentence-BERT motivates efficient frozen sentence representations, while ANLI motivates adversarial
relational testing. Neither source establishes financial-domain validity by itself.
([Sentence-BERT](https://aclanthology.org/D19-1410/),
[ANLI](https://aclanthology.org/2020.acl-main.441/))

## DEV extraction tournament

| Candidate | Precision | Recall | F1 | Decision |
|---|---:|---:|---:|---|
| Regex B0 | 0.9722 | 1.0000 | 0.9859 | Retained runtime |
| TF-IDF word | 0.6400 | 0.6857 | 0.6621 | Rejected |
| TF-IDF char | 0.6316 | 0.8571 | 0.7273 | Rejected |
| TF-IDF combined | 0.6400 | 0.6857 | 0.6621 | Rejected |
| MiniLM embedding + logistic | 0.7273 | 0.9143 | 0.8101 | Rejected |
| Fixed TF-IDF/MiniLM ensemble | 0.7273 | 0.9143 | 0.8101 | Rejected |
| XGBoost stack | 0.9722 | 1.0000 | 0.9859 | Rejected: no lift |
| XGBoost + hard-negative weight | 0.9722 | 1.0000 | 0.9859 | Rejected: no lift |

XGBoost's paired bootstrap delta from regex was `0.0000` with descriptive 95% interval
`[0.0000, 0.0000]`. Native TreeSHAP showed `regex_nomination` mean absolute contribution `3.06`,
far above the next feature (`0.28`). The nonlinear model learned to copy the rules; hard-negative
weighting had no measurable effect. TreeSHAP describes the fitted score, not causality.

## Frozen holdout

| Candidate | Precision | Recall | F1 | FP | FN | Promotion |
|---|---:|---:|---:|---:|---:|---|
| Regex B0 | 1.0000 | 0.2500 | 0.4000 | 0 | 30 | Retained by safety gate |
| TF-IDF combined | 0.8000 | 1.0000 | 0.8889 | 10 | 0 | Rejected |
| MiniLM embedding + logistic | 0.7273 | 1.0000 | 0.8421 | 15 | 0 | Rejected |

The learned candidates found unseen processed-claim wording but confused approval or obligation with
completion. MiniLM classified “The refund should have been processed by now” as completed; both
models classified “Your full refund … has been approved” as processed. These are precisely the
false semantic claims that can create bad financial holds.

The frozen result initially reported a structural exact-sentence rate of 1.0. A separate post-hoc
audit correctly tested **unique** grounding against the full document. Repeated identical quotes
were ambiguous: TF-IDF uniquely grounded 30/50 positive nominations (`0.6000`), MiniLM 35/55
(`0.6364`). Through the unchanged gate, both produced 20 false PASS outcomes; MiniLM additionally
produced 5 false BLOCK outcomes. The frozen artifact was not edited, no threshold was retuned, and
the correction is saved separately.

## Calibration, conformal selection, and OOD

MiniLM raw calibration had Brier `0.0602`, NLL `0.2499`, and ECE-5 `0.1495`. Cross-fit Platt scaling
reduced ECE-5 to `0.0372` but worsened Brier to `0.0682`, NLL to `0.3163`, and AURC from `0.0398`
to `0.1312`; it was rejected. This demonstrates why a single calibration statistic is insufficient.
Post-hoc calibration is motivated by known neural calibration failures, not by an assumption that
every calibration transform helps. ([Guo et al.](https://proceedings.mlr.press/v70/guo17a.html))

Grouped cross-conformal empirical coverage was roughly `0.88–0.89`, below the nominal `0.90` on
this small synthetic corpus. It is reported as a diagnostic, not a guarantee. Risk–coverage is the
operational view: abstention must be evaluated against retained error, not presented as model
confidence. ([SelectiveNet](https://proceedings.mlr.press/v97/geifman19a),
[selective NLP](https://aclanthology.org/2022.repl4nlp-1.23/))

Nearest-cosine embedding distance separated all 16 constructed OOD examples (AUROC `1.0`, OOD
rejection `1.0`) at a 5.1% in-domain false-reject rate. The set is too small and constructed to
support a production claim. Energy-based OOD was investigated but not claimed because it was not
implemented in the retained candidate. ([Energy OOD](https://arxiv.org/abs/2010.03759))

## Contradiction experiment

| Method | Precision | Recall | F1 | Status |
|---|---:|---:|---:|---|
| Literal polarity rules | 1.0000 | 0.4000 | 0.5714 | Baseline |
| `cross-encoder/nli-MiniLM2-L6-H768` | 1.0000 | 0.6000 | 0.7500 | Retained experimentally |

The cross-encoder cleared the task-level +5-point F1 gate without adding false positives. It solved
the coreference and synonym cases that literal rules missed, but still failed amount, reference,
and temporal contradictions. Twenty synthetic pairs cannot justify a financial gate. The model is
therefore visible in `/ai`, pinned to revision
`b95119ce93d3e065de6214e38cd4a97b0f2f2c6d`, and not integrated.

## Systems measurements

| Candidate | Warm p95 per sentence | Serialized/cache bytes | External inference cost |
|---|---:|---:|---:|
| TF-IDF combined | 0.032 ms | 23,287 | $0 |
| MiniLM embedding | 1.050 ms | 91,578,415 | $0 |
| XGBoost stack | 0.002 ms | 64,813 | $0 |
| NLI cross-encoder | 11.507 ms | model cache measured separately | $0 |

NLI cached cold load was `838.625 ms`. These are measurements on one Windows 11 CPU-only run, not
service guarantees. Local hardware/electricity cost was not monetized.

## Rejected complexity

- **Constrained LLM:** not run; no pinned local instruction model met CPU latency/schema-validity
  preconditions, and provider inference would violate the offline comparison boundary.
- **LoRA/token classifier/SetFit:** rejected as data/compute-ineligible after frozen embeddings
  failed the safety gate; 70 positive synthetic sentences are not a credible fine-tuning study.
- **Learned final-gate risk model:** rejected before training because its candidate features generate
  the synthetic labels. Training would be target leakage.
- **RAG:** retained only as versioned exact-citation guidance; there is no generated-answer lift task.
- **MCP:** design-only future connector boundary; no authenticated external source is needed here.
- **MLflow/Langfuse server:** not added. The artifact already records MLflow-style run parameters,
  versions, metrics, curves, per-example predictions, abstentions, and local spans without adding a
  service judges must run.

## Deployment decision

`regex-baseline-v1` remains the runtime extractor. This is not because rules won every metric—the
holdout shows a large recall weakness—but because no learned candidate simultaneously preserved
precision, unique grounding, and downstream false-BLOCK safety. NLI remains a bounded research aid.
Any future model requires a new versioned dataset of de-identified, consented merchant evidence,
domain-reviewed labels, a newly frozen holdout, and the same promotion gates.

## Reproducibility

```powershell
uv run --isolated --with "sentence-transformers>=3,<4" --with "xgboost>=2.1,<4" --with "langgraph>=0.6,<1" scripts/run_ai_research_study.py --split dev --include-embeddings --include-nli --include-xgboost
uv run --isolated --with "sentence-transformers>=3,<4" --with "xgboost>=2.1,<4" --with "langgraph>=0.6,<1" scripts/run_ai_research_study.py --freeze-dev
uv run --isolated --with "sentence-transformers>=3,<4" --with "xgboost>=2.1,<4" --with "langgraph>=0.6,<1" scripts/run_ai_research_study.py --split holdout --include-embeddings --confirm-final-holdout
uv run --extra dev python scripts/audit_ai_holdout_grounding.py --confirm-posthoc
```

- DEV artifact SHA-256: `7fc51f5c206ad1d15539f2ea6e165783009f2b972ce07e484e2d62f0c0587c62`
- Freeze SHA-256: `99c2d3beae7adae89cf3eef7407fb4dcb6aff4b17a853344cc80d11305b246a9`
- HOLDOUT artifact SHA-256: `1508afc7a8bb8e9126970c7f1813eb0abf46213d77cfb270234eedb685423d28`
- Post-hoc audit SHA-256: `ec549143fc4dc196dc16a2cebe06b3b518e9fe4ee261cf281cb3d269d1b25599`

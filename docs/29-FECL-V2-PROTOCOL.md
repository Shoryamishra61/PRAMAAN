# 29 — Financial Evidence Consistency Learning v2 protocol

Status: pre-registered before the first v2 test run  
Date: 2026-09-01  
Authority boundary: research-only; the deterministic `refund_not_processed_v1` gate is unchanged

## Observation and open question

The v1 claim-extraction study showed that sentence classifiers can recover unseen processed-refund
paraphrases but can also create false PASS/BLOCK outcomes after grounding. A document classifier does
not observe the relation between what a communication claims and the authoritative payment state.

The open question is therefore relational:

> Given an evidence bundle \(E\) and authoritative state \(S\), can a learned representation detect
> material semantic inconsistency under unseen wording families more reliably than literal rules or
> a communication-only classifier, while abstaining on unsupported inputs?

This study does **not** estimate dispute win probability, fraud propensity, legal correctness, or
merchant savings.

## Task and labels

Each synthetic case contains a customer communication, a typed authoritative refund state, amount,
currency, and event time. The binary research label is `material_contradiction`.

For an evidence claim tuple \(c=(z,a,u,t)\) and authoritative tuple
\(s=(z_s,a_s,u_s,t_s)\), the generator labels a contradiction when a material semantic state differs
or, for completed refunds, amount/currency differ:

\[
y(c,s)=\mathbb{1}[z\ne z_s \lor
(z=\texttt{processed}\land(a\ne a_s\lor u\ne u_s))].
\]

The timestamp is retained for temporal slices but final chronology remains deterministic. Ambiguous,
malformed, instruction-like, unsupported-language, and missing-state cases form an OOD/abstention set
and are never assigned a forced financial decision.

## Dataset design

- Dataset ID: `DIG-FECL-SYN-v2`.
- Synthetic diagnostic benchmark; not production prevalence.
- Minimal pairs share entities and authoritative state while one material evidence fact changes.
- Train, development, and test are isolated by wording/template family.
- Entity IDs, amounts, dates, and currencies are deterministically randomized from seed `20260901`.
- Required phenomena: processed/not-processed/pending/failed status, amount/currency mismatch,
  temporal phrasing, multi-refund language, Hinglish, distractors, cross-document contradiction,
  prompt injection, malformed money, incomplete state, and unsupported language.
- The test manifest and runner hash are frozen after DEV artifacts are generated and before the one
  confirmed final test execution.

## Candidate tournament

| ID | Candidate | Learned information | Status before run |
|---|---|---|---|
| B0 | Literal relation rules | none | required baseline |
| B1 | Communication-only word+character TF-IDF logistic | document semantics only | required baseline |
| B2 | Pair-text TF-IDF logistic | serialized evidence/state relation | required |
| B3 | Frozen MiniLM communication embedding + logistic | contextual document representation | required when pinned model loads |
| B4 | Frozen MiniLM relational representation | communication/state embeddings, absolute difference and product | primary representation hypothesis |
| B5 | Multi-task neuro-symbolic relation model | learned semantic-state head plus deterministic relation edges | primary hybrid hypothesis |
| B6 | Relational XGBoost | same B5 feature contract, nonlinear learner | complexity ablation |
| B7 | Relational MLP | same B5 feature contract, five seeds | capacity ablation |

No GNN is trained because every v2 case has the same tiny generated topology and no cross-case
entity network. A GNN without varying topology would be architecture theatre. No LoRA/QLoRA or token
classifier is trained because the authenticated Hugging Face account is non-Pro/read-only and this
synthetic corpus cannot justify a publishable fine-tuning claim. These are rejection results, not
missing leaderboard rows.

## Fixed representations

The B4 relational vector is

\[
r=[h_E;h_S;|h_E-h_S|;h_E\odot h_S],
\]

where \(h_E\) and \(h_S\) are pinned normalized MiniLM embeddings. B5 first predicts the evidence
semantic state using train-only labels, then constructs typed relation-edge features against the
authoritative state. Money, identifiers, currencies, and timestamps are parsed and compared by code,
not by a model.

## Training and split discipline

- Fixed train families: `formal`, `support`, `portal`, `terse`, `hinglish_train`.
- Fixed DEV families: `narrative`, `passive`.
- Frozen test families: `indirect`, `temporal`, `hinglish_holdout`.
- Hyperparameters are fixed in the runner; no test-selected threshold.
- Logistic candidates use class balancing and maximum 2,000 iterations.
- XGBoost uses depth 2, 120 trees, learning rate 0.05, and one thread.
- MLP uses hidden layers `(32, 16)`, early stopping, and seeds 20260901–20260905.
- Platt calibration and the selective threshold are fitted on DEV only.
- The v1 frozen holdout is never read by this runner.

## Metrics and statistical tests

Report precision, recall, F1, PR-AUC, confusion counts, Brier score, NLL, 10-bin ECE, latency,
serialized bytes, and per-slice counts. Critical operational metrics are false PASS (missed
contradiction), false BLOCK (false contradiction), coverage, selective risk, and expected loss under
the explicitly illustrative cost grid `FN=25`, `FP=5`, `REVIEW=1`.

Uncertainty reporting includes paired case bootstrap confidence intervals, exact McNemar tests for
paired errors, five-seed MLP mean/standard deviation, and risk–coverage curves. Synthetic confidence
intervals describe this benchmark only.

## Promotion and falsification gates

B4 or B5 is a research winner only when the frozen test shows all of:

1. F1 improves by at least 0.05 over B0 and B2;
2. false PASS is no worse than both comparators;
3. paired McNemar \(p<0.05\) against B0 after the preregistered exact test;
4. selective risk at 80% coverage is lower than raw 100% risk;
5. at least 95% of OOD cases abstain under the DEV-fitted controller;
6. all predictions, hashes, plots and costs are saved.

Failure of any gate means `NOT_PROMOTED`. Even a research winner cannot alter the product gate until
validated on consented, de-identified merchant data with a new protocol.

## Reproducibility command

```powershell
.research-venv\Scripts\python.exe scripts\run_fecl_v2.py --stage dev
.research-venv\Scripts\python.exe scripts\run_fecl_v2.py --freeze
.research-venv\Scripts\python.exe scripts\run_fecl_v2.py --stage test --confirm-final-test
```

Every output number used by the UI or paper must be read from the generated JSON/CSV artifacts.

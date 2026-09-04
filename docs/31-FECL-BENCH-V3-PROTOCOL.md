# 31 — FECL-Bench v3 preregistered protocol

Status: frozen before generation of the final TEST result  
Date: 2026-09-01  
Authority: research-only; `refund_not_processed_v1` runtime remains unchanged

## Task

Financial Evidence Consistency Learning (FECL) maps a heterogeneous case graph
\(G=(V,E,\tau_V,\tau_E,X)\) to a contradiction label \(y\), a grounded causal subgraph \(G^*\),
and an abstention decision. Node types are Payment, Refund, Claim, Document, Policy, Order, and
Event. Relations cover document containment, claim targets, order/payment/refund identity,
chronology, policy scope, and evidence provenance.

The learned model predicts semantics and consistency. External code remains authoritative for
amount, currency, identifiers, timestamps, hashes, state transitions, and final PASS/REVIEW/BLOCK.

## Benchmark

- Dataset ID: `DIG-FECL-BENCH-v3`.
- Fully synthetic and provenance-marked; no production prevalence claim.
- Every in-distribution example belongs to a paired counterfactual group.
- One financially causal fact changes between pair members: status, amount, currency, reference,
  aggregate/partial amount, or timestamp.
- Graph topology varies through one-to-three Refunds, one-to-three Claims, one-to-two Documents,
  and two-to-six Events.
- Required slices: explicit and implicit claims, negation, paraphrase, Indian English, Hinglish,
  partial refunds, multiple refunds, wrong amount/currency/reference, delayed state, chronology,
  cross-document contradiction, distractors, and matched controls.
- OOD includes malformed graph schema, unsupported language, prompt injection, impossible event
  order, unknown currencies, missing authoritative nodes, and oversized distractor graphs.
- Each contradiction has node/edge IDs for the smallest generator-known causal subgraph and a
  single-field repair operation.

## Leakage controls

- TRAIN families: `formal_ops`, `support_chat`, `portal_log`, `merchant_note`, `hinglish_train`.
- DEV families: `narrative_indirect`, `passive_voice`, `indian_english_dev`.
- TEST families: `temporal_implicit`, `hinglish_holdout`, `cross_document_holdout`,
  `paraphrase_holdout`.
- Template text, paraphrase functions, entity prefixes, and counterfactual pairs are split-local.
- Pair/group IDs never cross splits.
- Encoders are frozen and pinned. Vocabulary, thresholds, calibration, early stopping, loss weights,
  and conformal/selective parameters are fitted on TRAIN/DEV only.
- TEST is opened once after protocol, runner, manifest, DEV artifacts, and promotion gates are hashed.
- FECL v1/v2 frozen holdouts are never training inputs.

## Proposed method

The proposed Evidence-State Relation Attention Network (ESRAN) uses node-type projections,
relation-specific key/value transformations, typed attention bias, edge attributes, residual message
passing, and graph attention pooling. The architecture itself is not claimed novel; the research
hypothesis concerns its training target and benchmark.

For case loss \(L_c\), relation reconstruction \(L_r\), causal-node grounding \(L_g\), paired
representation margin \(L_h\), and counterfactual logit margin \(L_{cf}\):

\[
L=L_c+0.20L_r+0.35L_g+0.15L_h+0.30L_{cf}.
\]

The weights and margins are fixed on DEV and cannot be changed after freezing. `ESRAN-case-only`
removes every auxiliary term. Further ablations remove relation types, temporal edges, financial
edge attributes, grounding loss, representation margin, and counterfactual margin.

## Required comparators

1. deterministic literal financial rules;
2. communication-only TF-IDF/logistic;
3. linearized graph TF-IDF/logistic;
4. relational XGBoost;
5. frozen MiniLM bi-encoder relation vector;
6. pinned NLI cross-encoder over claim/state pairs;
7. mean GraphSAGE;
8. relation-agnostic GAT;
9. R-GCN;
10. FECL-v2 neuro-symbolic baseline;
11. ESRAN and preregistered ablations.

Unavailable candidates remain explicit missing results; no metric is imputed.

## Seeds and optimization

- Generator seed: `20260903`.
- Neural seeds: `20260903` through `20260907`.
- AdamW, learning rate 0.002, weight decay 0.0001, maximum 80 epochs, DEV early stopping patience 10.
- Hidden width 64, two message-passing layers, four attention heads, dropout 0.15.
- Batch size 32 graphs. Frozen MiniLM node embeddings are cached before neural training.
- Primary neural score is the five-seed ensemble mean; per-seed metrics and dispersion are saved.

## Metrics

Primary: contradiction F1 and illustrative asymmetric cost (`false PASS=25`, `false BLOCK=5`,
`REVIEW=1`). Secondary: precision, recall, PR-AUC, Brier, ECE, NLL, latency, bytes, family and
phenomenon slices, pair-both-correct, causal sensitivity, and OOD rejection.

Explanation metrics: causal-node/edge precision, recall and F1; exact-subgraph match; sufficiency;
comprehensiveness/deletion drop; insertion recovery; extracted node/edge count; and repair flip rate.
Attention weights are diagnostic only and never count as an explanation metric.

Statistics: paired group bootstrap with 2,000 resamples, exact McNemar against rules, linearized
TF-IDF, R-GCN, and FECL-v2, plus five-seed mean/standard deviation. Confidence intervals describe
this synthetic benchmark only.

## Risk control

- DEV fits thresholds and optional probability calibration.
- Selective risk is reported over coverage; REVIEW is explicit.
- Split-conformal or conformal-risk results are reported only as empirical DEV/TEST diagnostics.
  Because TEST uses unseen families, exchangeability is violated and no distribution-free guarantee
  may be claimed.
- The learned model may only increase caution. Verified deterministic contradictions remain BLOCK;
  malformed, OOD, unavailable, or uncertain learned outputs remain REVIEW.

## Primary promotion gates

ESRAN is a research success only if frozen TEST satisfies all:

1. F1 exceeds the strongest eligible comparator, including XGBoost and NLI when executed, by at
   least 0.03;
2. paired bootstrap 95% CI for F1 lift over the strongest eligible comparator excludes zero;
3. exact McNemar p < 0.05 against the strongest preregistered comparator;
4. false PASS count is lower than the strongest comparator;
5. pair-both-correct improves by at least 0.05 over FECL-v2;
6. selective risk at 80% coverage is lower than 100% risk;
7. combined deterministic-plus-learned OOD rejection is at least 0.95;
8. causal-subgraph F1 is at least 0.75 and deletion drop exceeds random-subgraph deletion;
9. single-field repair flips at least 0.80 of correctly detected contradictory pairs;
10. all data, predictions, per-seed results, hashes, plots, and failures are saved.

Failure of one gate produces `NO_GO_METHOD_REJECTED`. Passing all gates still produces
`RESEARCH_CANDIDATE_NOT_DEPLOYED` until evaluation on consented, de-identified, temporally split
merchant data.

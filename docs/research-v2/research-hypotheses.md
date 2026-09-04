# Pre-registered research hypotheses

**DESIGN DECISION:** These hypotheses define a new `research-v2` program. They do not reopen, relabel, threshold-tune or otherwise reuse the frozen v1 holdout for development.

## H1 — grounded material-claim extraction

- **HYPOTHESIS:** A span-supervised encoder improves recall for material completed-refund claims over regex while maintaining case-level false-BLOCK safety.
- **NULL:** The encoder does not improve grouped DEV claim F1 by at least 0.05, or it increases false-BLOCK rate beyond the predeclared limit.
- **BASELINE:** frozen `regex-baseline-v1` plus exact unique grounding.
- **TREATMENT:** sentence/span encoder with a joint claim-type and evidence-span objective; DeBERTa-v3-base is a candidate only after data sufficiency.
- **DEPENDENT METRICS:** exact-span F1, material-claim precision/recall, unique-grounding rate, false PASS/BLOCK, latency and size.
- **DATASET:** de-identified, consented refund communications with domain-reviewed exact spans plus synthetic stress cases kept in a separate slice.
- **SPLIT:** merchant + template family + chronology grouped; untouched v2 holdout.
- **FAILURE:** fewer than 500 independently reviewed positive material spans, unstable seeds, or any safety regression without compensating abstention.
- **PROMOTION:** paired 95% bootstrap lower bound for case-level F1 delta above 0; material precision at least 0.98; false-BLOCK upper confidence bound below the business threshold; unique grounding at least 0.99.

## H2 — relation model for semantic contradiction

- **HYPOTHESIS:** A cross-encoder trained on domain relation pairs detects paraphrase, negation, temporal and amount-qualified contradictions missed by literal polarity rules.
- **NULL:** It fails to add at least 0.05 macro-F1 or creates unacceptable material false contradictions.
- **BASELINE:** typed lexical polarity/amount/reference/time rules.
- **TREATMENT:** DeBERTa/RoBERTa NLI cross-encoder with domain hard negatives; generic NLI is a pretrained initialization, not evidence.
- **DEPENDENT METRICS:** contradiction precision/recall/F1, slice F1, evidence-pair grounding, false BLOCK and abstention coverage.
- **DATASET:** paired grounded claims and authoritative fact statements with human relation labels.
- **SPLIT:** case/merchant/template/chronology grouped.
- **FAILURE:** generic NLI transfer without domain lift, or amount/reference/time errors remain unresolved.
- **PROMOTION:** contradiction precision at least 0.99 on material pairs, statistically supported lift, and deterministic verifier can veto/abstain.

## H3 — explicit evidence graph representation

- **HYPOTHESIS:** Typed claim-to-fact edges improve cross-document integrity classification over a flat semantic model when cases contain multi-document relations.
- **NULL:** Graph features/models do not improve case-level expected loss or explanation fidelity after controlling for the same inputs.
- **BASELINE:** flat concatenated features and flat cross-encoder.
- **TREATMENTS:** (A) deterministic typed claim graph with relational features; (B) learned graph model only if dataset scale and topology justify it.
- **DEPENDENT METRICS:** expected loss, macro-F1, critical slice recall, edge-label F1, deletion/insertion explanation fidelity and latency.
- **DATASET:** case bundles with at least two evidence documents, authoritative ledger nodes and reviewed relation edges.
- **SPLIT:** connected-entity components and merchant/time isolation.
- **FAILURE:** the graph merely restates deterministic joins or has fewer than 1,000 sufficiently diverse labeled graphs.
- **PROMOTION:** relational features add significant paired lift; a GNN must then beat those features, not only the flat text model.

## H4 — selective risk control

- **HYPOTHESIS:** A separately calibrated selection policy lowers false PASS/BLOCK risk at useful coverage compared with max-score classification.
- **NULL:** No operating point dominates the baseline after review cost, or exchangeability/size assumptions are not credible.
- **BASELINE:** fixed threshold plus current mandatory REVIEW rules.
- **TREATMENTS:** calibrated uncertainty, ensemble disagreement, OOD indicator, selective classifier; CRC only on an untouched calibration set.
- **DEPENDENT METRICS:** risk-coverage, critical-error upper bound, review load, expected cost and threshold stability.
- **DATASET:** v2 calibration split plus frozen holdout and shift/OOD sets.
- **FAILURE:** empirical coverage misses target, calibration reused adaptively, or coverage is operationally negligible.
- **PROMOTION:** predeclared critical risk target met with stated finite-sample assumptions and useful coverage; otherwise report empirical abstention only.

## H5 — hybrid learned semantics plus deterministic invariants

- **HYPOTHESIS:** Learned claim nomination followed by deterministic money/ID/time/ledger reconciliation produces lower expected loss than either semantics-only or rules-only systems.
- **NULL:** The hybrid does not beat rules-only expected loss, or semantic-only achieves apparent lift through leakage.
- **BASELINES:** rules-only and semantic-only ablations.
- **TREATMENT:** learned grounded claims -> deterministic invariants -> selective policy.
- **DEPENDENT METRICS:** case-level expected loss, false PASS/BLOCK, coverage, latency and analyst repair time.
- **DATASET/SPLIT:** same v2 case-level protocol as H1–H4.
- **FAILURE:** any learned field directly supplies authoritative money, identifier, timestamp or final state.
- **PROMOTION:** paired expected-loss lift and all safety constraints satisfied.


# 30 — FECL v3 prior-art falsification and technical whitespace

Status: research scoping record, not a novelty or freedom-to-operate opinion  
Search date: 2026-09-01

## Result

The broad claim "use a heterogeneous graph neural network to find contradictions in financial
evidence" is **not novel**. Every major ingredient has close prior art. FECL v3 therefore makes no
architecture-first novelty claim. The only testable whitespace retained is a task-and-evaluation
contribution:

1. case-local graphs joining grounded language to authoritative payment/refund state;
2. causally controlled counterfactual pairs where one financially material fact changes;
3. joint case, typed-relation, grounding, representation-separation, and counterfactual objectives;
4. annotated minimum contradictory subgraphs evaluated by deletion/insertion rather than attention;
5. a deployment boundary where learned outputs cannot override deterministic financial invariants.

This combination remains a hypothesis until it wins the preregistered unseen-family tests. A failed
experiment must be published as a NO-GO.

## Literature that narrows the claim

| Prior work | What it already establishes | Consequence for FECL v3 |
|---|---|---|
| Heterogeneous Graph Transformer, Hu et al. (2020), https://arxiv.org/abs/2003.01332 | Node/edge-type-dependent attention and relative temporal encoding | Typed relation-aware attention is prior art, not the contribution |
| R-GCN, Schlichtkrull et al. (2018), https://arxiv.org/abs/1703.06103 | Relation-specific message passing | R-GCN is a required baseline |
| GraphSAGE, Hamilton et al. (2017), https://arxiv.org/abs/1706.02216 | Inductive neighborhood aggregation | GraphSAGE is a required relation-agnostic baseline |
| GAT, Veličković et al. (2018), https://openreview.net/forum?id=rJXMpikCZ | Learned attention over graph neighborhoods | Attention visualizations cannot be presented as faithful explanations |
| Reasoning Over Semantic-Level Graph for Fact Checking, Zhong et al. (ACL 2020), https://aclanthology.org/2020.acl-main.549/ | Graph reasoning across multiple textual evidence items | FECL is not the first graph-based fact-verification formulation |
| Program Enhanced Fact Verification, Yang et al. (EMNLP 2020), https://aclanthology.org/2020.emnlp-main.628/ | Neural plus symbolic/program evidence fusion | Neuro-symbolic evidence verification is prior art |
| FACTKG simplification study, Opsahl (FEVER 2024), https://aclanthology.org/2024.fever-1.32/ | Simple logical retrieval can beat heavier retrieval methods | Rules and linearized evidence remain serious baselines |
| Evidence Grounding vs. Memorization, Upadhyay et al. (FEVER 2026), https://aclanthology.org/2026.fever-1.3/ | Linearized BERT strongly outperformed GNNs on FACTKG | FECL's graph hypothesis is plausibly false and must beat linearized text |
| GNNExplainer, Ying et al. (NeurIPS 2019), https://openreview.net/forum?id=pVywBxmyYC | Compact explanatory subgraphs | Compact subgraph extraction is prior art |
| Robust Counterfactual Explanations on Graphs, Bajaj et al. (NeurIPS 2021), https://openreview.net/forum?id=Uq_tGs7N54M | Edge-removal counterfactual explanations and robustness | Counterfactual explanation is prior art; FECL evaluates domain-grounded causal repair instead |
| SelectiveNet, Geifman and El-Yaniv (ICML 2019), https://proceedings.mlr.press/v97/geifman19a.html | Integrated reject option | Selective prediction is a baseline risk-control method |
| Conformal Risk Control, Angelopoulos et al. (ICLR 2024), https://openreview.net/forum?id=33XGfHLtZg | Distribution-free risk control under stated exchangeability conditions | No conformal guarantee may be claimed under family shift |

## Industry and competitor boundary

- Stripe Smart Disputes compiles and submits evidence using an AI rules engine over transaction,
  internal, historical, and cardholder data:
  https://docs.stripe.com/disputes/set-up-smart-disputes
- Adyen exposes automated defense states, dispute analytics, and defense-document APIs:
  https://docs.adyen.com/risk-management/dispute-and-fraud-monitoring
- Visa announced AI-assisted Dispute Intelligence and Dispute Doc Analyzer in 2026, while CE 3.0
  formalizes structured matching evidence:
  https://investor.visa.com/news/news-details/2026/Visa-Unveils-New-Services-to-Modernize-Dispute-Resolution-Process/default.aspx
- Mastercard merchant guidance requires evidence to address the reason code directly:
  https://www.mastercard.com/us/en/news-and-trends/Insights/2024/how-can-merchants-dispute-credit-card-chargebacks.html

The product distinction is therefore not "AI for disputes." It is pre-submission integrity checking
with visible contradiction causality and no autonomous evidence submission or money action.

## Patent search boundary

Searches found patents/applications for ML-based dispute recommendations, dispute contestation,
knowledge-graph contradiction analysis, and accounting evidence chains, including:

- US20250124419A1: ML models ingest dispute evidence and transaction data to recommend outcomes.
- US20250200587A1: dispute contestation automation using rules and ML.
- CN118113884B: knowledge graphs and GNNs over contradiction/dispute data.
- CN121616112A: accounting-event graphs with contradiction evidence chains and GNN reasoning.
- CN110675023A: multi-party evidence association and neural prediction of litigation requests.

Sources: https://patents.google.com/patent/US20250124419A1/en,
https://patents.google.com/patent/US20250200587A1/en,
https://patents.google.com/patent/CN118113884B/en,
https://patents.google.com/patent/CN121616112A/en, and
https://patents.google.com/patent/CN110675023A/en.

This was a keyword search, not a legal claim-chart or freedom-to-operate review. It is sufficient to
reject broad novelty language, not to establish patentability.

## Falsification criteria

The proposed method is rejected if it fails any primary gate in the frozen protocol, if gains vanish
against linearized-text or R-GCN baselines, if minimum subgraphs are not more faithful than a
deterministic causal annotation baseline, or if false-PASS cost is not improved without an
unacceptable false-BLOCK increase. A graph diagram, many losses, or polished UI cannot rescue a
failed hypothesis.

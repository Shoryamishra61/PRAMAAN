# Asian fintech research review

## Verified high-relevance work

| Source | Institution / problem | Result | Transfer decision |
|---|---|---|---|
| **RESEARCH RESULT:** [Pareto-optimal fraud prevention rule sets](https://arxiv.org/abs/2311.00964), KDD 2024 ADS | Ant Group; interpretable rule-pool selection on public/proprietary data and two Alipay scenarios | diversity plus a Pareto-front stage improved the final rule-set selection in the reported experiments | **DESIGN DECISION:** expose precision/recall/review-load Pareto alternatives; never collapse model choice into one accuracy score. |
| **RESEARCH RESULT:** [HACUD](https://ojs.aaai.org/index.php/AAAI/article/view/3884), AAAI 2019 | Ant Financial data; cash-out-user detection with attributed heterogeneous information networks | hierarchical attention over heterogeneous relations improved the authors' task | **DESIGN DECISION:** relevant to coordinated abuse, not to a single refund packet; do not add it to this MVP. |
| **RESEARCH RESULT:** [PC-GNN](https://doi.org/10.1145/3442381.3449989), WWW 2021 | CAS and Alibaba; imbalanced graph fraud | label-balanced graph sampling and neighborhood choice improved reported graph-fraud results | **DESIGN DECISION:** require real entity edges, grouped entity splits and enough positive subgraphs before a GNN branch. |
| **RESEARCH RESULT:** [SemiGNN](https://arxiv.org/abs/2003.01171), 2020 preprint | Alipay user relations; few labeled fraud examples | multi-view semi-supervised attentive graph model reported gains | **DESIGN DECISION:** do not treat unlabeled synthetic evidence as an equivalent setting. |
| **RESEARCH RESULT:** [GTAN](https://arxiv.org/abs/2412.18287), 2024 preprint | Tencent-affiliated authors; temporal transaction graph and few labels | reports performance on a real-world transaction dataset and public fraud datasets | **DESIGN DECISION:** temporal graph modeling belongs to cross-case transaction fraud, not the evidence debugger without such data. |
| **RESEARCH RESULT:** [SEFraud](https://arxiv.org/abs/2406.11389), 2024 preprint | ICBC-affiliated industrial team; self-explainable transaction fraud | uses learnable feature/edge masks and reports ICBC deployment alignment with experts | **DESIGN DECISION:** explanation masks must be validated for fidelity; SHAP or attention is never presented as causality. |
| **RESEARCH RESULT:** [xFraud](https://www.vldb.org/pvldb/vol15/p427-rao.pdf), PVLDB 2022 | eBay China + ETH Zurich; billion-scale heterogeneous transaction graph | detector plus graph explainer scales to the reported industrial graph | **DESIGN DECISION:** copy the separation of detector and explainer evaluation, not the architecture absent data scale. |

## Geographic search outcome

- **FACT:** The targeted search covered named Chinese, Hong Kong and Japanese institutions, but the highest-relevance accessible sources for this exact task were primarily Ant/Alibaba/CAS, ICBC and eBay-China collaborations.
- **UNVERIFIED:** No reviewed public paper from the named Japanese universities was found that directly studies grounded refund-dispute evidence reconciliation with deterministic ledger checks.
- **DESIGN DECISION:** Geographic prestige is not used as evidence. A source enters the architecture only when its dataset, unit of prediction and failure mode match.

## Industrial lessons that survive transfer

- **DESIGN DECISION:** Keep interpretable rules as a strong candidate, not a straw baseline.
- **DESIGN DECISION:** Evaluate a Pareto frontier under asymmetric loss and analyst capacity.
- **DESIGN DECISION:** Treat graph structure as data, not decoration; a rendered evidence graph can be useful for explanation without implying a learned GNN.
- **DESIGN DECISION:** Separate explanation fidelity from predictive accuracy.
- **DESIGN DECISION:** Use time/entity/template isolation to prevent relational leakage.


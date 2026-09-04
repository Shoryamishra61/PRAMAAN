# Model tournament

## Tournament contract

- **DESIGN DECISION:** Candidates compete on identical case-level inputs, grouped splits, saved predictions and predeclared thresholds.
- **DESIGN DECISION:** The rules-only system is B0 and remains eligible to win.
- **DESIGN DECISION:** A candidate that wins F1 but loses material precision, grounding, expected loss, latency or abstention behavior is rejected.

## Stages

| Stage | Candidates | Question | Promotion gate |
|---|---|---|---|
| **DESIGN DECISION:** B0 | exact regex + deterministic reconciler | What can transparent domain rules solve? | reference baseline, never weakened to make ML win |
| **DESIGN DECISION:** B1 | word/char TF-IDF + calibrated logistic regression | Does sparse lexical learning recover paraphrases cheaply? | paired case-level lift and safety gate |
| **DESIGN DECISION:** B2 | MiniLM, BGE-small, E5-small frozen embeddings + logistic/linear SVM | Do general semantic representations add stable information? | beat B1, not merely B0, with latency/size reported |
| **DESIGN DECISION:** B3 | XGBoost/LightGBM/CatBoost on deterministic + semantic + completeness features | Is nonlinear fusion useful beyond copying regex? | SHAP/ablation must show non-rule lift; grouped bootstrap positive |
| **DESIGN DECISION:** B4 | DeBERTa/RoBERTa NLI cross-encoders | Do pairwise models resolve negation, qualification and coreference? | material contradiction precision and hard-slice lift |
| **DESIGN DECISION:** B5 | span/token classifier | Does supervised evidence extraction improve exact grounding? | exact-span and case decision lift with enough real labels |
| **DESIGN DECISION:** B6 | constrained LLM extraction | Does generation beat extractive encoders under schema, grounding, outage, latency and cost constraints? | exact-span/content fidelity + safe failure + cost gate |
| **DESIGN DECISION:** B7 | LoRA/SFT lightweight open model | Does domain adaptation beat B5/B6? | only with >=1,000 high-quality examples and a frozen v2 holdout |
| **DESIGN DECISION:** B8 | deterministic relational features, then GraphSAGE/GAT/HGT | Does graph topology add information unavailable to flat features? | graph ablation lift and topology/data sufficiency |
| **DESIGN DECISION:** B9 | calibrated ensembles / selective models | Can disagreement reduce critical risk at useful coverage? | risk-coverage and expected-cost Pareto dominance |

## Required ablations

- **DESIGN DECISION:** text only; deterministic features only; text + deterministic features.
- **DESIGN DECISION:** no grounding loss; no hard negatives; no amount/reference/time features.
- **DESIGN DECISION:** flat features; explicit relation features; learned graph.
- **DESIGN DECISION:** raw scores; calibration only; OOD only; disagreement only; full selector.
- **DESIGN DECISION:** remove the regex-nomination feature from every stack to expose copying.

## Current v1 evidence

- **RESEARCH RESULT:** On frozen v1, TF-IDF and MiniLM improved extraction recall/F1 but produced unsafe semantic confusions and grounding failures; neither was promoted.
- **RESEARCH RESULT:** The XGBoost stack tied the regex baseline and was dominated by the regex feature, so it was rejected as a rules copier.
- **RESEARCH RESULT:** A pinned NLI cross-encoder beat literal contradiction rules on 20 synthetic pairs but failed relational slices and remains research-only.
- **DESIGN DECISION:** No v2 deep model will be trained on the current 70 positive synthetic DEV sentences; this is an explicit data-sufficiency rejection, not unfinished work.

## Hugging Face investigation

- **FACT:** Dataset Viewer inspection found `alexkstern/european_credit_card_fraud_dataset` contains 15,473 rows with anonymized V1–V28 transaction features; it does not contain dispute documents, grounded claims or ledger relations.
- **FACT:** `orgrctera/legalbenchrag_contractnli` exposes 977 exact-span contract retrieval examples and is methodologically relevant to evidence attribution, but its legal NDA domain is not a payment label source.
- **FACT:** `stanfordnlp/snli` provides 570,152 general NLI rows but has no refund/ledger semantics.
- **DESIGN DECISION:** None is eligible as the v2 target dataset. ContractNLI/SNLI may support pretraining or sanity baselines only; the anonymized transaction dataset is rejected as task-mismatched.

## Training infrastructure decision

- **DESIGN DECISION:** Hugging Face TRL/LoRA training is not launched until the labeled-data gate is met, a writable authenticated Hub target exists, cost is approved, and the model can be evaluated against B5/B6.
- **DESIGN DECISION:** Local frozen-encoder experiments remain the cheapest next step; managed GPU complexity is not a research contribution.


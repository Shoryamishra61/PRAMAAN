# Patent landscape

**Disclaimer:** **FACT:** This is a technical prior-art scan, not a legal freedom-to-operate opinion.

## High-relevance families

| Publication | Assignee / status | Disclosed capability | Effect on novelty |
|---|---|---|---|
| **FACT:** [US20250200587A1](https://patents.google.com/patent/US20250200587A1/en), priority 2023-12-18 | PayPal; Google Patents lists pending | ML win-likelihood scores, merchant/transaction data, templates, contestation document and automatic submission | **DESIGN DECISION:** We cannot claim novelty for ML-based contest decisioning, evidence compilation or auto-submission. |
| **FACT:** [US12175468B2 / US20210390550A1](https://patents.google.com/patent/US20210390550A1/en), priority 2020-06-15 | Bolt Financial; Google Patents lists active/granted | model-based chargeback representment, feedback from outcomes, contextual features and automatic initiation | **DESIGN DECISION:** Outcome-trained representment selection is prior art and outside scope. |
| **FACT:** [US11049112B2](https://patents.google.com/patent/US11049112B2/en), priority 2018-05-24 | PayPal; Google Patents lists active | parses text/image/video evidence, extracts relevant data, creates processor-formatted representment data and submits batches | **DESIGN DECISION:** Automated evidence extraction and formatting are prior art. |
| **FACT:** [EP4473465A1](https://patents.google.com/patent/EP4473465A1/en), priority 2022-03-03 | Worldpay; Google Patents lists pending | ensembles/probabilities for chargeback representment recommendations and false-positive reduction | **DESIGN DECISION:** Multi-model representment recommendations are not differentiating. |
| **FACT:** [US20240062041A1](https://patents.google.com/patent/US20240062041A1/en), priority 2022-08-12 | current assignee shown on patent page; pending | GNN fraud detection with labeled/unlabeled transaction graph nodes | **DESIGN DECISION:** A GNN label alone offers no novelty. |

## Claim-space interpretation

- **RESEARCH RESULT:** The prior-art landscape is dense around automated evidence parsing, representment generation/submission, win-likelihood scoring, feedback learning and transaction graphs.
- **UNVERIFIED:** This bounded keyword/family scan is not exhaustive across all jurisdictions, continuations or unpublished applications.
- **HYPOTHESIS:** The narrower combination of exact grounded claim spans, deterministic reconciliation to authoritative refund state, typed safe abstention, and interactive counterfactual repair may be less directly represented in the reviewed claims.
- **DESIGN DECISION:** No patentability, freedom-to-operate, “world first,” or “only solution” claim will be made without professional search and claim construction.

## Engineering response

- **DESIGN DECISION:** Keep the system read-only and omit win prediction, autonomous contesting and generated representment letters.
- **DESIGN DECISION:** Treat the evidence graph as an auditable intermediate representation, not as a claim to generic knowledge-graph novelty.
- **DESIGN DECISION:** Preserve a dated source/claim matrix for later counsel rather than shaping the hackathon around speculative patent avoidance.


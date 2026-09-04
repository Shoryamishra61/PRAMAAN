# 24 — Source & Evidence Ledger

Verified on **2026-08-23** unless stated otherwise.

## Razorpay primary sources

### SRC-RZP-01 — Razorpay AI Buildathon
URL: https://razorpay.com/buildathon/
Supports:
- student-only hiring program;
- public repo, 5-minute pitch video, architecture;
- Track 02 wording;
- held-out precision/recall;
- honest false-positive cost;
- defense-only;
- stipend/duration/location.

Does **not** expose a universal weighted judging rubric in the text we verified.

### SRC-RZP-02 — Dispute webhook events
URL: https://razorpay.com/docs/webhooks/disputes/
Supports:
- `payment.dispute.created`;
- won/lost/closed/under_review/action_required events;
- dispute/payment payload examples;
- evidence object categories.

### SRC-RZP-03 — Webhook best practices / validation
URLs:
- https://razorpay.com/docs/webhooks/best-practices/
- https://razorpay.com/docs/webhooks/validate-test/
Supports:
- raw body HMAC SHA-256;
- `X-Razorpay-Signature`;
- `x-razorpay-event-id` uniqueness/idempotency;
- at-least-once delivery;
- out-of-order possibility;
- 2xx within 5 seconds;
- retry behavior.

### SRC-RZP-04 — Contest dispute API
URL: https://razorpay.com/docs/api/disputes/contest/
Supports:
- `PATCH /v1/disputes/:id/contest`;
- draft vs submit action;
- evidence documents/text;
- minimum one document for contest submission.

Reference only; MVP does not invoke it.

### SRC-RZP-05 — Accept dispute API
URL: https://razorpay.com/docs/api/disputes/accept/
Supports:
- `POST /v1/disputes/:id/accept`;
- accepting changes open → lost;
- irreversible.

Reference only; MVP does not invoke it.

### SRC-RZP-06 — Submit Evidence / reason-code guidance
URL: https://razorpay.com/docs/payments/disputes/submit-evidence/
Supports:
- reason-code-specific **suggested documents**;
- Visa 13.6 = Credit Not Processed;
- Visa 13.7 = Cancelled Merchandise/Services;
- RZP04 = Refund not Processed;
- examples of refund evidence/customer communication/policy.

Important: document list is described as suggested on the page; do not universally relabel as mandatory.

### SRC-RZP-07 — Subscribe to dispute webhooks
URL: https://razorpay.com/docs/payments/disputes/subscribe-to-webhooks/
Supports:
- event list;
- `payment.dispute.action_required` meaning: evidence insufficient, unreadable, or not corresponding to contested amount.

### SRC-RZP-08 — Dispute entity
URL: https://razorpay.com/docs/api/disputes/entity/
Supports:
- `id`, `payment_id`, `amount`, `currency`, `reason_code`, `respond_by`, `status`, `phase`, `created_at`, evidence fields;
- statuses and phases.

### SRC-RZP-09 — About disputes
URL: https://razorpay.com/docs/payments/disputes/
Supports:
- dispute process;
- merchant can accept or contest;
- issuer reviews submitted evidence.

### SRC-RZP-10 — UPI 1061 Credit Not Processed evidence guidance
URL: https://razorpay.com/docs/payments/disputes/submit-evidence/
Re-verified: 2026-09-01.
Supports:
- UPI reason `1061` is Credit Not Processed;
- Razorpay describes proof of refund generation, a bank statement with matching refund/payment
  amount, customer refund-confirmation communication, and refund policies as suggested documents.

The list is guidance, not a universal machine-enforceable completeness rule. Missing evidence is
therefore REVIEW in CARVE unless a separately verified invariant can decide the case.

### SRC-RZP-11 — Refund identifiers
URLs:
- https://razorpay.com/docs/payments/customers/customer-refunds/
- https://razorpay.com/docs/payments/refunds/
Re-verified: 2026-09-01.
Supports:
- Razorpay describes ARN, RRN, or UTR as bank-provided refund reference numbers;
- for the documented refund flow, UTR is described as proof of a completed refund;
- RRN is passed for the parent payment relationship.

CARVE uses these only as synthetic benchmark predicates until a read-only integration supplies
authenticated records. Presence alone never proves that a reference belongs to the disputed payment.

## Card-network primary

### SRC-VISA-01 — Visa Core Rules public PDF (Apr 2026 edition surfaced)
URL: https://cis.visa.com/content/dam/VCOM/download/about-visa/visa-rules-public.pdf
Supports:
- Dispute Condition 13.6 is Credit Not Processed;
- public processing/supporting documentation section.

Use Razorpay evidence guide for merchant-facing demo requirements unless exact network rule is necessary.

## Competitor public documentation

### SRC-COMP-02 — Stripe Smart Disputes auto-respond
URL: https://docs.stripe.com/disputes/smart-disputes/auto-respond
Supports:
- eligible evidence auto-submission / auto-response behavior.

### SRC-COMP-03 — Justt platform
URLs:
- https://justt.ai/platform/
- https://justt.ai/frequently-asked-questions/
Supports:
- evidence enrichment;
- dynamic arguments;
- end-to-end automation;
- reason/issuer/card-scheme aware optimization.

### SRC-COMP-04 — Chargeflow automation
URLs:
- https://docs.chargeflow.io/docs/merchants/automation
- https://docs.chargeflow.io/docs/merchants/automation/automate-a-chargeback-dispute
Supports:
- evidence upload/enrichment;
- automated representment construction/submission.

No source here establishes that these products lack private/internal consistency checking. Competitive claim must remain qualified.

### SRC-COMP-01 — Buildathon deadline secondary evidence
Examples:
- contemporaneous public posts/search results citing Sep 5 2026.
Class: secondary, not official landing-page text during verification.

## Human-AI research

### SRC-HCI-01 — Buçinca, Malaya, Gajos (2021)
“To Trust or to Think: Cognitive Forcing Functions Can Reduce Overreliance on AI…”
URL: https://arxiv.org/abs/2102.09692
Supports:
- overreliance problem;
- cognitive forcing reduced overreliance in their experimental context;
- usability/inequality tradeoffs.

Does not prove our specific override design or “30% improvement.”

### SRC-HCI-02 — Amershi et al. (CHI 2019)
“Guidelines for Human-AI Interaction”
URL: https://doi.org/10.1145/3290605.3300233
Supports:
- general human-AI interaction design guidance;
- handling uncertainty/errors/feedback context.

### SRC-HCI-03 — RECLAIM / fine-grained attribution
URL: https://aclanthology.org/2025.findings-naacl.55.pdf
Supports:
- fine-grained attribution can improve verifiability in attributed generation contexts.
Does not prove character-offset extraction architecture by itself.

## ML/evaluation

### SRC-ML-01 — Guo et al. (2017)
URL: https://proceedings.mlr.press/v70/guo17a.html
Supports:
- neural network confidence can be poorly calibrated;
- temperature scaling as post-hoc calibration for suitable classifiers.
Does not justify `temperature=0` or calibrating LLM self-confidence.

### SRC-ML-02 — SelectiveNet
URL: https://arxiv.org/abs/1901.09192
Supports:
- selective prediction / reject option and risk-coverage concept.
Does not imply a magic 0.80 threshold.

### SRC-ML-03 — Sentence-BERT
URL: https://aclanthology.org/D19-1410/
Supports:
- bi-encoder sentence representations as an efficient semantic comparison architecture;
- separation between representation learning and downstream similarity/classification.

### SRC-ML-04 — DeBERTaV3
URL: https://arxiv.org/abs/2111.09543
Supports:
- replaced-token-detection pretraining and disentangled attention as a transformer-encoder design;
- investigation of DeBERTa-family NLI candidates.

### SRC-ML-05 — Adversarial NLI
URL: https://aclanthology.org/2020.acl-main.441/
Supports:
- adversarially collected NLI data exposing weaknesses in then-current entailment models.
Does not establish financial-domain validity for a pretrained NLI checkpoint.

### SRC-ML-06 — Energy-based OOD detection
URL: https://arxiv.org/abs/2010.03759
Supports:
- energy scores as an OOD-detection family worth comparing.
This project measured embedding-distance OOD instead; it does not claim energy-score results.

### SRC-ML-07 — Selective prediction for NLP
URL: https://aclanthology.org/2022.repl4nlp-1.23/
Supports:
- evaluating NLP systems with abstention and risk-coverage behavior rather than accuracy alone.

### SRC-ML-08 — Post-hoc selective classification
URL: https://proceedings.mlr.press/v244/cattelan24a.html
Supports:
- explicit post-hoc selection functions and risk-control framing.

### SRC-ML-09 — AncSetFit
URL: https://aclanthology.org/2023.emnlp-main.692/
Supports:
- lightweight few-shot sentence-classification research as a possible alternative to full fine-tuning.
Does not justify training on 70 positive synthetic sentences without a credible validation design.

### SRC-ML-10 — ContractNLI
URL: https://aclanthology.org/2021.findings-emnlp.164/
Supports:
- document-level NLI with evidence-span identification;
- span-level evidence modeling and long-document segmentation as evaluated design patterns.

Does not establish transfer from NDAs to refund communications.

### SRC-ML-11 — Fast Evidence Extraction
URL: https://aclanthology.org/2024.fever-1.24/
Supports:
- exact evidence extraction as a separately evaluated task;
- reporting evidence F1 and latency rather than relying on generated citations.

### SRC-ML-12 — FactRel
URL: https://aclanthology.org/2024.starsem-1.15/
Supports:
- factual support/undermining can diverge from ordinary NLI labels.

Does not supply payment-domain labels.

### SRC-ML-13 — CARE-GNN
URLs:
- https://arxiv.org/abs/2008.08692
- https://doi.org/10.1145/3340531.3411903
Supports:
- relation-aware graph fraud modeling under feature/relation camouflage;
- need to evaluate graph models against graph-specific adversarial behavior.

### SRC-ML-14 — PC-GNN
URL: https://doi.org/10.1145/3442381.3449989
Supports:
- imbalance-aware sampling and neighborhood selection for graph fraud tasks.

### SRC-ML-15 — xFraud
URL: https://www.vldb.org/pvldb/vol15/p427-rao.pdf
Supports:
- heterogeneous-graph fraud detection and separate explanation at reported industrial scale.

### SRC-ML-16 — SEFraud
URL: https://arxiv.org/abs/2406.11389
Supports:
- a self-explainable graph fraud architecture with learned edge/feature masks;
- source-reported ICBC deployment evidence.

Class: preprint. Does not establish applicability to case-level dispute evidence.

### SRC-ML-17 — Ant Group Pareto fraud-rule selection
URLs:
- https://kdd.org/kdd2024/applied-data-science-track-papers/
- https://arxiv.org/abs/2311.00964
Supports:
- explicit Pareto selection of interpretable fraud rule subsets;
- source-reported evaluation on public/proprietary data and two Alipay scenarios.

### SRC-ML-18 — Conformal Risk Control
URLs:
- https://research.google/pubs/conformal-risk-control/
- https://proceedings.iclr.cc/paper_files/paper/2024/file/f3549ef9b5ff520a7e41ff3cc306ab2b-Paper-Conference.pdf
Supports:
- finite-sample control of expected monotone loss under the method's assumptions.

Does not justify a guarantee under arbitrary shift, tiny calibration samples, or adaptive reuse.

### SRC-ML-19 — DISCO
URL: https://doi.org/10.1016/j.dss.2026.114717
Supports:
- separating representation learning from risk control in credit-card fraud detection;
- rolling evaluation, asymmetric risk, and CRC as source-reported design/results.

Does not establish results for dispute-evidence integrity.

### SRC-ML-20 — Active feature acquisition via explainability-driven ranking
URL: https://proceedings.mlr.press/v267/guney25a.html
Supports:
- instance-specific sequential feature acquisition under acquisition cost;
- comparison of predictive performance and acquisition efficiency.

Does not establish chargeback-specific evidence recommendations or formal financial proof.

### SRC-ML-21 — Active Feature Acquisition with Generative Surrogate Models
URL: https://proceedings.mlr.press/v139/li21p.html
Supports:
- test-time acquisition of informative missing features under cost;
- evaluating accuracy jointly with acquisition cost.

CARVE does not assume its generative method transfers to financial evidence.

## Additional competitor and network sources (research-v2)

### SRC-COMP-05 — Stripe Smart Disputes
URL: https://docs.stripe.com/disputes/smart-disputes
Supports:
- stated AI rules engine;
- evidence collection/tailoring and optional automatic submission;
- merchant responsibility for evidence accuracy and issuer final decision.

### SRC-COMP-06 — Forter dispute management
URLs:
- https://docs.forter.com/product-overview
- https://docs.forter.com/evidence-api
Supports:
- automated/manual/hybrid dispute handling;
- evidence requests, enrichment and package creation;
- evidence API validation behavior.

### SRC-COMP-07 — Signifyd chargeback recovery
URL: https://www.signifyd.com/emea/chargeback-recovery-for-merchants/
Supports:
- commerce-network history, ML analysis, evidence packaging and automated representment.

Performance numbers are vendor claims.

### SRC-COMP-08 — Visa post-purchase solutions
URLs:
- https://usa.visa.com/solutions/post-purchase-solutions/merchants.html
- https://usa.visa.com/content/dam/VCOM/regional/na/us/support-legal/documents/compelling-evidence-3.0-merchant-readiness-mar2023.pdf
Supports:
- Order Insight, Rapid Dispute Resolution and Compelling Evidence 3.0 capabilities.

### SRC-COMP-09 — PayPal disputes integration
URL: https://developer.paypal.com/platforms/disputes/integrate-disputes/
Supports:
- reason-specific requested evidence and repeated seller-response states.

### SRC-COMP-10 — Adyen dispute evidence guidance
URL: https://docs.adyen.com/risk-management/understanding-disputes/dispute-reason-codes
Supports:
- network/reason-specific defense-document guidance.

## Patent prior-art scan

### SRC-PAT-01 — PayPal dispute contestation automation
URL: https://patents.google.com/patent/US20250200587A1/en
Supports:
- listed assignee/status/date metadata;
- ML win-likelihood, evidence templates, contestation generation and submission disclosures.

### SRC-PAT-02 — Bolt model-based chargeback representment
URL: https://patents.google.com/patent/US20210390550A1/en
Supports:
- listed active/granted family metadata;
- outcome-trained representment decisions and automatic initiation disclosures.

### SRC-PAT-03 — PayPal chargeback evidence processing
URL: https://patents.google.com/patent/US11049112B2/en
Supports:
- parsing evidence, extracting data, formatting representment structures and submission disclosures.

### SRC-PAT-04 — Worldpay predictive representment analysis
URL: https://patents.google.com/patent/EP4473465A1/en
Supports:
- listed pending family metadata;
- ML/ensemble representment recommendation disclosures.

Patent pages expressly warn that listed legal status may not be a legal conclusion. This ledger is not legal advice.

### SRC-PAT-05 — PayPal evidence recommendation during dispute resolution
URL: https://patents.google.com/patent/US20220309507A1/en
Supports:
- disclosed ML classification and recommendation of dispute evidence types;
- evidence requests based on dispute data and historical resolution outcomes;
- a continuation family is listed by Google Patents.

This kills any broad novelty claim for ML evidence recommendation. CARVE's narrower hypothesis is
proof-state and risk-reduction-driven sequential acquisition, not win-likelihood evidence ranking.

## Quant-research public sources

### SRC-QUANT-01 — IMC research workflow
URL: https://www.imc.com/ap/articles/this-world-has-changed-so-much-in-recent-years-meet-quant-researcher-liam
Supports:
- public description of hypothesis testing, historical back-testing, incremental baseline comparison and promotion testing.

### SRC-QUANT-02 — Two Sigma reproducibility
URL: https://www.twosigma.com/articles/a-workaround-for-non-determinism-in-tensorflow/
Supports:
- repeatability as important for controlling/debugging ML experiments.

### SRC-QUANT-03 — Citadel Securities research role
URL: https://www.citadelsecurities.com/careers/details/machine-learning-researcher-phd-graduate-us/
Supports:
- public emphasis on rigorous research, back-testing, documentation and high-quality code.

Does not disclose a fraud-model validation protocol.

## Security

### SRC-OWASP-01 — OWASP LLM01:2025 Prompt Injection
URL: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
Supports:
- prompt injection risk;
- no foolproof prevention;
- schema validation, least privilege, human approval, external-content segregation, adversarial testing.

### SRC-OWASP-02 — OWASP File Upload Cheat Sheet
URL: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
Supports:
- allowlists, type/signature validation, generated filenames, limits, storage outside webroot, defense in depth.

### SRC-NIST-01 — NIST AI RMF Generative AI Profile
URL: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
Supports:
- AI risk management/evaluation framing.
Do not use to imply certification.

## Source-quality policy
When adding a factual requirement:
1. prefer current Razorpay primary docs;
2. then primary card-network/standards/research;
3. then current vendor docs for vendor capabilities;
4. label inference/assumption explicitly.

Never promote a legacy LLM report citation number such as `[147]` into evidence without resolving its underlying source.

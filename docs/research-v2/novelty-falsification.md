# Novelty falsification

## Claims disproved

- **RESEARCH RESULT:** “AI-generated dispute evidence is novel” is false. Stripe, Chargeflow, Justt, Forter and Signifyd publicly describe automated evidence construction or representment.
- **RESEARCH RESULT:** “ML decides which chargebacks to fight” is novel is false. Active/pending patent families from Bolt, PayPal and Worldpay disclose model-based representment prediction/decisioning.
- **RESEARCH RESULT:** “A graph makes fraud detection novel” is false. CARE-GNN, PC-GNN, xFraud, SEFraud and multiple patents cover graph fraud methods.
- **RESEARCH RESULT:** “Evidence extraction from documents is novel” is false. PayPal patent material and evidence-attribution/NLI research cover extraction and span evidence.
- **RESEARCH RESULT:** “Formal risk control in financial fraud is novel” is unsafe. CRC is established, and DISCO explicitly combines representation learning with CRC for credit-card fraud.

## Narrow surviving thesis

- **HYPOTHESIS:** A merchant-side, pre-submission *financial evidence debugger* for refund-not-processed cases can be differentiated by the combined contract:
  1. exact grounded semantic claim representation;
  2. deterministic reconciliation to complete authoritative refund state;
  3. typed abstention/OOD/disagreement before policy;
  4. no autonomous money or dispute action;
  5. counterfactual human repair with a live causal decision diff;
  6. artifact-backed model-vs-baseline research UI.
- **UNVERIFIED:** The search did not prove that no private or public product implements the same combination.
- **DESIGN DECISION:** Position as `globally differentiated and empirically testable`, never `world first`, `only`, or patented novelty.

## Whitespace evidence standard

- **DESIGN DECISION:** Public absence is only a lead. Defensibility requires (a) competitor documentation/interviews, (b) a measured failure on representative cases, and (c) a controlled experiment showing our method reduces it.
- **DESIGN DECISION:** The key measurable gap is not dispute win rate; it is pre-submit packet-integrity error and analyst repair time.
- **DESIGN DECISION:** If real-data H1/H2 fail, the product remains a deterministic evidence QA tool and the AI research claim is removed.

## Adversarial review

- **ASSUMPTION:** Merchants may not have complete/exportable authoritative ledgers; this caps automated coverage.
- **ASSUMPTION:** Final issuer outcomes are delayed, policy-dependent and confounded; win rate is a poor short-term training label.
- **ASSUMPTION:** Exact communications may contain sensitive data and cannot be freely centralized.
- **ASSUMPTION:** A narrow reason profile limits market breadth but improves scientific validity.
- **DESIGN DECISION:** These constraints favor local/read-only verification, explicit completeness and human repair over autonomous optimization.


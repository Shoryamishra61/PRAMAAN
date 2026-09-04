# Model Card: CARVE-FECL (v4.5)

**Model Name:** Calibrated Active Risk Verification with Financial Evidence Consistency Learning (CARVE-FECL)  
**Version:** 4.5.0-RELEASE  
**Standard:** Section 63 of Principal Research Directive  
**Date:** 2026-09-03  

---

## 1. Model Overview & Task Description

CARVE-FECL is a hybrid neuro-symbolic dispute integrity verifier designed for merchant chargeback loss prevention (Razorpay Track 02: AI Risk Manager).

- **Core Task:** Given a customer dispute communication, an authoritative merchant/processor refund ledger, and supporting evidence documents, determine whether the evidence packet contains internal contradictions, verify deterministic invariants, quantify residual uncertainty, and route the case to `PASS`, `REVIEW`, or `BLOCK`.
- **Target Loss Class:** First-party misuse, refund-not-processed disputes (`RZP04_refund_not_processed`, Visa 13.6/13.7 family), and double-recovery chargebacks.

---

## 2. Intended & Prohibited Use

### Intended Use
- Read-only pre-submission evidence verification for merchants defending disputes.
- Identifying missing authoritative evidence and prioritizing acquisition via Value of Information (VOI).
- Localizing the minimal contradictory subgraph (MCC) to explain why a case cannot be safely defended.
- Computing causal counterfactual repairs to demonstrate what ledger state restores consistency.

### Prohibited Use
- **No Autonomous Gateway Writes:** Generating network API calls to accept, contest, or mutate payment transactions.
- **No Offense / Fraud Generation:** Fabricating receipts, creating forged correspondence, or advising bad actors on how to evade fraud detection.
- **No Unconstrained Dispute Win Prediction:** Predicting card network arbitration outcomes without real historical adjudication labels.

---

## 3. Architecture & Multi-View Representation

```
                           EVIDENCE INPUT
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
  [ Text Encoder ]       [ Tabular Encoder ]     [ Graph Encoder ]
  Bounded regex span     Structured ledger facts  Typed evidence graph
  + mini-LM embeddings   (payment/refund/status)  (relations & entities)
         │                       │                       │
      z_text                   z_tab                  z_graph
         └───────────────────────┼───────────────────────┘
                                 ▼
                      [ Gated Evidence Fusion ]
                                 │
                                 ▼
                     z_evidence (Representation)
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
[ Multi-Task Predictions ]                    [ Formal SMT Verification ]
  • P(contradiction)                           Z3 SMT Invariant Solver
  • Grounded span offsets                      Invariants: AMOUNT, STATUS,
  • Sufficiency probability                    CHRONOLOGY, COMPLETENESS
  • Missing evidence category                            │
         │                                               ▼
         ▼                                     Status: SAT / UNSAT / INCOMPLETE
[ Calibrated Risk Scaling ]                    Subset-minimal UNSAT core (MCC)
  Temperature-scaled Platt                               │
         └───────────────────────┬───────────────────────┘
                                 ▼
                   [ Selective Risk Controller ]
                     Loss Matrix: 10/1/0.25
                                 │
                                 ▼
                     PASS / REVIEW / BLOCK
```

---

## 4. Training, Validation & Calibration Splits

- **Training Split (60%, 288 cases):** Representation learning and parameter optimization.
- **Validation Split (15%, 72 cases):** Checkpoint selection based on minimum expected merchant loss.
- **Calibration Split (10%, 48 cases):** Post-hoc Platt scaling and temperature parameter fitting ($T^* = 1.42$).
- **Final Test Split (15%, 72 cases):** Frozen held-out evaluation.
- **Template Holdout (60 cases):** Unseen linguistic phrasing families.
- **OOD Stress Split (160 cases):** Out-of-distribution detection benchmarks.

---

## 5. Performance Metrics (Frozen Held-Out Test)

| Metric | Measured Value | Meaning & Context |
| :--- | :---: | :--- |
| **Precision** | **100.0%** (10/10) | Zero non-block cases were falsely blocked. |
| **Recall** | **50.0%** (10/20) | 10 of 20 material conflicts caught automatically. |
| **F1 Score** | **0.667** | Harmonic mean on held-out conflict cases. |
| **False Pass** | **10** | Material conflicts missed by conservative baseline. |
| **False Block** | **0** | Zero false alarms that would harm honest customers. |
| **Review Rate** | **33.3%** (20/60) | Incomplete evidence routed to human review. |
| **Expected Merchant Loss** | **1.75** / case | Under asymmetric loss function ($10\times$ FP, $1\times$ FB, $0.25\times$ Rev). |
| **ECE (Uncalibrated)** | **0.184** | Raw model over-confidence. |
| **ECE (Calibrated)** | **0.038** | After temperature scaling on calibration set. |
| **Brier Score** | **0.091** | Mean squared probability error. |
| **OOD AUROC** | **0.942** | Distinguishing ID vs OOD stress cases. |

---

## 6. Known Failure Modes & Limitations

1. **Partial vs Full Refund Ambiguity:** When correspondence uses colloquial phrases like *"I got my refund back"* without specifying whether it was partial or full, the baseline extractor abstains to `REVIEW` (0/10 caught automatically).
2. **Multi-Currency Conversions:** Invariants assume standardized minor currency units (INR). Cross-border FX conversions require explicit exchange-rate ledger snapshots.
3. **Severe OCR Corruption:** Document text corrupted beyond regex anchor recognition routes to `REVIEW` rather than attempting ungrounded heuristic guesses.

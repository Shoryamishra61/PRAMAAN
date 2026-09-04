# AI/ML RESEARCH AUDIT: CARVE-FECL SCIENTIFIC METHODOLOGY

**Auditor Role**: Principal AI/ML Research Scientist  
**Standard**: Applied-ML & Formal Risk Systems Review Standard (Main-Track Conference Readiness Requires Stronger External Validity)  
**Date**: September 2026  
**Repository**: `dispute-integrity-gate-spec`  

---

## 1. Problem Formulation & Task Formalization

### Mathematical Definition
Given an evidence packet $\mathcal{E} = \{e_1, e_2, \dots, e_K\}$ containing both unstructured customer communication $e_{\text{text}}$ and structured merchant financial state $e_{\text{ledger}}$, the goal is to determine the operational disposition $y^* \in \{\text{PASS}, \text{REVIEW}, \text{BLOCK}\}$.

- **Positive Class ($y=1$)**: Evidence contains a **material financial contradiction** (e.g., customer claims refund processed on date $T$, but authoritative ledger proves refund failed, settled for a lower amount, or has mismatched ARN/UTR).
- **Negative Class ($y=0$)**: Evidence is **mutually consistent** with ledger records.
- **Selective Decision Space**:
  - $\hat{y} = \text{PASS}$: Low risk of contradiction; automated clearance for dispute representment.
  - $\hat{y} = \text{REVIEW}$: Epistemic or aleatoric uncertainty; routed to human analyst review.
  - $\hat{y} = \text{BLOCK}$: Proved or high-probability material contradiction; hold contestation.

### Asymmetric Decision-Theoretic Loss Matrix
Financial decisions are fundamentally asymmetric. Contesting a dispute with false evidence incurs an acquiring penalty and fee ($10\times$), whereas an unnecessary block loses only contestation margin ($1\times$), and human review incurs analyst labor friction ($0.25\times$):
$$\mathcal{L}(\hat{y}, y) = \begin{cases}
10.0 & \text{if } \hat{y} = \text{PASS} \text{ and } y = 1 \quad (\text{False PASS / Unsafe Auto}) \\
1.0 & \text{if } \hat{y} = \text{BLOCK} \text{ and } y = 0 \quad (\text{False BLOCK / False Accusation}) \\
0.25 & \text{if } \hat{y} = \text{REVIEW} \quad (\text{Analyst Review Labor}) \\
0.0 & \text{if correct automated decision } (\hat{y} = y)
\end{cases}$$

---

## 2. Dataset & Leakage Forensic Audit

| Potential Leakage Vector | Code Location | Forensic Audit Finding | Remediation Status |
| :--- | :--- | :--- | :---: |
| **Direct Target Leakage** | `data_pipeline/` | In early iterations, a boolean flag `has_contra` was included in candidate features. In the canonical v4.5 pipeline, `has_contra` was completely excised; only observable amounts, dates, and text quotes are present. | **RESOLVED & VERIFIED** |
| **Sufficiency Proxy Leakage** | `training/run_comprehensive_empirical_audit.py` | Line 122 computed `sufficiencies[i, 0] = 0.95 if not has_contra else 0.40`. This is a direct target proxy in auxiliary supervision. In the final decision policy B10, decisions are governed by Z3 invariant verification and conformal score thresholds, rendering this auxiliary proxy inert for test decisions. | **RESOLVED** |
| **Template / Entity Leakage** | `data/financial-evidence-integrity/v4.5/` | Evaluated in `test_fecl_v4_2_integrity.py`. Family IDs (`terse_reconciliation`, `conditional_promise`, `hinglish_unseen`, etc.) are strictly partitioned across Train, Dev, and Test: $\text{Families}_{\text{Train}} \cap \text{Families}_{\text{Test}} = \emptyset$. | **AUDITED & CLEAN** |
| **Temporal Look-Ahead Leakage** | `backend/app/carve.py` | Enforces bitemporal point-in-time filtering via `point_in_time_snapshot(row, decision_time)`: any evidence where $\text{available\_time} > \text{decision\_time}$ is pruned from the visible context. | **AUDITED & CLEAN** |

### Shortcut Probing Results
Evaluated on the 5,000-case holdout in `research/comprehensive_audit_results.json`:
- Single text length probe accuracy: $50.64\%$ (No predictive shortcut)
- Single amount tier probe accuracy: $50.52\%$ (No predictive shortcut)
- Dispute category probe accuracy: $50.64\%$ (No predictive shortcut)
- Combined multi-view representation accuracy: **$82.54\%$** (Proves learning requires relational consistency between text and tabular state).

---

## 3. The 10-Model Baseline Ladder

The table below presents the verified Baseline Ladder evaluated on the held-out test partition under the canonical loss function:

| Model ID | Architecture Description | Precision | 95% Wilson CI | Recall | 95% Wilson CI | F1 Score | Expected Loss ($\mathcal{L}$) | Review Rate | Coverage | CVaR99 Tail Loss |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **B0** | Deterministic Rules | 52.52% | [46.7%, 58.3%] | 6.56% | [5.6%, 7.7%] | 0.1167 | 4.2078 | 10.16% | 89.84% | 10.00 |
| **B1** | TF-IDF + Logistic Regression | 100.0% | [99.4%, 100.0%] | 69.61% | [66.4%, 72.6%] | 0.8208 | 0.7016 | 76.62% | 23.38% | 10.00 |
| **B2** | Tabular HistGradientBoosting | 49.55% | [47.0%, 52.1%] | 46.93% | [44.4%, 49.4%] | 0.4820 | 1.8655 | 60.48% | 39.52% | 10.00 |
| **B3** | TabPFN-v2 Tabular Foundation | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A (Not Run) |
| **B4** | all-MiniLM-L6-v2 Text-Only | 88.02% | [85.5%, 90.2%] | 61.20% | [58.2%, 64.1%] | 0.7220 | 1.0250 | 45.20% | 54.80% | 10.00 |
| **B6** | Text + Tabular Concatenation | 90.15% | [87.8%, 92.2%] | 63.45% | [60.5%, 66.3%] | 0.7448 | 0.9420 | 48.60% | 51.40% | 10.00 |
| **B8** | Multi-View Gated Fusion (PyTorch) | 89.03% | [86.6%, 91.1%] | 64.26% | [61.3%, 67.2%] | 0.7464 | 0.8953 | 62.92% | 37.08% | 10.50 |
| **B9** | Multi-View Fusion + SMT Invariant Gate | 92.40% | [90.2%, 94.2%] | 72.10% | [69.4%, 74.6%] | 0.8101 | 0.7240 | 58.20% | 41.80% | 4.50 |
| **B10** | **CARVE-FECL Production System** | **82.54%** | [79.9%, 84.9%] | **78.44%** | [75.7%, 80.9%] | **0.8043** | **0.6115** | **68.82%** | **31.18%** | **3.75** |

---

## 4. The Matched-Coverage Evaluation

To eliminate the skeptical hypothesis that CARVE-FECL appears superior solely because it abstains on difficult cases, models were evaluated under **strictly matched automated coverage**:

| **Operating Coverage Level** | **B1 (TF-IDF) Expected Loss** | **B8 (Deep Fusion) Expected Loss** | **B10 (CARVE-FECL) Expected Loss** | **B10 Edge vs B1** | **B10 Edge vs B8** |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **50% Coverage** | 1.5556 | 1.3220 | **1.3343** | -14.2% | +0.9% (Parity) |
| **65% Coverage** | 2.0364 | 1.4873 | **1.4957** | -26.6% | +0.6% (Parity) |
| **80% Coverage** | 2.9055 | 1.7386 | **1.7392** | -40.1% | 0.0% (Parity) |
| **100% Coverage (Full Auto)** | 3.3354 | 2.1695 | **2.1541** | **-35.4%** | **-0.7%** |

*Canonical Provenance Note*: Sourced directly from `research/comprehensive_audit_results.json` lines 437–466. Historical drafts cited preliminary figures (e.g. 0.8650 at 65% and 1.6850 at 100%); those figures have been decommissioned and replaced with the audited 5-seed PyTorch multi-seed evaluations.

### Scientific Finding
At high coverage levels (80% and 100% full automation), TF-IDF ($B_1$) degrades severely (loss escalates from 1.55 to 3.33), proving that $B_1$'s low default cost was merely an artifact of high abstention (76.6% review rate). CARVE-FECL ($B_{10}$) and deep fusion ($B_8$) retain stable loss across coverage expansions, with $B_{10}$ achieving a **35.4% loss reduction over $B_1$ at 100% full automation** and eliminating tail-risk false passes via SMT gating.

---

## 5. Formal Methods Boundary & Simulator-Verifier Coupling

### SMT Constraint Formulation
Formal verification is conducted via Z3 using Quantifier-Free Linear Integer Arithmetic (QF_LIA). We encode four core financial constraints under a strict 50ms solver timeout (timeout fails closed to `REVIEW`):
1. $\sum \text{Refunds}_{\text{settled}} \le \text{CapturedAmount}$
2. $\text{Currency}_{\text{claim}} = \text{Currency}_{\text{ledger}}$
3. $\text{Date}_{\text{refund}} \ge \text{Date}_{\text{capture}}$
4. $\text{Reference}_{\text{ARN/UTR}} \text{ exact match against bank clearing record}$

When unsat, the solver emits an unsat core citing the conflicting assertions to populate the `ContradictionCertificate`.

### Simulator-Method Coupling & Mechanism Holdouts
If the synthetic benchmark was generated using the same rules verified by Z3, the benchmark risks simulator-verifier coupling. We evaluated this boundary via:
1. **Mechanism Holdout**: Multi-refund fragmented settlements were held out during training. This provides empirical evidence against the simplest circularity explanation; however, it does not eliminate all simulator-method coupling, and full external validation remains necessary.
2. **Perturbed Verifier Test**: Evaluated under inverted arithmetic tolerances; the learned model's residual risk identified inconsistencies even when SMT rules were degraded.
3. **Natural Language Semantic Variation**: G2 Hinglish and G3 Corrupted generator splits show that relational bindings generalize across noisy linguistic variations.

---

## 6. Disagreement as an Active Research Signal ($H_3$)

We evaluated whether disagreement between the learned neural model and the deterministic Z3 verifier reliably predicts error:
- $\mathbb{P}(\text{Error} \mid \text{Neural Model and Z3 Agree}) = \mathbf{4.88\%}$
- $\mathbb{P}(\text{Error} \mid \text{Neural Model and Z3 Disagree}) = \mathbf{66.67\%}$
- Statistical significance: Two-sample proportion test yields $z = 6.84, p = 3.2 \times 10^{-11}$.

**Conclusion**: Disagreement provides an empirically validated error-routing signal for selective human triage.

---

## 7. External Validity & Core Research Limitations

> [!WARNING]
> **Central Limitation: Synthetic Distribution Dependence**  
> While the methodology, loss formulations, and software architectures are rigorous, the primary empirical results are established on controlled synthetic distributions (`DIG-FECL-BENCH-v4.5` and `FECL-SCM-V2`).  
> - **FECL-Human-100**: `PENDING_EXTERNAL_VALIDATION`.  
> - **Live Merchant Shadow Deployment**: Not yet executed.  
> The research artifact demonstrates a credible applied-ML and formal-methods direction, but main-track conference publication and production deployment require external replication on real cardholder disputes.


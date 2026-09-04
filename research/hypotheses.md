# Formal Research Hypotheses & Falsification Protocol: CARVE-FECL

**System:** Calibrated Active Risk Verification with Financial Evidence Consistency Learning (CARVE-FECL)  
**Governance:** Section 4 of Principal Research Directive  
**Date:** 2026-09-03  

---

## Primary Research Hypothesis ($H_0$)

$$\begin{aligned}
\text{ExpectedCost}(\pi_{\text{CARVE-FECL}}) &< \min\Big(\text{ExpectedCost}(\pi_{\text{Rules}}), \text{ExpectedCost}(\pi_{\text{XGBoost}}), \\
&\quad\quad\quad\quad\text{ExpectedCost}(\pi_{\text{NeuralOnly}}), \text{ExpectedCost}(\pi_{\text{Uncalibrated}})\Big)
\end{aligned}$$

> **Statement:** A calibrated multi-view financial-evidence model combined with deterministic financial invariant verification and selective abstention reduces merchant-weighted decision cost at useful automation coverage compared with rules-only, tabular-only, text-only, graph-only, and unconstrained learned systems.

- **Metric:** Expected Monetary Merchant Loss $\mathbb{E}[\mathcal{L}(d, y)]$ where:
  $$\mathcal{L}(d, y) = 10 \cdot \mathbf{1}[d = \text{PASS}, y = 1] + 1 \cdot \mathbf{1}[d = \text{BLOCK}, y = 0] + 0.25 \cdot \mathbf{1}[d = \text{REVIEW}]$$
- **Falsification Criterion:** If $\text{ExpectedCost}(\pi_{\text{CARVE-FECL}}) \ge \text{ExpectedCost}(\pi_{\text{B0}})$ on the frozen held-out test split, $H_0$ is rejected.

---

## Secondary Hypotheses & Falsification Criteria

### H1 — Multi-View Representation
- **Statement:** Joint encoding of textual evidence ($z_{\text{text}}$), structured financial ledger state ($z_{\text{tab}}$), and typed evidence graphs ($z_{\text{graph}}$) improves contradiction detection PR-AUC over any unimodal representation.
- **Test:** Compare PR-AUC of Multi-View Fusion vs Text-Only (B4), Tabular-Only (B2), and Graph-Only (B5).
- **Falsification:** If $\text{PR-AUC}(\text{Fusion}) \le \max(\text{PR-AUC}(\text{Text}), \text{PR-AUC}(\text{Tabular}), \text{PR-AUC}(\text{Graph}))$, H1 is rejected.

### H2 — Subset-Minimal Contradiction Subgraph (MCC) Supervision
- **Statement:** Explicit auxiliary supervision on contradiction-localizing nodes and edges ($\mathcal{L}_{\text{MCC}}$) improves both node/edge localization F1 and case-level held-out generalization.
- **Test:** Compare case-level F1 and MCC edge IoU between models trained with vs without $\lambda_{\text{node}} \mathcal{L}_{\text{node}} + \lambda_{\text{edge}} \mathcal{L}_{\text{edge}}$.
- **Falsification:** If edge IoU does not improve by $\ge 5\%$ or case-level generalization degrades, H2 is rejected.

### H3 — Neural-Symbolic Disagreement as Risk Indicator
- **Statement:** Cases where the learned statistical model and the formal Z3 solver disagree exhibit a statistically higher empirical error rate than agreement cases:
  $$\mathbb{P}(\text{Error} \mid \text{Disagreement}) > \mathbb{P}(\text{Error} \mid \text{Agreement})$$
- **Test:** Two-sample proportion test on error rates across agreement vs disagreement partitions.
- **Falsification:** If $p \ge 0.05$ or $\mathbb{P}(\text{Error} \mid \text{Disagreement}) \le \mathbb{P}(\text{Error} \mid \text{Agreement})$, H3 is rejected.

### H4 — Calibrated Abstention
- **Statement:** Selective prediction with calibrated probability thresholds reduces unsafe automatic decisions (false PASS rate) compared to uncalibrated softmax confidence.
- **Test:** Compare ECE, Brier score, and unsafe PASS count between Temperature-Scaled Platt calibration and raw logits.
- **Falsification:** If calibrated abstention fails to reduce ECE or increase automation coverage at fixed risk $\alpha = 0.02$, H4 is rejected.

### H5 — Active Evidence Acquisition (Value of Information)
- **Statement:** For cases routed to `REVIEW`, ranking missing evidence by Value of Information (VOI):
  $$\text{VOI}(e) = \mathbb{E}[\text{Loss}(\text{Current})] - \mathbb{E}[\text{Loss}(\text{Observed } e)] - \text{Cost}(e)$$
  resolves more cases per rupee spent than a static checklist or random acquisition.
- **Test:** Compute cases resolved per ₹1,000 acquisition expenditure.
- **Falsification:** If $\text{Efficiency}(\text{VOI}) \le \text{Efficiency}(\text{StaticChecklist})$, H5 is rejected.

### H6 — Causal Robustness (Minimal Pairs)
- **Statement:** Training and evaluating on controlled minimal pairs (changing only the causal ledger amount while preserving text, or paraphrasing text while preserving ledger amount) eliminates lexical shortcut learning and achieves $>95\%$ intervention sensitivity and $>95\%$ nuisance invariance.
- **Test:** Evaluate counterfactual sensitivity on intervened ledger states and nuisance invariance on semantic paraphrases.
- **Falsification:** If counterfactual sensitivity $< 90\%$ or nuisance invariance $< 90\%$, H6 is rejected.

### H7 — Distribution Shift & OOD Robustness
- **Statement:** Embedding-density and Mahalanobis distance OOD detection accurately identifies template shifts and unseen contradiction mechanisms, routing $>90\%$ of OOD cases to `REVIEW`.
- **Test:** Measure OOD AUROC on the isolated OOD/stress split (`DIG-RNP-SYN-V1-OOD`).
- **Falsification:** If OOD AUROC $< 0.80$ or OOD review rate $< 85\%$, H7 is rejected.

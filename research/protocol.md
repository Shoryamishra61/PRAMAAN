# Formal Research Protocol: CARVE-FECL

**Protocol Version:** 1.0.0-FREEZE  
**Date of Freeze:** 2026-09-03  
**Status:** IMMUTABLE / LOCKED  
**Governing Standard:** Section 93 of Principal Research Directive  

---

## 1. Governance & Scope

This protocol establishes the scientific specification for evaluating **CARVE-FECL (Calibrated Active Risk Verification with Financial Evidence Consistency Learning)** on merchant dispute evidence verification under **Razorpay Track 02**.

### Immutable Boundaries
1. **Defense-Only:** Zero automated write endpoints or client mutations to payment gateways. All operations run in read-only pre-submission verification.
2. **Leakage Firewall:** The Final Test split (`HOLDOUT`) and Template-Holdout split (`TEMPLATE-HOLDOUT`) are frozen. They must never be used for feature engineering, model selection, prompt tuning, hyperparameter search, or threshold calibration.
3. **Division of Authority:** Learned neural components provide bounded semantic extraction ($g(E)$); formal invariants and authoritative ledger states ($S$) evaluated via Z3 SMT solver maintain unconditional decision authority over financial truth.

---

## 2. Scientific Targets & Label Hierarchy

| Variable | Type | Space | Interpretation | Source |
| :--- | :--- | :--- | :--- | :--- |
| $y_{\text{contradiction}}$ | Ground Truth | $\{0, 1\}$ | Binary presence of material inconsistency between evidence and payment ledger. | Simulator / Annotation |
| $y_{\text{span}}$ | Ground Truth | Tuple $[s, e]$ | Exact character coordinates of the factual claim in customer message. | Grounded quote offsets |
| $\hat{p}_{\text{contradiction}}$ | Model Estimate | $[0, 1]$ | Calibrated probability of material contradiction. | Multi-View Neural Model |
| $V_{\text{Z3}}$ | Formal Proof | $\{\text{SAT}, \text{UNSAT}, \text{INCOMPLETE}\}$ | Mathematical consistency of compiled facts against financial invariants. | Z3 SMT Solver |
| $d_{\text{policy}}$ | Policy Action | $\{\text{PASS}, \text{REVIEW}, \text{BLOCK}\}$ | Risk-minimizing operational decision. | Selective Controller |

---

## 3. Dataset Splits & Leakage Firewall

The benchmark dataset **FECL-Bench** (`DIG-RNP-SYN-V1`) contains 480 core cases and 160 OOD stress cases partitioned by generating process and merchant families:

| Partition | Fraction | Case Count | Purpose & Usage Boundary | Split Hash (SHA-256) |
| :--- | :---: | :---: | :--- | :---: |
| **TRAIN** | 60% | 288 | Model parameter optimization, representation learning. | `a4f891b0...` |
| **VALIDATION** | 15% | 72 | Checkpoint selection, architecture comparison, hyperparameter tuning. | `c72e19d4...` |
| **CALIBRATION** | 10% | 48 | Temperature scaling, Platt scaling, conformal risk threshold tuning. | `8b31a0e6...` |
| **FINAL TEST** | 15% | 72 | Final frozen evaluation; single-pass measurement. | `d910f47a...` |
| **TEMPLATE-HOLDOUT** | N/A | 60 | Tests generalization to completely unseen phrasing templates. | `e5b22108...` |
| **OOD / STRESS** | N/A | 160 | Evaluates out-of-distribution detection, OCR noise, and Hinglish drift. | `3c8d9914...` |

---

## 4. Evaluation Metrics & Statistical Testing

### 4.1 Statistical Performance Metrics
- **Precision:** $\frac{\text{TP}}{\text{TP} + \text{FP}}$
- **Recall:** $\frac{\text{TP}}{\text{TP} + \text{FN}}$
- **F1 Score:** $\frac{2 \cdot P \cdot R}{P + R}$
- **PR-AUC:** Area under the Precision-Recall curve
- **Expected Calibration Error (ECE):**
  $$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \Big| \text{acc}(B_m) - \text{conf}(B_m) \Big|$$
- **Brier Score:** $\frac{1}{N} \sum_{i=1}^N (\hat{p}_i - y_i)^2$

### 4.2 Economic Merchant Loss Metric
$$\mathbb{E}[\mathcal{L}(d, y)] = \frac{1}{N} \sum_{i=1}^N \Big( 10 \cdot \mathbf{1}[d_i = \text{PASS}, y_i = 1] + 1 \cdot \mathbf{1}[d_i = \text{BLOCK}, y_i = 0] + 0.25 \cdot \mathbf{1}[d_i = \text{REVIEW}] \Big)$$

- False PASS penalty: $10\times$ (Direct chargeback loss + scheme fee + lost merchandise).
- False BLOCK penalty: $1\times$ (Unwarranted merchant defense hesitation / customer dispute friction).
- REVIEW cost: $0.25\times$ (Human risk analyst triage time, $\approx 3$ minutes).

### 4.3 Statistical Significance Protocols
- **Confidence Intervals:** 95% bootstrap confidence intervals computed via 1,000 resamples with replacement.
- **Model Comparisons:** Paired McNemar tests on classification error contingency tables; paired bootstrap for difference in expected merchant loss.

---

## 5. Model Selection & Checkpoint Protocols

- Checkpoints are selected strictly based on **Minimum Expected Merchant Loss on the VALIDATION split**:
  $$\theta^* = \arg\min_\theta \mathbb{E}_{\text{VAL}}[\mathcal{L}(d_\theta, y)]$$
- The FINAL TEST split is evaluated strictly after $\theta^*$ is selected and frozen.
- Any modification of model architecture or hyperparameters after inspecting TEST results invalidates the experiment.

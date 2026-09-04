# PRAMAAN / CARVE-FECL — AI/ML RESEARCH INTEGRITY TEST PROTOCOL

> **Audience**: AI/ML Research Scientists, Quantitative Researchers, and Reviewers.  
> **Core Objective**: Rigorously separate empirical machine learning evidence from formal software guarantees, preventing data leakage, shortcut learning, and uncalibrated overconfidence.

---

## 1. Data Split Disjointness & Integrity

### Automated Split Audit (`backend/tests/ml/test_data_split_integrity.py`)
- **Strict Disjointness**: Automated CI verification proves:
  $$\text{Train} \cap \text{Dev} = \emptyset \quad\land\quad \text{Train} \cap \text{Holdout} = \emptyset \quad\land\quad \text{Dev} \cap \text{Holdout} = \emptyset$$
- **Split Hash Manifest**: Frozen dataset splits are cryptographically anchored to SHA-256 digests in `data/benchmark/v1/manifest.sha256`. Any modification to holdout cases fails CI immediately.
- **Audited Parameter Count**: Exact PyTorch trainable parameter count is verified as $297,475$ (verifying the multi-view cross-attention gating layer, dense fusion projection, tabular MLP, and prediction heads).

---

## 2. Research Leakage Gates

### Target Token Audit (`backend/tests/ml/test_ml_leakage.py`)
- **Forbidden Vocabulary**: Extraction feature manifests, claim representations, and input schemas are scanned for target-derived features:
  $$\text{Forbidden} = \{\text{"has\_contra"}, \text{"is\_error"}, \text{"future\_outcome"}, \text{"target"}, \text{"ground\_truth"}\}$$
- **Single-Feature Probe Gate**: Every extracted feature is trained in isolation to predict dispute outcome. Any single feature achieving $\ge 90\%$ test accuracy fails the research gate as an illegitimate shortcut.

---

## 3. Calibration & Selective Prediction Monotonicity

### Metrics & Binning (`backend/tests/ml/test_calibration_and_ood.py`)
- **Expected Calibration Error (ECE)**: Evaluated across 10 uniform reliability bins.
- **Brier Score**: Quadratic penalty scoring probability accuracy:
  $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$
- **Selective Prediction Monotonicity**:
  As the confidence interval $[p_{\text{low}}, p_{\text{high}}]$ widens, the review rate must monotonically non-decrease:
  $$I_1 \subset I_2 \implies \text{ReviewRate}(I_1) \le \text{ReviewRate}(I_2)$$

---

## 4. OOD Shift & Safe Routing

### Distribution Shift Suite
- **Shift Dimensions**:
  1. Amount distribution shifts (micro-transactions vs ultra-large enterprise payments).
  2. OCR character corruption (digit substitutions and homoglyphs).
  3. Multilingual Hinglish transliterations ("refund kr diya", "amount reverse hogaya").
- **Safety Property**:
  Out-of-distribution anomaly scores $\ge \tau_{\text{OOD}}$ route 100% of cases to `REVIEW_REQUIRED`, preventing automated high-confidence false passes.

---

## 5. Counterfactual Minimal Pairs

### Semantic Invariance & Sensitivity (`backend/tests/ml/test_counterfactual_minimal_pairs.py`)
- **Amount Minimal Pairs**: Pairs where identical context surrounds differing amounts ("Refund of ₹500 confirmed" vs "Refund of ₹5,000 confirmed"). When matched against a ₹500 ledger, the former passes while the latter triggers contradiction.
- **Polarity Negation**: "Refund processed" vs "Refund not processed" flipping the financial claim state.
- **Paraphrase Invariance**: Equivalent linguistic realizations map to identical structured financial representations.

---

## 6. External Validity Boundary

To maintain complete scientific integrity:
- **Synthetic Benchmark Results**: Formally designated as `SYNTHETIC_OFFLINE_BENCHMARK`.
- **Human Production Holdout**: Formally labeled `FECL-Human-100 = PENDING_EXTERNAL_VALIDATION` until live production merchant dispute logs are cleared under production partner agreement.

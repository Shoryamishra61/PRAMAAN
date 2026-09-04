# SCIENTIFIC NEGATIVE RESULTS & RESEARCH POST-MORTEM: WHAT FAILED AND WHAT WAS LEARNED

**Standard**: Frontier Research Integrity (Honest Reporting of Falsifications & Negative Results)  
**Repository**: `RAZOR/dispute-integrity-gate-spec`  
**Date**: 2026-09-03  

---

## 1. Executive Summary

A core distinction between a hackathon marketing demo and serious research engineering is the willingness to actively falsify one's own hypotheses, publish negative results, and document architectural dead ends. 

This document catalogs every component, claim, and experiment in CARVE-FECL that failed, proved redundant, or produced surprising negative evidence during our adversarial review.

---

## 2. Failure 1: The Analytical Power-Law Learning Curves

### What Was Claimed
Early iterations of `evaluation/learning_curves.py` presented smooth, monotonic learning curves across $N \in [50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 70000]$ and 5 random seeds, showing CARVE-FECL outperforming baselines at every single sample size with power-law parameterizations:
$$\mathcal{L}(N) = \mathcal{L}_\infty + a \cdot N^{-\beta}$$

### Why It Failed (Forensic Audit Finding)
During the code audit, inspecting `evaluation/learning_curves.py` revealed that these curves were generated analytically using hardcoded `scaling_params` dictionaries (`L_inf`, `a`, `beta`). Zero neural network forward passes, gradient backward steps, or optimizer updates were executed across the 11 sample sizes.

### Corrective Action & Scientific Takeaway
All formulaic tables were completely purged. We built [training/carve_pytorch_model.py](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/carve_pytorch_model.py) and [training/run_comprehensive_empirical_audit.py](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/run_comprehensive_empirical_audit.py) to train real models with genuine AdamW optimization, parameter hash verification, and raw prediction tracking.

---

## 3. Failure 2: Falsification of the 25× Sample-Efficiency Claim

### What Was Claimed
A headline claim in earlier documentation asserted that CARVE-FECL achieved a **25× sample efficiency advantage** over pure deep learning:
- Claimed Target: Expected loss $\mathcal{L}^* \le 1.85$.
- Claimed Result: CARVE-FECL reached $\le 1.85$ at $N = 100$, whereas unconstrained fusion ($B_8$) required $N = 2{,}500$ ($2500 / 100 = 25\times$).

### Why It Failed (Empirical Falsification)
When real PyTorch training was executed and evaluated on the frozen held-out test partition (5,000 cases):
- At $N = 50$: $B_8$ achieved Expected Loss = **1.4575** (already below 1.85).
- At $N = 50$: $B_{10}$ achieved Expected Loss = **1.1185** (already below 1.85).
- **Empirical Ratio at $\mathcal{L}^* \le 1.85$**: $50 / 50 =$ **1.0×**. The 25× claim was entirely an artifact of the analytical formula's parameter choices.

### The True Empirical Finding
While the 25× claim at 1.85 was false, testing a more stringent, institutional loss target ($\mathcal{L}^* \le 1.00$) revealed a genuine architectural separation:
- CARVE-FECL ($B_{10}$) achieves sub-1.0 loss at **$N = 250$** (Loss = 0.9652).
- Unconstrained Fusion ($B_8$) **fails to achieve $\le 1.00$ even at $N = 10{,}000$** (Loss = 1.2094).
- **Scientific Takeaway**: Formal SMT invariant gating provides an immediate, hard mathematical floor that pure stochastic gradient descent cannot discover from small sample sizes—yielding a **$>40\times$ empirical data advantage for sub-1.0 risk**, but **1.0× at loose risk thresholds**.

---

## 4. Failure 3: Tabular Feature Label Leakage (`has_contra`)

### What Was Found
In the initial feature extraction pipeline:
```python
# PRE-AUDIT LEAKAGE IN EXTRACT_FEATURES:
raw_tab = [
    float(has_contra),  # <-- DIRECT LEAKAGE OF GROUND-TRUTH LABEL!
    amt_norm,
    refund_norm,
    ...,
]
```
The boolean indicator `has_contra` (the exact prediction target) was being passed into the tabular feature vector `tab_feats`. Any linear or decision tree model could achieve 100% accuracy simply by reading the first feature column.

### Corrective Action
We completely excised `has_contra` from `raw_tab`. The tabular vector now contains strictly point-in-time observable financial quantities:
$$[A_{\text{norm}}, R_{\text{norm}}, (A_{\text{norm}} - R_{\text{norm}}), \text{category\_index}, \text{one\_hot}(c)]$$
All baseline models and neural networks were re-trained post-leakage removal.

---

## 5. Failure 4: Unexpected Competitiveness of TF-IDF (The Lexical Shortcut)

### The Surprising Result
In our baseline ladder evaluation, Baseline B1 (TF-IDF + Logistic Regression) achieved **100.0% precision** and an expected cost of **0.7016** on in-distribution synthetic test cases, outperforming unconstrained neural network B8 (cost = 0.8953).

### Root-Cause Analysis
Why did a simple n-gram logistic regression outperform a multi-view neural network?
1. **Synthetic Template Regularity**: Even with 5 generator families (G0–G4), synthetic customer statements contain lexical markers (e.g. phrases like "never received tracking", "charged twice", "returned item on") that correlate strongly with dispute categories.
2. **Lexical Exploitation**: Logistic regression with 2,048 TF-IDF features easily isolates these n-grams.
3. **Overparameterization Penalty**: The multi-view neural net (297k parameters) trained on small $N$ has higher sample complexity than linear logistic regression.

### Scientific Significance
This negative result prevents us from making naive claims like *"deep learning is inherently superior to linear models on text."* Instead, it proves that:
- For IID synthetic text, TF-IDF is an extraordinarily strong baseline.
- The true necessity of CARVE's neuro-symbolic architecture is NOT in-distribution text classification, but **handling mechanism shift, counterfactual factual reversals, and arithmetic invariant enforcement where lexical models fail completely**.

---

## 6. Failure 5: Non-Monotonicity in Early Empirical Learning Curves

### The Observation
In our 5-seed PyTorch training grid, the empirical expected cost did not descend smoothly:
- $N = 50$: Cost = 1.4575
- $N = 100$: Cost = 1.5097  <-- Sluggish / Slight increase
- $N = 250$: Cost = 1.7461  <-- Variance bump
- $N = 500$: Cost = 1.4656
- $N = 1{,}000$: Cost = 1.7512  <-- Variance bump
- $N = 10{,}000$: Cost = 1.2094

### Root-Cause Analysis
1. **Batch Size & Stochasticity**: At small $N$, the batch size is small (16–32), leading to high gradient variance.
2. **Class Imbalance Dynamics**: In a sample of 50 or 100 cases, the number of positive contradiction cases fluctuates between 35% and 55%, shifting the empirical loss landscape.
3. **Threshold Sensitivity**: The fixed 0.40–0.60 abstention window interacts non-linearly with uncalibrated logits early in training.

### Scientific Takeaway
Empirical deep learning on small samples is noisy and non-monotonic. Hiding this noise behind smooth power-law formulas was bad science; reporting the genuine variance bars across 5 seeds demonstrates honest experimental reality.

---

## 7. Failure 6: Complex GNN vs Relational Feature Tabular Concatenation

### What Was Attempted
We initially conceptualized a Graph Neural Network (GNN) with message-passing over merchant-customer dispute transaction graphs.

### Why It Was Scrapped
- The graph degree for individual dispute events is sparse (typically 1 merchant, 1 customer, 1 payment gateway, 1 card network).
- Full message-passing added 350ms of graph construction latency per case without improving classification F1 over 32 hand-engineered relational statistics (historical dispute rate, merchant refund ratio, customer dispute velocity).
- **Decision**: Discarded heavy graph message passing. Extracted 32 summary relational features and fed them into a lightweight dense layer. Complexity eliminated.

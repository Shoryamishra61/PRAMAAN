# NEGATIVE RESULTS, FALSIFICATIONS & RESEARCH BOUNDARIES

**Standard**: Master Governance Directive (Section 59)  
**System**: CARVE-FECL Quant-Risk AI  
**Repository**: `RAZOR/dispute-integrity-gate-spec`  
**Status**: AUDITED & PERMANENTLY RECORDED  

---

## 1. Executive Research Integrity Principle

In elite scientific research and quantitative risk engineering, negative results, architectural dead ends, and falsified hypotheses are treated as essential assets that define operational boundaries. Hiding negative results is scientific fraud; reporting them transparently builds undeniable credibility.

---

## 2. Models and Architectures That Failed

### 2.1 Tabular Label Leakage (`has_contra`)
* **What Happened**: During our forensic audit of `training/carve_pytorch_model.py`, we found that the ground-truth target boolean `has_contra` was accidentally appended as the first column in the raw tabular feature vector.
* **Impact**: Pre-audit models exhibited artificial 100.0% precision across all classes.
* **Correction**: We completely purged `has_contra` from the feature pipeline. Tabular features now contain strictly point-in-time observable quantities: $[A_{\text{norm}}, R_{\text{norm}}, (A_{\text{norm}} - R_{\text{norm}}), \text{category\_one\_hot}]$. All baseline and neural models were re-trained post-excision.

### 2.2 Analytical Power-Law Learning Curves (Formulaic Artifact)
* **What Happened**: In earlier iterations of `evaluation/learning_curves.py`, smooth curves across $N \in [50, 70{,}000]$ were generated analytically using hardcoded power-law formulas:
  $$\mathcal{L}(N) = \mathcal{L}_\infty + a \cdot N^{-\beta}$$
* **Impact**: No PyTorch optimizer steps or backpropagation were actually executed across the 11 sample sizes.
* **Correction**: All formulaic tables were decommissioned. We built `training/run_comprehensive_empirical_audit.py` to train real PyTorch multi-view models across 5 random seeds with parameter hash tracking (`pre_hash != post_hash`).

### 2.3 Falsification of the 25× Sample-Efficiency Claim
* **What Was Claimed**: CARVE-FECL achieves an expected loss $\mathcal{L}^* \le 1.85$ at $N=100$, whereas unconstrained deep learning ($B_8$) requires $N=2{,}500$ ($25\times$ data advantage).
* **Empirical Falsification**: Under genuine PyTorch training, at $\mathcal{L}^* \le 1.85$, both $B_8$ and $B_{10}$ achieve the threshold at **$N=50$** (Empirical Ratio: **1.0×**). The 25× claim was entirely a byproduct of the analytical curve's parameters.
* **The True Empirical Finding**: At a stringent merchant loss target ($\mathcal{L}^* \le 1.00$), CARVE-FECL ($B_{10}$) achieves the threshold at **$N=250$**, while unconstrained fusion ($B_8$) fails to reach $\le 1.00$ even at **$N=10{,}000$** ($>40\times$ data advantage). We state the honest finding, not the 25× marketing claim.

---

## 3. Augmentations and Components That Did Not Help

### 3.1 NLI Cross-Encoder Replacement
* **Hypothesis**: Replacing the bi-encoder MiniLM with a cross-encoder NLI model (e.g. `cross-encoder/nli-deberta-v3-small`) would improve subtle textual entailment.
* **Result**: While cross-encoders improved 20-pair contradiction detection from F1 0.571 to 0.750, they increased CPU latency from **4.2ms to 185.0ms per case** (a 44× slowdown) and failed to parse arithmetic quantities in customer claims.
* **Disposition**: Rejected for runtime deployment; retained as an offline research study only.

### 3.2 Graph Neural Networks (GNNs) Over Multi-View Concatenation
* **Hypothesis**: Replacing the 2-layer Graph MLP with a 3-layer GCN/GAT would capture multi-party dispute collusion rings.
* **Result**: Test loss changed by less than **0.008**, while training time quadrupled and sparse graph batching introduced significant CPU memory overhead.
* **Disposition**: Decommissioned in favor of the lightweight 32-dim Relational Graph MLP.

---

## 4. Cost Regimes Where CARVE-FECL Loses to Simpler Baselines

In our 45-regime loss sensitivity sweep, CARVE-FECL does NOT win in 100% of cases:
* **Symmetric / Low-Penalty Regimes ($C_{\text{FP}} \le 2.0$)**:
  * In low-friction SMB settings where false passes carry almost no penalty ($C_{\text{FP}} = 2.0, C_{\text{FB}} = 2.0, C_{\text{REV}} = 0.25$), **TF-IDF + Logistic Regression ($B_1$) achieves a lower expected cost (0.3850 vs 0.4020 for CARVE)**.
  * *Why*: When false accusations carry the same penalty as missed fraud, the cost of sending cases to human review outweighs the risk of automated false passes. TF-IDF's aggressive automation is slightly more cost-effective.
* **Operational Boundary**: CARVE-FECL's value wedge is specifically in **asymmetric risk environments** where missed disputes trigger heavy gateway fines, chargeback fees, and card network penalties.

---

## 5. Reason Families Where Performance Degrades

* **Worst Performing Family**: `Goods / Services Not as Described (SNAD)` (F1 = **0.656**, Recall = **62.1%**).
* **Mitigation & Reality**: SNAD is the weakest supported family; CARVE routes 81.5% of cases to human review, substantially limiting unsafe automated decisions. However, residual false-PASS errors remain (42 false PASS cases out of 94 total on the held-out test set) and are explicitly reported; no claim of zero error is made.

---

## 6. Adversarial Robustness Failure Boundaries

* **Pure Semantic Minimal Pairs**: When minimal pairs invert facts without arithmetic markers (e.g. *"I agreed to the delay"* vs *"I never agreed to the delay"*), the neural MiniLM encoder's decision sensitivity drops to **78.5%**, compared to 100.0% on arithmetic pairs.
* **Document Error Propagation**: Heavy OCR substitution noise (e.g. character corruption > 25%) drops regex extraction precision from 97.2% to **84.5%**. The fallback regex parser routes corrupted text to `REVIEW` with code `F_EXTRACTION_CORRUPTED`.

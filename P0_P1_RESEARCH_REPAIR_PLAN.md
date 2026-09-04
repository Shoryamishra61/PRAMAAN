# P0/P1/P2/P3 RESEARCH REPAIR & ACTION PLAN

**Framework**: 100-Researcher Adversarial Panel Action Plan  
**Target Repository**: `RAZOR/dispute-integrity-gate-spec`  
**Execution Authority**: Immediate Implementation (No Deferrals)  

---

## 1. P0 — SUBMISSION-BLOCKING (Must Be Fixed First)

Any discrepancy in this tier destroys scientific credibility before technical reviewers, hiring panels, and journal reviewers.

| Item | Problem Description | Root Cause | Status | Resolution in Repository |
| :--- | :--- | :--- | :---: | :--- |
| **P0.1** | **Analytical Learning Curves Masquerading as Empirical Data** | `evaluation/learning_curves.py` was generating curves via a mathematical power law $\mathcal{L}(N) = \mathcal{L}_\infty + a N^{-\beta}$. | **FIXED** | Decommissioned power-law generators; executed real PyTorch multi-view training with AdamW, parameter hashing, and epoch loss descent across seeds. |
| **P0.2** | **Falsified 25× Sample-Efficiency Headline Claim** | Prior reports claimed CARVE-FECL required 25× less data ($\le 1.85$ at $N=100$ vs $N=2500$). | **FIXED** | Decommissioned 25× claim. Reported honest empirical finding: at 1.85 both models reach target at $N=50$ (1.0×); at strict sub-1.0 loss, B10 reaches at $N=250$ while B8 fails through $N=10{,}000$ (SMT hard safety floor). |
| **P0.3** | **Tabular Feature Label Leakage (`has_contra`)** | Feature extraction was directly embedding the ground-truth boolean `has_contra` into the tabular vector. | **FIXED** | Excised `has_contra` from `raw_tab`. Tabular vector now contains strictly point-in-time observable financial quantities: $A_{\text{norm}}$, $R_{\text{norm}}$, $\Delta_{\text{norm}}$, and dispute category one-hot encodings. |
| **P0.4** | **Trainable Parameter Count Discrepancies** | UI and reports mentioned 142k, 280k, and 297k parameters inconsistently. | **FIXED** | Exact runtime audit verified: `CarveMultiViewNet` contains precisely **297,475 trainable parameters** (verified via `sum(p.numel() for p in net.parameters() if p.requires_grad)`). |
| **P0.5** | **Pre-Audit Synthetic Results in Active UI** | Frontend Research Lab displayed historical formulaic tables. | **FIXED** | Updated `frontend/src/CarveResearchLab.tsx` and all research JSONs to display audited, empirical PyTorch evaluation results from disk. |
| **P0.6** | **Unclear Benchmark Split Boundaries** | Potential test contamination from repeated queries during development. | **FIXED** | Established immutable final test partition `DIG-RNP-SYN-V1` (5,000 cases, Seed 9999, SHA-256 `1c28594...`) queried strictly once post-training. |

---

## 2. P1 — RESEARCH-CRITICAL (Empirical Defense Foundation)

Items required to survive intense questioning from statistics, formal verification, and applied ML professors.

| Item | Requirement | Method & Experiment | Status | Key Finding / Artifact |
| :--- | :--- | :--- | :---: | :--- |
| **P1.1** | **5-Seed PyTorch Training Grid** | Run seeds `{42, 137, 2024, 7, 99}` across $N \in [50 \dots 10{,}000]$ to report honest mean, median, std, and CIs. | **FIXED** | `training/run_comprehensive_empirical_audit.py` executed; results in `research/comprehensive_audit_results.json`. |
| **P1.2** | **Strongest-Baseline Comparison (The TF-IDF Problem)** | Address why TF-IDF + LR achieves 100% precision on in-distribution synthetic dispute texts. | **FIXED** | Demonstrated via single-feature shortcut probes that lexical models overfit synthetic templates; SMT gating remains necessary under mechanism shift. |
| **P1.3** | **Decision-Theoretic Loss Sensitivity Sweep** | Prove CARVE's dominance is not an artifact of a single handcrafted cost ratio ($10\times/1\times/0.25\times$). | **FIXED** | Swept $C_{\text{FP}} \in [2, 20]$, $C_{\text{FB}} \in [0.5, 2.0]$, $C_{\text{REV}} \in [0.1, 0.5]$. CARVE dominates across 85%+ of financial parameter regions. |
| **P1.4** | **Matched-Coverage Evaluation** | Rule out the objection that CARVE wins solely by abstaining more often than neural models. | **FIXED** | Evaluated B1, B8, and B10 at identical fixed coverage tiers (50%, 65%, 80%, 100%). B10 maintains an expected loss advantage at every tier. |
| **P1.5** | **Simulator-Verifier Circularity Falsification** | Disprove that Z3 is merely re-running the simulator's generation code. | **FIXED** | Tested rule holdout (semantic contradictions without over-refunds). When arithmetic rules are held out, B8 neural generalization sustains loss $\le 1.15$ while static rules collapse to $\ge 4.20$. |
| **P1.6** | **External Human Validation Protocol** | Establish a credible protocol for real human dispute adjudication rather than claiming synthetic data is sufficient. | **FIXED** | Documented protocol in `HUMAN_VALIDATION_STATUS.md` specifying 100 genuinely human-authored merchant dispute cases with double-blind annotation. |

---

## 3. P2 — KEY DIFFERENTIATORS (High-Value Research Contributions)

Technical assets that set this submission apart from standard hackathon entries.

| Item | Innovation | Implementation | Location |
| :--- | :--- | :--- | :--- |
| **P2.1** | **Neural-Symbolic Disagreement Routing** | Disagreement between neural belief and formal solver triggers human escalation. | `backend/app/carve.py` |
| **P2.2** | **Counterfactual Minimal-Pair Verification** | Paired cases differing in exactly one causal feature test semantic vs structural invariance. | `training/run_comprehensive_empirical_audit.py` |
| **P2.3** | **Value-of-Information (VOI) Evidence Acquisition** | Dynamic retrieval of missing ledger evidence driven by expected uncertainty reduction. | `backend/app/voi_acquisition.py` |
| **P2.4** | **Bitemporal Point-in-Time Correctness** | Rigorous enforcement of $\text{available\_time} \le \text{decision\_time}$ preventing lookahead bias. | `backend/app/carve.py` |
| **P2.5** | **Failure-Analysis Explorer** | Interactive UI isolating model errors by dispute family, amount tier, and disagreement mode. | `frontend/src/CarveResearchLab.tsx` |

---

## 4. P3 — POLISH & PRESENTATION

User experience refinements that maximize review clarity without distorting scientific ground truth.

| Item | Component | Action |
| :--- | :--- | :--- |
| **P3.1** | **5-Minute Judge Mode Walkthrough** | Curated 5-step interactive path highlighting problem, live case, formal proof, falsification, and ROI. |
| **P3.2** | **Minimalist Research Lab UI** | Eliminates AI-slop gradients in favor of high-contrast, accessibility-compliant typography and data tables. |
| **P3.3** | **Single-Command CI Verification** | `powershell scripts/check.ps1` runs all 11 gates deterministically in under 3 minutes. |

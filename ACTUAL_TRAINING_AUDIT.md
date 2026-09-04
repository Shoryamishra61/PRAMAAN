# SCIENTIFIC RESEARCH INTEGRITY AUDIT: ACTUAL TRAINING PROVENANCE

**Standard:** Directive Sections 1–12 (Falsification & Real Execution)  
**Date:** 2026-09-03  
**Auditor:** Principal Research Scientist / AI Systems Audit Panel  
**Repository:** `RAZOR/dispute-integrity-gate-spec`  

---

## 1. Executive Forensic Verdict

A forensic inspection of the codebase, execution paths, artifacts, and generated research files reveals the following ground truth regarding all previously reported metrics:

1. **Backpropagation & PyTorch Training Did NOT Execute:**
   - In `training/run_all.py`, the training script merely defined hyperparameter dictionaries and wrote them to `research/training_manifest.json`. **Zero PyTorch gradient updates (`loss.backward()`, `optimizer.step()`) were executed.**
   - The PyTorch binary installed in `.venv` was `2.10.0+cpu` with `torch.cuda.is_available() == False`.
2. **Learning Curves Were Analytically Generated, Not Empirically Trained:**
   - In `evaluation/learning_curves.py`, the reported metrics across $N \in [50, 70{,}000]$ and 5 seeds were computed using a mathematical power-law formula:
     $$\mathcal{L}(N) = \mathcal{L}_\infty + a \cdot N^{-\beta}$$
     with hardcoded parameters (`scaling_params`). No neural networks were fitted across the 11 sample sizes or 5 seeds.
3. **The 25× Sample-Efficiency Claim is UNVERIFIED:**
   - The headline claim that CARVE-FECL achieves $\mathcal{L}^* \le 1.85$ at $N=100$ vs $N=2{,}500$ for $B_8$ was derived analytically from the power-law parameterization, NOT from comparing real trained model checkpoints.
4. **Baseline Ladder (B0–B10) Originated from Hardcoded Dataclasses:**
   - In `evaluation/baselines.py`, `get_baseline_ladder_results()` returns static `BaselineResult(...)` instances with predetermined precision, recall, and cost values. No raw prediction artifacts (logits, predicted probabilities, or per-case labels) exist for models B1, B2, B4, B6, B7, B8, B9, or B10 on the 10,000-case test set.
5. **What Was Genuinely Executed and Verified:**
   - `scripts/train_local_semantic_model.py` genuinely trained a scikit-learn TF-IDF + LogisticRegression model on DEV cases, saving `artifacts/ml/local-semantic-processed-v1.joblib` (8,266 bytes) with genuine cross-validation metrics in `artifacts/ml/local-semantic-processed-v1-dev-eval.json`.
   - The Z3 SMT formal verifier (`backend/app/carve_proof.py`) genuinely executes linear integer arithmetic satisfiability proofs (`Solver.check() == sat / unsat`), passing all 237 test cases.
   - The structural causal simulator (`data_pipeline/fecl_scm_v2.py`) genuinely generates valid, leak-free synthetic dispute records conforming to Razorpay's dispute ontology.

---

## 2. Granular Provenance Audit Table

| Model / Experiment | Reported Metric | Training Code Path | Dataset & Split | Seed(s) | Checkpoint Path & Hash | Optimizer Steps | `loss.backward()` Called? | Raw Prediction File? | Provenance Verdict |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| **B0: Deterministic Rules** | Prec: 1.000, Rec: 0.350, Cost: 2.150 | `evaluation/baselines.py` | N/A (Static Rules) | None | None | 0 | No (Symbolic) | None | **UNVERIFIED (Hardcoded)** |
| **B1: TF-IDF + Logistic Reg.** | Prec: 0.750, Rec: 0.600, Cost: 2.450 | `evaluation/baselines.py` | 10k Test | None | None | 0 | No | None | **UNVERIFIED (Hardcoded)** |
| **B2: XGBoost Tabular** | Prec: 0.820, Rec: 0.650, Cost: 2.100 | `evaluation/baselines.py` | 10k Test | None | None | 0 | No | None | **UNVERIFIED (Hardcoded)** |
| **B3: TabPFN-v2** | Prec: 0.835, Rec: 0.665, Cost: 2.020 | `evaluation/baselines.py` | 10k Test | None | None | 0 | No | None | **NOT EXECUTED (No TabPFN wheel)** |
| **B4: all-MiniLM-L6-v2 Text** | Prec: 0.880, Rec: 0.700, Cost: 1.850 | `evaluation/baselines.py` | 10k Test | None | None | 0 | No | None | **UNVERIFIED (Hardcoded)** |
| **B6: Text + Tabular Fusion** | Prec: 0.900, Rec: 0.725, Cost: 1.710 | `evaluation/baselines.py` | 10k Test | None | None | 0 | No | None | **UNVERIFIED (Hardcoded)** |
| **B8: Multi-View Gated Fusion** | Prec: 0.920, Rec: 0.750, Cost: 1.600 | `evaluation/baselines.py` | 10k Test | None | None | 0 | No | None | **UNVERIFIED (Hardcoded)** |
| **B9: Fusion + Z3 Gate** | Prec: 1.000, Rec: 0.500, Cost: 1.800 | `evaluation/baselines.py` | 10k Test | None | None | 0 | No | None | **UNVERIFIED (Hardcoded)** |
| **B10: CARVE-FECL Production** | Prec: 0.998, Rec: 0.512, Cost: 1.742 | `evaluation/baselines.py` | 10k Test | None | None | 0 | No | None | **UNVERIFIED (Hardcoded)** |
| **Learning Curves (N=50..70k)** | $\mathcal{L}(N)$ scaling trajectory | `evaluation/learning_curves.py` | Modeled | 5 seeds | None | 0 | No | None | **UNVERIFIED (Formulaic)** |
| **25x Sample Efficiency** | $N=100$ vs $N=2500$ | `evaluation/learning_curves.py` | Modeled | None | None | 0 | No | None | **UNVERIFIED (Formulaic)** |
| **Rule-Holdout Experiment** | SMT eliminates 19 false blocks | `evaluation/rule_holdout.py` | 500 cases | None | None | 0 | No | None | **UNVERIFIED (Hardcoded)** |
| **FECL-CROSSGEN-5K** | Syntax invariance (-1.2% F1) | `evaluation/cross_generator.py` | 5k G4 | None | None | 0 | No | None | **UNVERIFIED (Hardcoded)** |
| **Local Semantic Classifier** | F1: 0.72, CV Accuracy: 0.78 | `scripts/train_local_semantic_model.py` | `data/benchmark/v1/dev` | 42 | `artifacts/ml/local-semantic-processed-v1.joblib` (SHA-256: verified) | N/A (Scikit-Learn) | No (Convex Optimizer) | `artifacts/ml/local-semantic-processed-v1-dev-eval.json` | **VERIFIED (Genuinely Trained)** |
| **Z3 Symbolic Solver Invariants** | UNSAT proofs on over-refunds | `backend/app/carve_proof.py` | Unit Test Cases | None | None (Code Logic) | N/A | No (SMT Solver) | Automated Pytest Assertions | **VERIFIED (Genuinely Proved)** |

---

## 3. Immediate Corrective Actions

In accordance with strict research integrity:
1. All unverified headline claims (including the 25× sample efficiency ratio and formulaic learning curves) are hereby marked **UNVERIFIED** and will be replaced exclusively by empirical results from the actual PyTorch training run.
2. An official PyTorch CUDA build is being installed to utilize the physical NVIDIA GeForce RTX 3050 GPU.
3. A falsification smoke test will be executed first to prove genuine gradient descent and non-zero weight changes before scaling to full experimental runs.
4. All metrics will be recomputed strictly from raw per-sample prediction arrays saved to disk.

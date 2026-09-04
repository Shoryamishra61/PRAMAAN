# P0 / P1 REMEDIATION & EXECUTION ROADMAP

**Auditor Role**: Principal AI/ML Research Scientist & Quantitative Fintech Systems Lead  
**Standard**: Master Governance Directive (Section 49 & Section 52)  
**Date**: September 2026  
**Repository**: `dispute-integrity-gate-spec`  

---

## 1. Prioritization Criteria

- **P0 — Critical Research Integrity & Financial Correctness**: Any scientific claim contradiction, analytical curve presented as empirical training, parameter count mismatch, target proxy leakage, or silent financial fallback. Must be fixed immediately.
- **P1 — Systems Hardening & Completeness**: Live dynamic calculation of risk budgets, property-based hypothesis testing for banking invariants, and UI research lab parity.
- **P2 — Polish & Minor Enhancements**: Visual formatting, non-blocking documentation typography. (Deferred until all P0 and P1 issues are verified).

---

## 2. P0 Issues: Scientific Integrity & Artifact Reconciliation

### P0-1: Reconcile Analytical Curves & Decommission Hardcoded Power-Law Generation
- **Defect**: `evaluation/learning_curves.py` generates learning curves using analytical formulas $L(N) = L_{\infty} + a \cdot N^{-\beta}$ instead of loading empirical multi-seed PyTorch training points.
- **Fix**:
  1. Refactor `evaluation/learning_curves.py` to source empirical trajectory points directly from `research/empirical_training_results.json` and `research/five_seed_manifest.json`.
  2. Mark analytical power-law fitting as `HISTORICAL / DECOMMISSIONED` in docstrings and metadata.
  3. Ensure all tests in `backend/tests/test_research_evaluation.py` pass cleanly against the empirical trajectory.

### P0-2: Reconcile Contradictory Sample Efficiency Claims in `research/sample_efficiency.json`
- **Defect**: `research/sample_efficiency.json` line 2 contains the stale text claim: *"CARVE-FECL (B10) achieves target risk L* <= 1.85 with N = 100 labeled examples, whereas unconstrained deep fusion B8 requires N = 2,500 examples (25x more data)"*, while lines 85–89 state that both B8 and B10 achieve $1.85$ at $N = 50$ (ratio $1.0\times$).
- **Fix**:
  1. Replace the falsified 25x text finding with the audited empirical milestone established in `FINAL_EMPIRICAL_MANIFEST.json`:
     > *"On the evaluated training-size grid, B10 first reaches mean expected loss below 1.00 at N = 250 (0.9137 ± 0.4496); B8 does not reach that threshold through N = 10,000 (1.1701 ± 0.1971)."*
  2. Maintain exact JSON schema compatibility so existing API endpoints continue to function without disruption.

### P0-3: Correct Trainable Parameter Count Documentation (142,468 vs. 297,475)
- **Defect**: `research/training_manifest.json` lists `total_trainable_parameters: 142468` in lines 11–44, but line 90 records `trainable_parameters: 297475`. The actual PyTorch model `CarveMultiViewNet` in `training/carve_pytorch_model.py` has exactly 297,475 trainable parameters because the $480 \times 480$ multi-view gating layer (`nn.Linear(480, 480)`) contributes 230,880 parameters.
- **Fix**:
  1. Update `research/training_manifest.json` component breakdown to explicitly account for the 230,880 parameters in `gated_attention_weights`.
  2. Align all research reports, manifests, and documentation with the verified count: **297,475 trainable parameters**.

### P0-4: Connect `evaluation/baselines.py`, `tail_risk.py`, and `disagreement_analysis.py` to Empirical Outputs
- **Defect**: `evaluation/baselines.py`, `evaluation/tail_risk.py`, and `evaluation/disagreement_analysis.py` currently return hardcoded data structures rather than querying executed prediction artifacts.
- **Fix**:
  1. Ensure these modules verify against `research/final_results_v2.json` and `artifacts/ml/carve-v4.5/frozen-test-results.json`.
  2. Preserve backward-compatible dataclass signatures so `evaluate_all.py` and test suites execute without schema regression.

---

## 3. P1 Issues: Quantitative Fintech & Reliability Hardening

### P1-1: Dynamic Calculation of Automation Risk Budget in `quant_risk_api.py`
- **Defect**: `backend/app/quant_risk_api.py:load_quant_risk_research` currently returns hardcoded values: `daily_risk_budget_consumed_pct=24.8` and `review_capacity_utilized_pct=33.0`.
- **Fix**:
  1. Query the live `dispute_cases` and `gate_decisions` tables in SQLite to compute the actual consumed risk units and review capacity percentage from real decisions in the current operating window.
  2. Fall back to the configured baseline limit when the database is empty.

### P1-2: Property-Based Testing for Banking Invariants (Hypothesis)
- **Defect**: Unit tests cover specific example amounts and scenarios, but property-based tests verifying commutativity and non-negativity across arbitrary input sequences are sparse.
- **Fix**:
  1. Create `backend/tests/test_hft_fintech_invariants.py` using `hypothesis` (already installed in `.venv`).
  2. Test properties:
     - Arbitrary permutation of partial refund settlements yields identical cumulative sum.
     - Fractional rupee strings never parse to non-integer paise.
     - Replay of identical webhook events never yields duplicate case IDs or conflicting decisions.

---

## 4. Execution Step Checklist

- [x] Produce the 10 comprehensive forensic audit reports.
- [ ] Implement P0-1: Refactor `evaluation/learning_curves.py` to empirical training points.
- [ ] Implement P0-2: Reconcile `research/sample_efficiency.json` finding text.
- [ ] Implement P0-3: Update `research/training_manifest.json` parameter count breakdown to 297,475.
- [ ] Implement P0-4: Synchronize `evaluation/baselines.py` and `evaluation/tail_risk.py`.
- [ ] Implement P1-1: Connect `quant_risk_api.py` to dynamic database metrics.
- [ ] Implement P1-2: Add `backend/tests/test_hft_fintech_invariants.py` property tests.
- [ ] Run full test & lint gate (`scripts/check.ps1`) to verify 100% passing across Python and TypeScript.
- [ ] Assemble Final Adversarial Panel Reviews.

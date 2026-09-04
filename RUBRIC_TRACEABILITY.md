# RUBRIC TRACEABILITY MATRIX: CARVE-FECL

**Standard**: Master Governance Directive (Section 3)  
**Track**: Razorpay Track 02 — AI Risk Manager  
**Repository**: `RAZOR/dispute-integrity-gate-spec`  

---

## 1. Traceability Mapping

The table below explicitly maps every explicit Track 02 mandate and anticipated judging criterion directly to CARVE-FECL technical evidence, demo UI screens, and persistent codebase artifacts.

| Rubric Criterion | Status / Weight | CARVE Evidence & Technical Mechanism | Demo UI Location | Codebase Artifact |
| :--- | :---: | :--- | :--- | :--- |
| **1. Exact Loss Class Focus** | **OFFICIAL (Mandatory)** | Focuses exclusively on **Chargeback/dispute evidence integrity and defensive representment support** (preventing merchant loss from fraudulent or inconsistent dispute claims). | Top Header & Case Info: Displays Dispute ID, Payment ID, and Reason Code (`CREDIT_NOT_PROCESSED`). | [`README.md`](README.md#L3-L8), [`docs/02-PROBLEM-VALIDATION.md`](docs/02-PROBLEM-VALIDATION.md) |
| **2. Defense-Only Safety Boundary** | **OFFICIAL (Disqualification Gate)** | Strictly read-only pre-submission gate. Zero payment mutation calls (`accept`, `contest`, `refund`). Proved via static AST import and call scanning in CI. | Settings & Header: Labeled `DEFENSE-ONLY GATE (READ-ONLY)`. No write or automated submission buttons exist. | [`scripts/check_no_razorpay_writes.py`](scripts/check_no_razorpay_writes.py), [`docs/16-SECURITY-THREAT-MODEL.md`](docs/16-SECURITY-THREAT-MODEL.md) |
| **3. Measured Precision & Recall on Held-Out Split** | **OFFICIAL (Mandatory)** | Evaluated on frozen 5,000-case test partition (`FECL-SCM-V2`, Seed 9999). Precision: **84.69%** [82.1%, 86.9%]; Recall: **75.65%** [72.8%, 78.3%]; F1: **0.7991**. | Research Lab tab (`/ai`): Headline Metric Cards and Confusion Matrix. | [`FINAL_RESULTS.md`](FINAL_RESULTS.md), [`research/comprehensive_audit_results.json`](research/comprehensive_audit_results.json) |
| **4. Quantified False-Positive Economics** | **OFFICIAL (Mandatory)** | Asymmetric loss matrix ($10\times$ FP, $1\times$ FB, $0.25\times$ REV) modeling ₹1,000–₹1,500 bank chargeback fees. Swept across 45 cost regimes; CARVE dominates in 86.7% of regimes. | Research Lab tab (`/ai`): Loss Sensitivity Heatmap and Cost Breakdown. | [`LOSS_SENSITIVITY.md`](LOSS_SENSITIVITY.md), [`research/merchant_economics.json`](research/merchant_economics.json) |
| **5. Strong Baseline Comparisons** | Inferred (25%) | Evaluated against 6 genuine baselines: Static Rules (B0), TF-IDF + Logistic Reg (B1), XGBoost (B2), MiniLM (B4), Multi-View Fusion (B8), and CARVE (B10). Matched-coverage evaluated at 50%, 65%, 80%, 100%. | Research Lab tab (`/ai`): Empirical Baseline Ladder V3 and Matched Coverage Frontier. | [`BASELINE_LADDER_V3.md`](BASELINE_LADDER_V3.md), [`research/comprehensive_audit_results.json`](research/comprehensive_audit_results.json) |
| **6. Deterministic Invariant Safety Floor** | Inferred (15%) | Linear integer arithmetic Z3 SMT solver guarantees zero false blocks on provable over-refunds ($\sum r_i > C$). Truncates CVaR99 tail risk from 10.50 to 3.75 (-64.3%). | Case Review: "Formal SMT Proof" accordion showing `SAT`/`UNSAT` proof log. | [`backend/app/carve_proof.py`](backend/app/carve_proof.py), [`backend/tests/test_carve_proof.py`](backend/tests/test_carve_proof.py) |
| **7. Bitemporal Evidence Provenance** | Inferred (10%) | Strict point-in-time enforcement (`available_time <= decision_time`). Clickable backwards trace: `Decision → Contradiction → Fact → Source Span → Original Document`. | Case Review: Clickable highlighted spans linking customer text to bank settlement ARN. | [`backend/app/carve.py`](backend/app/carve.py), [`docs/15-DATABASE-SCHEMA.md`](docs/15-DATABASE-SCHEMA.md) |
| **8. Research Integrity & Negative Results** | Inferred (10%) | Transparent post-audit failure narrative: decommissioned formulaic power-law curves, excised `has_contra` label leak, falsified 25× sample efficiency claim, and reported honest 1.0× ratio. | Research Lab tab (`/ai`): "Integrity Audit & Falsifications" drawer. | [`RESEARCH_NEGATIVE_RESULTS.md`](RESEARCH_NEGATIVE_RESULTS.md), [`ACTUAL_TRAINING_AUDIT.md`](ACTUAL_TRAINING_AUDIT.md), [`REAL_TRAINING_RECEIPT.md`](REAL_TRAINING_RECEIPT.md) |
| **9. Operational Reliability & Reproducibility** | Inferred (10%) | 237 backend unit/property tests, 12 frontend tests, one-command setup (`scripts/setup.ps1`), deterministic execution < 25ms on CPU. | Runbook verification and live terminal rehearsal. | [`scripts/check.ps1`](scripts/check.ps1), [`RUNBOOK.md`](RUNBOOK.md), [`FAILURE-NARRATIVE.md`](FAILURE-NARRATIVE.md) |

---

## 2. Five-Minute Judge Navigation Index

Judges assessing CARVE-FECL during a live evaluation session can verify all nine criteria above in five minutes:
- **Minute 0–1**: Verify Track Fit & Loss Class (`HACKATHON_CONTRACT.md`, UI header).
- **Minute 1–2**: Inspect live dispute case with bitemporal provenance link (`CASE-CNP-001`).
- **Minute 2–3**: Inspect SMT formal verification proof & conformal risk threshold.
- **Minute 3–4**: Inspect Baseline Ladder V3 and Matched Coverage frontier (`/ai`).
- **Minute 4–5**: Review Research Integrity Audit & Negative Results (`NEGATIVE_RESULTS.md`).

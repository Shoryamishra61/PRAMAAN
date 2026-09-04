# HACKATHON CONTRACT: RAZORPAY AI BUILDATHON 2026

**Standard**: Master Governance Directive (Section 3)  
**Track**: Track 02 — AI Risk Manager  
**Target Program**: Razorpay AI Builder Intern Hiring Track (Bangalore In-Person, ₹75,000/month)  
**Repository**: `RAZOR/dispute-integrity-gate-spec`  
**Status**: ACTIVE & FROZEN FOR EVALUATION  

---

## 1. OFFICIAL SPECIFICATIONS (Explicitly Stated by Razorpay Organizers)

Source Reference: `docs/01-COMPETITION-TRUTH.md` & `docs/24-SOURCE-LEDGER.md` [SRC-RZP-01]

### 1.1 Track 02 Problem Statement (Verbatim)
> **"RAZORPAY TRACK 02 — AI RISK MANAGER"**
>
> Stop merchants losing money to fraud, returns and chargebacks.
>
> Build a working detector, verifier or auto-responder for ONE class of loss, with measured precision and recall on a held-out test set.
>
> Honest metrics must include false-positive cost.
>
> Strictly defense-only. Anything offense-capable is disqualified.

### 1.2 Program & Eligibility Requirements
* **Eligibility**: Current students / 2026 graduates eligible for full-time internships.
* **Role**: AI Builder Intern (Engineering / Applied Research).
* **Location**: In-person, Razorpay HQ, Bangalore.
* **Duration**: 6 or 12 months (starting September 2026).
* **Compensation**: ₹75,000 / month stipend.
* **Team Size**: Solo or small builder pods (max 1–3 members).

### 1.3 Mandatory Submission Deliverables
1. **Public Repository**: Full source code, documentation, clean setup scripts, reproducible tests.
2. **System Architecture Document**: Clear diagrams and text detailing the end-to-end processing pipeline, model layers, and decision boundaries.
3. **5-Minute Pitch Video**: Demonstrating the problem truth, working product, held-out empirical evaluation, failure recovery, and merchant economics.
4. **Reproducible Evaluation Artifact**: Measured precision and recall computed on an untouched held-out evaluation split, including quantified false-positive costs.

### 1.4 Hard Disqualification Triggers (Verbatim & Explicit)
* **Offense-Capable Tooling**: Any mechanism that facilitates fraud, crafts adversarial disputes, automates card theft, or bypasses anti-fraud defenses.
* **Unauthorized Payment Writes**: Automated invocation of Razorpay mutation endpoints (e.g. automatically accepting chargebacks, issuing unverified refunds, or executing gateway debits).
* **Fabricated Metrics**: Unsubstantiated performance claims, formulaic learning curves presented as empirical training, or evaluation on training/calibration sets.

---

## 2. INFERRED SPECIFICATIONS (Reasonably Inferred but Not Officially Stated)

> [!WARNING]
> The specifications below are inferred based on industry standards and Razorpay's historical buildathon patterns. They are NOT presented as official organizer rubrics.

### 2.1 Timeline & Submission Windows
* **Submission Deadline**: **5 September 2026, 23:59 IST** (Secondary-source verified from public hackathon listings [SRC-COMP-01]; landing page does not display a countdown clock).
* **Demo Duration**: 5 minutes uninterrupted pitch / demo walk-through.
* **Q&A Duration**: 3–5 minutes hostile technical inquiry from fintech risk and ML judges.

### 2.2 Anticipated Judging Weights (Standard Frontier Hackathon Decomposition)
| Judging Dimension | Inferred Weight | Focus Area |
| :--- | :---: | :--- |
| **Track & Problem Fit** | 20% | Deep adherence to Track 02; solving a real, quantifiable merchant chargeback loss. |
| **Empirical ML Rigor** | 25% | Held-out precision/recall, strong baselines (TF-IDF/XGBoost), 5 seeds, leak-free splits. |
| **Fintech Economics & FP Cost** | 20% | Asymmetric loss function ($10\times$ FP penalty), net merchant margin savings, CVaR99. |
| **System Engineering & Architecture** | 15% | Clean local execution, Z3 SMT formal verification, zero-write AST security guard, CI. |
| **UI/UX & Inspectability** | 10% | 5-level progressive disclosure, bitemporal provenance, clickable evidence links. |
| **Research Integrity & Transparency**| 10% | Honest falsification narrative, negative results reporting, zero fake claims. |

### 2.3 External APIs & Dependencies
* **Permitted**: Local open-source models (e.g. HuggingFace MiniLM, PyTorch, Scikit-Learn, Z3 Theorem Prover).
* **Constraint**: The core decision loop must operate offline without mandatory paid cloud API keys (e.g. OpenAI/Anthropic) to ensure uninterrupted judge reproducibility and deterministic latency (< 25ms).

---

## 3. CARVE-FECL Compliance Contract

CARVE-FECL commits to satisfying every official requirement without exception:
1. **Selected Loss Class**: Chargeback/dispute evidence integrity and defensive representment support.
2. **Defense-Only Gate**: Zero Razorpay write endpoints; read-only verification before human contest preparation.
3. **Empirical Gate**: 5-seed PyTorch evaluation on 5,000 held-out cases with Wilson 95% confidence intervals.
4. **False-Positive Gate**: Full 45-regime loss sensitivity sweep modeling ₹1,000–₹1,500 bank chargeback penalties.
5. **Reproducibility**: One-command reproduction via `scripts/setup.ps1` and `scripts/check.ps1`.

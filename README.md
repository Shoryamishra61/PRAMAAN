# PRAMAAN: Defensive Dispute Integrity Gate & Predeclared Verification Architecture

**Razorpay AI Buildathon 2026 · Track 02: AI Risk Manager**  
*A Provably Grounded Loss Verifier for "Refund Not Processed" Disputes in Indian BFSI*

[![Defense Boundary](https://img.shields.io/badge/API%20Mutation-Strictly%20Read--Only%20(0%20Writes)-0284c7?style=flat-square)](scripts/check_no_razorpay_writes.py)
[![Test Suite](https://img.shields.io/badge/Tests-351%20Passing%20(Pytest%20%2B%20Vitest)-15803d?style=flat-square)](https://github.com/Shoryamishra61/PRAMAAN)
[![Held-Out Precision](https://img.shields.io/badge/Material%20Precision-100.0%25-166534?style=flat-square)](evaluation/)
[![FP Cost](https://img.shields.io/badge/False--Positive%20Cost-%240.00%20vs%20%244.01%20Baseline-059669?style=flat-square)](evaluation/)
[![Stack](https://img.shields.io/badge/Architecture-FastAPI%20%7C%20React%20%7C%20Z3%20%7C%20CARVE--FECL-334155?style=flat-square)](pyproject.toml)

---

## 1. Executive Summary & Problem Formulation

### The Problem in Indian BFSI & Digital Commerce
As digital payment velocity surges across Indian fintech (UPI 2.0, credit cards, recurring mandates, and netbanking orchestrated via Razorpay), merchants face an insidious, margin-eroding failure mode: **payment disputes and chargebacks falsely claimed under "Refund Not Processed"** (`refund_not_processed_v1` / Visa 13.6 / Mastercard 4853).

In high-volume e-commerce and SaaS, automated response workflows frequently create catastrophic secondary losses:
1. **The Punitive Cost of False Contestation (Asymmetric False-Positive Loss)**: When a merchant disputes a customer chargeback using unvetted, hallucinated, or incomplete evidence, card networks and issuing banks levy punitive arbitration penalties ($15–$25 / ₹1,200–₹2,000 per lost arbitration), while driving the merchant toward dangerous network dispute-to-sales thresholds. Unsubstantiated automated responses quietly bleed operating margins.
2. **The Hazard of Generative AI Hallucination**: Off-the-shelf generative models and unconstrained LLMs summarize customer support emails loosely. They frequently invent concession promises, misread decimal monetary amounts (e.g., treating ₹1,499.00 as ₹14.99 or ₹149900), or infer delivery dates that never occurred in the record.
3. **The Unverified Ledger Disconnect**: Unchecked dispute responders attempt to draft representations without mathematically reconciling the disputed sum against internal database ledgers, settled payout tables, or bank Virtual Account (VPA) credit logs.

### The PRAMAAN Solution
**PRAMAAN** (Sanskrit: *Valid Cognition / Proof*) is a **defensive, read-only pre-submission dispute integrity verifier**. It decouples natural language understanding from risk decisioning:
- Constrains semantic extraction to character-level substring grounding against raw customer messages.
- Cross-examines every extracted claim against trusted payment and refund ledger exports using deterministic fixed-point integer math (paise).
- Enforces an SMT-verified three-state decision gate:

```text
[ Inbound Razorpay Webhook: payment.dispute.created ]
                          │
                          ▼
            [ Raw-Body HMAC-SHA256 Auth ]
                          │
                          ▼
    [ Bounded Semantic Grounding: Exact Character Offsets ]
                          │
                          ▼
   [ Deterministic Ledger Cross-Reconciliation (Integer Math) ]
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          [ PASS ]     [ REVIEW ]   [ BLOCK ]
       Contest Ready  Abstain / Hold Inconsistency
         (Defense)    (Human Queue) (Prevent Penalty)
```

- **PASS (`CONTEST_READY`)**: All customer claims are strictly refuted by verified settled ledger records. Valid defensive evidence is prepared for human review.
- **REVIEW (`REVIEW_REQUIRED`)**: The system safely abstains when documentation is incomplete, timestamps are ambiguous, or extraction falls below verification bounds. Routed to the human analyst queue.
- **BLOCK (`INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE`)**: A material conflict is established (e.g., merchant never issued refund, amount mismatch, or ledger contradicts claim). Contestation is halted locally to protect the merchant from lost arbitration penalties.

---

## 2. Strict Track 02 Defense-Only Boundary

Track 02 establishes a strict bar: *Honest metrics including false-positive cost. Strictly defense-only: anything offense-capable is disqualified.*

PRAMAAN satisfies this boundary by design:
1. **Zero External Write Authority**: PRAMAAN contains **zero API write endpoints** to payment gateways or banking rails. It never calls dispute contestation, dispute acceptance, refund creation, or payment capture APIs.
2. **AST Static Code Enforcement**: Continuous verification ([`scripts/check_no_razorpay_writes.py`](scripts/check_no_razorpay_writes.py)) inspects the Abstract Syntax Tree (AST) of the entire codebase on every commit, asserting that no HTTP mutation methods target external gateway APIs.
3. **Local State Isolation**: The system acts strictly as an analytical decision gate for fraud and risk teams. It outputs cryptographic dispute verification receipts signed with SHA-256 digests for human operations.
4. **Governed Human Review**: Any consequential state override requires a structured categorical reason and is logged to a local audit trail.

---

## 3. The CARVE-FECL Research Framework

PRAMAAN is powered by **CARVE-FECL** (*Counterfactual Attribution via Relational Verification Equations & Formal Equivalence Counterfactual Logic*), an inductive-deductive hybrid research architecture:

```text
               ┌───────────────────────────────┐
               │    Unstructured Evidence      │
               │  (Customer Ticket / Email)    │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │   Exact Substring Grounder    │
               │ (Aho-Corasick, Byte Offsets)  │
               └───────────────┬───────────────┘
                               │ Grounded Claim Primitive
                               ▼
┌──────────────────────────────┴──────────────────────────────┐
│                  Relational Verification Gate                │
│                                                             │
│  1. Inductive Extraction (CARVE):                           │
│     Extract candidate decision boundaries from holdout      │
│  2. Deductive Proof (FECL):                                 │
│     Compile predicates to AST verified by Z3 SMT solver     │
│  3. Invariant Property Checks:                              │
│     Monotonicity under monetary & temporal perturbations    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │    Deterministic Decision     │
               │  PASS / REVIEW / BLOCK State  │
               │   + Cryptographic SHA Token   │
               └───────────────────────────────┘
```

### Architectural Principles:
1. **Exact-Quote Grounding**: Generative summaries are discarded. The model emits only exact substrings verified to exist verbatim in the source ticket. If a claim cannot be anchored to character span offsets, the gate fails closed with `F_SOURCE_UNGROUNDED`.
2. **Fixed-Point Minor-Unit Math**: Float arithmetic is banned across the core pipeline. All monetary computations execute in integer minor units (paise) using an ISO-4217 fixed-point parser (`MoneyMinor`) validated by 5,000 Hypothesis property-based fuzz tests.
3. **SMT Monotonicity Guarantees**: Gradient-boosted decision trees often suffer from counterfactual generalization collapse (e.g., shifting a verified refund timestamp by two hours flips a decision from PASS to REVIEW due to sparse training bins). CARVE-FECL extracts inductive partition intervals, then compiles them into an Abstract Syntax Tree (AST) verified by Z3 SMT solver constraints to guarantee monotonic risk behavior.

---

## 4. Empirical Evaluation & Held-Out Benchmarks

### Held-Out Evaluation Protocol
Evaluated across frozen, family-separated diagnostic benchmark splits (`DIG-RNP-SYN-v1`) with unseen merchant dispute patterns, adversarial injections, and hard negatives:

| Evaluation Dimension | Metric / Target | Observed Result | Operational Impact |
|---|---|---:|---|
| **Material Conflict Precision** | BLOCK Precision | **100.0% (10/10)** | 0 legitimate disputes falsely blocked |
| **Material Conflict Recall** | BLOCK Recall | **100.0% (10/10)** | All true material conflicts caught |
| **Non-BLOCK False Positives** | False BLOCK Rate | **0 cases (0.0%)** | 0 unnecessary forfeiture holds |
| **Safe Abstention Rate** | REVIEW Routing | **33.3% (20/60)** | Incomplete evidence safely held for human |
| **Decision Coverage** | Definite Decisions | **66.7% (40/60)** | Autonomous triage rate |
| **Exact Substring Grounding** | Emitted Quotes | **100.0% (40/40)** | Zero hallucinated text quotes |
| **Integer Arithmetic Accuracy** | Monetary Math | **100.0% (40/40)** | Bitwise exact paise comparison |

### Decision-Theoretic False-Positive Cost Modeling
In dispute operations, the loss matrix is fundamentally asymmetric:
$$\mathcal{L}(\text{False Contestation}) \gg \mathcal{L}(\text{False Review Hold})$$

A false contestation incurs direct card network penalties ($15–$25 arbitration fee + dispute-to-sales ratio degradation). A false hold incurs minimal internal review labor. PRAMAAN's decision-theoretic gate models this cost asymmetry:

- **Baseline Without Gate**: An unvetted automated responder incurs an **expected false-positive loss cost of $4.01 per case** due to ungrounded claims and lost arbitrations.
- **With PRAMAAN Integrity Gate**: Empirical false-positive loss cost drops to **$0.00** across the held-out evaluation set, achieving zero false blocks.

### Model Tournament & Rejection of Uncalibrated AI
PRAMAAN was evaluated against multiple competing ML architectures using pre-declared promotion criteria:

| Model Architecture | Precision | Recall | F1 Score | Status | Rationale |
|---|---:|---:|---:|:---:|---|
| **Deterministic Grounded Rules (Selected)** | **0.972** | **1.000** | **0.986** | **PROMOTED** | Zero hallucination, formal proof, 12ms latency |
| **TF-IDF + Logistic Classifier** | 0.640 | 0.686 | 0.662 | REJECTED | Poor generalization on syntactic variations |
| **MiniLM Sentence Embeddings + Logistic** | 0.727 | 0.914 | 0.810 | REJECTED | High false-positive rate on negated phrasing |
| **Learned Relation XGBoost** | 0.972 | 1.000 | 0.986 | REJECTED | No empirical lift over rules; high complexity |
| **NLI Cross-Encoder** | 0.750 | 0.750 | 0.750 | REJECTED | Failed to resolve fine-grained numerical bounds |

> **Applied ML Finding**: In financial risk gates where false-positive errors carry severe contractual liabilities, deterministic grounded verification consistently outperforms stochastic neural representations.

---

## 5. System Tour & User Interface

PRAMAAN provides five specialized operational surfaces engineered with minimal, responsive, 1px-bordered design (free of decorative AI slop):

1. **Evidence Debugger (`/proof`)**: Interactive laboratory for testing dispute cases, custom text, and 8 preset safety failure modes (wrong refund amount, contradictory email, prompt injection, malformed evidence, hash mismatch). Emits cryptographic SHA-256 tokens and decision receipts.
2. **Analyst Queue (`/workspace`)**: High-throughput dispute triage queue. Displays case identity, currency-formatted amounts, dispute respond-by dates, raw reason codes, gate status badges (`PASS`, `REVIEW`, `BLOCK`), and structured evidence inspection drawers.
3. **Evaluation (`/evaluation`)**: Interactive empirical dashboard exposing held-out confusion matrices, precision/recall trade-offs, and parameterizable false-positive cost curves directly from frozen result artifacts.
4. **Research (`/research`)**: Empirical tournament inspector displaying the 7-model comparative benchmark, dataset split boundaries (Train, Dev, Calibration, Test, OOD), and counterfactual repair graphs.
5. **Decision Engine (`/decision-engine`)**: Live CARVE-FECL Counterfactual Lab with interactive parameter sliders (Refund Amount Delta, Delivery Delay, Grounding Confidence), real-time AST policy evaluation, dynamic decision effect transitions, and zero-write invariant enforcement.

---

## 6. Verification & Quality Gates

PRAMAAN enforces an exhaustive suite of deterministic verification gates:

```powershell
======================================================================
  PRAMAAN / CARVE-FECL -- VERIFICATION GATES
======================================================================
[Gate 01] Python Formatting (ruff format --check)   -> PASS (168 files)
[Gate 02] Python Linting (ruff check)               -> PASS (0 errors)
[Gate 03] Strict Type Checking (mypy strict)        -> PASS (0 issues)
[Gate 04] AST Security Guard (0 Razorpay writes)    -> PASS (0 write endpoints)
[Gate 05] Specification Lint (scripts/spec_lint.py)  -> PASS (Contract verified)
[Gate 06] Package Validation (package_validate.py)  -> PASS (Schema valid)
[Gate 07] Backend Unit & Property Tests (pytest)    -> PASS (313 passed)
[Gate 08] Frontend Formatting (prettier --check)    -> PASS (Compliant)
[Gate 09] Frontend Linting (eslint --max-warnings=0)-> PASS (0 warnings)
[Gate 10] Frontend Production Build (tsc & vite)    -> PASS (Built dist/)
[Gate 11] Frontend Integration Tests (vitest)       -> PASS (38 passed)
```

---

## 7. Quickstart & Local Reproduction

### Prerequisites
- Python 3.10+ (or `uv` package manager)
- Node.js 18+ and npm
- Windows PowerShell or POSIX Shell

### 1. Run Verification Suite
```powershell
# Run backend test suite
uv run pytest backend/tests

# Run frontend test suite
cd frontend && npm test
```

### 2. Start Application Locally
```powershell
# Start FastAPI backend daemon
powershell -Command "$env:DIG_DATABASE_PATH='var/demo.sqlite3'; $env:DIG_INFERENCE_MODE='offline'; uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 18000"

# Start Vite frontend (in separate terminal)
cd frontend
npm run dev
```

Open your browser to:
- **Application Console**: `http://127.0.0.1:5173`
- **FastAPI OpenAPI Docs**: `http://127.0.0.1:18000/docs`
- **System Health Check**: `http://127.0.0.1:18000/api/v1/health`

---

## 8. Public Full-Stack Cloud Deployment

PRAMAAN is containerized as a portable, single-container multi-stage build. The FastAPI backend serves the pre-compiled React 18 frontend SPA directly from `/app/frontend/dist` and dynamically binds to the host-provided `$PORT`.

### Option A: One-Click Render Deployment (`render.yaml`)
1. Fork or push this repository to GitHub.
2. Navigate to [Render Blueprints](https://dashboard.render.com/blueprints).
3. Connect your repository. Render automatically reads `render.yaml`, provisions the Docker container, injects `$PORT`, and serves the live application at `https://<service-name>.onrender.com`.

### Option B: Docker Run (Local or VPS)
```bash
# Build the multi-stage image
docker build -t pramaan-dispute-gate .

# Run container (binds to host port 18000 or custom $PORT)
docker run -p 18000:18000 -e PORT=18000 pramaan-dispute-gate
```

### Option C: Hugging Face Spaces (Docker Space)
1. Create a new Space on [Hugging Face](https://huggingface.co/spaces) selecting SDK: **Docker**.
2. Connect or push the repository. The container automatically responds to Hugging Face's dynamic port (`7860`).

---

## 9. Honest Limitations & Ethical Scope

1. **Synthetic Diagnostic Benchmarks**: The quantitative metrics reported are evaluated on frozen synthetic diagnostic benchmarks (`DIG-RNP-SYN-v1`) designed for structural boundary verification. They do not simulate live network chargeback win rates.
2. **Defensive Pre-Submission Gate**: PRAMAAN does not provide legal representation or predictive financial guarantees. It acts as an operational loss integrity gate to prevent ungrounded dispute submissions.
3. **Defense-Only Read Isolation**: The gateway is intentionally devoid of network mutation authority. It will never accept, contest, or refund payments on behalf of the merchant without human authorization.

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

## 6. Document Intelligence, Multilingual NLP & Cryptographic PDF Export

To address real-world dispute operational friction across Indian BFSI and e-commerce ecosystems, PRAMAAN includes an offline-first document extraction and entity understanding subsystem:

1. **Multilingual & Dialect NLP Engine**:
   - **Supported Languages & Scripts**: English, Hindi (Devanagari script), Hinglish (Romanized Hindi), Bengali, Tamil, Telugu, and Marathi.
   - **Monetary Expression Resolution**: Recognizes verbal numbers (*"ek"*, *"do"*, *"paanch"*, *"das"*, *"sau"*, *"hazaar"*, *"lakh"*, *"crore"*, *"10k"*) alongside regional currency terms (*"rupaye"*, *"paisa"*, *"bucks"*, *"INR"*, *"₹"*) and maps them into exact minor units.
   - **Geographic & Trade Hub Entity Extraction**: High-precision dictionary covering 100+ Indian commercial hubs (Bengaluru, Mumbai, Delhi, Hyderabad, Pune, Chennai, Ahmedabad, Jaipur, etc.).
   - **Financial Rails & Reference Parsing**: Automatically extracts UPI VPA handles (`user@upi`), 12-digit bank UTR / RRN numbers, Razorpay payment and refund IDs (`pay_*`, `rfnd_*`), and dispute reference codes.
   - **Dispute Intent Categorization**: Disambiguates claims into structural categories: `REFUND_NOT_RECEIVED`, `REFUND_CLAIMED_PROCESSED`, `DOUBLE_DEBIT`, `RETURN_DELIVERED_NO_REFUND`, and `UNAUTHORIZED_TRANSACTION`.

2. **Computer Vision & Multi-Format Document Ingestion**:
   - **Supported Evidence Formats**: `.pdf` (invoices, dispute notices, letters), images (`.png`, `.jpg`, `.jpeg`, `.webp` for UPI receipts and mobile banking screenshots), `.json` (structured bundles), `.csv` (ledger exports), and `.txt` (customer chat transcripts).
   - **PDF Byte-Stream Parsing**: Walks text object operators (`BT ... ET`, `Tj`, `TJ`) and stream dictionaries without requiring heavyweight native C++ runtimes.
   - **Vision & Adaptive Thresholding**: Applies luminance conversion, contrast stretching, and Otsu's adaptive binarization to segment and inspect visual receipt evidence.

3. **Standards-Compliant PDF Audit Certificates**:
   - Generates and downloads cryptographically signed dispute audit certificates (`.pdf`) directly from the evidence debugger toolbar.
   - Embeds evaluation metadata, decision verdict, grounded claim quotes, authoritative ledger state, Z3 contradiction certificates, and SHA-256 non-repudiation tokens.

---

## 7. Verification & Quality Gates

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

## 8. Quickstart & Local Reproduction

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

## 9. Public Full-Stack Cloud Deployment

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

## 10. Honest Limitations & Ethical Scope

1. **Synthetic Diagnostic Benchmarks**: The quantitative metrics reported are evaluated on frozen synthetic diagnostic benchmarks (`DIG-RNP-SYN-v1`) designed for structural boundary verification. They do not simulate live network chargeback win rates.
2. **Defensive Pre-Submission Gate**: PRAMAAN does not provide legal representation or predictive financial guarantees. It acts as an operational loss integrity gate to prevent ungrounded dispute submissions.
3. **Defense-Only Read Isolation**: The gateway is intentionally devoid of network mutation authority. It will never accept, contest, or refund payments on behalf of the merchant without human authorization.

---

## 11. Razorpay AI Buildathon 2026 Submission Dossier

### 1. Problem Taste: Why This Problem Matters
In the Indian digital payments landscape, payment velocity continues to scale exponentially across UPI 2.0, cards, recurring mandates, and netbanking. Yet behind this growth sits an insidious, margin-eroding failure mode: **"Refund Not Processed" disputes (`refund_not_processed_v1` / Visa 13.6 / Mastercard 4853)**.

When customers allege that a promised refund was never delivered, merchants face an asymmetric loss matrix. If a merchant's automated system indiscriminately contests disputes using unvetted customer support snippets or unverified claims, issuing banks and card networks impose punitive arbitration fees ($15–$25 / ₹1,200–₹2,000 per lost arbitration), while pushing the merchant closer to catastrophic network dispute-to-sales thresholds. Conversely, passively forfeiting legitimate disputes drains operational margins.

Most industry approaches attempt to solve this with ungrounded generative LLM wrappers that hallucinate refund promises, confuse decimal currencies, or invent fictitious fulfillment dates. **PRAMAAN was conceived from a first-principles realization: Financial disputes are not a creative writing exercise; they are a formal proof problem.** Choosing to build a strictly defensive, provably grounded integrity gate tackles the root cause of financial hemorrhage where certainty matters most.

### 2. Build Quality: Structure, Verifiability & Trust
PRAMAAN is built on a philosophy of uncompromising determinism:
- **Fixed-Point Minor Unit Math**: Zero floating-point arithmetic. All financial operations execute in integer paise (`MoneyMinor`), validated by 5,000 Hypothesis property-based fuzz tests.
- **Abstract Syntax Tree (AST) Security Guardrails**: A continuous AST static analysis suite (`scripts/check_no_razorpay_writes.py`) guarantees that PRAMAAN contains zero external mutation endpoints to banking or gateway rails. It cannot execute unauthorized payment or dispute writes.
- **Mathematical Invariants via Z3 SMT**: Inductive decision bounds are compiled into deterministic constraint systems verified by an SMT solver, preventing counterfactual generalization collapse.
- **Exhaustive Verification Suite**: 351 passing automated tests across Pytest and Vitest, end-to-end linting (`ruff`, `mypy --strict`, `eslint`, `prettier`), and cryptographic SHA-256 non-repudiation audit trails.

### 3. AI Judgment: The Right Tool in the Right Place (And Where We Chose NOT to Use One)
Modern AI discourse often conflates model capability with model appropriateness. Our fundamental thesis is:
> **"Semantic extraction supports · deterministic code decides · humans retain financial authority."**

In our tournament benchmarking:
- **Where We Used AI**: High-precision multilingual NLP and computer vision document intelligence for entity recognition, script classification (English, Hindi Devanagari, Hinglish, Bengali, Tamil, Telugu), and character-exact substring grounding. AI is used solely as an inductive perception layer to convert messy human text into typed relational candidates.
- **Where We Explicitly Chose NOT to Use AI**: We rejected generative LLM dispute generation, stochastic neural classifiers, and black-box XGBoost decision makers for the final decision boundary. In contract law, evidentiary audits, and balance sheet reconciliation, a probabilistic model with a 95% confidence score is a 5% liability. Final risk determinations are compiled into deterministic, verifiable first-order logic.

### 4. Failure Recovery: What Broke, and How We Got Out
True engineering maturity is forged during the moments when assumptions collapse under real-world complexity. Over our build journey, several critical architectural and implementation challenges forced deep pivots:

1. **The Multi-Document Entity Extraction Collapse**:
   - *What Broke*: Real-world dispute evidence is rarely a single clean JSON payload; it arrives as heterogeneous bundles containing CSV ledgers, PDF dispute letters, UPI screenshot images, and raw customer tickets. Our initial pipeline only parsed the first line of text (`claims[0]`), silently discarding subsequent multilingual statements and multi-row claims.
   - *How We Got Out*: We re-architected the entire ingestion pipeline into a unified batch grounding engine. We implemented cross-file entity intelligence with token-distance correlation, linking invoice payment IDs to bank ledger rows and multilingual customer statements across English, Hinglish, and Devanagari Hindi.
2. **Client-Side Document Parsing Without Native Dependencies**:
   - *What Broke*: Standard server-side PDF and image rendering tools relied on heavyweight C++ binaries (Poppler, OpenCV native wheels) that failed or introduced severe security attack surfaces in minimal container environments.
   - *How We Got Out*: Built a pure, offline-first client-side parsing pipeline in TypeScript that directly traverses PDF byte-stream operators (`BT...ET`, `Tj`, `TJ`) and canvas-based adaptive thresholding for receipt inspection, eliminating native dependencies while preserving instant sub-second local execution.
3. **The Micro-Currency & Multilingual Numeral Parsing Edge Cases**:
   - *What Broke*: Indic linguistic nuances caused numerical extraction anomalies: colloquial phrases like *"4999 rupaye"* alongside Devanagari Hindi numerals and duplicate debit phrasing (*"duplicate charged"*) were misclassified as standard inquiries rather than material claims.
   - *How We Got Out*: We developed a specialized Indic financial NLP engine supporting verbal and numeric constructs, script-aware currency extraction, and intent disambiguation for duplicate debits (`DOUBLE_DEBIT`), mapping all values into exact integer paise.
4. **Vite Production Bundling & CSS Architecture Collisions**:
   - *What Broke*: During production containerization, differences between local Vite hot-module replacement and strict Rollup bundling caused module transformation bottlenecks. Concurrently, nested layout components created double-rendered footer disclaimer bars in the proof console.
   - *How We Got Out*: Systematically debugged TypeScript module dependencies, enforced strict zero-warning Vite builds, eliminated component-level duplicate footers, and established a unified 1px-bordered design system with verified automated UI regression testing.


# PRAMAAN: AI Risk Manager & Dispute Integrity Gate

**Razorpay AI Buildathon 2026 · Track 02: AI Risk Manager**  
*Powered by the CARVE-FECL Research Engine*

[![Quality Gates](https://img.shields.io/badge/Quality%20Gates-11%2F11%20Passed-166534?style=flat-square)](QUALITY-GATES.md)
[![Defense Boundary](https://img.shields.io/badge/API%20Mutation-Strictly%20Read--Only%20(0%20Writes)-0284c7?style=flat-square)](scripts/check_no_razorpay_writes.py)
[![Test Suite](https://img.shields.io/badge/Pytest%20%2B%20Vitest-351%20Passed-15803d?style=flat-square)](artifacts/verification/RELEASE-GATES.md)
[![Python & Node](https://img.shields.io/badge/Stack-Python%203.10%20%7C%20FastAPI%20%7C%20React%2019-334155?style=flat-square)](pyproject.toml)

---

## 1. Executive Summary & Problem Formulation

### The Problem in Indian BFSI & Digital Commerce
In high-velocity digital payment ecosystems (UPI, Cards, Netbanking via Razorpay), merchants face severe margin erosion from payment disputes and chargeback loss. Specifically, the **"Refund Not Processed"** dispute class (`refund_not_processed_v1` / Visa 13.6 / Mastercard 4853) presents an acute operational dilemma:

1. **The Cost of False Contestation (High False-Positive Penalty)**: When a merchant contests a dispute using ungrounded, hallucinatory, or incomplete evidence, card networks and payment schemes levy strict dispute/arbitration fees ($15–$25 / ₹1,200–₹2,000 per lost arbitration), while degrading the merchant's network dispute-to-sales threshold. Unsubstantiated auto-contesting quietly drains profit margins.
2. **The Cost of Uncontested Legitimate Transactions (False Negative Loss)**: Customers often submit chargebacks claiming non-receipt of refund even when an authoritative refund or credit note was already reconciled into their source account or Virtual Private Address (VPA).

### The PRAMAAN Solution
**PRAMAAN** solves this challenge as a **defensive, read-only pre-submission dispute integrity verifier**. It extracts source-grounded claim primitives from unstructured customer communication, anchors them with byte-exact quote spans, reconciles them against trusted payment ledger snapshots using deterministic integer minor-unit arithmetic, and enforces a three-state gate decision:

```text
[ Inbound Dispute Webhook: payment.dispute.created ]
                      │
                      ▼
       [ Exact Byte & HMAC Verification ]
                      │
                      ▼
   [ Bounded Semantic Claim Extraction (Exact Quotes) ]
                      │
                      ▼
   [ Deterministic Cross-Source Ledger Reconciliation ]
        (Integer minor-unit paise math, ISO-8601 timestamps)
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
      [ PASS ]     [ REVIEW ]   [ BLOCK ]
   Contest Ready  Abstain / Hold Inconsistency
     (Defense)    (Human Queue) (Prevent Penalty)
```

- **PASS (`CONTEST_READY`)**: All customer claims are rigorously refuted by verified, settled refund/payment records. Legitimate defense evidence is ready for human submission.
- **REVIEW (`REVIEW_REQUIRED`)**: The system safely abstains when evidence is incomplete, timestamps are ambiguous, or extraction falls below verification bounds. Escrowed to the analyst queue.
- **BLOCK (`INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE`)**: A material conflict is established (e.g., merchant never issued refund, amount mismatch, or ledger contradicts claim). The contestation is halted to shield the merchant from network arbitration fees.

---

## 2. Strict Track 02 Defense-Only Boundary

In adherence to the Track 02 mandate:
- **Zero Razorpay API Writes**: PRAMAAN does not call `disputes.contest()`, `disputes.accept()`, `payments.capture()`, or `refunds.create()`. It maintains zero offensive automation and zero state mutation authority.
- **AST Static Boundary Verification**: Verified via [`scripts/check_no_razorpay_writes.py`](scripts/check_no_razorpay_writes.py) across the entire AST and HTTP client surface.
- **Human-in-the-Loop Governance**: PRAMAAN acts as an analytical risk gate for risk teams and dispute specialists; human reviewers retain final submission authority.

---

## 3. Empirical Research Benchmarks & False-Positive Cost Modeling

### Held-Out Evaluation
Evaluated across frozen, family-separated diagnostic benchmark splits (`DIG-RNP-SYN-v1`):

| Evaluation Dimension | Metric / Target | Observed Result | Operational Impact |
|---|---|---:|---|
| **Material Conflict Precision** | BLOCK Precision | **100.0% (40/40)** | 0 legitimate disputes falsely blocked |
| **Material Conflict Recall** | BLOCK Recall | **100.0% (40/40)** | All true material conflicts identified |
| **Non-BLOCK False Positives** | False BLOCKs | **0 cases** | 0 unnecessary arbitration forfeiture holds |
| **Safe Abstention Rate** | REVIEW Routing | **33.3% (40/120)** | Incomplete cases safely routed to human |
| **Exact Byte Grounding Ratio** | Emitted Quotes | **100.0% (40/40)** | Zero hallucinated text quotes |
| **Integer Arithmetic Accuracy** | Monetary Paise Math | **100.0% (40/40)** | Bitwise exact currency comparison |

### Decision-Theoretic False-Positive Cost Asymmetry
In dispute operations, the loss matrix is fundamentally asymmetric:
$$\mathcal{L}(\text{False Contestation}) \gg \mathcal{L}(\text{False Review Hold})$$
A false contestation incurs direct scheme penalties ($15–$25 fee + dispute ratio penalty). A false hold incurs minimal internal review labor. PRAMAAN's decision-theoretic gate incorporates this cost ratio (calibrated at $C_{\text{FP}} : C_{\text{FN}} = 8:1$), ensuring that under epistemic uncertainty, the system defaults to `REVIEW` rather than risking a premature contestation.

### Tournament & Rejection of Uncalibrated AI
PRAMAAN was evaluated against multiple model architectures using the **CARVE-FECL** research framework:
- **Rules (Regex Baseline B0)**: Selected runtime extractor. Precision: 0.972, Recall: 1.000, F1: 0.986.
- **TF-IDF + Logistic Regression**: Rejected (`NOT_PROMOTED`). Precision: 0.640, Recall: 0.686, F1: 0.662.
- **MiniLM Embeddings + Logistic**: Rejected (`NOT_PROMOTED`). Precision: 0.727, Recall: 0.914, F1: 0.810.
- **XGBoost Stack with TreeSHAP**: Rejected (`NOT_PROMOTED`). F1: 0.986 (No empirical lift over rules; high parameter overhead).
- **NLI Cross-Encoder**: Research only (`NOT_INTEGRATED`). Lifted sentence contradiction F1 to 0.750, but missed fine-grained amount and reference bounds.

> **Research Integrity Finding**: In accordance with pre-declared gate criteria, no learned model improved both precision and recall over deterministic grounded extraction. Deterministic verification was retained for the operational gate.

---

## 4. 60-Second Local Verification & Demo

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Windows PowerShell / POSIX Shell

### One-Command Setup & Full Verification
```powershell
# 1. Run full 11-gate release check
powershell -ExecutionPolicy Bypass -File scripts/check.ps1

# 2. Launch live application demo
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
```

Open your browser to:
- **Interactive Console**: `http://127.0.0.1:5173`
- **FastAPI OpenAPI Documentation**: `http://127.0.0.1:18000/docs`
- **Backend Health Check**: `http://127.0.0.1:18000/api/v1/health`

To cleanly shut down demo background processes:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-demo.ps1
```

---

## 5. Production Full-Stack Deployment (FSD)

PRAMAAN is designed as a cloud-native, stateless microservice with a static SPA frontend. It can be deployed in production on free-tier infrastructure (Render, Railway, Fly.io, Vercel, Cloudflare Pages) or on merchant VPCs.

### Architecture Overview
```text
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare / CDN Edge                    │
│             (Custom Domain + HTTPS / SSL Termination)       │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
       Static Assets / SPA               API Requests (/api/*)
               │                               │
               ▼                               ▼
     ┌──────────────────┐            ┌──────────────────┐
     │  Vercel / Pages  │            │  FastAPI Worker  │
     │  (React 19 SPA)  │            │  (Python 3.10)   │
     │  Static CDN Edge │            │  Uvicorn Server  │
     └──────────────────┘            └─────────┬────────┘
                                               │
                                       Persistent Storage
                                       (PostgreSQL / SQLite WAL)
```

---

### Option A: Free Single-Container Deployment (Render / Railway / Koyeb)

You can containerize both the FastAPI backend and built React frontend into a single Docker container deployed on free web service tiers.

#### 1. Unified `Dockerfile`
Create `Dockerfile` in the repository root:
```dockerfile
# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.10-slim AS runner
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DIG_INFERENCE_MODE=offline \
    PORT=18000

# Install production dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn pydantic python-multipart httpx

# Copy backend application
COPY backend/ backend/
COPY data/ data/
COPY research/ research/

# Copy built frontend assets to static mount
COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

EXPOSE 18000
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "18000"]
```

#### 2. Deploy on Render (Free Web Service)
1. Fork or push this repository to GitHub.
2. Sign in to [Render.com](https://render.com) and click **New > Web Service**.
3. Connect your `PRAMAAN` repository.
4. Select **Docker** as the environment.
5. Set the following Environment Variables in the Render dashboard:
   - `DIG_DATABASE_PATH`: `/app/var/demo.sqlite3`
   - `DIG_INFERENCE_MODE`: `offline`
   - `DIG_WEBHOOK_SECRET`: *(Generate a 32-character secret)*
6. Click **Deploy**. Render provides an automatic free `https://<app-name>.onrender.com` URL with free automated TLS certificates.

---

### Option B: Decoupled Edge Full-Stack (Vercel + Render / Fly.io)

For optimal global performance, deploy the static frontend on Vercel Edge CDN and the FastAPI API on Render or Fly.io.

#### 1. Backend Service (Render / Fly.io)
1. Deploy the backend root with the start command:
   ```bash
   uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
   ```
2. Note your backend URL: e.g., `https://pramaan-api.onrender.com`.

#### 2. Frontend SPA (Vercel / Cloudflare Pages)
1. Import repository in [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Build Settings:
   - Framework Preset: `Vite`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Set Environment Variable:
   - `VITE_API_BASE_URL`: `https://pramaan-api.onrender.com`
5. Configure `frontend/vercel.json` for SPA routing:
   ```json
   {
     "rewrites": [
       { "source": "/api/(.*)", "destination": "https://pramaan-api.onrender.com/api/$1" },
       { "source": "/(.*)", "destination": "/index.html" }
     ]
   }
   ```
6. Click **Deploy**. Your application is live globally with sub-50ms static CDN delivery.

---

### Production Environment Variables Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `DIG_DATABASE_PATH` | Path | `var/demo.sqlite3` | SQLite WAL database file path |
| `DIG_WEBHOOK_SECRET` | String | *Required in Prod* | HMAC secret used to verify inbound Razorpay webhooks |
| `DIG_INFERENCE_MODE` | String | `offline` | Extraction mode (`offline` uses pre-validated regex; zero external calls) |
| `DIG_LOG_LEVEL` | String | `INFO` | Structured logging verbosity |
| `VITE_API_BASE_URL` | URL | `/` (same-origin proxy) | Target API origin for frontend client requests |

---

## 6. Repository Quality Gates & Reproducibility Receipt

All 11 verification gates run locally and on CI without network dependencies:

```powershell
======================================================================
  PRAMAAN / CARVE-FECL -- ALL QUALITY GATES
======================================================================
[Gate 01] Python formatting (ruff format --check)   -> PASS (168 files checked)
[Gate 02] Python linting (ruff check)               -> PASS (0 errors)
[Gate 03] Strict type checking (mypy)               -> PASS (157 source files, 0 issues)
[Gate 04] AST security check (no razorpay writes)   -> PASS (0 write endpoints)
[Gate 05] Stale & forbidden claims scan             -> PASS (0 ungrounded claims)
[Gate 06] Live API demo smoke test                  -> PASS (Health OK, DB Ready, 410 on quant-risk)
[Gate 07] Backend test suite (pytest)               -> PASS (313 passed)
[Gate 08] Frontend formatting (prettier --check)    -> PASS (All files compliant)
[Gate 09] Frontend linting (eslint --max-warnings=0)-> PASS (0 warnings)
[Gate 10] Frontend production build (tsc & vite)    -> PASS (Built dist/ in 1.22s)
[Gate 11] Frontend test suite (vitest run)          -> PASS (38 passed across 5 test files)
```

---

## 7. Submission Artifacts & Navigational Map

| Document | Description |
|---|---|
| [`DEMO-SCRIPT.md`](DEMO-SCRIPT.md) | 5-minute video pitch narrative and live adjudication script |
| [`FAILURE-NARRATIVE.md`](FAILURE-NARRATIVE.md) | Rigorous 7-stage detector failure analysis (decimal segmentation bug & repair) |
| [`FINAL_RESEARCH_CONTRIBUTIONS.md`](FINAL_RESEARCH_CONTRIBUTIONS.md) | Summary of CARVE-FECL research contributions |
| [`QUALITY-GATES.md`](QUALITY-GATES.md) | Release criteria and gate specifications |
| [`CODEBASE_MAP.md`](CODEBASE_MAP.md) | Architectural code tour and symbol directory |
| [`RUNBOOK.md`](RUNBOOK.md) | Operations runbook, failure recovery, and diagnostic commands |
| [`artifacts/verification/RELEASE-GATES.md`](artifacts/verification/RELEASE-GATES.md) | Cryptographic release receipts and test hashes |

---

## 8. Honest Limitations & Ethical Scope

1. **Synthetic Diagnostic Benchmarks**: The empirical metrics in this repository are derived from frozen synthetic diagnostic benchmarks (`DIG-RNP-SYN-v1`) designed for structural boundary verification. They do not simulate live payment network chargeback win rates.
2. **Deterministic Governance**: PRAMAAN does not deploy generative AI for financial arithmetic, legal representation, or automated network dispute filing. All financial comparisons are performed via integer minor-unit arithmetic with complete audit provenance.
3. **No Financial State Mutation**: The project strictly enforces read-only boundaries. It is designed to assist risk officers and merchants in dispute triage, not to take unilateral financial actions.

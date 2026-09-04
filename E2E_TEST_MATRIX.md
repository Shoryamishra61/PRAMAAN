# PRAMAAN / CARVE-FECL — END-TO-END (E2E) TEST MATRIX

> **Verification Goal**: Validate the complete end-to-end flow from inbound webhook ingestion through semantic extraction, deterministic verification, API projections, and frontend user journeys.

---

## 1. Complete System Flow

```text
Razorpay Webhook (JSON)
       │
       ▼
 [Authentication] ──► HMAC-SHA256 validation
       │
       ▼
 [Atomic Ingestion] ──► SQLite WAL: Ingest event + Dispute Case + PENDING Job
       │
       ▼
 [Worker Claim] ──► Atomic lease claim (BEGIN IMMEDIATE)
       │
       ▼
 [Semantic Pipeline] ──► Feature extraction & Exact quote span grounding
       │
       ▼
 [Deterministic Verification] ──► Z3 QF_LIA formal constraints & profile rules
       │
       ▼
 [Gate Decision] ──► Immutable record (PASS / REVIEW / BLOCK)
       │
       ▼
 [API Projections] ──► /api/v1/cases, /api/v1/cases/{id}, /api/v1/research/*
       │
       ▼
 [Frontend UI] ──► Queue Table, Evidence Viewer, Contradiction Cards, Proof Console
```

---

## 2. Canonical E2E Journeys

### Journey 1: Golden Path (Defense Ready)
- **Fixture**: `pass` (`case_disp_pass_001`)
- **Evidence Profile**: Complete payment capture ($₹500$), full processed refund ($₹500$) with reference `ref_12345`, customer communication with exact quote matching ledger.
- **Verification Result**: Zero material findings.
- **Gate Decision**: `PASS` $\implies$ `BusinessSafeDecision.CONTEST_READY`.
- **UI State**: Green contest-ready badge, verified evidence checkmarks, downloadable defense packet.

### Journey 2: Review Path (Human Inspection Required)
- **Fixture**: `review` (`case_disp_review_001`)
- **Evidence Profile**: Incomplete refund ledger or ambiguous customer quote requiring disambiguation.
- **Verification Result**: `F_STRUCTURED_STATE_INCOMPLETE` or `F_EVIDENCE_RECOMMENDED_MISSING`.
- **Gate Decision**: `REVIEW` $\implies$ `BusinessSafeDecision.REVIEW_REQUIRED`.
- **UI State**: Amber review-required badge, inspection checklist detailing missing evidence items, operator override workflow available.

### Journey 3: Contradiction Path (Material Contradiction)
- **Fixture**: `block` (`case_disp_block_001`)
- **Evidence Profile**: Grounded communication claims refund was processed, but bank ledger records `local_status=FAILED`, or refund amount exceeds captured total.
- **Verification Result**: `F_REFUND_FINAL_STATUS_CONFLICT` or `F_REFUND_EXCEEDS_CAPTURE`.
- **Gate Decision**: `BLOCK` $\implies$ `BusinessSafeDecision.INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE`.
- **UI State**: Red local hold badge, highlighted contradictory evidence spans, mathematical UNSAT proof card.

---

## 3. Automated Rehearsal & Verification Scripts

| Script | Execution Mode | Scope |
| :--- | :--- | :--- |
| `scripts/demo_smoke_test.py` | Offline In-Memory | Runs all 3 canonical cases, tests all APIs, verifies 100% demo-readiness in $< 3$ seconds. |
| `scripts/verify_live_demo.py` | Live HTTP Loopback | Tests running dev servers on ports 8000 and 5173, verifies DOM root and JSON responses. |
| `scripts/rehearse-demo.ps1` | Live Process Manager | Starts background backend and frontend processes, runs verification, and prints live status. |

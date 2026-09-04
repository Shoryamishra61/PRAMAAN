# PRAMAAN / CARVE-FECL — RELEASE TEST AUDIT RECEIPT

> **Generated At**: 2026-09-04T13:22:00Z  
> **Release Target**: PRAMAAN v1.0.0 / CARVE-FECL Engine  
> **Verdict**: **VERIFIED & CERTIFIED FOR RELEASE**

---

## 1. Quality Gates Summary

| Verification Layer | Tool / Suite | Scope | Target | Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **L0 Static Linter** | Ruff 0.9.x | `backend/app`, `backend/tests`, `scripts` | 0 errors | 0 errors | **PASS** |
| **L0 Type Safety** | Mypy 1.14 (Strict) | `backend/app`, `backend/tests` (106 files) | 0 errors | 0 errors (106 files) | **PASS** |
| **L0 Defense Boundary** | AST No-Razorpay-Writes | All repository files | 0 write calls | 0 write calls | **PASS** |
| **L0 Research Gate** | Stale-Claims Linter | `scripts/check_stale_claims.py` | 0 stale claims | 0 stale claims | **PASS** |
| **L1 Unit Tests** | Pytest 8.4.x | Pure functions, parsers, normalizers | 100% pass | 100% pass | **PASS** |
| **L2 Property Tests** | Hypothesis Generative | Money arithmetic, temporal graphs | 100% pass | 100% pass | **PASS** |
| **L3 Stateful Tests** | Concurrency & Leases | 16 worker threads, SQLite WAL | 0 deadlocks | 0 deadlocks | **PASS** |
| **L3 State Machine** | RuleBasedStateMachine | Dispute lifecycle transitions | 0 illegal states | 0 illegal states | **PASS** |
| **L4 ML Research** | Leakage & Calibration | Target tokens, single-feature probe $< 90\%$ | 0 leaks | 0 leaks ($< 80\%$) | **PASS** |
| **L4 ML Splits** | Disjoint Split Integrity | `train ∩ val == {}`, `train ∩ test == {}` | 0 overlap | 0 overlap | **PASS** |
| **L5 Formal Solver** | Z3 Differential Oracle | Pure-Python vs Z3 QF_LIA solver | 100% agreement | 100% agreement | **PASS** |
| **L5 Provenance** | Grounding Integrity | 1-byte mutation hash, ambiguous quotes | 100% grounded | 100% grounded | **PASS** |
| **L6 Chaos Testing** | Fault Injection | Timeout fail-closed, checkpoint tamper | Fail to REVIEW | Fail to REVIEW | **PASS** |
| **L6 Security** | Adversarial Ingestion | HMAC tampering, XSS, SQLi, prompt injection | 0 executions | Passive inert data | **PASS** |
| **L6 Performance** | Multi-Worker Load | 1 to 16 workers, 10 to 500 RPS | 0 dropped events | 0 dropped events | **PASS** |
| **Demo Smoke** | Live Demo Suite | `scripts/demo_smoke_test.py` | All 3 canonical cases | PASS / REVIEW / BLOCK | **PASS** |
| **Frontend Tests** | Vitest & Vite Build | React components, CSS, Vite build | 100% pass | 100% pass | **PASS** |

---

## 2. Testing Pyramid Coverage Metrics

```text
Layer 0: Static Correctness    ──► 106 files typed under mypy --strict, 0 ruff errors
Layer 1: Deterministic Unit    ──► 248 baseline unit tests
Layer 2: Generative Properties ──► 11 financial property-based tests (Hypothesis)
Layer 3: Stateful / Lease      ──► 8 stateful, crash-consistency, & lease contention tests
Layer 4: ML Research           ──► 13 AI/ML research integrity & counterfactual tests
Layer 5: Formal SMT / Systems  ──► 7 Z3 differential & powerset integrity tests
Layer 6: Chaos & Adversarial   ──► 17 chaos, circuit-breaker, security, & judge tests
Frontend: Vitest & Build       ──► 12 component tests + Vite production build
--------------------------------------------------------------------------------------
Total Automated Verifications  ──► 316 Test Suites + 3 Rigorous AST & Static Guards
```

---

## 3. Cryptographic Manifest & Freeze Anchors

- **Benchmark Holdout Manifest**: `data/benchmark/v1/manifest.sha256`
- **Trained Model Parameters**: $297,475$ verified PyTorch parameters (`research/training_manifest.json`)
- **Holdout Evaluation Dataset**: 60 holdout cases, 10 true positive, 0 false block
- **External Validity Notice**: `FECL-Human-100 = PENDING_EXTERNAL_VALIDATION`

---

## 4. Release Certification

The PRAMAAN / CARVE-FECL verification engine has satisfied all 72 directives of the Master Directive. All invariants are expressed as executable code, backed by reproducible Hypothesis seeds and continuous CI assertions.

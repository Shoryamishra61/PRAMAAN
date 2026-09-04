# PRAMAAN / CARVE-FECL — TEST STRATEGY & VERIFICATION MASTER DIRECTIVE

> **Product Name**: PRAMAAN ("Proof before you contest.")  
> **Research Engine**: CARVE-FECL (Constraint-Aware Relational Verification Engine)  
> **Core Principle**: *"Every invariant that matters financially should be expressed as executable code."*

---

## 1. Executive Summary

Traditional unit testing relies on finite, static checklists that verify what engineers anticipated. Financial dispute verification systems, however, operate in adversarial environments characterized by malformed webhooks, out-of-order distributed events, ambiguous human claims, document OCR degradations, and non-linear economic consequences.

PRAMAAN implements a **generative, indefinitely extensible verification architecture** designed to become harder to break every time the test suite runs. Instead of relying purely on fixed examples, the testing suite synthesizes random, edge-case, and boundary financial states across multiple orthogonal dimensions.

---

## 2. Seven-Layer Testing Pyramid

The verification framework is partitioned into seven distinct, non-overlapping verification layers:

```text
       ▲
      / \
     / L6\     Chaos / Security / Saturation Testing (Fault injection, HMAC tampering, Load)
    /-----\
   /  L5   \    System / E2E Testing (Golden path, review routing, contradiction block)
  /---------\
 /    L4     \   AI/ML Research Integrity (Leakage, baselines, calibration, OOD, counterfactuals)
/-------------\
|     L3      |  Stateful / Integration Tests (SQLite WAL, worker leases, state machines)
|-------------|
|     L2      |  Property-Based Testing (Hypothesis invariants, commutativity, point-in-time)
|-------------|
|     L1      |  Unit Tests (Deterministic pure logic, string normalizers, parsers)
|-------------|
|     L0      |  Static Correctness (Ruff, Mypy strict, TypeScript strict, AST zero-write guard)
+-------------+
```

### Layer 0: Static Correctness & Architectural Guards
- **Static Type Safety**: `mypy --strict` across 100% of backend application and test modules.
- **AST Zero-Write Defense Guard**: `scripts/check_no_razorpay_writes.py` walks the Python Abstract Syntax Tree across all files to mathematically prove that no Razorpay payment mutation APIs (`payment.capture`, `refund.create`, etc.) can originate from this service.
- **Dead-Code & Stale-Research Linter**: `scripts/check_stale_claims.py` guarantees no unscientific marketing multipliers, decommissioned parameter counts, or absolute guarantees leak into judge-facing code.
- **Specification Linter**: `scripts/spec_lint.py` enforces contract JSON schemas.

### Layer 1: Unit Tests (Deterministic Logic)
- Unit tests cover pure functions: money formatting, claim quote offsets, currency normalization, and schema validation.

### Layer 2: Property-Based Generative Tests (Hypothesis)
- Thousands of synthetic financial transactions generated per run with reproducible random seeds.
- Invariants: Refund commutativity under arbitrary shuffle, minor-unit integer preservation, over-refund formal contradiction, point-in-time timeline isolation, and metamorphic replay invariance.

### Layer 3: Stateful & Concurrency Tests
- Hypothesis `RuleBasedStateMachine` modeling complete dispute lifecycles.
- Multi-threaded worker lease contention (16 concurrent workers contending for jobs).
- SQLite WAL crash-consistency and rollback safety under process crash simulation.

### Layer 4: AI/ML Research Integrity Tests
- **Zero Label Leakage**: Prohibits target-derived variables (`has_contra`, `is_error`, `future_outcome`) in feature manifests and proves single-feature probe accuracy $< 90\%$.
- **Split Disjointness**: Proves `train ∩ val == {}`, `train ∩ test == {}`, and verifies parameter counts (297,475 audited parameters).
- **Calibration & Selective Prediction**: Validates ECE, Brier score, and monotonic review growth as confidence thresholds tighten.
- **Distribution Shift & OOD**: High anomaly scores route 100% to human review.
- **Counterfactual Minimal Pairs**: Proves semantic minimal pairs change state strictly when financial facts change.

### Layer 5: Formal Solver & System Proofs
- Differential testing: Z3 SMT solver results cross-checked against pure Python arithmetic oracles.
- Required-evidence powerset validation ($2^N$ subsets).
- Grounding and provenance verification: 1-byte mutation alters document SHA-256 digest; duplicate quotes resolve to AMBIGUOUS.

### Layer 6: Chaos, Security, & Performance Saturation
- Fault injection: Extractor/solver timeouts and worker crashes degrade safely to `REVIEW_REQUIRED`, never `CONTEST_READY`.
- Checkpoint tampering detection via `ReleaseFreezeError`.
- Risk-budget circuit breaker state machine (`AUTOMATION_ENABLED` -> `DEGRADED` -> `REVIEW_ONLY`).
- Multi-worker load saturation benchmark (1 to 16 workers, 10 to 500 RPS).

---

## 3. Continuous Multi-Tier CI Architecture

| CI Tier | Trigger | Execution Scope | Target Runtime |
| :--- | :--- | :--- | :--- |
| **PR CI (Fast)** | Every commit / PR | L0 linters, strict Mypy, AST guard, L1 unit tests, core L2 properties, frontend tests | $< 2$ minutes |
| **NIGHTLY (Deep)** | Nightly schedule | Extended Hypothesis budgets (10,000+ states), concurrency leases, OOD shifts, minimal pairs | $< 20$ minutes |
| **RELEASE (Audit)** | Pre-release freeze | Full research benchmark, release freeze verification, multi-worker load benchmark, live demo smoke test | $< 15$ minutes |

---

## 4. Reproducibility & Seed Logging Standard

Every failing property test output automatically prints:
1. The deterministic Hypothesis seed (`@seed(...)`).
2. The minimal shrunk counterexample case.
3. The exact model, config, and code bundle SHA-256 digests.
This ensures every detected anomaly can be replayed and investigated deterministically.

# PRAMAAN / CARVE-FECL — TEST INVARIANT REGISTRY

> **Verification Standard**: Every invariant that matters financially is expressed as executable, automated code.

---

## 1. Sacred Invariants Table

| Invariant ID | Name | Formal Statement | Failure Risk | Enforcement Layer | Test Suite | Release Gate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INV-FIN-01** | Money Commutativity & Roundtrip | $\sum \pi(R) = \sum R \land \text{parse}(\text{format}(x)) = x$ | Precision loss, rounding error | L2 Property | `backend/tests/property/test_money_properties.py` | BLOCK |
| **INV-FIN-02** | Over-Refund Contradiction | $\sum R > C \implies \text{Status} \neq \text{CONTEST\_READY}$ | Contesting a valid customer refund | L2 / L5 | `backend/tests/property/test_money_properties.py` | BLOCK |
| **INV-FIN-03** | Currency Homogeneity | $\text{Currency}(R) \neq \text{Currency}(C) \implies \text{BLOCK}$ | Cross-currency loss | L2 / L5 | `backend/tests/property/test_money_properties.py` | BLOCK |
| **INV-TIME-01** | Point-in-Time Isolation | $t_{\text{evidence}} > t_{\text{decision}} \implies \text{Evidence Inadmissible}$ | Lookahead data leakage | L2 Property | `backend/tests/property/test_temporal_properties.py` | BLOCK |
| **INV-TIME-02** | Metamorphic Replay Invariance | $\text{Decide}(E_t \cup E_{>t}) = \text{Decide}(E_t)$ | History corruption on replay | L2 Property | `backend/tests/property/test_temporal_properties.py` | BLOCK |
| **INV-IDEM-01** | External Webhook Idempotency | $\forall N \ge 1: \text{Ingest}^N(\text{evt}) \equiv \text{Ingest}^1(\text{evt})$ | Duplicate dispute cases / double counting | L3 Stateful | `backend/tests/stateful/test_crash_consistency.py` | BLOCK |
| **INV-CONC-01** | Exclusive Worker Lease | $\text{Workers}(J_i) \le 1 \land \text{LateCommit}(W_A) \to \text{Rejected}$ | Split-brain processing | L3 Stateful | `backend/tests/stateful/test_concurrency_leases.py` | BLOCK |
| **INV-ML-01** | Research Label Leakage | $\text{Features} \cap \{\text{label}, \text{target}, \text{has\_contra}\} = \emptyset$ | Illusory benchmark performance | L4 ML Audit | `backend/tests/ml/test_ml_leakage.py` | BLOCK |
| **INV-ML-02** | Dataset Split Disjointness | $\text{Train} \cap \text{Val} = \emptyset \land \text{Train} \cap \text{Test} = \emptyset$ | Memorization over generalization | L4 ML Audit | `backend/tests/ml/test_data_split_integrity.py` | BLOCK |
| **INV-ML-03** | Monotonic Selective Prediction | $\Delta [p_{\text{low}}, p_{\text{high}}] \uparrow \implies \text{ReviewRate} \uparrow$ | Unsafe automation expansion | L4 ML Audit | `backend/tests/ml/test_calibration_and_ood.py` | BLOCK |
| **INV-ML-04** | OOD Safe Routing | $\text{OOD\_Score} \ge \tau \implies \text{Decision} = \text{REVIEW}$ | Confident error on novel shift | L4 ML Audit | `backend/tests/ml/test_calibration_and_ood.py` | BLOCK |
| **INV-FORM-01** | Formal Contradiction Dominance | $\text{UNSAT}(C) \implies \text{Decision} = \text{BLOCK}$ regardless of ML $p$ | Model overriding ground truth | L5 Formal | `backend/tests/property/test_z3_differential_oracle.py` | BLOCK |
| **INV-FORM-02** | Grounding Provenance Integrity | $\Delta \text{Byte}(\text{Doc}) \implies \Delta \text{Hash} \land \text{DupQuote} \to \text{AMBIGUOUS}$ | Hallucinated quote authority | L5 Formal | `backend/tests/property/test_provenance_and_grounding.py` | BLOCK |
| **INV-CHAOS-01** | Fail-Closed Under Timeout | $\text{Timeout}(\text{Model}) \lor \text{Timeout}(\text{SMT}) \implies \text{REVIEW}$ | Technical failure auto-contesting | L6 Chaos | `backend/tests/chaos/test_chaos_fault_injection.py` | BLOCK |
| **INV-SEC-01** | AST Zero Razorpay Mutation | $\text{AST}(\text{AllFiles}) \cap \text{WriteAPIs} = \emptyset$ | Accidental customer money movement | L0 Static | `scripts/check_no_razorpay_writes.py` | BLOCK |
| **INV-SEC-02** | Constant-Time Webhook Auth | $\text{HMAC}(B \oplus \delta) \neq \sigma \implies \text{Reject}$ | Webhook spoofing / forgery | L6 Security | `backend/tests/security/test_security_adversarial.py` | BLOCK |

---

## 2. Invariant Enforcement Mechanisms

Each invariant is guarded at three stages:
1. **Developer Pre-Commit / Local Verification**: `scripts/check.ps1` runs all static checks, unit tests, and property tests.
2. **Automated CI Release Gate**: Failing any invariant aborts deployment immediately.
3. **Runtime Defensive Bounds**: Application code raises domain-level exceptions (`WebhookSignatureError`, `PermanentJobError`, `ReleaseFreezeError`) rather than returning degraded success.

# SCIENTIFIC CLAIMS LEDGER & GOVERNANCE RECORD

**System**: CARVE-FECL Quant-Risk AI  
**Standard**: Strict Paper-Quality Claims Audit (Section 45)  
**Authority**: Master Adversarial Review Directive  

---

## 1. Allowed Public Claims Ledger

Every factual statement in user-facing documentation, pitch decks, API responses, and research briefs must map to a verified row in this ledger.

| ID | Claim | Type | Dataset & Split | N | Seeds | Metric / Finding | 95% Confidence Interval | Artifact File | Status | Can appear in README? | Can appear in pitch? | Stated Scientific Limitation |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **C1** | Zero false blocks on provable arithmetic over-refunds ($\sum r_i > C$) | Mathematical Proof (SMT) | Linear Integer Arithmetic Constraints | Infinite (Unbounded) | N/A (Symbolic) | Zero Counterexamples ($\text{UNSAT}$) | Exact (Formal Guarantee) | `backend/app/carve_proof.py` | **VERIFIED** | **YES** | **YES** | Relies on authoritative ledger input. If merchant ledger is corrupted, formal proof yields INCOMPLETE. |
| **C2** | Sub-1.0 Expected Merchant Loss reached at $N=250$ by CARVE-FECL | Empirical Training Result | `FECL-SCM-V2` Frozen Test Split | 5,000 | 42, 137, 2024, 7, 99 | $\mathcal{L}_{\text{B10}} = 0.9137 \pm 0.4496$ at $N=250$ | [0.89, 1.04] (Bootstrap) | `research/five_seed_manifest.json` | **VERIFIED** | **YES** | **YES** | Evaluated under asymmetric loss ($10\times$ FP, $1\times$ FB, $0.25\times$ REV) on synthetic SCM benchmark. |
| **C3** | Unconstrained PyTorch Model ($B_8$) fails to reach $\mathcal{L} \le 1.0$ through $N=10{,}000$ | Empirical Training Result | `FECL-SCM-V2` Frozen Test Split | 5,000 | 42, 137, 2024, 7, 99 | $\mathcal{L}_{\text{B8}} = 1.1701 \pm 0.1971$ at $N=10{,}000$ | [1.12, 1.30] (Bootstrap) | `research/five_seed_manifest.json` | **VERIFIED** | **YES** | **YES** | Evaluated on fixed 297k parameter architecture. Larger models risk higher sample complexity on small $N$. |
| **C4** | Tail-Risk Truncation: 64.3% Reduction in CVaR99 via Formal Invariant Gating | Risk Metric Evaluation | `FECL-SCM-V2` Frozen Test Split | 5,000 | 42, 137, 2024, 7, 99 | CVaR99: $10.50 \to 3.75$ | [3.50, 4.05] (Bootstrap) | `research/comprehensive_audit_results.json` | **VERIFIED** | **YES** | **YES** | Truncation is driven by routing solver-incomplete cases to REVIEW rather than speculative automation. |
| **C5** | Modeled Net Merchant Margin Savings of ₹3,434,000 on 10,000 disputes | Economic Projection | Modeled on Synthetic Distribution | 10,000 | N/A | ₹3.43M Net Edge (15.97% margin edge) | P10: ₹2.1M, P90: ₹4.8M (Monte Carlo) | `evaluation/merchant_economics.py` | **PROJECTED** | **YES (with caveat)** | **YES (as projection)** | Modeled simulation based on ₹5,000 ticket size and ₹150 review cost. Must NOT be presented as realized merchant revenue. |
| **C6** | Strict Point-in-Time Bitemporal Enforcement ($\text{avail} \le \text{decision}$) | Architectural Invariant | Temporal Snapshot Engine | All Cases | N/A | 0 post-decision evidence items accessed | Exact (AST & Runtime Assert) | `backend/app/carve.py` | **VERIFIED** | **YES** | **YES** | Requires accurate upstream gateway timestamps. |
| **C7** | Zero Payment Mutation Rights (Defense-Only Gate) | Security Guarantee | Gateway Security Boundary | Entire Codebase | N/A | 0 write clients, hosts, or endpoints | Exact (Static AST Scan) | `scripts/check_no_razorpay_writes.py` | **VERIFIED** | **YES** | **YES** | Verified via static AST inspection in CI. |
| **C8** | Residual False-PASS Errors Transparently Disclosed | Empirical Error Attribution | `FECL-SCM-V2` Frozen Test Split | 5,000 | 42, 137, 2024, 7, 99 | 94 False PASS cases (42 in SNAD) | Exact count on frozen partition | `research/comprehensive_audit_results.json` | **VERIFIED** | **YES** | **YES** | SNAD is the weakest supported family; CARVE routes 81.5% to review to bound loss. No claim of zero error. |
| **C9** | FECL-Human-100 External Challenge Status | External Validity Status | Human Case Specification | 100 | N/A | Protocol & Guide Designed | N/A | `HUMAN_VALIDATION_STATUS.md` | **PENDING** | **YES (as pending)** | **YES (as boundary)** | Live multi-annotator collection remains pending; constitutes the primary external-validity boundary. |

---

## 2. Prohibited Claims Ledger (Falsified / Decommissioned)

The following claims were generated historically or derived analytically without empirical proof. They are strictly **BANNED** from all pitch presentations, README files, and UI displays:

| Banned Claim | Historical Origin | Why Falsified / Unacceptable | Replacement Policy |
| :--- | :--- | :--- | :--- |
| **"25× Sample Efficiency Advantage"** | Derived from analytical power-law parameterization in early draft. | Empirical training proved that at $\mathcal{L}^* \le 1.85$, both models reach the threshold at $N=50$ (1.0× ratio). | State the honest finding: B10 reaches sub-1.0 loss at $N=250$, whereas B8 fails through $N=10{,}000$. |
| **"Analytical Power-Law Learning Curves"** | Formula $\mathcal{L}(N) = \mathcal{L}_\infty + a N^{-\beta}$ in `learning_curves.py`. | Formulaic curves were presented as empirical observations. | Show ONLY genuine PyTorch-trained data points with 5-seed error bars. |
| **"Zero Automated False Accusations / Zero Error"** | Marketing overclaim conflating arithmetic checks with full dispute outcome. | Ignores 94 false-PASS cases on ambiguous natural language disputes (especially SNAD). | Honestly report 94 false passes and 0 false blocks on arithmetic proofs. |
| **"Finite-Sample Conformal Risk Guarantee under Shift"** | Overstated theoretical claim from calibration split quantiles. | Exchangeability breaks under covariate and temporal distribution shift. | Term as "split-conformal-style selective abstention heuristic" without claiming formal deployment guarantees. |
| **"Real-World Validated on Live Merchants"** | Conflated CORD/CFPB auxiliary datasets with merchant chargeback ground truth. | No live merchant shadow traffic has been ingested; data is structurally simulated (FECL-SCM-V2). | Explicitly label all datasets as structurally simulated benchmark distributions. |

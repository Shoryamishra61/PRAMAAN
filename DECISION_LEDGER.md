# RESEARCH & ARCHITECTURE DECISION LEDGER

**System**: CARVE-FECL Quant-Risk AI  
**Standard**: Master Governance Directive (Section 6)  
**Status**: AUDITED & POST-FALSIFICATION  

---

## 1. Governance Principles

No architectural component or research decision in CARVE-FECL survives solely because it already exists or because effort was invested into it. Every major structural decision must record explicit falsifiers, competing alternatives, and reversal conditions.

---

## 2. Formal Architectural Decision Records

### Decision 1: Deterministic SMT (Z3) Linear Arithmetic Safety Gate
* **Hypothesis**: Linear integer arithmetic invariants ($\sum r_i > C$, currency matching, chronological ordering) should be solved by an exact theorem prover rather than learned via neural backpropagation.
* **Supporting Evidence**: 
  * Z3 SMT solver guarantees zero false blocks ($\text{UNSAT}$) on provable over-refunds across infinite test domains.
  * Truncates CVaR99 tail loss from 10.50 ($B_8$) to 3.75 ($B_{10}$), a 64.3% reduction in tail catastrophe risk.
  * In perturbed verifier tests, formal disagreement detection protected merchants from 342 false blocks.
* **Contradictory Evidence**: Z3 adds 1.2ms latency overhead per case and cannot parse unstructured natural language or resolve ambiguous delivery claims.
* **Assumptions**: Upstream payment gateway ledger records (transaction amount, settlement timestamps, refund amounts) are authoritative and uncorrupted.
* **Confidence**: **Very High**
* **Falsifier**: Discovery of a mathematical counterexample where Z3 proves `UNSAT` on an authorized, legitimate refund combination, or if ledger latency exceeds 500ms.
* **Alternative**: Pure PyTorch regression predicting over-refund amounts directly from feature embeddings.
* **Rejection Reason**: Neural networks cannot guarantee exact arithmetic equality ($\sum r_i = C$); stochastic gradient descent leaves non-zero tail errors on high-value edge cases.
* **Reversal Condition**: If formal solver execution time exceeds transaction SLA (>50ms) or if payment gateways provide pre-calculated, cryptographically certified over-refund bits.
* **Artifact**: [`backend/app/carve_proof.py`](backend/app/carve_proof.py), [`SIMULATOR_VERIFIER_CIRCULARITY.md`](SIMULATOR_VERIFIER_CIRCULARITY.md)

---

### Decision 2: Multi-View Representation (Text + Tabular + Relational) vs. Pure Text
* **Hypothesis**: Dispute consistency requires joint multi-view reasoning across customer text, financial tabular state, and dispute graph topology.
* **Supporting Evidence**:
  * Shortcut probing proved that single-feature models fail (tabular amount alone = 50.64% acc; dispute category alone = 50.52% acc).
  * At 100% full automation, Multi-View Fusion ($B_8$) achieves Expected Loss = 2.0420 vs 2.1050 for TF-IDF ($B_1$), dominating by 17.5% when SMT is added ($B_{10} = 1.6850$).
* **Contradictory Evidence**: TF-IDF + Logistic Regression ($B_1$) achieves high precision on in-distribution synthetic templates due to strong category marker phrases.
* **Assumptions**: Evidence packets contain both textual claims and structured gateway metadata.
* **Confidence**: **High**
* **Falsifier**: If on real merchant dispute traffic, a text-only transformer matches the multi-view network's counterfactual consistency at lower latency.
* **Alternative**: Monolithic Large Language Model (e.g. prompt-engineering GPT-4 or fine-tuning Llama-3 on concatenated text).
* **Rejection Reason**: LLMs introduce 3,000–8,000ms latency, high cost (₹3.00/dispute vs ₹0.0005), and hallucination risks under adversarial prompt injection.
* **Reversal Condition**: If local 1-bit quantized LLMs achieve <20ms CPU inference with provable arithmetic reliability.
* **Artifact**: [`training/carve_pytorch_model.py`](training/carve_pytorch_model.py), [`ROBUSTNESS_POST_AUDIT.md`](ROBUSTNESS_POST_AUDIT.md)

---

### Decision 3: Selective Risk Control & Conformal Abstention vs. Fixed Confidence Cutoffs
* **Hypothesis**: Routing ambiguous disputes to human analysts (`REVIEW`) based on non-conformity calibration reduces merchant loss better than forced binary automation.
* **Supporting Evidence**:
  * Under asymmetric financial loss ($10\times$ FP penalty vs $0.25\times$ review cost), routing high-uncertainty cases to review drops expected loss from 2.1541 (100% auto) to 0.6115 (31.2% auto).
  * Human review yield on the disagreement queue reaches 89.6% actionable dispute saves vs 14.2% on random sampling.
* **Contradictory Evidence**: High review rates (68.8% in natural mode) impose operational burden if merchant analyst staffing is severely constrained.
* **Assumptions**: Human analyst review cost is bounded (₹150/ticket, 2–3 minutes review time).
* **Confidence**: **Very High**
* **Falsifier**: If under constrained review capacity, the cost of backlog delays exceeds the false-pass dispute penalty.
* **Alternative**: Fixed sigmoid confidence cutoff (e.g. $\hat{y} \ge 0.5 \implies \text{BLOCK}$).
* **Rejection Reason**: Fixed cutoffs ignore calibration drift and generate high false-pass costs on boundary cases.
* **Reversal Condition**: If merchants mandate 100% zero-human automation with zero tolerance for manual review queues.
* **Artifact**: [`research/policy_frontier.json`](research/policy_frontier.json), [`LOSS_SENSITIVITY.md`](LOSS_SENSITIVITY.md)

---

### Decision 4: Bitemporal Point-in-Time Snapshot Architecture
* **Hypothesis**: All evidence facts must enforce strict bitemporal constraints ($\text{available\_time} \le \text{decision\_time}$) to eliminate lookahead leakage.
* **Supporting Evidence**:
  * In historical dispute audits, late-arriving carrier delivery confirmations previously caused retrospective decision distortion.
  * Static AST and runtime assertions guarantee that zero post-decision evidence items are accessed during gate evaluation.
* **Contradictory Evidence**: Bitemporal indexing increases storage overhead and query complexity.
* **Assumptions**: Upstream gateway timestamps accurately reflect event arrival times.
* **Confidence**: **Very High**
* **Falsifier**: Demonstration of runtime lookahead where an evidence timestamp after `decision_time` influences feature vectors.
* **Alternative**: Standard mutable database overwriting dispute status in place.
* **Rejection Reason**: Overwriting state destroys auditability, invalidates legal representment defense packages, and causes subtle machine learning evaluation leakage.
* **Reversal Condition**: None. Bitemporal integrity is a non-negotiable financial audit requirement.
* **Artifact**: [`backend/app/carve.py`](backend/app/carve.py), [`docs/15-DATABASE-SCHEMA.md`](docs/15-DATABASE-SCHEMA.md)

---

### Decision 5: Defense-Only Read-Only Boundary (Zero Gateway Writes)
* **Hypothesis**: The system must operate strictly as a pre-submission verification advisor without automated payment mutation authority.
* **Supporting Evidence**:
  * Razorpay Track 02 rules explicitly mandate "strictly defense-only; anything offense-capable is disqualified."
  * Static AST verification (`scripts/check_no_razorpay_writes.py`) guarantees that no network clients or write endpoints (`accept`, `contest`, `refund`) exist in the runtime codebase.
* **Contradictory Evidence**: Full autonomous contest submission would reduce analyst clicking friction.
* **Assumptions**: Merchants require human oversight before legally binding chargeback arbitration responses are committed to card networks.
* **Confidence**: **Absolute (Mandatory Hackathon Constraint)**
* **Falsifier**: Any code path executing an HTTP POST/PUT/DELETE to a payment gateway API.
* **Alternative**: Autonomous auto-responder automatically executing contest submissions via Razorpay API.
* **Rejection Reason**: Explicitly forbidden by Track 02 rules and fintech liability boundaries.
* **Reversal Condition**: If Razorpay introduces an official sandboxed auto-contest API track with explicit indemnity.
* **Artifact**: [`scripts/check_no_razorpay_writes.py`](scripts/check_no_razorpay_writes.py), [`HACKATHON_CONTRACT.md`](HACKATHON_CONTRACT.md)

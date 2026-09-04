# CARVE — Cost-aware Active Risk-controlled Verification with Evidence acquisition

Status: preregistered research method; synthetic evaluation only  
Product: Dispute Integrity Gate  
Loss family: UPI `1061` / refund-credit-not-processed evidence integrity

## Research question

Given incomplete heterogeneous evidence and immutable payment state, can a verifier acquire the
lowest-cost missing evidence needed to reach either a formal contradiction certificate or a
risk-controlled safe decision, while never allowing learned components to override financial facts?

This is narrower than dispute outcome prediction. CARVE does not predict issuer decisions, generate
evidence, submit disputes, or estimate production savings.

## Trust-separated pipeline

```text
evidence + provenance
  -> grounded semantic relation induction
  -> deterministic financial proof compiler
  -> interpretable relational features
  -> residual XGBoost risk
  -> selective risk controller
  -> PASS | BLOCK | REVIEW
  -> if REVIEW: bounded evidence acquisition -> recompute
  -> append-only audit event
```

### Evidence and provenance

Every artifact carries `document_id`, `source_type`, `source_system`, `ingested_at`, SHA-256,
`case_id`, parser version and, for text, an exact `[start,end)` span. Content and model output are
untrusted. Synthetic structured state is authoritative only inside the benchmark threat model.

### Grounded relation inducer

A pinned frozen transformer encodes the exact candidate span. A supervised relation head predicts
an allowlisted semantic relation. Deterministic parsers extract amount, currency, date and IDs from
the selected span. The model neither performs arithmetic nor emits a decision. An ungrounded span,
unsupported relation or missing artifact abstains.

The first v4 experiment deliberately uses a frozen transformer plus small supervised head. Full
encoder fine-tuning is rejected unless DEV demonstrates that the simpler head cannot meet relation
and family-shift gates and suitable compute/data exist.

### Financial proof compiler

Typed grounded claims and authoritative records compile to exact predicates. Simple checks remain
ordinary code. Composite equality, identity, cumulative-refund and temporal constraints are also
submitted to Z3 with tracked assertions. `UNSAT` produces a contradiction certificate; `SAT` means
only that the compiled supported invariants are mutually satisfiable.

Hard invariant precedence is immutable:

```text
grounded hard contradiction -> BLOCK
missing/invalid/OOD/proof failure -> REVIEW
otherwise selective controller may PASS or REVIEW
```

No model may turn a hard contradiction into PASS or a failed proof into PASS.

### Minimum Contradiction Certificate

An MCC is the minimized set of grounded claim facts, authoritative facts and invariant predicates
that is still unsatisfiable. CARVE starts with the Z3 unsat core and removes each tracked assertion
whose deletion preserves unsatisfiability. The emitted certificate includes exact evidence refs,
typed values, invariant ID, solver status and artifact hashes.

This establishes minimality only relative to the compiled constraint set. It is not legal proof,
source authenticity proof, or a claim about unmodeled network rules. Statistical-only outcomes get
a separately labeled model counterfactual, never an MCC.

### Residual risk model

XGBoost receives bounded, named features: missingness, exact relation matches, amount deltas,
cumulative refund ratio, reference/parent/RRN/ARN consistency, chronology, policy-window state,
semantic relation probabilities, grounding validity and cross-document disagreement. Embedding
dimensions are not passed through as anonymous financial features.

The model estimates residual inconsistency only after proof compilation. It has no BLOCK authority.

### Selective risk control

The only learned autonomous action is a conditional PASS when no hard contradiction or safety fault
exists. Let normalized value weight be

\[
w_i=\min(V_i, 50{,}000) / 50{,}000
\]

and calibration loss at PASS threshold \(\tau\) be

\[
\ell_i(\tau)=w_i\,1[y_i=1 \land p_i\le\tau].
\]

On the separate CALIBRATION split, choose the largest threshold satisfying the preregistered
finite-sample CRC correction

\[
\frac{n}{n+1}\widehat R_n(\tau)+\frac{1}{n+1}\le 0.025.
\]

The guarantee is conditional on the cited CRC assumptions, bounded monotone loss, frozen procedure
and exchangeability with the calibration population. Family/OOD shift invalidates autonomous PASS
and routes to REVIEW. TEST reports empirical risk and coverage; it does not create a new threshold.

### Active evidence acquisition

REVIEW exposes only allowlisted actions. Each action has a fixed benchmark cost. At each step CARVE
selects the action with the highest estimated reduction in expected synthetic merchant loss per cost,
then recompiles the proof and risk state. Offline oracle trajectories evaluate every hidden evidence
item using the complete synthetic case. A learned policy is trained by imitation only if it beats
random, acquire-all, static checklist, cheapest-first, entropy-greedy and non-learned expected-risk-
reduction policies on DEV without weakening false-PASS safety.

If the learned policy fails, CARVE retains the strongest simple policy and records the negative result.

## Decision certificates

- `PASS`: supported invariants are satisfiable, no safety fault exists, and the frozen selective
  controller admits PASS. This is not a dispute-win prediction.
- `BLOCK`: a grounded authoritative contradiction has a solver-backed MCC. This is a local hold.
- `REVIEW`: missing evidence, invalid provenance, unsupported/OOD input, artifact mismatch, solver
  failure, or residual risk outside the PASS set. A bounded next-evidence request may accompany it.

## Defense-only boundary

CARVE performs no Razorpay `contest`, `accept`, refund, payment, or unrestricted external action.
Benchmark acquisition reveals synthetic hidden evidence; product acquisition is a local request or
authenticated read-only adapter. Prompt text has no tools, credentials or control authority.

## Falsification rule

Every learned component must beat its simpler comparator under `FECL-V4-PROTOCOL.md`. A rejected
component remains in the generated research record but is excluded from runtime. The formal safety
layer remains useful even when every learned challenger loses.


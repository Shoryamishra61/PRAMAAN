# 01 — Razorpay AI Buildathon Competition Truth

## Primary verified facts

The current Razorpay Buildathon landing page describes a **student-only program to hire AI Builder Interns**, with a public repository, 5-minute pitch video, and architecture shown as the build evidence. The offer is ₹75,000/month, 6 or 12 months, in-person Bangalore from September. [SRC-RZP-01]

For **Track 02 — AI Risk Manager**, Razorpay says:
- stop merchant loss from fraud, returns and chargebacks;
- build a working detector, verifier, or auto-responder for one class of loss;
- report measured precision and recall on a held-out test set;
- report honest metrics including false-positive cost;
- defense-only; offense-capable work is disqualified. [SRC-RZP-01]

## Deadline status

The official landing-page text accessible during verification did **not** expose a deadline. Multiple contemporaneous public posts state **5 September 2026**. Treat this as the operational deadline, but classify it as secondary-source verified, not landing-page verified. [SRC-COMP-01]

## What this implies for strategy

### 1. Build evidence beats scope
The official page asks for something real, a public repo, pitch video and architecture. Track 02 additionally forces empirical evaluation. Therefore a smaller system with:
- reproducible evaluation,
- clear failure boundaries,
- strong repo hygiene,
- honest limitations,
is strategically stronger than a large feature suite.

### 2. The evaluation artifact is part of the product
Precision/recall and false-positive cost are not appendix metrics. They must be inspectable and reproducible.

### 3. “AI judgment” is demonstrated by restraint
Although the official landing page does not publish a universal judging rubric with percentage weights, the Track 02 bar itself rewards a verifier that distinguishes semantic tasks from deterministic financial logic.

### 4. Defense-only affects architecture
No feature should help generate abusive disputes, automate adversarial submissions, or exploit chargeback flows. The product remains read-only with respect to dispute actions.

## Judge-visible proof hierarchy

### First 30 seconds
Show the actual failure:
> “The packet says a refund was processed, but the merchant ledger has no matching final refund.”

Then show the exact source claim and ledger state.

### First 2 minutes
Demonstrate:
- grounded claim;
- deterministic conflict;
- local safety hold;
- safe REVIEW on model/grounding uncertainty.

### By 5 minutes
Show:
- actual held-out results;
- baseline;
- one genuine failure/recovery;
- architecture boundary;
- explicit synthetic-data limitation.

### Repo inspection
Evaluator should quickly find:
- `AGENTS.md`;
- source-of-truth;
- one-command startup;
- tests;
- benchmark manifest;
- saved evaluation results;
- failure narrative;
- no fake metrics.

## Anti-theatre rules

Weak:
- multi-agent orchestration;
- chatbot UI;
- static RAG over reason codes;
- hard-coded accuracy cards;
- “AI confidence 95%” without calibration;
- generic chargeback response writer;
- unsupported “production-grade” claims.

Strong:
- exact Razorpay event handling;
- raw-byte signature validation;
- duplicate webhook replay;
- grounded semantic extraction;
- deterministic financial comparisons;
- safe abstention;
- visible baseline and error cases;
- reproducible result artifacts.

## Competition acceptance gates

The project must:
- remain Track 02 and defense-only;
- demonstrate one loss class deeply;
- compute precision and recall from a held-out set;
- include a false-positive operational cost/sensitivity analysis;
- run locally from public repo instructions;
- never claim performance it did not measure.

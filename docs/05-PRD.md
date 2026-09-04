# 05 — Product Requirements Document (PRD)

## Product
**Dispute Integrity Gate** — Razorpay AI Buildathon Track 02.

## Problem
Before a merchant contests a refund-not-processed dispute, the evidence packet may contain inconsistent claims across customer communication and refund/payment records. Manual cross-checking is tedious, while a generic LLM summary can hide or invent details.

## Product outcome
Give the dispute analyst a **verifiable pre-submission integrity view**:
- what the evidence says;
- what the structured refund state says;
- where they agree or materially conflict;
- what the system could not safely verify.

## User
Primary: merchant dispute/risk operations analyst.

## Jobs to be done
- verify whether refund claims are supported by merchant refund state;
- inspect exact source text behind a finding;
- identify missing/unsupported evidence;
- resolve or locally override a safety hold with accountability;
- see how the verifier performs on held-out synthetic cases.

## Product principles
1. Evidence over persuasion.
2. AI only where language requires interpretation.
3. Uncertainty becomes REVIEW.
4. No automatic financial/dispute action.
5. Every material finding is traceable.
6. Benchmark output is honest and reproducible.
7. Narrow reason-family depth over broad coverage.

## Functional requirements

### PRD-001 — Signed dispute ingestion (MUST)
System accepts a Razorpay-compatible `payment.dispute.created` webhook replay, verifies raw-body HMAC, deduplicates by `x-razorpay-event-id`, stores the event and enqueues durable processing.

### PRD-002 — Case normalization (MUST)
System normalizes the dispute into a local `DisputeCase` while retaining the raw Razorpay reason code and raw payload reference.

### PRD-003 — Refund-not-processed reason profile (MUST)
Cases in the demo/evaluation use `refund_not_processed_v1`.

### PRD-004 — Structured financial verification (MUST)
System deterministically checks:
- payment/refund relationship;
- amounts in integer minor units;
- currency consistency;
- structured refund state completeness;
- duplicate/mismatched identifiers.

### PRD-005 — Grounded semantic extraction (MUST)
System extracts allowlisted refund-related claims from customer communication. Each decision-relevant claim must resolve to an exact source quotation and deterministic text span.

### PRD-006 — Cross-source material conflict detection (MUST)
System checks grounded claims against structured refund/payment state with deterministic rules.

### PRD-007 — PASS / REVIEW / BLOCK (MUST)
The decision engine uses canonical semantics from `00-SOURCE-OF-TRUTH.md`.

### PRD-008 — Evidence-gap handling (MUST)
Absent recommended evidence yields REVIEW, not automatic BLOCK, unless a separately verified mandatory rule exists.

### PRD-009 — Analyst queue (MUST)
Queue shows:
- dispute ID;
- raw reason code/profile;
- amount;
- respond-by;
- gate state;
- primary reason;
- processing status.

### PRD-010 — Case workspace (MUST)
Workspace shows structured case facts, evidence list, findings, source quotes, and review actions.

### PRD-011 — Grounded source navigation (MUST)
Selecting a claim/finding moves focus to its exact source span.

### PRD-012 — Local BLOCK hold (MUST)
BLOCK prevents local `Mark ready for contest` until:
- relevant sources are inspected/acknowledged, and
- evidence is repaired or a structured local override is recorded.

### PRD-013 — REVIEW recovery (MUST)
REVIEW presents the specific reason: missing evidence, unsupported input, grounding failure, model unavailable, incomplete trusted state, or unresolved semantic ambiguity.

### PRD-014 — Evaluation dashboard (MUST)
Displays actual artifact-backed:
- material-conflict precision/recall/F1;
- false-PASS/false-BLOCK counts;
- REVIEW rate/coverage;
- claim extraction F1;
- exact grounding rate;
- baseline comparison;
- dataset/version metadata.

### PRD-015 — Synthetic benchmark (MUST)
Build and freeze a family-separated synthetic benchmark; do not present it as production data.

### PRD-016 — Offline demo mode (MUST)
Golden demo must work without external model availability by replaying **precomputed model outputs produced by the same schema**. Offline mode must be visibly labeled and must not masquerade as a live model run.

### PRD-017 — Failure visibility (MUST)
Model, parsing, and processing failures must be visible and cannot become PASS.

### PRD-018 — Audit events (MUST)
Record case decision, evidence inspection, repair/override actions and processing failures.

### PRD-019 — Tamper-evident audit chain (SHOULD)
Add only after core loop is stable. Describe accurately as tamper-evident.

### PRD-020 — Optional semantic pair classifier/NLI (COULD)
Evaluate only as an ablation for conflicts between two unstructured statements. Not required for core demo.

### PRD-021 — Offline AI/ML evidence lab (SHOULD)
The product exposes a clearly separated experimental lab that demonstrates:
- a locally trained, versioned semantic claim classifier;
- DEV-only grouped evaluation against the regex baseline;
- exact-quote grounding and interpretable feature contributions;
- bounded retrieval-augmented guidance over an allowlisted local corpus with exact citations.

The lab makes no external model/API call, never reads the frozen holdout during development, never returns PASS/REVIEW/BLOCK, and has no authority over the selected gate path. If the candidate model does not beat the simpler baseline on the predeclared DEV protocol, the UI must say that it was **not promoted**.

### PRD-022 — Interactive verifier sandbox (MUST)
The default demo entry lets a user supply synthetic refund communication and trusted ledger
state, then invokes the real local extraction, grounding, verification, and decision path. The
result exposes the exact extracted quote/span, normalized structured values, rule finding, and
PASS/REVIEW/BLOCK state. The sandbox is bounded, ephemeral, visibly synthetic, and performs no
external request, persistence, holdout access, or Razorpay write. Raw `reason_code` is preserved
verbatim and never mapped to a card-network code by assumption. Incomplete or unsupported state
must route to REVIEW. Preset cases execute directly rather than only populating fields. Every run
shows an observable staged trace and brings the output into view on stacked layouts. Any deliberate
UI pacing must be disclosed as presentation and must not be reported as model or network latency.
The default surface is an evidence debugger rather than a dashboard: it provides deliberate wrong-
amount, incomplete-ledger, contradictory-communication, prompt-injection, malformed-input, and
extractor-outage cases. Every finding links to the exact communication and/or ledger evidence that
caused it. A user can attach repaired ledger evidence and see the deterministic decision change in
a before/repair/after diff. Semantic extraction and deterministic truth checks remain visually
distinct; no confidence score or autonomous financial action is shown.

### PRD-023 — Empirically justified semantic intelligence (MUST)

Every learned semantic component must be treated as a falsifiable research hypothesis. The project
must compare strong rules, sentence-level statistical learning, contextual embeddings, and—where
data and compute justify them—NLI, constrained generation, or lightweight fine-tuning. Experiments
must use grouped splits, exact-source outputs, calibration and selective-risk analysis, OOD and
robustness slices, latency/footprint measurements, saved per-example predictions, and predeclared
promotion gates. A model that does not deliver measurable safety-preserving lift remains research-
only or is removed. Financial reconciliation and final gate authority remain deterministic.

## Non-functional requirements

### PRD-NFR-001 Reproducibility
Fresh clone + documented commands must seed, run tests, start backend/frontend, and replay demo.

### PRD-NFR-002 Webhook timing
Successful durable consume returns a 2xx response within Razorpay's documented 5-second timeout. Do not impose an unmeasured 15ms target.

### PRD-NFR-003 Data correctness
Money represented as integer minor units; timestamps normalized to UTC internally.

### PRD-NFR-004 Accessibility
Target WCAG 2.2 AA patterns; no state indicated by color alone; keyboard-accessible core workflow.

### PRD-NFR-005 Security
No secrets/model tools in untrusted semantic path; parameterized SQL; safe logging.

## MoSCoW

### MUST
- webhook verification/idempotency;
- durable ingest/job state;
- deterministic refund verification;
- grounded claim extraction;
- cross-source verifier;
- PASS/REVIEW/BLOCK;
- queue/workspace/evidence highlighting;
- structured override;
- synthetic benchmark/evaluation;
- offline demo;
- failure recovery/tests.
- interactive user input through the local verifier path.

### SHOULD
- hash-chained audit events;
- baseline-ablation UI;
- offline AI/ML evidence lab with citation-only local retrieval;
- simple evidence repair/import;
- formative usability test.

### COULD
- dedicated NLI classifier;
- live Razorpay Test Mode read API;
- PDF text normalization if scope later demands.

### WON'T
- contest/accept API writes;
- letter generation;
- win probability;
- multi-reason-code production coverage;
- OCR;
- chat/copilot;
- agentic web/search;
- authoritative or open-ended RAG/vector DB;
- enterprise auth stack.

## Three golden scenarios

### PASS — refund evidence consistent
Communication: “Your ₹2,500 refund was processed; reference RF-101.”  
Ledger: processed refund ₹2,500 INR linked to same payment/reference.  
Result: PASS — no supported integrity issue.

### REVIEW — unable to verify safely
Communication references a refund, but quoted sentence cannot be grounded exactly or refund ledger export is incomplete.  
Result: REVIEW with explicit unresolved evidence reason.

### BLOCK — grounded processed-refund claim conflicts with ledger
Communication: “We processed a full refund of ₹2,500 on Aug 10.” Exact quote is grounded.  
Trusted fixture ledger: complete export, no matching refund; payment remains unrefunded.  
Result: BLOCK local hold with both evidence sources shown.

## Product success criteria
A judge can reproduce and understand the core advantage without trusting our prose:
- signed replay;
- exact grounded claim;
- deterministic conflict;
- safe fallback;
- held-out metrics.

# AGENTS.md — Engineering Constitution

This file governs every coding-agent action in this repository.

## 1. Truth hierarchy

Before changing code, read:
`docs/00-SOURCE-OF-TRUTH.md` → `docs/05-PRD.md` → `docs/06-SRS.md` → the subsystem spec → `docs/20-TRACEABILITY-MATRIX.md`.

Never invent Razorpay events, API routes, fields, reason-code rules, network requirements, benchmark results, legal conclusions, or production capabilities.

External facts must map to `docs/24-SOURCE-LEDGER.md`. If a needed fact is absent, record it as `VERIFY` in `docs/21-RISK-ASSUMPTIONS-DECISIONS.md`; do not silently guess.

## 2. Product boundaries

MVP is a **defensive, read-only pre-submission verifier** for the `refund_not_processed_v1` reason family.

No automatic `contest`, `accept`, refund, payment, or network write.
No representment-letter generator.
No win-probability score.
No fraud/offensive tooling.
No AI for money arithmetic, identifiers, timestamps, webhook authentication, state transitions, or final gate policy.

`PASS` means only “no supported integrity issue detected.”  
`BLOCK` means only “local evidence hold.”  
`REVIEW` is the mandatory fail-safe for uncertainty, missing evidence, unsupported input, ungrounded model output, or model outage.

## 3. AI contract

The default AI task is **typed claim extraction from unstructured text**.
The model must return schema-valid claims with exact source quotations/document IDs. Local code finds/verifies offsets.

Model output is untrusted data. It has:
- no tool access,
- no database credentials,
- no secrets,
- no authority to mutate state,
- no direct PASS/BLOCK authority.

Do not add NLI, agents, RAG, vector DBs, or another model stage unless an evaluation task proves measurable value over the simpler architecture.

Never treat model-generated confidence as calibrated probability.

## 4. Benchmark integrity

Never fabricate or hard-code evaluation numbers.
Never edit `data/benchmark/v1/holdout/` after its manifest is frozen.
If holdout content or labels must change, create a new benchmark version and invalidate prior results.

Every metric shown in the UI/README must be computed from saved prediction artifacts.

Synthetic performance must be labeled **synthetic benchmark performance**, never production win-rate impact.

## 5. Implementation loop

For every task:

1. identify requirement IDs;
2. inspect existing code/contracts/tests;
3. implement the smallest correct change;
4. run formatter/typecheck/lint;
5. run targeted tests;
6. run relevant integration/property/security tests;
7. if behavior affects evaluation, run dev-set regression only;
8. inspect failures and fix root cause;
9. add a regression test for any discovered bug;
10. update `TASKS.md` and traceability only after evidence passes.

Never mark work complete because code compiles.

## 6. Failure rules

Degraded semantics may never silently PASS.

- model timeout/schema failure/ungrounded span → REVIEW
- unsupported language/type → REVIEW
- missing suggested evidence → REVIEW
- webhook authentication failure → reject ingestion
- malformed trusted structured state → processing ERROR/REVIEW, not BLOCK
- grounded material conflict against trusted structured state → BLOCK

Do not use BLOCK as a generic error bucket.

## 7. Architecture discipline

Default stack: FastAPI + SQLite WAL + durable jobs table + React/TypeScript.
No Kafka, Redis, Celery, Kubernetes, microservices, vector database, or PDF/OCR stack unless a documented requirement and measured need justify it.

In-process work may be used only if durable job state survives restart.

## 8. Security language

Hashing proves content identity relative to a recorded digest, not authenticity.
Hash-chained logs are **tamper-evident under the documented threat model**, not immutable.
Regex is partial PII minimization, not full de-identification.
Do not claim PCI/GDPR/DPDP compliance.

## 9. UX discipline

Cognitive forcing is allowed only on consequential BLOCK override paths.
No arbitrary minimum-character justification rule.
Require the operator to inspect the cited conflict and choose a structured override reason.
Standard keyboard and accessibility semantics outrank clever shortcuts.

## 10. Honesty gate

Before README/demo/pitch changes, verify every numeric or capability claim against:
- an executable test,
- a saved evaluation artifact,
- or a primary source.

If evidence is missing, write `NOT YET MEASURED` or remove the claim.

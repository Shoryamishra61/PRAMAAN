# MUST requirement coverage

Verified on 2026-08-23. Every mandatory ID below maps to an evidence-complete P0 task and a passing test surface. Optional `PRD-019` / `SRS-023` hash chaining, `PRD-020` / `AI-010` NLI, and P1 integrations are deliberately excluded and disclosed as unimplemented.

Final command: `powershell -ExecutionPolicy Bypass -File scripts/check.ps1`.

Observed result: Ruff format/check, strict mypy, package/spec/schema validation, the static Razorpay no-write guard, 178 backend tests, frontend format/lint/production build, and 11 frontend tests passed. The command did not load or evaluate the frozen HOLDOUT.

| Mandatory requirements | Evidence-complete tasks | Passing acceptance surfaces |
|---|---|---|
| `PRD-001` | T007, T008, T010 | `test_security.py`, `test_ingestion.py`, `test_webhook_replay.py` |
| `PRD-002` | T002 | `test_database.py`, `test_ingestion.py` |
| `PRD-003` | T003, T004 | `test_profile.py`, `test_demo_fixtures.py` |
| `PRD-004` | T005 | `test_verification.py` unit/property tests |
| `PRD-005` | T011, T012 | `test_extraction.py`, `test_grounding.py` |
| `PRD-006` | T005, T015 | `test_verification.py`, `test_case_pipeline.py` |
| `PRD-007` | T003, T006 | `test_decision.py`, demo fixture tests |
| `PRD-008` | T004 | profile missing-evidence tests |
| `PRD-009`, `PRD-010` | T020 | `test_case_api.py`, `App.test.tsx` |
| `PRD-011` | T012, T021 | grounding tests and source-focus frontend test |
| `PRD-012` | T023, T027 | case-action integration, override UI, no-write guard |
| `PRD-013` | T013, T022 | semantic failure and local reprocess tests |
| `PRD-014` | T014, T018, T019, T024, T029, T030, T032 | evaluator/metrics/artifact/API/dashboard/talk-track tests |
| `PRD-015` | T016, T017, T019, T029 | benchmark generator/integrity/evaluator tests |
| `PRD-016` | T025, T030 | offline replay parity/miss/schema tests and visible UI badge |
| `PRD-017` | T009, T013, T031, T032 | job recovery, semantic failures, executable injected outage |
| `PRD-018` | T023 | inspection/override/mark-ready audit integration |
| `PRD-022` | T110 | sandbox API three-state/validation tests, frontend POST interaction, live browser replay |
| `PRD-NFR-001` | T001, T028, T032 | isolated clean-source setup/full-gate/rehearsal reproduction |
| `PRD-NFR-002` | T010 | durable webhook ACK p95 contract under five seconds |
| `PRD-NFR-003` | T028 | minor-unit, currency, UTC, and property tests |
| `PRD-NFR-004` | T028 | status text, source focus, modal focus trap/Escape/restore tests plus live keyboard path |
| `PRD-NFR-005` | T007, T026 | HMAC, schema, injection, logging, SQL, health, and secret-boundary tests |
| `SRS-001` | T001 | configuration tests and placeholder-only `.env.example` |
| `SRS-002`–`SRS-005` | T002, T007, T008, T010 | raw webhook, signature, event, adapter, forward-compatible parsing tests |
| `SRS-006`, `SRS-007` | T011 | exact text/JSON MIME allowlist and strict bounded extractor tests |
| `SRS-008` | T012, T021 | exact/ambiguous/missing quote and UI source-focus tests |
| `SRS-009`–`SRS-012` | T002, T005, T006, T015 | financial/time/domain/verifier/policy tests |
| `SRS-013` | T027 | static route/import/host/client no-write guard and integration assertions |
| `SRS-014`, `SRS-015` | T023 | local mark-ready and inspection-gated structured override tests |
| `SRS-016`, `SRS-017` | T009, T010, T013 | durable job restart and bounded retry/failure-routing tests |
| `SRS-018`–`SRS-020` | T016–T019, T024, T025, T029 | split guard, freeze, artifact, dashboard, offline cache tests |
| `SRS-021`, `SRS-022` | T023, T026, T031 | safe structured log and append-only application-action tests |
| `SRS-024` | T026 | truthful health endpoint tests |
| `SRS-027` | T110 | ephemeral request schema, exact money, grounding, side-effect, and three-state tests |
| `AI-001`–`AI-003` | T011 | provider-neutral protocol, closed output, adversarial bounded interface |
| `AI-004`, `AI-005` | T012 | exact grounding and deterministic semantic normalization |
| `AI-006` | T011, T025 | provider-neutral protocol and offline replay parity |
| `AI-007` | T013 | timeout/schema/grounding failure routes and bounded retries |
| `AI-008` | T025 | cache v2 text/config/prompt/schema key-binding tests |
| `AI-009` | T026 | prompt-injection containment tests |
| `AI-011` | T013 | no model self-confidence; deterministic REVIEW routing |
| `AI-012`, `AI-013` | T014, T019 | regex baseline and shared case-level metric protocol |
| `AI-014` | T026 | no raw evidence/secret/prompt logging tests |
| `POL-001`–`POL-003` | T003, T004, T005 | scope and incomplete-source policy tests |
| `POL-004`–`POL-012` | T005, T015 | grounding eligibility and every deterministic conflict/promise/policy rule test |
| `API-001` | T007, T008 | inbound webhook contract tests |
| `API-002`, `API-003` | T020 | queue/detail contract, filtering, pagination, parameterization tests |
| `API-004` | T022 | local reprocess/idempotency tests |
| `API-005`–`API-007` | T023 | inspect/override/mark-ready contracts and failure preconditions |
| `API-008` | T024 | digest-verified artifact-only evaluation projection tests |
| `API-009` | T026 | safe truthful health projection tests |
| `API-010` | T107 | bounded local AI-lab model/retrieval projection tests |
| `API-011` | T110 | interactive sandbox contract and browser-backed input/output tests |

Judge-visible golden-path evidence is in T028–T032 and `RELEASE-GATES.md`. Task-level requirement IDs and commands remain in `artifacts/verification/T001.md` through `T032.md`.

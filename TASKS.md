# TASKS — Initial Build Queue

Status: `[ ]` pending, `[~]` in progress, `[x]` evidence-complete, `[!]` blocked.

Every task references only requirement IDs that are actually defined in the canonical specs. Do not invent new IDs in this file without first defining them in the appropriate specification and traceability matrix.

## P0 — Must ship
- [x] **T001** Initialize backend/frontend/test structure and config. REQ: `SRS-001`, `PRD-NFR-001`. EVIDENCE: `artifacts/verification/T001.md`.
- [x] **T002** Implement SQLite schema, foreign keys, indexes, and migration/init path. REQ: `PRD-002`, `SRS-005`, `SRS-009`, `SRS-010`, `SRS-016`. EVIDENCE: `artifacts/verification/T002.md`.
- [x] **T003** Seed deterministic PASS/REVIEW/BLOCK smoke fixtures for `refund_not_processed_v1`. REQ: `PRD-003`, `PRD-007`, `POL-001`. EVIDENCE: `artifacts/verification/T003.md`.
- [x] **T004** Implement reason profile and suggested-evidence metadata. REQ: `PRD-003`, `PRD-008`, `POL-001`, `POL-003`. EVIDENCE: `artifacts/verification/T004.md`.
- [x] **T005** Implement deterministic structured-state and refund conflict rules. REQ: `PRD-004`, `PRD-006`, `SRS-011`, `POL-002`, `POL-005`, `POL-006`, `POL-007`, `POL-008`, `POL-009`, `POL-010`, `POL-011`, `POL-012`. EVIDENCE: `artifacts/verification/T005.md`.
- [x] **T006** Implement decision schema and PASS/REVIEW/BLOCK precedence. REQ: `PRD-007`, `SRS-012`. EVIDENCE: `artifacts/verification/T006.md`.
- [x] **T007** Implement raw-body Razorpay webhook HMAC verifier. REQ: `PRD-001`, `SRS-002`, `PRD-NFR-005`, `API-001`. EVIDENCE: `artifacts/verification/T007.md`.
- [x] **T008** Implement documented event filtering + `x-razorpay-event-id` idempotency. REQ: `PRD-001`, `SRS-003`, `SRS-004`, `API-001`. EVIDENCE: `artifacts/verification/T008.md`.
- [x] **T009** Implement durable jobs table/worker recovery. REQ: `SRS-016`, `SRS-017`, `PRD-017`. EVIDENCE: `artifacts/verification/T009.md`.
- [x] **T010** Implement webhook replay, duplicate, raw-body mutation, and restart tests. REQ: `PRD-001`, `PRD-NFR-002`, `SRS-002`, `SRS-016`. EVIDENCE: `artifacts/verification/T010.md`.
- [x] **T011** Implement semantic extractor protocol + strict schema. REQ: `PRD-005`, `SRS-006`, `SRS-007`, `AI-001`, `AI-002`, `AI-003`, `AI-006`. EVIDENCE: `artifacts/verification/T011.md`.
- [x] **T012** Implement exact-quote grounding/span resolver and deterministic value normalization. REQ: `PRD-005`, `PRD-011`, `SRS-008`, `AI-004`, `AI-005`. EVIDENCE: `artifacts/verification/T012.md`.
- [x] **T013** Implement provider/schema/grounding failure → REVIEW behavior and bounded retries. REQ: `PRD-013`, `PRD-017`, `SRS-017`, `AI-007`, `AI-011`. EVIDENCE: `artifacts/verification/T013.md`.
- [x] **T014** Implement strong regex/keyword semantic-extraction baseline with the same resolver. REQ: `PRD-014`, `AI-012`, `AI-013`. EVIDENCE: `artifacts/verification/T014.md`.
- [x] **T015** Integrate grounded claims with deterministic refund conflict rules end-to-end. REQ: `PRD-006`, `SRS-011`, `POL-004`, `POL-005`, `POL-006`, `POL-010`, `POL-011`. EVIDENCE: `artifacts/verification/T015.md`.
- [x] **T016** Implement synthetic benchmark generator with unseen-family DEV/HOLDOUT split and hard negatives. REQ: `PRD-015`, `SRS-018`. EVIDENCE: `artifacts/verification/T016.md`.
- [x] **T017** Freeze benchmark v1 manifest/hashes and guard holdout access. REQ: `PRD-015`, `SRS-018`. EVIDENCE: `artifacts/verification/T017.md`.
- [x] **T018** Implement per-case prediction/result artifact writer with config/commit/dataset provenance. REQ: `PRD-014`, `SRS-019`. EVIDENCE: `artifacts/verification/T018.md`.
- [x] **T019** Implement precision/recall/F1, counts, operational rates, baseline delta, and parameterized cost sensitivity. REQ: `PRD-014`, `PRD-015`, `AI-013`, `SRS-019`. EVIDENCE: `artifacts/verification/T019.md`.
- [x] **T020** Implement queue and case workspace backed by local APIs. REQ: `PRD-009`, `PRD-010`, `API-002`, `API-003`. EVIDENCE: `artifacts/verification/T020.md`.
- [x] **T021** Implement evidence quote highlight/source navigation. REQ: `PRD-011`, `SRS-008`. EVIDENCE: `artifacts/verification/T021.md`.
- [x] **T022** Implement REVIEW reasons and recovery/reprocess actions. REQ: `PRD-013`, `API-004`. EVIDENCE: `artifacts/verification/T022.md`.
- [x] **T023** Implement BLOCK local hold, evidence inspection acknowledgements, structured override, and local mark-ready flow. REQ: `PRD-012`, `PRD-018`, `SRS-014`, `SRS-015`, `SRS-022`, `API-005`, `API-006`, `API-007`. EVIDENCE: `artifacts/verification/T023.md`.
- [x] **T024** Implement evaluation page that reads saved result artifacts only. REQ: `PRD-014`, `SRS-019`, `API-008`. EVIDENCE: `artifacts/verification/T024.md`.
- [x] **T025** Implement offline replay adapter with visible mode badge and same grounding/policy path. REQ: `PRD-016`, `SRS-020`, `AI-006`, `AI-008`. EVIDENCE: `artifacts/verification/T025.md`.
- [x] **T026** Add security/logging/failure tests and health endpoint. REQ: `PRD-NFR-005`, `SRS-021`, `SRS-024`, `AI-009`, `AI-014`, `API-009`. EVIDENCE: `artifacts/verification/T026.md`.
- [x] **T027** Prove no Razorpay write client/code path exists in MVP. REQ: `SRS-013`, `PRD-012`. EVIDENCE: `artifacts/verification/T027.md`.
- [x] **T028** Fresh-clone runbook, one-command seeded demo, typecheck/lint/test scripts. REQ: `PRD-NFR-001`, `PRD-NFR-003`, `PRD-NFR-004`. EVIDENCE: `artifacts/verification/T028.md`.
- [x] **T029** Freeze code/prompt/schema/model config and run final HOLDOUT evaluation per protocol. REQ: `PRD-014`, `PRD-015`, `SRS-018`, `SRS-019`. EVIDENCE: `artifacts/verification/T029.md`.
- [x] **T030** Generate README/dashboard metrics strictly from final artifact and complete mocked-vs-working disclosures. REQ: `PRD-014`, `PRD-016`, `SRS-019`. EVIDENCE: `artifacts/verification/T030.md`.
- [x] **T031** Write `FAILURE-NARRATIVE.md` only from a genuine build defect or clearly labeled fault injection. REQ: `PRD-017`, `SRS-021`. EVIDENCE: `artifacts/verification/T031.md`.
- [x] **T032** Rehearse 2-minute golden demo + 5-minute video with current measured values only. REQ: `PRD-014`, `PRD-017`, `PRD-NFR-001`. EVIDENCE: `artifacts/verification/T032.md`.
- [x] **T110** Implement the default interactive synthetic-input verifier using the real offline extraction, grounding, deterministic policy, and PASS/REVIEW/BLOCK path. REQ: `PRD-005`, `PRD-006`, `PRD-007`, `PRD-016`, `PRD-022`, `PRD-NFR-003`, `PRD-NFR-004`, `SRS-008`, `SRS-009`, `SRS-011`, `SRS-012`, `SRS-013`, `SRS-027`, `AI-001`, `AI-002`, `AI-003`, `AI-004`, `AI-005`, `POL-005`, `POL-006`, `API-011`. EVIDENCE: `artifacts/verification/T110.md`.
- [x] **T111** Make preset cases execute directly and expose an honest, responsive staged processing experience without fabricating model latency. REQ: `PRD-022`, `PRD-NFR-004`, `SRS-027`, `API-011`. EVIDENCE: `artifacts/verification/T111.md`.
- [x] **T112** Replace the proof dashboard with an interactive evidence debugger covering six safe break modes, exact-source findings, explicit semantic/deterministic boundaries, user-driven evidence repair, live decision diff, and artifact-only evaluation. REQ: `PRD-022`, `PRD-NFR-003`, `PRD-NFR-004`, `SRS-027`, `API-011`. EVIDENCE: `artifacts/verification/T112.md`.
- [x] **T113** Execute the pre-registered semantic research study: repair train/serve granularity, compare rules/TF-IDF/contextual embeddings/NLI where feasible, evaluate calibration/selective risk/OOD/robustness/latency, preserve exact grounding and deterministic authority, and publish only generated results. REQ: `PRD-023`, `SRS-028`, `AI-017`, `AI-018`, `AI-019`, `AI-020`. EVIDENCE: `artifacts/verification/T113.md`.
- [x] **T114** Execute and freeze the FECL-v2 relational model tournament, bind artifact-backed `/ai` inspection to the once-opened synthetic test result, and compile an auditable research manuscript with generated tables, figures, cards, limitations, and reproducibility evidence. REQ: `PRD-023`, `SRS-028`, `AI-017`, `AI-018`, `AI-019`, `AI-020`. EVIDENCE: `artifacts/verification/T114.md`.
- [x] **T115** Convert the evidence debugger into a live CARVE research instrument with local JSON/TXT import, downloadable normal/contradiction/missing/Hinglish/OOD/adversarial bundles, compiled proof constraints, completeness-based uncertainty, minimum-cost evidence acquisition, authority comparison, formal certificate digest, and safe unsupported-input abstention. REQ: `PRD-022`, `PRD-023`, `PRD-NFR-004`, `PRD-NFR-005`, `SRS-027`, `SRS-028`, `AI-003`. EVIDENCE: `artifacts/verification/T115.md`.
- [x] **T116** Replace the dense evidence dashboard with a beginner-friendly four-step walkthrough, explicit run control, measured local elapsed time, plain-language findings, progressive mechanics disclosure, and technical details isolated from the primary journey. REQ: `PRD-022`, `PRD-NFR-003`, `PRD-NFR-004`, `SRS-027`, `AI-015`. EVIDENCE: `artifacts/verification/T116.md`.
- [x] **T117** Make the research authority inspectable with generated split counts, a frozen model comparison, retained and rejected results, a model-authority ladder, and fail-closed evidence-integrity, OCR-corruption, and model-outage injections. REQ: `PRD-017`, `PRD-023`, `PRD-NFR-005`, `SRS-028`, `AI-015`. EVIDENCE: `artifacts/verification/T117.md`.
- [x] **T118** Complete the production-readiness audit: fail-fast quality gates, archived benchmark-debt accounting, non-blocking API execution, bounded webhook/import inputs, shared request and formatting boundaries, coherent design tokens, URL-backed navigation, accessibility metadata, dependency audit, and full regression. REQ: `PRD-NFR-001`, `PRD-NFR-004`, `PRD-NFR-005`, `SRS-002`, `SRS-027`, `SRS-028`. EVIDENCE: `artifacts/verification/T118.md`.

## P1 — Only after P0 green
- [ ] **T101** Evaluate dedicated NLI/cross-encoder as a DEV-set ablation; retain only if it materially improves a predeclared metric without unacceptable false holds. REQ: `PRD-020`, `AI-010`.
- [ ] **T102** Optional tamper-evident audit hash chain + verifier. REQ: `PRD-019`, `SRS-023`.
- [ ] **T103** Optional formative human-factors comparison of warning-only vs evidence-inspection override. REQ: `PRD-012`, `PRD-NFR-004`.
- [ ] **T104** Optional Razorpay Test Mode read/fetch integration if documentation/keys support it; no write path. REQ: `SRS-013`.
- [ ] **T105** Optional normalized PDF-text ingestion only through a new ADR/benchmark version if judge-critical. REQ: `PRD-NFR-005`.
- [x] **T106** Train a reproducible local TF-IDF/logistic semantic candidate on DEV with scenario-family-grouped out-of-fold evaluation, exact-quote nominations, signed feature contributions, and a predeclared promotion rule. REQ: `PRD-021`, `SRS-025`, `AI-015`. EVIDENCE: `artifacts/verification/T106.md`.
- [x] **T107** Implement bounded local retrieval over an allowlisted, exact-citation corpus with no network, vector service, generation, or gate authority. REQ: `PRD-021`, `SRS-026`, `AI-016`, `API-010`. EVIDENCE: `artifacts/verification/T107.md`.
- [x] **T108** Replace the dashboard-first entry with the approved responsive landing page, four-step guided case, and artifact-backed offline AI lab. REQ: `PRD-009`, `PRD-011`, `PRD-021`, `API-010`. EVIDENCE: `artifacts/verification/T108.md`.
- [x] **T109** Replace the rejected landing/tutorial paradigm with a judge-facing proof console integrating the canonical case trace, bounded AI/ML governance, saved HOLDOUT confusion/cost evidence, code-aligned architecture, recorded REVIEW failure recovery, and analyst handoff. REQ: `PRD-009`, `PRD-011`, `PRD-014`, `PRD-017`, `PRD-021`, `SRS-019`, `SRS-021`, `SRS-025`, `SRS-026`, `AI-015`, `AI-016`. EVIDENCE: `artifacts/verification/T109.md`.

## Explicitly out of scope
- Razorpay contest/accept/refund/payment writes
- auto-generated representment letters
- win-probability prediction
- multi-agent orchestration
- vector database or authoritative/open-ended RAG
- Kafka/Redis/Celery/Kubernetes
- OCR/scanned-image support in MVP
- broad multi-reason-code coverage


## Current hardening follow-up — 2026-09-05

Earlier checked tasks are historical implementation records, not current release certification.

- [x] Centralize bounded multi-file ingestion; preserve source offsets and malformed-file recovery; prevent narrative text from establishing financial state.
- [x] Remove fabricated certificates, timed processing phases, and typed-in quant-risk projections; preserve artifact-backed research and honest abstention.
- [x] Fix decimal source segmentation and aggregate-refund matching using DEV failures and regression tests; retain the weaker trained model as unpromoted.
- [x] Simplify light-mode surfaces and make tour guidance follow actual input errors and case stages; prevent edits during parsing/evaluation.
- [ ] Complete rendered desktop/mobile, keyboard, contrast, loading/error/retry, and full tour walkthrough checks. No browser surface was available on this run.
- [ ] Establish new independent held-out/external evidence before making claims about the repaired runtime's generalization or merchant-loss savings.

Evidence: `artifacts/verification/RELEASE-GATES.md` and `artifacts/verification/dev-hardening-20260905/README.md`.

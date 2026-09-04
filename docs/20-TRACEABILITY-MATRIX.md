# 20 — Requirement Traceability Matrix

| Requirement | Failure eliminated | Evidence/source | Component | Test | Demo proof |
|---|---|---|---|---|---|
| PRD-001 | spoofed/duplicate dispute ingest | SRC-RZP-02/03 | webhook ingest | signature + duplicate + out-of-order tests | signed replay |
| PRD-002 | inconsistent raw payloads leak into domain logic | engineering contract | adapter/schema | schema/normalization tests | normalized case metadata |
| PRD-003 | reason-code scope drifts or conflates 13.6/13.7 | SRC-RZP-06, SRC-VISA-01 | reason profile | profile fixture tests | scope badge + README |
| PRD-004 | financial mismatch/model math | system safety | structured verifier | property/unit tests | ledger comparison |
| PRD-005 | unstructured refund claims hidden | AI hypothesis | extractor/grounder | extraction benchmark | click grounded quote |
| PRD-006 | evidence says processed, ledger disagrees | product thesis | resolver | golden/BLOCK cases | side-by-side material conflict |
| PRD-007 | unsafe forced decisions | HCI/AI safety | decision policy | state/precedence tests | PASS/REVIEW/BLOCK |
| PRD-008 | evidence gaps falsely treated clean | SRC-RZP-06 | profile/policy | missing-evidence tests | REVIEW reason |
| PRD-009 | analyst misses urgent/unresolved cases | workflow hypothesis | queue API/UI | sorting/filter tests | triage queue |
| PRD-010 | analyst cannot inspect case coherently | HCI/product need | case workspace | E2E rendering tests | case workspace |
| PRD-011 | black-box AI finding | SRC-HCI-03 | evidence viewer | source-focus/grounding tests | highlighted quote |
| PRD-012 | analyst bypasses material conflict without inspection | SRC-HCI-01 | local hold UI | override precondition test | evidence-directed BLOCK override |
| PRD-013 | REVIEW becomes a dead-end | recovery requirement | review panel/workflow | reason-specific recovery tests | explicit recovery action |
| PRD-014 | unsupported performance claims | SRC-RZP-01 | evaluation engine/UI + proof console | artifact provenance and proof-console interaction tests | held-out proof chapter + artifact-backed cost controls |
| PRD-015 | no held-out evidence | SRC-RZP-01 | benchmark | split/manifest/hash tests | dataset card |
| PRD-016 | demo depends on external model availability | reliability | offline adapter | parity/schema tests | OFFLINE REPLAY badge |
| PRD-017 | model/parser outage silently passes | safety | worker/policy + proof console | failure-injection and recorded-recovery interaction tests | REVIEW failure chapter |
| PRD-018 | untraceable operator/system actions | HCI/security | audit events | integration tests | audit timeline |
| PRD-019 | undetected local audit-row mutation | security SHOULD | optional hash chain | chain-tamper test | integrity check if built |
| PRD-020 | optional NLI complexity added without evidence | AI judgment | experiment harness | dev ablation | only shown if retained |
| PRD-021 | hackathon AI claims are decorative or unverifiable | user requirement + AI boundary | offline AI lab + integrated proof-console model boundary | grouped DEV model/retrieval and proof-console interaction tests | selected B0, rejected challenger, signed n-grams, and exact citations |
| PRD-022 | demo has no user-controlled causal product loop or safe failure proof | direct user acceptance feedback + defense boundary | ephemeral sandbox API + four-step guided evidence walkthrough + proof compiler + repair diff | break-case and sample-bundle backend tests + explicit-run/progressive-navigation frontend tests + import/download/build | add evidence, explicitly run, inspect grounded claim, compare authoritative state, observe PASS/REVIEW/BLOCK, acquire or repair evidence, compare decision diff |
| PRD-023 | learned semantics become decorative, uncalibrated, or unjustifiably complex | AI research protocol + primary ML literature | versioned study harness + artifact-backed research lab with split counts, frozen model table, negative results, and authority ladder | grouped split, calibration, OOD, grounding, promotion, artifact-row-count, and reproducibility tests | inspect hypothesis, frozen metrics, observed failure, retained/rejected outcome, and permitted authority |
| PRD-NFR-001 | judge cannot reproduce system/results or a failed check reports green | Buildathon build-quality signal | runbook + fail-fast master check | fresh-clone smoke test + native exit-code propagation | one-command setup and check |
| PRD-NFR-002 | webhook delivery retries due to slow ACK | SRC-RZP-03 | ingestion path | measured p95 + <5s contract test | ingest diagnostics |
| PRD-NFR-003 | financial/time representation drift | engineering correctness | domain/storage | property + timezone tests | structured trace |
| PRD-NFR-004 | critical workflow inaccessible by keyboard/AT | SRC-HCI-02 + WCAG target | shared design tokens, skip links, labelled bounded forms, live errors, focus handling, responsive frontend | keyboard/semantic interaction tests + blocked browser audit record | keyboard demo plus named visual-QA limit |
| PRD-NFR-005 | untrusted evidence/model output changes authority | SRC-OWASP-01/02 | security boundaries | adversarial/security tests | safe REVIEW/injection fixture |
| SRS-002 | webhook attack/replay or oversized body exhausts service | SRC-RZP-02/03 + trust-boundary engineering | HMAC API, 1 MB body cap, transactional deduplication | signature, oversized-body, duplicate, and atomic-ingest tests | rejected unsafe input plus accepted signed replay |
| SRS-006 | unsupported evidence type enters semantic boundary | evidence contract | extractor request | exact text/JSON allowlist test | disclosed MIME boundary |
| SRS-008 | hallucinated/ambiguous source offsets | grounding principle | grounder | exact/repeated quote tests | source jump |
| SRS-013 | accidental automated dispute write | Track02 defense-only | architecture | static/integration guard | working-vs-not-built disclosure |
| SRS-016 | acknowledged work lost on crash | reliability | durable jobs worker | restart/recovery test | fault demo |
| AI-003 | indirect prompt injection | SRC-OWASP-01 | extractor | adversarial test | injection fixture |
| AI-008 | cached output reused across prompt/config versions | AI boundary | offline cache v2 | text/config/prompt/schema key test | versioned offline badge |
| AI-010 | unnecessary NLI stage | AI judgment | optional experiment | dev-set ablation | only if proven |
| AI-015 | local model becomes an opaque or authoritative gate | bounded ML contract | semantic classifier lab | grouped evaluation + exact-quote + no-authority tests | candidate model card |
| AI-016 | retrieval invents rules or silently changes policy | source ledger + bounded retrieval contract | local citation retriever | corpus allowlist/citation/no-network tests | retrieved guidance with citations |
| SRS-025 | model result is tuned on frozen holdout or unreproducible | benchmark integrity | local training harness | holdout-denial + artifact-digest tests | DEV ablation artifact |
| SRS-026 | open-ended RAG leaks unsupported policy into decisions | deterministic authority boundary | local retriever | allowlist + mutation-boundary tests | advisory retrieval panel |
| SRS-027 | custom demo input bypasses money, grounding, policy, or no-write boundaries | deterministic trust boundary | sandbox request schema + existing evaluator | exact money/schema/side-effect/three-state API tests | local input → grounded output |
| SRS-028 | semantic experiments leak holdout, mismatch train/serve granularity, or cannot be reproduced | AI research protocol | research dataset/runner/artifact schemas | holdout refusal, group isolation, hash, metric, and exact-quote tests | generated research artifact with per-candidate evidence |
| POL-005 | grounded processed-refund claim has no complete-ledger match | reason profile | rule engine | BLOCK scenario family | main demo |
| UX-BLOCK | automation overreliance at consequential override | SRC-HCI-01 | UI | interaction/user test | inspect + structured override |
| EVAL-HOLDOUT | prompt/rule tuning leakage | Track02 held-out bar | benchmark runner | manifest guard | results metadata |

## Rule
No MUST feature enters implementation without a row mapping:
`failure → requirement → implementation → test → judge-visible evidence`.

When implementation creates a new requirement, update this matrix before marking the task complete.

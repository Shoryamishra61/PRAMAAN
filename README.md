# PRAMAAN: AI Risk Manager & Dispute Integrity Gate

Razorpay AI Buildathon 2026 · Track 02 · Powered by CARVE-FECL Engine

**PRAMAAN** is a defensive, read-only pre-submission integrity gate for merchant chargeback loss
prevention. It extracts bounded, source-grounded claims from customer communication, reconciles
them against trusted payment and refund records with deterministic integer minor-unit rules, and
returns PASS (CONTEST_READY), REVIEW (REVIEW_REQUIRED), or BLOCK
(INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE) before a human decides the local next step. **CARVE-FECL**
is the research engine that evaluates learned candidates, calibration, and bounded Z3
cross-checks; it has no payment or product-decision authority.

It does not generate chargeback letters, predict dispute wins, issue a legal verdict, or call Razorpay accept, contest, refund, or payment write endpoints.

## Research question

Can grounded semantic extraction plus deterministic cross-source verification detect material refund-evidence conflicts while safely abstaining when inputs are incomplete or unsupported?

This offline build answers only for frozen, family-separated synthetic diagnostic benchmarks. A
generated model tournament compares rules, TF-IDF, frozen MiniLM embeddings, ensembles, XGBoost,
hard-negative weighting, calibration/conformal/OOD methods, and a pinned NLI cross-encoder. No
learned extractor cleared the pre-registered deployment gate; the required B0 regex extractor
remains selected. The project does not claim production prevalence, issuer outcomes, real merchant
savings, or model-backed production improvement.

The FECL-v2 extension evaluates financial evidence/state consistency on 640 training cases, a
256-case development split, a once-opened 384-case family-shifted synthetic holdout, and 40 OOD
cases. Its neuro-symbolic research candidate improves frozen-test F1 over literal rules (0.713 vs
0.338) but still produces 68 false BLOCKs and is explicitly not deployed. Open `/ai` to inspect the
generated model tournament, counterfactual evidence pairs, calibration damage, OOD behavior, and
the unchanged deterministic runtime. The reproducible manuscript is in `paper/main.tex`; the
compiled artifact is `paper/dispute-integrity-gate-research.pdf`.

## Current hardening evidence (2026-09-05)

The saved August HOLDOUT result belongs to its frozen baseline; current runtime bytes differ.
It is not an evaluation of this working tree. No frozen HOLDOUT was rerun for these repairs.

On the 120 synthetic DEV cases, regression analysis found decimal amounts split at the period
and valid aggregate refunds falling through to a missing-ledger finding. Fixing both reduced
false BLOCKs from 10 to 0 (BLOCK precision 40/50 to 40/40; recall stayed 40/40). Forty cases
still abstain to REVIEW. These are development results used to repair the implementation,
not generalization evidence. Claim extraction is not perfect: refund-amount precision is 56/72.

Fresh family-grouped DEV training kept TF-IDF/logistic regression **NOT_PROMOTED**:
precision 0.814, recall 0.972, F1 0.886, below the regex comparator on that separate
communication-classification protocol. A weaker learned model does not gain decision authority.
See the [before/after artifacts and reproduction commands](artifacts/verification/dev-hardening-20260905/README.md)
and [current release receipt](artifacts/verification/RELEASE-GATES.md). Rendered UI validation
remains pending; automated component tests do not establish visual quality.

## 60-second local demo

Prerequisites: Windows PowerShell, Python 3.10+, and Node.js/npm.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
```

Open `http://127.0.0.1:5173`. Stop the recorded local processes with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-demo.ps1
```

The initial setup may need package-registry access and trains the reproducible DEV-only candidate. The running demo uses no external provider or model API. Full operational notes are in [RUNBOOK.md](RUNBOOK.md).

## What the demo proves

The one-command seed path:

1. signs exact Razorpay-compatible `payment.dispute.created` fixture bytes with a synthetic demo secret;
2. authenticates and durably ingests each event with `x-razorpay-event-id` idempotency;
3. replays a versioned precomputed-regex extraction result through the same exact-quote grounding path;
4. applies deterministic money, currency, identifier, evidence-completeness, and conflict rules;
5. opens on an interactive verifier where a user changes synthetic communication/refund-ledger input and receives the real grounded PASS/REVIEW/BLOCK API result;
6. integrates the DEV-only local ML challenger, promotion decision, and exact n-gram contributions beside the selected gate path;
7. exposes held-out confusion/cost evidence, code-aligned architecture, and recorded REVIEW failure recovery as adjacent proof chapters;
8. keeps every action local and exposes evaluation only from saved, digest-verified artifacts.

```text
signed inbound fixture
  → durable event/case/job
  → bounded regex/offline claim extraction
  → exact quote grounding + typed normalization
  → deterministic structured-state verifier
  → PASS / REVIEW / BLOCK
  → local analyst queue, inspection, override, and artifact-backed evaluation
```

PASS means no supported integrity problem was detected in the available evidence; it is not a chargeback-win prediction. REVIEW means the system abstained because evidence or extraction could not be verified safely. BLOCK is a local safety hold for a deterministically established material inconsistency; it is not a legal verdict.

## Working, synthetic, mocked, and future

| Boundary | Current status |
|---|---|
| Raw-body webhook HMAC, documented event parsing, event-ID deduplication, durable SQLite job creation | Working locally |
| Integer minor-unit/timezone normalization, exact grounding, deterministic verifier and gate policy | Working locally |
| Analyst queue, evidence focus, REVIEW recovery, BLOCK inspection/structured override, local mark-ready | Working locally |
| Structured safe logs, queue-derived health, restart/retry tests, no-write static guard | Working locally |
| Evaluation writer, sidecar verification, frozen split guard, artifact-only dashboard | Working locally |
| Interactive evidence debugger with six break modes, exact-source findings, deterministic reconciliation, live repair diff, and artifact-only evaluation | Working locally |
| Ephemeral custom-input verifier using the real regex extraction, exact grounding, deterministic rules, and three-state gate API | Working locally; synthetic input, no persistence/network/write |
| Generated model tournament, grouped ablations, calibration/conformal/OOD, TreeSHAP, NLI challenge, and per-example predictions | Working locally at `/ai`; learned extractors `NOT_PROMOTED`, no gate authority |
| Local TF-IDF retrieval over an allowlisted exact-citation corpus | Working locally as guidance only; no generated evidence or network call |
| Dispute events, payment/refund state, communications, expected labels | Synthetic fixtures; not real Razorpay or merchant data |
| Offline extraction cache | Precomputed from the regex fixture extractor and visibly labeled; not model output |
| Merchant refund/payment resolver | Mocked by versioned local JSON/SQLite snapshots |
| Razorpay read APIs and Test Mode account integration | Not implemented |
| Razorpay accept/contest/refund/payment writes | Deliberately not implemented; prohibited in MVP |
| Live LLM/provider adapter, generative RAG, and model-backed B1 promotion | Not implemented in the offline/regex submission |
| OCR/PDF, production auth/RBAC/multitenancy, real merchant validation | Future work only |

The configuration enum validates that a hypothetical live mode has a key, but there is no implemented live extractor. The fixed demo operator is a disclosed local-demo boundary, not production authorization.

## AI Research Lab — generated artifacts only

Open `http://127.0.0.1:5173/ai`. The lab switches the same exact evidence sentence among rules,
TF-IDF, MiniLM, a fixed ensemble, XGBoost, and hard-negative XGBoost. It renders generated
leaderboard, confusion, PR, calibration, risk–coverage, conformal/OOD, TreeSHAP, latency/size,
per-example failures, and NLI slices. Scores are explicitly model scores, not
customer confidence or financial truth.

Grouped DEV extraction results:

| Candidate | Precision | Recall | F1 | Decision |
|---|---:|---:|---:|---|
| Regex B0 | 0.9722 | 1.0000 | 0.9859 | selected |
| TF-IDF combined | 0.6400 | 0.6857 | 0.6621 | rejected |
| MiniLM embedding + logistic | 0.7273 | 0.9143 | 0.8101 | rejected |
| Fixed ensemble | 0.7273 | 0.9143 | 0.8101 | rejected |
| XGBoost stack | 0.9722 | 1.0000 | 0.9859 | rejected: no lift |
| XGBoost + hard negatives | 0.9722 | 1.0000 | 0.9859 | rejected: no lift |

On frozen holdout, TF-IDF and MiniLM improved extraction F1 to `0.8889` and `0.8421`, but precision
fell to `0.8000` and `0.7273`. A separately hashed post-hoc grounding audit found repeated-quote
ambiguity, 20 false PASS outcomes for both, and 5 false BLOCK outcomes for MiniLM. No threshold was
retuned and the frozen artifact was not rewritten. The NLI cross-encoder improved a 20-pair
synthetic contradiction challenge from F1 `0.5714` to `0.7500`, but remains `NOT_INTEGRATED` after
missing amount, reference, and temporal relations.

Full methodology, negative results, hashes, and commands are in
[`artifacts/research/ai-systems-study-v1.md`](artifacts/research/ai-systems-study-v1.md). The older
whole-document TF-IDF artifact remains historical evidence; it is not the current tournament.

## Saved synthetic HOLDOUT result (frozen 2026-08-23)

Source of every number below: `results/holdout-regex-v1-20260823-final.json`, exact-byte SHA-256 `15349fd24f2fbceb1c6a38edafee92d5953f22af2e9611efcda17ba20f1992b8`.

Dataset: `DIG-RNP-SYN-v1`, 60 frozen HOLDOUT cases, family-separated from 120 DEV cases, manifest SHA-256 `1c285947c38bd0623b56cfb156dcc2eb3157505e5b8fc8bca45c089158ab3681`. The class balance is diagnostic and is not production prevalence.

| Saved metric | Final synthetic value |
|---|---:|
| Material-conflict precision | 10/10 = 1.0000 |
| Material-conflict recall | 10/20 = 0.5000 |
| Material-conflict F1 | 0.6667 |
| True BLOCK predicted PASS | 10 cases |
| Non-BLOCK predicted BLOCK | 0 cases |
| REVIEW rate | 20/60 = 0.3333 |
| Automatic decision coverage | 40/60 = 0.6667 |
| Three-class macro-F1 | 0.8222 |
| Claim micro precision / recall / F1 | 20/40 = 0.5000 / 20/50 = 0.4000 / 0.4444 |
| Exact grounding among emitted grounded predictions | 40/40 = 1.0000 |
| Normalized-value accuracy among comparable matched claims | 20/20 = 1.0000 |

The key failure slice is `partial_full_amount`: all 10 cases were expected BLOCK but predicted PASS. This is a serious limitation of the selected regex-only semantic boundary, not a result to hide or tune after holdout.

The evaluated frozen system was B0: `regex-baseline-v1` plus the deterministic verifier. Because the user selected offline/regex-only operation, the saved comparator is the identical B0 protocol and all baseline deltas are exactly zero. No model-backed B1 result is claimed.

Saved local evaluation timing for this run was 1.2395 ms p50 / 1.5737 ms p95 per end-to-end case and 0.0604 ms p50 / 0.0943 ms p95 for regex extraction. These are measurements from this local synthetic run, not latency guarantees or provider measurements.

The artifact also computes three explicitly illustrative, unitless cost scenarios from 10 false PASS, 0 false BLOCK, and 20 REVIEW cases: 120, 160, and 340 illustrative cost units. They are sensitivity inputs, not INR, fees, savings, or ROI.

## Evaluation integrity

- The frozen holdout was not used during detector development.
- The default evaluator split is DEV.
- HOLDOUT requires `--confirm-frozen` and a verified release-freeze manifest.
- The final run was executed once after the complete pre-holdout gate passed.
- Detector/evaluator bundle SHA-256: `77e178b83e427fc4d5328cef1aa15582b5e22ae087088d258d17a7061a519996`.
- Extractor/config SHA-256: `24ce16ba08a8b4edcbb843aa9fc9720e8f1db70358ffba22430e6251344f45b1`.
- The historical artifact records `UNAVAILABLE_NOT_A_GIT_REPOSITORY`. The present checkout has Git metadata; its revision and uncommitted state are recorded in the release receipt.
- Current runtime hardening changed detector bytes after that freeze. These saved measurements are historical baseline evidence, not a fresh evaluation of the current revision. No test set was retuned or rewritten.
- The dashboard verifies the artifact sidecar and never computes client-side placeholder metrics.

## Failure behavior and security boundary

Missing evidence, unsupported input, malformed schema, cache/provider failure, or ungrounded/ambiguous quotes route to REVIEW. No generic technical failure becomes BLOCK or PASS. The semantic boundary has no tools, secrets, database access, or state authority. Its output schema rejects confidence, decision, status, offsets, and tool-call fields.

Logs accept only allowlisted IDs, hashes, versions, status, measured latency, and failure classes. They have no raw-evidence, prompt, credential, or raw-response field. SQL is parameterized. The browser accepts bounded UTF-8 JSON/TXT/CSV locally. A single ingestion path retains same-name files, isolates read/parse errors, preserves full communication with source offsets, and rejects oversized combined input without truncation. Only a schema-valid JSON request may populate financial fields; text and CSV never establish authoritative values or ledger completeness. Imported records are not authenticated.

The release guard parses backend imports, runtime endpoint strings, browser fetch targets, and the FastAPI route surface for prohibited Razorpay write clients and paths. This is a bounded static check, complemented by API tests, not a universal proof of runtime behavior.

## Reproducibility evidence

Current verification and its limitations are recorded in [the release receipt](artifacts/verification/RELEASE-GATES.md). Run `scripts/check.ps1` for formatting, lint, types, boundary checks, artifact validation, backend tests, and frontend tests/build. The ML smoke test executes real forward/loss/backward/optimizer steps and verifies identical checkpoint reload outputs; it is not a model-quality evaluation.

The UI uses one light-mode token system and a single file-ingestion path. Sample repairs are visibly simulated; custom cases require editing actual source inputs. Tour explanations react to input errors, file count, pending requests and observed decisions. Browser visual, responsive and keyboard verification remains a separate release gate.

The legacy `/api/v1/research/quant-risk` endpoint returns 410: its typed-in merchant economics and made-up budget percentages are retired. `training/run_all.py` was removed because it wrote a completion manifest without training. The old training manifest is explicitly historical configuration; the saved surrogate-feature experiments do not prove language understanding, graph learning or real merchant benefit. Use the current artifact-backed extraction study and CARVE v4.5 evaluation for the submission, with their synthetic limitations.

## Limitations and responsible next step

The benchmark is generated, small, class-balanced, and template-derived. It has no issuer outcomes, real merchant prevalence, user study, or evidence of chargeback-win lift. Regex behavior is brittle under unseen semantic forms, as the final partial/full slice demonstrates. The exact-grounding ratio covers emitted grounded predictions and must be read beside the low claim recall.

The next justified step is not more infrastructure. It is a new, separately versioned DEV study on de-identified, consented dispute bundles with domain review, followed by a predeclared model-backed B1 extractor only if it materially improves false-PASS and claim-recall behavior without unacceptable false holds. The frozen v1 holdout must not be modified or reused for tuning.

## Primary sources

- [Razorpay dispute webhook events](https://razorpay.com/docs/webhooks/disputes/)
- [Razorpay webhook validation and testing](https://razorpay.com/docs/webhooks/validate-test/)
- [Razorpay webhook best practices](https://razorpay.com/docs/webhooks/best-practices/)
- [Razorpay dispute evidence guidance](https://razorpay.com/docs/payments/disputes/submit-evidence/)
- [Razorpay contest API — reference only, never called](https://razorpay.com/docs/api/disputes/contest/)
- [Razorpay accept API — reference only, never called](https://razorpay.com/docs/api/disputes/accept/)

The evidence registry and supported claims are in `docs/24-SOURCE-LEDGER.md`.

## 5-Minute Razorpay Judge Navigation & Research Integrity Audit

For evaluators from the Razorpay AI Hiring Committee, Risk Engineering, and Research Review Panels:

1. **[FINAL_RAZORPAY_JUDGE_BRIEF.md](FINAL_RAZORPAY_JUDGE_BRIEF.md)**: Curated 5-minute adjudication path, competitor comparisons (vs. LLM agents & naive XGBoost), and answers to hostile review questions.
2. **[FAILURE-NARRATIVE.md](FAILURE-NARRATIVE.md)**: Technically rigorous 7-stage failure post-mortem (Observation → Hypothesis → Falsification → Root Cause → Repair → Re-evaluation → Lesson).
3. **[REAL_TRAINING_RECEIPT.md](REAL_TRAINING_RECEIPT.md)**: Reproducible PyTorch training receipt with pre/post parameter SHA-256 hashes, L2 norms, 5-seed empirical learning curves, and bitwise zero-drift reload checks.
4. **[RESEARCH_NEGATIVE_RESULTS.md](RESEARCH_NEGATIVE_RESULTS.md)**: Honest scientific post-mortem detailing falsified analytical curves, excision of tabular label leakage, and what was learned.
5. **[P0_P1_RESEARCH_REPAIR_PLAN.md](P0_P1_RESEARCH_REPAIR_PLAN.md)**: Prioritized action plan tracking resolution of all submission-blocking (P0) and research-critical (P1) issues.
6. **[CLAIMS_LEDGER.md](CLAIMS_LEDGER.md)**: Formal ledger of verified public claims and strictly prohibited/decommissioned statements.
7. **[BASELINE_LADDER_V3.md](BASELINE_LADDER_V3.md)**: Empirical evaluation of models B0 through B10, including matched-coverage stress testing.
8. **[LOSS_SENSITIVITY.md](LOSS_SENSITIVITY.md)**: Decision-theoretic sensitivity sweep across 45 asymmetric financial risk regimes (CARVE dominates in 86.7%).
9. **[SIMULATOR_VERIFIER_CIRCULARITY.md](SIMULATOR_VERIFIER_CIRCULARITY.md)**: Falsification experiments (rule holdout, perturbed verifier) disproving simulator-verifier circularity.
10. **[HUMAN_VALIDATION_STATUS.md](HUMAN_VALIDATION_STATUS.md)**: 7-tier external validity hierarchy and double-blind protocol for 100 human-authored dispute cases.
11. **[ROBUSTNESS_POST_AUDIT.md](ROBUSTNESS_POST_AUDIT.md)**: 20 minimal counterfactual pairs and 8 adversarial stress suites.
12. **[FINAL_RESEARCH_CONTRIBUTIONS.md](FINAL_RESEARCH_CONTRIBUTIONS.md)**: The three hardened, paper-quality contributions that survived falsification.

### Fast Reproduction Command
```powershell
# Verify entire test and quality gate suite (11 gates, 313 pytest tests, 38 frontend tests, full build)
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
```

## Read order for coding agents

1. `AGENTS.md`
2. `docs/00-SOURCE-OF-TRUTH.md`
3. `docs/01-COMPETITION-TRUTH.md`
4. `docs/05-PRD.md`
5. `docs/06-SRS.md`
6. `docs/09-AI-ML-SPEC.md`
7. `docs/10-DATA-BENCHMARK-SPEC.md`
8. `docs/12-DECISION-POLICY.md`
9. `docs/13-ARCHITECTURE.md`
10. `docs/14-API-CONTRACTS.md`
11. `docs/15-DATABASE-SCHEMA.md`
12. `docs/07-UI-UX-SPEC.md`
13. `docs/16-SECURITY-THREAT-MODEL.md`
14. `docs/17-RELIABILITY-TESTING.md`
15. `docs/20-TRACEABILITY-MATRIX.md`
16. `TASKS.md`

When specifications conflict, current official Razorpay documentation has precedence, followed by the canonical source of truth, PRD/SRS/contracts, and then supporting architecture/testing documents. Legacy reports outside this repository are non-authoritative.

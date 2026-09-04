# Release-gate acceptance evidence

Verified on 2026-08-23. This evidence backs every checked item in `QUALITY-GATES.md` and `docs/23-DEFINITION-OF-DONE.md`.

## Automated release gate

`powershell -ExecutionPolicy Bypass -File scripts/check.ps1` passed with:

- 78 Python paths formatted;
- Ruff lint green;
- strict mypy green;
- package/spec/source/schema validation green;
- static Razorpay no-write guard green;
- 178 backend tests passed;
- Prettier and ESLint green;
- TypeScript/Vite production build green;
- 11 frontend tests passed.

The only current local warning is FastAPI/Starlette's TestClient/httpx deprecation. A fresh Python 3.14 environment also emitted upstream `pytest-asyncio` deprecation warnings for APIs planned for removal in Python 3.16; no warning was treated as evidence of functionality.

## Source, product, grounding, security, reliability

- Source/spec lint distinguishes corrective legacy mentions from implementation event names and enforces `payment.dispute.created`, raw-body HMAC, event-ID idempotency, the 5-second durable-ACK contract, and correct Visa 13.6/13.7 language.
- Route/import/host/client analysis and integration responses prove no Razorpay contest/accept/refund/payment write path. Letter generation, win probability, and generic-error BLOCK behavior are absent.
- Exact/missing/repeated grounding, deterministic amount/currency/ID/state conflict rules, decision precedence, prompt injection, schema failure, transient timeout, raw-log exclusion, SQL-injection text, duplicate delivery, restart recovery, and property invariants all have passing tests.
- A refined credential-pattern scan found no API key/private-key pattern. `.env.example` contains placeholders only. This workspace has no Git metadata, so no Git-history cleanliness claim is made.
- Hash chaining is not implemented; README correctly treats any future chain as tamper-evident rather than immutable.

## Evaluation integrity

- Frozen dataset: 120 DEV and 60 HOLDOUT synthetic cases with a frozen family split.
- HOLDOUT manifest SHA-256: `1c285947c38bd0623b56cfb156dcc2eb3157505e5b8fc8bca45c089158ab3681`.
- Release code bundle SHA-256: `77e178b83e427fc4d5328cef1aa15582b5e22ae087088d258d17a7061a519996`.
- Release config SHA-256: `24ce16ba08a8b4edcbb843aa9fc9720e8f1db70358ffba22430e6251344f45b1`.
- Final artifact SHA-256: `15349fd24f2fbceb1c6a38edafee92d5953f22af2e9611efcda17ba20f1992b8`.
- Release-freeze verification still reproduces all three frozen digests. Detector/evaluator/policy/config bytes were not changed after the once-only final HOLDOUT run. Later changes were demo scripts, frontend accessibility, tests, evidence docs, and a newly versioned offline cache; they do not affect the frozen evaluator.
- DEV scripts default/guard against HOLDOUT. The dashboard verifies and projects the saved sidecar-backed artifact without computing metrics.
- README prominently labels the benchmark synthetic and reports 10 false PASS plus the 0/10 `partial_full_amount` slice.

## UX and live golden path

- Frontend tests verify text-labeled states, exact-source focus, REVIEW recovery, BLOCK inspection preconditions, structured override, local mark-ready, initial modal focus, Tab/Shift+Tab focus trapping, Escape close, and trigger-focus restoration.
- The default screen now accepts editable synthetic evidence/ledger input and returns the real local extractor/grounder/verifier output. Live browser checks exercised BLOCK, PASS, and REVIEW and found no console warning/error.
- Preset controls now execute directly, disclose an honestly paced four-stage inspection trace, disable during execution, and bring output into view on stacked layouts; no artificial duration is presented as model latency.
- A live browser session exercised the queue, PASS/REVIEW/BLOCK states, preserved raw reason codes, BLOCK source/ledger comparison, exact-source navigation, local-only language, and the artifact-backed evaluation page.
- This is concrete keyboard/semantic pattern evidence, not a WCAG certification or completed screen-reader audit.

## Reproducibility and failure recovery

- An isolated clean-source copy explicitly verified `.venv`, Node modules, build output, Hypothesis/test/type/lint caches, and runtime state were absent.
- The first setup attempt genuinely failed because PATH Python lacked `venv`. Setup was fixed to probe Python 3.10+ plus `venv`, verify creation, and select the valid Windows launcher.
- The cache-free isolated copy then completed setup, the full 169-backend/9-frontend gate under newly resolved Python 3.14 packages, and `scripts/rehearse-demo.ps1`. The exact verified copy was moved to the Windows Recycle Bin afterward.
- The working tree also passed the 169-backend/9-frontend gate.
- The default demo command and the parameterized rehearsal each started, verified, and stopped their recorded local processes. No demo process-state file or listener on the demo ports remained.
- The rehearsal injects extractor unavailability (`REVIEW` / `F_MODEL_UNAVAILABLE`), restores offline cache v2, verifies recovery to PASS, and then checks three signed-webhook cases, offline health, final artifact digest/counts, frontend service, and `network_write_performed: false`.
- `DEMO-SCRIPT.md` has regression-validated contiguous 02:00 and 05:00 allocations and uses only saved measured values. It does not claim a recorded/submitted video.

The frozen HOLDOUT was not rerun during release-gate verification.

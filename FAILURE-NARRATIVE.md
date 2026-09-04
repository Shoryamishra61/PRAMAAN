# Failure narrative

These are observed build failures and one explicitly labeled fault injection. No incident rate, user impact, savings, or production history is inferred from them.

## 1. App initialization violated authentication-before-persistence

Symptom: after health initialization was added, the full gate failed `test_mutated_replay_with_original_signature_is_rejected_before_persistence`. The invalid signed-body replay correctly returned HTTP 401, but the database file already existed.

Reproduction:

```powershell
python -m pytest backend/tests/test_webhook_replay.py::test_mutated_replay_with_original_signature_is_rejected_before_persistence -q
```

Root cause: `create_app()` eagerly called `initialize_database()`. Constructing the app therefore persisted SQLite schema state before the webhook endpoint could authenticate the raw body. This weakened the intended trust boundary even though no dispute case or job was created.

Fix: remove database initialization from app construction. The health probe initializes/checks its local schema when explicitly called; business endpoints retain their existing post-authentication initialization. The HMAC rejection path now creates no database file.

Regression evidence: the focused replay/health suite passed, followed by the full 155-test backend gate at that cycle. The same replay test remains in every release check.

Residual risk: SQLite file existence is only one observable side effect. Production deployments would also need request tracing and infrastructure-level checks to prove that rejected requests do not reach downstream queues, caches, or telemetry sinks. Those systems do not exist in this local MVP.

Reference: `artifacts/verification/T026.md`. Git commit reference is unavailable because this workspace is not a Git repository.

## 2. Windows demo readiness and process-state assumptions failed

Symptom: both Uvicorn and Vite logged that they were listening, but `scripts/demo.ps1` timed out and stopped them. After the readiness fix, the first stop attempt refused to kill anything and reported combined PIDs.

Reproduction was the real demo command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
powershell -ExecutionPolicy Bypass -File scripts/stop-demo.ps1
```

Root causes:

- Windows PowerShell web cmdlets did not reach loopback under the machine proxy behavior in this environment.
- PowerShell 5 deserialized the top-level JSON array in a shape the stop script's `@(...)` wrapper treated as one aggregate record.

Fixes:

- readiness now probes the two explicit loopback TCP ports with `TcpClient`, then the verification step separately exercised actual health, case, and frontend HTTP responses;
- the process-state file now has an explicit versioned object with a `processes` array;
- the stop script supports both the old array and new object schema, verifies PID start-time ticks, refuses PID reuse, and removes stale state after failed startup.

Regression evidence: a subsequent start printed ready in 2.5 seconds, live health/case/frontend responses were read, and two later start/stop cycles stopped exactly the recorded backend and frontend PIDs.

Residual risk: a port-open probe alone does not prove application semantics. The runbook therefore pairs it with API/browser validation; production orchestration would use a real health check rather than this local launcher.

Reference: `artifacts/verification/T028.md`. Git commit reference is unavailable.

## 3. Intentional extractor-outage recovery

This is fault injection, not an accidental outage or production incident.

```powershell
python scripts/failure_demo.py
```

The command injects a bounded transient extractor failure twice, verifies `REVIEW` with `F_MODEL_UNAVAILABLE`, confirms the safe structured failure log contains no raw evidence, restores the versioned offline replay adapter, and re-evaluates the consistent synthetic case to PASS. It explicitly reports `network_write_performed: false`.

This demonstrates the safety invariant: degraded uncertainty does not silently become PASS. Recovery is deterministic for the bundled fixture; it does not prove provider availability or production recovery time.

## 4. Windows PowerShell did not auto-load the HTTP client assembly

Symptom: the first technical demo rehearsal seeded and started both services, then failed before its health assertion with `Cannot find type [System.Net.Http.HttpClientHandler]`. Its `finally` cleanup still stopped exactly the two recorded processes.

Root cause: Docker Desktop/WSL already owned port 8000. The launcher started a Uvicorn child that could not bind, then treated the unrelated listener as its backend because readiness checked only whether the port accepted TCP. The initial Windows PowerShell probe also depended on an HTTP assembly that host had not auto-loaded.

Fix: the launcher now refuses already-occupied requested ports, verifies both child processes remain alive during readiness, and supports explicit ports passed through to Vite's API proxy. The rehearsal uses collision-free ports and keeps PowerShell responsible only for process orchestration; `scripts/verify_live_demo.py` performs typed, proxy-disabled loopback HTTP and strict response assertions.

Regression evidence: the same rehearsal command subsequently completed its health, queue, evaluation-artifact, frontend, failure-injection, and cleanup assertions. This is local compatibility evidence, not a claim about other PowerShell editions.

## 5. Fresh-copy setup selected a Python without `venv`

Symptom: the isolated clean-source reproduction failed immediately with `No module named venv`, then attempted to invoke a `.venv` interpreter that had never been created.

Root cause: `scripts/setup.ps1` assumed the first `python` on PATH included the standard `venv` module and did not explicitly check the native command's exit code under Windows PowerShell.

Fix: setup now probes available Python launchers for both Python 3.10+ and an importable `venv` module, prefers the Windows `py` launcher when valid, tolerates expected probe failures while considering fallbacks, verifies environment creation, and otherwise stops with one actionable requirement message.

Regression evidence: an isolated clean-source directory with no copied Python environment, Node modules, build output, Hypothesis/test/type/lint caches, or runtime state successfully ran setup, the full test command, and the offline technical rehearsal. The full gate passed with 169 backend and 9 frontend tests under freshly resolved Python 3.14 dependencies; the demo then showed REVIEW-to-PASS failure recovery and signed-webhook PASS/REVIEW/BLOCK cases. The exact temporary directory was moved to the Windows Recycle Bin after its resolved path was verified.

Residual risk: Python 3.14 emitted dependency deprecation warnings from `pytest-asyncio`, and FastAPI's current test client emitted its documented Starlette/httpx deprecation warning. They did not fail the gate, but dependency updates should be tested before Python 3.16 removes the deprecated asyncio policy APIs.

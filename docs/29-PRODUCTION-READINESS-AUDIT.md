# 29 — Production-readiness audit

Date: 2026-09-02

## Scope

Executable backend and frontend modules, API contracts, database/job behavior, configuration,
research artifact readers, security boundaries, dependency health, build scripts, navigation,
forms, failure states, accessibility semantics, responsive CSS, and repository packaging.

## Material findings and resolutions

1. **False-green master check.** Windows PowerShell continued after failed formatting, mypy, and
   pytest commands and returned exit code 0. `scripts/check.ps1` now checks every native exit code
   and stops at the first failed gate.
2. **Frozen v4.1 research debt was hidden.** The archived generator contains 57 policy labels that
   are not grounded by the quoted text and 114 certificate annotations that disagree with the
   label-blind compiler. The frozen files were not edited. Tests now preserve these exact negative
   findings, while v4.5 remains the current protocol.
3. **Partial-refund proof naming was ambiguous.** A full-payment refund claim checked against a
   partial authoritative total now compiles as a cumulative-amount contradiction without reading
   benchmark labels or phenomenon names.
4. **Strict typing was not reproducible.** Z3 typing and test-package discovery prevented the
   declared mypy gate from passing. Package discovery, imports, and narrow external typing policy
   are now explicit.
5. **Synchronous work blocked async routes.** SQLite and artifact reads now run in FastAPI's worker
   thread path; the async webhook moves durable ingestion off the event loop.
6. **Webhook body size was unbounded.** Both declared and received bodies are capped at 1 MB before
   parsing or persistence. Oversized input has a regression test.
7. **Frontend requests could wait forever and hid recovery details.** A shared API boundary now
   applies a 10-second timeout and surfaces safe backend validation messages. Research and
   evaluation errors include retry and exit paths.
8. **Local evidence import trusted arbitrary JSON and size.** JSON bundles are checked against the
   sandbox contract, text is bounded, and files over 256 KB are rejected before reading.
9. **Formatting was duplicated and inconsistent.** Currency, timestamps, and machine-token labels
   now use shared locale-aware helpers.
10. **Three CSS roots competed globally.** One token system now owns typography, colors, controls,
    radii, focus, and surfaces. Proof and research views alias rather than replace it. An undefined
    display-font token was fixed.
11. **Navigation state was not reflected in the URL.** Product routes now update browser history,
    restore on Back/Forward, and support direct `/start`, `/walkthrough`, and `/complete` entry.
12. **Accessibility metadata was uneven.** Skip links cover the verifier, analyst, research, and
    legacy lab surfaces; inputs have names/autocomplete behavior; imported evidence is bounded;
    error updates are announced; and control focus uses one visible token.

## Ponytail complexity audit

The no-op LangGraph sequence was removed from the active runner because typed Python calls already
define the execution order and the extra framework added no measured value. Z3, scikit-learn,
XGBoost, sentence-transformers, and historical FECL runners remain only where reproducibility tests
or frozen research artifacts use them. Ignored environments, bytecode, generated builds, databases,
logs, package metadata, and render caches are runtime material, not release source.

The 2,000-line `App.tsx` remains the largest maintainability risk. Splitting it without changing
behavior would move lines rather than remove complexity, so this pass fixed shared formatting,
routing, request, and token boundaries first. A later extraction is justified only when a second
team or independent release cadence requires route-level ownership.

Ponytail verdict: one no-value orchestration dependency and its duplicate trace surface were
removed; zero speculative abstractions were added.

## Verification

- Full Python formatting, lint, strict typing, specification lint, package validation, no-write
  boundary, backend tests, frontend formatting, lint, TypeScript build, and interaction tests run
  through the fail-fast master command.
- npm production and development audits report no known vulnerabilities.
- `uv pip check` reports a compatible Python environment.
- Live local smoke covers health, proof, research, case queue, evaluation, sandbox PASS/REVIEW/BLOCK,
  and injected model/integrity/corruption failures.

## Remaining risks

- The system is a local defense-only prototype with no user authentication, tenant isolation,
  production secret manager, or Razorpay write integration. Those are deployment blockers, not
  hidden capabilities.
- SQLite queue pagination loads the sorted result before applying the cursor; acceptable for the
  bounded demo, not for a large multi-tenant queue.
- FECL metrics are synthetic and do not establish real-merchant prevalence or financial savings.
- Product Design screenshot audit remains blocked because no in-app or extension browser was
  connected. Source, semantic, automated interaction, and responsive-rule checks do not substitute
  for pixel, contrast, zoom, mobile reflow, or screen-reader verification.
- The manual modal focus trap remains because it has explicit regression coverage. Migrating to the
  native dialog element should wait for browser-level cross-platform verification.

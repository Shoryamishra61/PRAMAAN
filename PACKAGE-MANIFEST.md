# Package Manifest

This repository contains the specification, working local application, frozen synthetic research
artifacts, and reproducibility tooling. Runtime output and dependency directories remain excluded.

## Control files
- `README.md` — entry point/read order
- `AGENTS.md` — coding-agent constitution
- `MASTER-BUILD-PROMPT.md` — autonomous implementation loop
- `QUALITY-GATES.md` — release gates
- `IMPLEMENTATION-PLAN.md` — implementation sequencing
- `TASKS.md` — initial executable backlog
- `SPEC-LINT-RULES.md` + `scripts/spec_lint.py` — spec regression guard
- `FAILURE-NARRATIVE-TEMPLATE.md` — honest build-failure template
- `IDE-HANDOFF.md` — exact coding-agent handoff procedure

## Canonical documentation
`docs/00` through `docs/27` cover competition truth, problem validation, product/SRS, UX, AI/ML, benchmark/evaluation, policy, architecture, APIs/database, security/reliability, demo, traceability, decisions/risks, source evidence, corrections, and panel defense.

## ADRs
- ADR-001: one bounded AI stage
- ADR-002: no Razorpay writes in MVP
- ADR-003: durable SQLite jobs
- ADR-004: text/JSON evidence v1
- ADR-005: family-separated holdout

## Machine-readable contracts
- `contracts/grounded-claim.schema.json`
- `contracts/gate-decision.schema.json`
- `contracts/refund_not_processed_v1.yaml`

The implementation agent must not edit the frozen source ledger/corrections merely to make an implementation decision appear compliant.

## Executable application

- `backend/app/` — FastAPI ingestion, durable local workflow, semantic boundary, deterministic verification, and artifact readers.
- `backend/tests/` — contract, property, security, failure, benchmark-integrity, and API tests.
- `frontend/src/` — evidence debugger, analyst workspace, generated evaluation, and CARVE research lab.
- `scripts/check.ps1` — fail-fast full quality gate.
- `scripts/demo.ps1` / `scripts/stop-demo.ps1` — bounded local runtime lifecycle.

## Excluded runtime material

Virtual environments, package caches, `node_modules`, compiled frontend output, Python bytecode,
SQLite runtime files, logs, and temporary PDF renders are ignored and are not release evidence.

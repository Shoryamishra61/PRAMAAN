# IDE / Coding-Agent Handoff

Copy this entire specification repository into the root of the implementation workspace (or into `/spec` while keeping `AGENTS.md` discoverable by the agent).

## First agent instruction
Use the exact contents of `MASTER-BUILD-PROMPT.md` as the initial implementation prompt.

## Required first actions by the agent
1. Read `AGENTS.md`.
2. Read the README read-order completely.
3. Run:
   ```bash
   python scripts/package_validate.py
   ```
4. State the canonical product boundary and the next unblocked task from `TASKS.md` before changing code.
5. Implement in vertical slices and update task status only with passing evidence.

## Do not give the coding agent the legacy reports as equal-authority context
They contain known errors and fabricated measurements. If retained in the workspace, place them under a clearly named `legacy-research/` directory and ensure `AGENTS.md` remains authoritative.

## Never let the agent “fill in” missing fintech facts
If a requirement requires an external fact not present in `docs/24-SOURCE-LEDGER.md`, the agent must mark it `VERIFY` and stop that branch rather than inventing an API field, reason-code rule, or network behavior.

## Final submission loop
Before release:
```bash
python scripts/package_validate.py
# implementation lint/typecheck/tests here
# dev benchmark here
# final holdout only after code/prompt/config freeze
```

Then complete:
- `FAILURE-NARRATIVE.md` from a genuine defect/fault injection;
- generated evaluation artifacts;
- README metrics from those artifacts only;
- 5-minute video using `docs/19-DEMO-PITCH-README.md`;
- panel preparation using `docs/26-JUDGE-DEFENSE.md`.

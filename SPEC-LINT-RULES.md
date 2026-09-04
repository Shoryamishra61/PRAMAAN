# Specification Lint Rules

Run `python scripts/spec_lint.py` before coding-agent handoff and after any spec change.

The linter checks authoritative specifications for regressions into known legacy errors, including:
- `dispute.opened` as an implementation event;
- automatic contest/forfeit language;
- fixed 0.80/0.85 AI-confidence policy;
- fabricated legacy metric/cost numbers;
- “immutable SQLite” / unsupported production-grade claims;
- Visa 13.6 cancellation-code conflation;
- arbitrary 50-character override rules.

`docs/24-SOURCE-LEDGER.md`, `docs/25-RESEARCH-CORRECTIONS.md`, and this lint-rules file are excluded because they intentionally quote rejected legacy phrases.

"""Dead-code and stale-research claims linter (Directive Section 60).

Fails with exit code 1 if judge-facing documentation or code contains:
- "25x" (unsubstantiated marketing multiplier)
- "142,468" (decommissioned synthetic claim count)
- "10000%" or "100% guaranteed" (unscientific absolute claims)

Allowed exceptions:
- Negative results, audits, and post-mortems documenting falsifications.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FORBIDDEN_PATTERNS = [
    (re.compile(r"\b25[xX]\b"), "Unsubstantiated 25x multiplier"),
    (re.compile(r"\b142[,_]?468\b"), "Decommissioned 142,468 synthetic count"),
    (re.compile(r"\b10000%\b"), "Unscientific 10000% claim"),
    (re.compile(r"\b100%\s+guaranteed\b", re.IGNORECASE), "Unscientific absolute guarantee"),
]

EXEMPT_FILES = {
    "NEGATIVE_RESULTS.md",
    "RESEARCH_NEGATIVE_RESULTS.md",
    "FAILURE-NARRATIVE.md",
    "CODEBASE_FORENSIC_AUDIT.md",
    "ML_RESEARCH_AUDIT.md",
    "ACTUAL_TRAINING_AUDIT.md",
    "P0_P1_EXECUTION_PLAN.md",
    "P0_P1_RESEARCH_REPAIR_PLAN.md",
    "RESEARCH_SIGNAL_SCORECARD.md",
    "FINAL_EMPIRICAL_MANIFEST.json",
    "check_stale_claims.py",
}

AUDIT_MARKERS = (
    "falsif",
    "prior",
    "historical",
    "analytical",
    "defect",
    "audit",
    "previous",
    "formula",
    "omitting",
)


def scan_for_stale_claims(repo_root: Path) -> list[str]:
    violations: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        parts = path.parts
        if any(p.startswith(".") or p in {"node_modules", "venv", ".venv"} for p in parts):
            continue
        if path.suffix not in {".md", ".py", ".json", ".txt", ".ts", ".tsx"}:
            continue
        if path.name in EXEMPT_FILES:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for line_no, line in enumerate(content.splitlines(), start=1):
            lower_line = line.lower()
            # If the line explicitly acknowledges an audited or falsified claim, skip
            if any(marker in lower_line for marker in AUDIT_MARKERS):
                continue
            for pattern, reason in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    rel_path = path.relative_to(repo_root).as_posix()
                    violations.append(f"{rel_path}:{line_no}: [{reason}] {line.strip()[:100]}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    violations = scan_for_stale_claims(args.repo_root)
    if violations:
        print("\n[FAIL] Stale-research / forbidden marketing claims detected:")
        for v in violations:
            print(f"  - {v}")
        print(
            "\nPer Directive Section 60, remove unsubstantiated marketing claims or move "
            "them to an explicitly marked negative-results document.\n"
        )
        return 1

    print(
        "[OK] No configured forbidden claim patterns found; "
        "this scan does not validate every metric."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

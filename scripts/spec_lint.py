from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {
    ROOT / "docs/24-SOURCE-LEDGER.md",
    ROOT / "docs/25-RESEARCH-CORRECTIONS.md",
    ROOT / "SPEC-LINT-RULES.md",
    ROOT / "scripts/spec_lint.py",
}

REQUIRED = [
    "README.md",
    "docs/00-SOURCE-OF-TRUTH.md",
    "docs/05-PRD.md",
    "docs/06-SRS.md",
    "docs/09-AI-ML-SPEC.md",
    "docs/10-DATA-BENCHMARK-SPEC.md",
    "docs/12-DECISION-POLICY.md",
    "docs/13-ARCHITECTURE.md",
    "docs/20-TRACEABILITY-MATRIX.md",
    "docs/24-SOURCE-LEDGER.md",
    "contracts/grounded-claim.schema.json",
    "contracts/gate-decision.schema.json",
]

BANNED = {
    r"\bdispute\.opened\b": (
        "Use documented payment.dispute.* events; legacy dispute.opened is wrong."
    ),
    r"\bauto[- ]?contest\b": "MVP has no automatic network write.",
    r"\bauto[- ]?forfeit\b": "MVP has no automatic accept/forfeit action.",
    r"(?:κ|kappa|confidence)[^\n]{0,40}(?:<|<=|threshold)[^\n]{0,10}0\.(?:80|85)": (
        "No magic LLM confidence thresholds."
    ),
    r"\b0\.89\b": "Legacy fabricated metric must not enter authoritative specs.",
    r"\b0\.81\b": "Legacy fabricated metric must not enter authoritative specs.",
    r"₹\s*70[, ]?100": "Legacy fabricated savings must not enter authoritative specs.",
    r"immutable\s+SQLite": "SQLite audit data is not immutable.",
    r"production[- ]grade": "Do not claim production grade in the specification without evidence.",
    r"13\.6\s*(?:=|is|:)\s*(?:Visa\s*)?(?:reason\s*)?(?:code\s*)?"
    r"Cancelled Merchandise": "Visa 13.6/13.7 conflation.",
    r"50[- ]character": "No arbitrary 50-character override gate.",
}


def files_to_scan() -> Iterator[Path]:
    # Scan implementation-authoritative specs. Meta/correction/source documents intentionally
    # quote rejected legacy phrases and are excluded from banned-phrase checks.
    for rel in [
        "README.md",
        "docs/00-SOURCE-OF-TRUTH.md",
        "docs/02-PROBLEM-VALIDATION.md",
        "docs/04-DOMAIN-MODEL.md",
        "docs/05-PRD.md",
        "docs/06-SRS.md",
        "docs/07-UI-UX-SPEC.md",
        "docs/08-DESIGN-SYSTEM.md",
        "docs/09-AI-ML-SPEC.md",
        "docs/10-DATA-BENCHMARK-SPEC.md",
        "docs/11-EVALUATION-TEVV.md",
        "docs/12-DECISION-POLICY.md",
        "docs/13-ARCHITECTURE.md",
        "docs/14-API-CONTRACTS.md",
        "docs/15-DATABASE-SCHEMA.md",
        "docs/16-SECURITY-THREAT-MODEL.md",
        "docs/17-RELIABILITY-TESTING.md",
        "docs/18-OBSERVABILITY-FAILURE-RECOVERY.md",
        "docs/19-DEMO-PITCH-README.md",
        "docs/22-IMPLEMENTATION-BACKLOG.md",
    ]:
        path = ROOT / rel
        if path.exists():
            yield path
    for path in sorted((ROOT / "adr").glob("*.md")):
        yield path


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            errors.append(f"MISSING required file: {rel}")

    safe_context = re.compile(
        r"\b(no|not|never|removed|remove|legacy|old|wrong|correct|unsupported|avoid|"
        r"prohibit|without proof|must not|do not|rather than)\b",
        flags=re.IGNORECASE,
    )
    for path in files_to_scan():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern, message in BANNED.items():
                if re.search(pattern, line, flags=re.IGNORECASE) and not safe_context.search(line):
                    errors.append(
                        f"{path.relative_to(ROOT)}:{lineno}: {message} / pattern={pattern}"
                    )

    if errors:
        print("SPEC LINT FAILED")
        for err in errors:
            print(f"- {err}")
        return 1
    print("SPEC LINT PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

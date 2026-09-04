from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def main() -> int:
    errors: list[str] = []

    lint = subprocess.run(
        [sys.executable, str(ROOT / "scripts/spec_lint.py")],
        capture_output=True,
        text=True,
    )
    if lint.returncode:
        fail(lint.stdout + lint.stderr, errors)

    for path in sorted((ROOT / "contracts").glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"Invalid JSON contract {path.name}: {exc}", errors)

    ledger = (ROOT / "docs/24-SOURCE-LEDGER.md").read_text(encoding="utf-8")
    defined = set(re.findall(r"###\s+(SRC-[A-Z0-9-]+)", ledger))
    used: set[str] = set()
    for path in ROOT.rglob("*.md"):
        if path.name == "24-SOURCE-LEDGER.md":
            continue
        used.update(re.findall(r"\b(SRC-[A-Z0-9-]+)\b", path.read_text(encoding="utf-8")))
    undefined = sorted(used - defined)
    if undefined:
        fail(f"Undefined source IDs: {undefined}", errors)

    prd = (ROOT / "docs/05-PRD.md").read_text(encoding="utf-8")
    trace = (ROOT / "docs/20-TRACEABILITY-MATRIX.md").read_text(encoding="utf-8")
    prd_ids = set(re.findall(r"###\s+(PRD(?:-NFR)?-\d+)", prd))
    trace_ids = set(re.findall(r"\b(PRD(?:-NFR)?-\d+)\b", trace))
    missing_trace = sorted(prd_ids - trace_ids)
    if missing_trace:
        fail(f"PRD requirements missing traceability rows: {missing_trace}", errors)

    # TASKS may reference only requirement IDs actually defined in canonical specs.
    canonical_text = "\n".join(
        (ROOT / rel).read_text(encoding="utf-8")
        for rel in [
            "docs/05-PRD.md",
            "docs/06-SRS.md",
            "docs/09-AI-ML-SPEC.md",
            "docs/12-DECISION-POLICY.md",
            "docs/14-API-CONTRACTS.md",
        ]
    )
    id_pattern = re.compile(r"\b(?:PRD(?:-NFR)?|SRS|AI|POL|API)-\d+\b")
    defined_req_ids = set(id_pattern.findall(canonical_text))
    task_req_ids = set(id_pattern.findall((ROOT / "TASKS.md").read_text(encoding="utf-8")))
    unknown_task_ids = sorted(task_req_ids - defined_req_ids)
    if unknown_task_ids:
        fail(f"TASKS references undefined requirement IDs: {unknown_task_ids}", errors)

    # Cross-track contamination guard for authoritative implementation files.
    core_paths = [
        ROOT / "docs/00-SOURCE-OF-TRUTH.md",
        ROOT / "docs/05-PRD.md",
        ROOT / "docs/06-SRS.md",
        ROOT / "docs/09-AI-ML-SPEC.md",
        ROOT / "docs/12-DECISION-POLICY.md",
        ROOT / "docs/13-ARCHITECTURE.md",
        ROOT / "AGENTS.md",
        ROOT / "MASTER-BUILD-PROMPT.md",
    ]
    forbidden_track3 = re.compile(
        r"\b(Hybrid Recovery Orchestrator|Z9|ZA|payday[- ]aligned|UPI retry|"
        r"four-attempt retry|4-attempt retry)\b",
        re.I,
    )
    for path in core_paths:
        text = path.read_text(encoding="utf-8")
        if forbidden_track3.search(text):
            fail(f"Track 03 contamination in {path.relative_to(ROOT)}", errors)

    if errors:
        print("PACKAGE VALIDATION FAILED")
        for err in errors:
            print("-", err)
        return 1

    print("PACKAGE VALIDATION PASSED")
    print(f"PRD requirements traced: {len(prd_ids)}")
    print(f"External source IDs referenced: {len(used)} / defined: {len(defined)}")
    print("JSON contracts: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

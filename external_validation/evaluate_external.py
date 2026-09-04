"""Evaluation runner for external challenge sets.

Evaluates CARVE-FECL pipeline on FECL-CROSSGEN-5K (cross-generator challenge)
and checks status of the external human blind challenge pack.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def evaluate_external_challenges() -> dict[str, Any]:
    manifest_path = ROOT / "external_validation" / "blind_manifest.json"
    human_status = "PENDING_EXTERNAL_VALIDATION"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        human_status = manifest.get("status", "PENDING_EXTERNAL_VALIDATION")

    crossgen_path = ROOT / "research" / "cross_generator_results.json"
    crossgen_metrics: dict[str, Any] = {}
    if crossgen_path.exists():
        crossgen_metrics = json.loads(crossgen_path.read_text(encoding="utf-8"))

    return {
        "human_blind_challenge": {
            "status": human_status,
            "target_scale": 500,
            "current_cases": 0,
            "external_validity_note": "Awaiting external cohort execution per protocol freeze.",
        },
        "cross_generator_challenge": crossgen_metrics,
    }


if __name__ == "__main__":
    out = evaluate_external_challenges()
    print(json.dumps(out, indent=2))

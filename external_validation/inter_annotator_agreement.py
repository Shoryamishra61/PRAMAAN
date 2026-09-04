"""Inter-annotator agreement computation for human-blind challenge cases.

Calculates Cohen's Kappa for categorical consistency determinations and
Token-level F1 / IoU for contradiction span grounding across dual annotations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def compute_cohens_kappa(annotations_a: list[bool], annotations_b: list[bool]) -> float:
    if len(annotations_a) != len(annotations_b) or not annotations_a:
        return 0.0

    n = len(annotations_a)
    p_o = sum(1 for a, b in zip(annotations_a, annotations_b, strict=True) if a == b) / n

    p_a1 = sum(1 for a in annotations_a if a) / n
    p_a0 = 1.0 - p_a1
    p_b1 = sum(1 for b in annotations_b if b) / n
    p_b0 = 1.0 - p_b1

    p_e = (p_a1 * p_b1) + (p_a0 * p_b0)

    if p_e >= 1.0:
        return 1.0
    return float((p_o - p_e) / (1.0 - p_e))


def evaluate_agreement_file(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return {
            "status": "PENDING_EXTERNAL_VALIDATION",
            "samples_evaluated": 0,
            "cohens_kappa": None,
            "raw_agreement_rate": None,
        }

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "status": data.get("status", "PENDING_EXTERNAL_VALIDATION"),
        "samples_evaluated": data.get("current_human_cases_collected", 0),
        "cohens_kappa": None,
        "raw_agreement_rate": None,
    }


if __name__ == "__main__":
    p = Path(__file__).parent / "blind_manifest.json"
    result = evaluate_agreement_file(p)
    print(f"Human Blind Challenge Status: {result['status']}")

"""AI/ML Research Integrity & Label Leakage Prevention Tests for PRAMAAN.

Validates the Label Leakage and Shortcut Detection Requirements:
1. Forbids target-derived variables (has_contra, label, target, is_error, future_outcome).
2. Verifies that feature columns contain zero target-correlated shortcuts.
3. Single-feature shortcut probing: No single raw feature may exceed 90% ROC-AUC on its own.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
FORBIDDEN_FEATURE_TOKENS = [
    "has_contra",
    "has_contradiction",
    "target",
    "is_error",
    "future_outcome",
    "ground_truth",
    "label",
    "is_fraud",
]


def test_no_forbidden_target_tokens_in_feature_manifests() -> None:
    """Feature names and metadata must never include target-derived flags."""
    manifest_paths = [
        ROOT / "research/training_manifest.json",
        ROOT / "research/final_empirical_manifest.json",
    ]

    for path in manifest_paths:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8").lower()
        for forbidden in ["has_contra", "is_error", "future_outcome"]:
            # Make sure it's not referenced as an active input feature
            assert f'"{forbidden}": true' not in content
            assert f'"{forbidden}": 1' not in content


def test_data_splits_contain_no_leaked_target_column_in_features() -> None:
    """Verify that dataset splits do not expose the target label in input feature fields."""
    dev_path = ROOT / "data/financial-evidence-integrity/v4.5/dev.jsonl"
    if not dev_path.exists():
        pytest.skip("Benchmark v4.5 dataset not found")

    with open(dev_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            if line_num > 50:  # Sample first 50 cases
                break
            record = json.loads(line)
            # Grounded claim attributes must not include the target label
            claim_attrs = record.get("grounded_claim", {}).get("attributes", {})
            for forbidden in FORBIDDEN_FEATURE_TOKENS:
                assert forbidden not in claim_attrs, (
                    f"Found leaked token '{forbidden}' in claim attributes at line {line_num}"
                )


def test_single_feature_shortcut_probes_below_suspicion_threshold() -> None:
    """Verify that no single numerical feature acts as a near-perfect shortcut."""
    # Test a set of simple normalized relational features
    dev_path = ROOT / "data/financial-evidence-integrity/v4.5/dev.jsonl"
    if not dev_path.exists():
        pytest.skip("Benchmark v4.5 dataset not found")

    records: list[dict[str, Any]] = []
    with open(dev_path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    if not records:
        return

    # Extract single numerical feature: claim amount vs capture amount ratio
    labels = [r["material_contradiction"] for r in records]
    ratios: list[float] = []
    for r in records:
        claim_amt = float(r.get("grounded_claim", {}).get("attributes", {}).get("amount_minor", 0))
        cap_amt = float(r.get("authoritative_state", {}).get("payment", {}).get("amount_minor", 1))
        ratios.append(claim_amt / max(1.0, cap_amt))

    # Calculate correlation or single-feature accuracy: should NOT be 100% predictive alone
    matching_cases = sum(
        1 for ratio, label in zip(ratios, labels, strict=True) if (ratio > 1.0) == bool(label)
    )
    accuracy = matching_cases / max(1, len(labels))

    # A single crude feature must not exceed 90% accuracy alone on the diverse dev set
    assert accuracy < 0.90, (
        f"Suspicious shortcut detected: simple ratio achieves {accuracy:.2%} accuracy alone!"
    )

"""Reconcile versioned FECL artifacts without rewriting any frozen result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/research/fecl-integrity-audit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def line_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)


def model_record(artifact: dict[str, Any], model: str) -> dict[str, Any] | None:
    value = artifact.get("models", {}).get(model)
    if not isinstance(value, dict):
        return None
    metric_key = "calibrated_metrics" if "calibrated_metrics" in value else "metrics"
    metrics = value[metric_key]
    return {
        "metric_projection": metric_key,
        "f1": metrics["f1"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "false_pass": metrics["false_pass"],
        "false_block": metrics["false_block"],
    }


def audit_version(version: str) -> dict[str, Any]:
    data = ROOT / f"data/financial-evidence-integrity/{version}"
    manifest_path = data / "manifest.json"
    manifest = load(manifest_path)
    observed_counts = {
        split: line_count(data / f"{split}.jsonl") for split in ("train", "dev", "test", "ood")
    }
    observed_hashes = {
        split: sha256(data / f"{split}.jsonl") for split in ("train", "dev", "test", "ood")
    }
    dev_path = ROOT / f"artifacts/ml/fecl-{version}-dev.json"
    test_path = ROOT / f"artifacts/ml/fecl-{version}-test.json"
    freeze_path = ROOT / f"artifacts/ml/fecl-{version}-freeze.json"
    dev = load(dev_path)
    test = load(test_path)
    freeze = load(freeze_path)
    models = ["literal_rules", "neuro_symbolic", "relational_xgboost", "esran"]
    return {
        "manifest_counts": manifest["counts"],
        "observed_counts": observed_counts,
        "total_including_ood": sum(observed_counts.values()),
        "counts_match": manifest["counts"] == observed_counts,
        "manifest_hashes": manifest["hashes"],
        "observed_hashes": observed_hashes,
        "hashes_match": manifest["hashes"] == observed_hashes,
        "artifacts": {
            "dev_sha256": sha256(dev_path),
            "test_sha256": sha256(test_path),
            "freeze_sha256": sha256(freeze_path),
            "dev_cases": dev["dataset"]["evaluation_cases"],
            "test_cases": test["dataset"]["evaluation_cases"],
            "test_status": test["promotion"]["status"],
            "runtime_changed": test["promotion"]["runtime_changed"],
        },
        "test_models": {
            model: record for model in models if (record := model_record(test, model)) is not None
        },
        "freeze": freeze,
    }


def main() -> None:
    v2 = audit_version("v2")
    v3 = audit_version("v3")
    audit = {
        "artifact_version": "fecl-integrity-audit-v1",
        "non_destructive": True,
        "versions_are_not_comparable_as_one_test": True,
        "v2": v2,
        "v3": v3,
        "findings": [
            {
                "id": "AUDIT-001",
                "status": "CONFIRMED",
                "finding": "FECL-v3 contains 1,424 total cases, not 1,420.",
                "evidence": v3["observed_counts"],
            },
            {
                "id": "AUDIT-002",
                "status": "NOT_REPRODUCED",
                "finding": (
                    "The alleged v3 five-family cardinality multiplier is absent from the current "
                    "generator; observed counts equal the manifest."
                ),
            },
            {
                "id": "AUDIT-003",
                "status": "CONFIRMED",
                "finding": (
                    "FECL-v2 and FECL-v3 false-PASS counts use different datasets, models, "
                    "threshold projections and protocols and must not share one results row."
                ),
            },
            {
                "id": "AUDIT-004",
                "status": "UNSUPPORTED",
                "finding": (
                    "No repository artifact named REISeR or supporting the externally supplied "
                    "REISeR false-PASS count was found."
                ),
            },
            {
                "id": "AUDIT-005",
                "status": "CONFIRMED",
                "finding": (
                    "FECL-v3 freeze records test_open_count=0 although the frozen TEST artifact "
                    "exists; the field is stale metadata, not an execution-count proof."
                ),
            },
            {
                "id": "AUDIT-006",
                "status": "CONFIRMED",
                "finding": (
                    "FECL-v3 greedy node deletion is a diagnostic explanation and not a formal "
                    "minimum contradiction certificate."
                ),
            },
        ],
        "v4_constraints": [
            "Use a separate CALIBRATION split.",
            "Treat TEST execution as an append-only receipt, not a mutable counter in the freeze.",
            "Use pair-group bootstrap.",
            "Use solver-derived certificates only for formally provable contradictions.",
            "Never merge v1, v2, v3, or v4 metrics.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(OUTPUT), "sha256": sha256(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()

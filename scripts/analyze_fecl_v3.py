"""Create a no-tuning, artifact-bound analysis of the frozen FECL v3 test run."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEST_ARTIFACT = ROOT / "artifacts/ml/fecl-v3-test.json"
FREEZE_ARTIFACT = ROOT / "artifacts/ml/fecl-v3-freeze.json"
TEST_DATA = ROOT / "data/financial-evidence-integrity/v3/test.jsonl"
OUTPUT = ROOT / "artifacts/ml/fecl-v3-analysis.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def metric(labels: list[int], decisions: list[int]) -> dict[str, Any]:
    pairs = list(zip(labels, decisions, strict=True))
    tp = sum(label == 1 and decision == 1 for label, decision in pairs)
    tn = sum(label == 0 and decision == 0 for label, decision in pairs)
    fp = sum(label == 0 and decision == 1 for label, decision in pairs)
    fn = sum(label == 1 and decision == 0 for label, decision in pairs)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "count": len(labels),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "false_pass": fn,
        "false_block": fp,
        "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def sliced(predictions: list[dict[str, Any]], model: str, field: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prediction in predictions:
        groups[prediction[field]].append(prediction)
    return {
        name: metric(
            [item["label"] for item in rows],
            [item["decisions"][model] for item in rows],
        )
        for name, rows in sorted(groups.items())
    }


def main() -> None:
    test = read_json(TEST_ARTIFACT)
    frozen = read_json(FREEZE_ARTIFACT)
    rows = read_jsonl(TEST_DATA)
    if test.get("promotion", {}).get("status") != "NO_GO_METHOD_REJECTED":
        raise RuntimeError("Expected the frozen FECL v3 NO-GO artifact.")
    if frozen.get("test_dataset_sha256") != sha256(TEST_DATA):
        raise RuntimeError("Frozen TEST dataset hash mismatch.")
    predictions = test["predictions"]
    if [row["case_id"] for row in rows] != [item["case_id"] for item in predictions]:
        raise RuntimeError("Dataset and prediction order differ.")

    model_order = sorted(
        test["models"], key=lambda name: test["models"][name]["metrics"]["f1"], reverse=True
    )
    headline_models = [
        "literal_rules",
        "relational_xgboost",
        "nli_cross_encoder",
        "graphsage",
        "gat",
        "rgcn",
        "fecl_v2_neuro_symbolic",
        "esran",
    ]
    model_table = []
    for name in model_order:
        record = test["models"][name]
        model_table.append(
            {
                "model": name,
                "architecture": record["architecture"],
                "metrics": record["metrics"],
                "pair_metrics": record.get("pair_metrics"),
                "grounding": record.get("grounding"),
                "conformal": record.get("conformal"),
                "seed_f1": record.get("seed_f1"),
            }
        )

    slices = {
        model: {
            "family": sliced(predictions, model, "family"),
            "phenomenon": sliced(predictions, model, "phenomenon"),
        }
        for model in headline_models
    }
    errors: dict[str, Any] = {}
    for model in headline_models:
        false_pass = [
            item["case_id"]
            for item in predictions
            if item["label"] == 1 and item["decisions"][model] == 0
        ]
        false_block = [
            item["case_id"]
            for item in predictions
            if item["label"] == 0 and item["decisions"][model] == 1
        ]
        errors[model] = {
            "false_pass_count": len(false_pass),
            "false_block_count": len(false_block),
            "false_pass_examples": false_pass[:12],
            "false_block_examples": false_block[:12],
        }

    esran_f1 = test["models"]["esran"]["metrics"]["f1"]
    ablations = []
    for name in test["models"]:
        if not name.startswith("esran_"):
            continue
        ablations.append(
            {
                "model": name,
                "f1": test["models"][name]["metrics"]["f1"],
                "delta_vs_full": round(test["models"][name]["metrics"]["f1"] - esran_f1, 6),
                "pair_both_correct": test["models"][name]["pair_metrics"]["both_correct_rate"],
            }
        )

    casebook = []
    for row, prediction in zip(rows, predictions, strict=True):
        casebook.append(
            {
                "case_id": row["case_id"],
                "pair_id": row["pair_id"],
                "counterfactual_case_id": row["counterfactual_case_id"],
                "family": row["family"],
                "phenomenon": row["phenomenon"],
                "label": row["material_contradiction"],
                "nodes": row["nodes"],
                "edges": row["edges"],
                "causal_subgraph": row["causal_subgraph"],
                "repair": row["repair"],
                "scores": prediction["scores"],
                "decisions": prediction["decisions"],
                "esran_grounding": prediction["esran_grounding"],
            }
        )

    analysis = {
        "artifact_version": "fecl-v3-analysis",
        "source_test_sha256": sha256(TEST_ARTIFACT),
        "source_freeze_sha256": sha256(FREEZE_ARTIFACT),
        "source_dataset_sha256": sha256(TEST_DATA),
        "tuning_performed": False,
        "boundary": {
            "synthetic": True,
            "frozen_test": True,
            "runtime_changed": False,
            "gate_authority": False,
        },
        "verdict": {
            "status": "NO_GO_METHOD_REJECTED",
            "retained_runtime": "regex-baseline-v1",
            "strongest_research_comparator": test["promotion"]["strongest_comparator"],
            "failed_gates": [
                name for name, passed in test["promotion"]["gates"].items() if not passed
            ],
            "interpretation": (
                "Relation-aware graph learning did not justify its added complexity on FECL-Bench "
                "v3. The frozen result retains deterministic runtime authority."
            ),
        },
        "model_table": model_table,
        "slices": slices,
        "errors": errors,
        "ablations": ablations,
        "statistical_tests": test["statistical_tests"],
        "explanation": test["models"]["esran"]["explanation"],
        "ood": test["ood"],
        "casebook": casebook,
    }
    OUTPUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "artifact": str(OUTPUT),
                "sha256": sha256(OUTPUT),
                "status": analysis["verdict"]["status"],
                "cases": len(casebook),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

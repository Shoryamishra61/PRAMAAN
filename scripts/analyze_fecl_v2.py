"""Generate non-tuning slice/error analysis from the frozen FECL v2 test artifact."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/ml/fecl-v2-test.json"
OUTPUT = ROOT / "artifacts/ml/fecl-v2-analysis.json"
TABLE_ROOT = ROOT / "paper/tables"
MODELS = (
    "literal_rules",
    "communication_tfidf",
    "pair_tfidf",
    "communication_embedding",
    "relational_embedding",
    "neuro_symbolic",
    "relational_xgboost",
    "relational_mlp",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(labels: list[int], predictions: list[int]) -> dict[str, Any]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    return {
        "count": len(labels),
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "f1": round(float(f1), 6),
        "false_pass": int(fn),
        "false_block": int(fp),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def score(row: dict[str, Any], model: str) -> float:
    return float(row.get("calibrated_scores", {}).get(model, row["scores"][model]))


def main() -> int:
    artifact = json.loads(SOURCE.read_text(encoding="utf-8"))
    if artifact["boundary"]["split"] != "TEST" or artifact["boundary"]["synthetic"] is not True:
        raise ValueError("Expected the frozen synthetic FECL v2 TEST artifact.")
    predictions = artifact["predictions"]
    slices: dict[str, dict[str, dict[str, Any]]] = {}
    for dimension in ("family", "phenomenon"):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in predictions:
            grouped[str(row[dimension])].append(row)
        slices[dimension] = {}
        for value, rows in sorted(grouped.items()):
            labels = [int(row["label"]) for row in rows]
            slices[dimension][value] = {
                model: metric(labels, [int(score(row, model) >= 0.5) for row in rows])
                for model in MODELS
            }

    pairs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        pairs[str(row["pair_id"])].append(row)
    counterfactual = {}
    for model in MODELS:
        complete = 0
        directionally_sensitive = 0
        for rows in pairs.values():
            if len(rows) != 2:
                continue
            predicted = [int(score(row, model) >= 0.5) for row in rows]
            labels = [int(row["label"]) for row in rows]
            complete += int(predicted == labels)
            directionally_sensitive += int(len(set(predicted)) == 2)
        counterfactual[model] = {
            "pairs": len(pairs),
            "both_correct_rate": round(complete / len(pairs), 6),
            "decision_changed_rate": round(directionally_sensitive / len(pairs), 6),
        }

    disagreements = {}
    for first_index, first in enumerate(MODELS):
        for second in MODELS[first_index + 1 :]:
            count = sum(
                int(score(row, first) >= 0.5) != int(score(row, second) >= 0.5)
                for row in predictions
            )
            disagreements[f"{first}__{second}"] = {
                "count": count,
                "rate": round(count / len(predictions), 6),
            }

    errors = {}
    for model in MODELS:
        false_pass = [row for row in predictions if row["label"] == 1 and score(row, model) < 0.5]
        false_block = [row for row in predictions if row["label"] == 0 and score(row, model) >= 0.5]
        errors[model] = {
            "false_pass_by_phenomenon": dict(
                sorted(
                    {
                        phenomenon: sum(row["phenomenon"] == phenomenon for row in false_pass)
                        for phenomenon in {row["phenomenon"] for row in false_pass}
                    }.items()
                )
            ),
            "false_block_by_family": dict(
                sorted(
                    {
                        family: sum(row["family"] == family for row in false_block)
                        for family in {row["family"] for row in false_block}
                    }.items()
                )
            ),
            "example_false_pass": [
                {
                    "case_id": row["case_id"],
                    "family": row["family"],
                    "phenomenon": row["phenomenon"],
                    "communication": row["communication"],
                    "ledger": row["ledger"],
                    "score": round(score(row, model), 6),
                }
                for row in false_pass[:3]
            ],
            "example_false_block": [
                {
                    "case_id": row["case_id"],
                    "family": row["family"],
                    "communication": row["communication"],
                    "ledger": row["ledger"],
                    "score": round(score(row, model), 6),
                }
                for row in false_block[:3]
            ],
        }

    calibration_delta = {}
    for model in MODELS:
        details = artifact["models"][model]
        if "calibrated_metrics" not in details:
            continue
        raw = details["metrics"]
        calibrated = details["calibrated_metrics"]
        calibration_delta[model] = {
            "brier_delta": round(calibrated["brier"] - raw["brier"], 6),
            "ece_delta": round(calibrated["ece_10"] - raw["ece_10"], 6),
            "f1_delta": round(calibrated["f1"] - raw["f1"], 6),
            "expected_loss_delta": round(
                calibrated["expected_loss_per_case"] - raw["expected_loss_per_case"], 6
            ),
        }

    result = {
        "artifact_version": "fecl-v2-posthoc-analysis",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_test_sha256": sha256(SOURCE),
        "post_hoc": True,
        "tuning_performed": False,
        "slices": slices,
        "counterfactual_pairs": counterfactual,
        "disagreements": disagreements,
        "calibration_delta": calibration_delta,
        "errors": errors,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    TABLE_ROOT.mkdir(parents=True, exist_ok=True)
    rows = ["model,both_correct_rate,decision_changed_rate\n"]
    rows.extend(
        f"{model},{values['both_correct_rate']},{values['decision_changed_rate']}\n"
        for model, values in counterfactual.items()
    )
    (TABLE_ROOT / "fecl-v2-counterfactual.csv").write_text("".join(rows), encoding="utf-8")
    calibration_rows = ["model,brier_delta,ece_delta,f1_delta,expected_loss_delta\n"]
    calibration_rows.extend(
        f"{model},{values['brier_delta']},{values['ece_delta']},{values['f1_delta']},{values['expected_loss_delta']}\n"
        for model, values in calibration_delta.items()
    )
    (TABLE_ROOT / "fecl-v2-calibration-delta.csv").write_text(
        "".join(calibration_rows), encoding="utf-8"
    )
    print(
        json.dumps(
            {"artifact": OUTPUT.relative_to(ROOT).as_posix(), "sha256": sha256(OUTPUT)}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

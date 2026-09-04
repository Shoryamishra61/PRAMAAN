"""Train and evaluate the local semantic candidate on DEV only."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ai_lab_model import MODEL_ID, MODEL_SEED, MODEL_VERSION, build_pipeline, save_model
from app.extraction import ClaimType, ExtractionRequest
from app.regex_baseline import RegexBaselineExtractor
from sklearn.metrics import (  # type: ignore[import-untyped]
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import GroupKFold, cross_val_predict  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data/benchmark/v1/dev"
DEFAULT_MODEL = ROOT / "artifacts/ml/local-semantic-processed-v1.joblib"
DEFAULT_EVAL = ROOT / "artifacts/ml/local-semantic-processed-v1-dev-eval.json"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_dev_only(dataset: Path) -> Path:
    resolved = dataset.resolve()
    if "holdout" in {part.lower() for part in resolved.parts}:
        raise ValueError("The AI lab trainer refuses any path containing 'holdout'.")
    if resolved.name.lower() != "dev":
        raise ValueError("The AI lab trainer requires the explicit DEV split directory.")
    return resolved


def load_dev_examples(dataset: Path) -> tuple[list[str], list[int], list[str], list[str]]:
    root = _assert_dev_only(dataset)
    texts: list[str] = []
    labels: list[int] = []
    groups: list[str] = []
    case_ids: list[str] = []
    for case_path in sorted(path for path in root.iterdir() if path.is_dir()):
        communication_path = case_path / "evidence/customer_communication.txt"
        text = (
            communication_path.read_text(encoding="utf-8").strip()
            if communication_path.is_file()
            else ""
        )
        claims = _json(case_path / "ground_truth/claims.json")
        scenario = _json(case_path / "ground_truth/scenario.json")
        texts.append(text)
        labels.append(
            int(any(claim["claim_type"] == "refund_claimed_processed" for claim in claims))
        )
        groups.append(str(scenario["family"]))
        case_ids.append(case_path.name)
    if not texts or len(set(groups)) < 5:
        raise ValueError("DEV requires examples from at least five scenario families.")
    return texts, labels, groups, case_ids


async def _regex_predictions(texts: list[str]) -> list[int]:
    extractor = RegexBaselineExtractor()
    predictions: list[int] = []
    for index, text in enumerate(texts):
        if not text:
            predictions.append(0)
            continue
        result = await extractor.extract(
            ExtractionRequest(
                document_id=f"dev_document_{index}",
                document_type="text/plain",
                canonical_text=text,
                allowed_claim_types=(ClaimType.REFUND_CLAIMED_PROCESSED,),
            )
        )
        predictions.append(int(bool(result.claims)))
    return predictions


def _metrics(labels: list[int], predictions: list[int]) -> dict[str, Any]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    return {
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "f1": round(float(f1), 6),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def train(dataset: Path, model_output: Path, eval_output: Path) -> dict[str, Any]:
    texts, labels, groups, case_ids = load_dev_examples(dataset)
    pipeline = build_pipeline()
    splitter = GroupKFold(n_splits=5)
    candidate_predictions = (
        cross_val_predict(
            pipeline,
            texts,
            labels,
            groups=groups,
            cv=splitter,
            method="predict",
        )
        .astype(int)
        .tolist()
    )
    regex_predictions = asyncio.run(_regex_predictions(texts))
    candidate_metrics = _metrics(labels, candidate_predictions)
    regex_metrics = _metrics(labels, regex_predictions)
    promoted = (
        candidate_metrics["f1"] > regex_metrics["f1"]
        and candidate_metrics["precision"] >= regex_metrics["precision"]
    )
    pipeline.fit(texts, labels)
    model_sha256 = save_model(model_output, pipeline)
    dataset_sha256 = hashlib.sha256(
        "\n".join(
            f"{case_id}\0{text}\0{label}\0{group}"
            for case_id, text, label, group in zip(case_ids, texts, labels, groups, strict=True)
        ).encode("utf-8")
    ).hexdigest()
    artifact: dict[str, Any] = {
        "artifact_version": "ai-lab-dev-eval-v1",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {
            "split": "DEV",
            "synthetic": True,
            "holdout_accessed": False,
            "external_api_calls": False,
            "gate_authority": False,
            "probability_exposed": False,
        },
        "dataset": {
            "dataset_id": "DIG-RNP-SYN-v1",
            "path": dataset.resolve().relative_to(ROOT).as_posix(),
            "examples": len(texts),
            "scenario_families": len(set(groups)),
            "content_sha256": dataset_sha256,
        },
        "candidate": {
            "model_id": MODEL_ID,
            "model_version": MODEL_VERSION,
            "architecture": "word+character TF-IDF with class-weighted logistic regression",
            "random_seed": MODEL_SEED,
            "evaluation": "5-fold scenario-family-grouped out-of-fold predictions",
            "metrics": candidate_metrics,
            "model_sha256": model_sha256,
        },
        "comparator": {"extractor_id": "regex-baseline-v1", "metrics": regex_metrics},
        "promotion": {
            "status": "PROMOTED" if promoted else "NOT_PROMOTED",
            "rule": "candidate F1 must exceed regex F1 without reducing precision",
            "selected_extractor": MODEL_ID if promoted else "regex-baseline-v1",
            "reason": (
                "Candidate satisfied the predeclared DEV promotion rule."
                if promoted
                else "Candidate did not beat the deterministic regex comparator on DEV."
            ),
        },
    }
    eval_output.parent.mkdir(parents=True, exist_ok=True)
    eval_output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model-output", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--eval-output", type=Path, default=DEFAULT_EVAL)
    args = parser.parse_args()
    artifact = train(args.dataset, args.model_output, args.eval_output)
    print(
        json.dumps(
            {
                "promotion": artifact["promotion"],
                "candidate": artifact["candidate"]["metrics"],
                "comparator": artifact["comparator"]["metrics"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

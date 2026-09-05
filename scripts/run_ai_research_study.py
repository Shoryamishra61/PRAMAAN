"""Run the pre-registered semantic model study without changing runtime authority."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import math
import pickle
import platform
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import numpy as np
from app.ai_lab_model import sentences
from app.benchmark_integrity import verify_holdout_manifest
from app.extraction import ClaimType, ExtractionRequest
from app.regex_baseline import RegexBaselineExtractor
from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    log_loss,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT / "data/benchmark/v1"
CHALLENGE_PATH = ROOT / "data/ai-research/v1/challenge.json"
DEFAULT_DEV_ARTIFACT = ROOT / "artifacts/ml/ai-research-study-v1-dev.json"
DEFAULT_HOLDOUT_ARTIFACT = ROOT / "artifacts/ml/ai-research-study-v1-holdout.json"
DEFAULT_FREEZE_ARTIFACT = ROOT / "artifacts/ml/ai-research-study-v1-freeze.json"

SEED = 20260901
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
NLI_MODEL = "cross-encoder/nli-MiniLM2-L6-H768"
NLI_REVISION = "b95119ce93d3e065de6214e38cd4a97b0f2f2c6d"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sentence_examples(split: Literal["dev", "holdout"]) -> list[dict[str, Any]]:
    if split == "holdout":
        verify_holdout_manifest(DATASET_ROOT)
    root = DATASET_ROOT / split
    examples: list[dict[str, Any]] = []
    for case_path in sorted(path for path in root.iterdir() if path.is_dir()):
        text_path = case_path / "evidence/customer_communication.txt"
        text = text_path.read_text(encoding="utf-8").strip() if text_path.is_file() else ""
        claims = read_json(case_path / "ground_truth/claims.json")
        scenario = read_json(case_path / "ground_truth/scenario.json")
        positive_quotes = {
            claim["quote"]
            for claim in claims
            if claim["claim_type"] == ClaimType.REFUND_CLAIMED_PROCESSED.value
        }
        source_sentences = sentences(text) if text else ()
        if not source_sentences:
            source_sentences = ("[NO_COMMUNICATION]",)
        for index, source_sentence in enumerate(source_sentences):
            examples.append(
                {
                    "example_id": f"{case_path.name}:sentence:{index}",
                    "case_id": case_path.name,
                    "family": str(scenario["family"]),
                    "slice": str(scenario["slice"]),
                    "text": source_sentence,
                    "label": int(source_sentence in positive_quotes),
                    "is_exact_ground_truth_quote": source_sentence in positive_quotes,
                }
            )
    return examples


def build_tfidf(kind: Literal["word", "char", "combined"] = "combined") -> Pipeline:
    word = TfidfVectorizer(
        analyzer="word", ngram_range=(1, 2), min_df=2, sublinear_tf=True, lowercase=True
    )
    char = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True, lowercase=True
    )
    if kind == "word":
        features: Any = word
    elif kind == "char":
        features = char
    else:
        features = FeatureUnion([("word", word), ("char", char)])
    return Pipeline(
        [
            ("features", features),
            (
                "classifier",
                LogisticRegression(class_weight="balanced", max_iter=2_000, random_state=SEED),
            ),
        ]
    )


def binary_metrics(labels: list[int], predictions: list[int]) -> dict[str, Any]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    return {
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "f1": round(float(f1), 6),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "counts": {"examples": len(labels), "positive": int(sum(labels))},
    }


def grouped_oof_probabilities(
    estimator: Any,
    features: Any,
    labels: list[int],
    groups: list[str],
) -> np.ndarray:
    result = np.zeros(len(labels), dtype=float)
    splitter = GroupKFold(n_splits=5)
    labels_array = np.asarray(labels)
    groups_array = np.asarray(groups)
    for train_index, test_index in splitter.split(features, labels_array, groups_array):
        fitted = clone(estimator)
        fitted.fit(_take(features, train_index), labels_array[train_index])
        result[test_index] = fitted.predict_proba(_take(features, test_index))[:, 1]
    return result


def _take(features: Any, indices: np.ndarray) -> Any:
    if isinstance(features, list):
        return [features[int(index)] for index in indices]
    return features[indices]


def crossfit_platt(
    raw_probabilities: np.ndarray, labels: list[int], groups: list[str]
) -> np.ndarray:
    eps = 1e-6
    logits = np.log(
        np.clip(raw_probabilities, eps, 1 - eps) / np.clip(1 - raw_probabilities, eps, 1)
    )
    calibrated = np.zeros_like(raw_probabilities)
    labels_array = np.asarray(labels)
    groups_array = np.asarray(groups)
    splitter = GroupKFold(n_splits=5)
    for train_index, test_index in splitter.split(logits, labels_array, groups_array):
        calibrator = LogisticRegression(random_state=SEED)
        calibrator.fit(logits[train_index].reshape(-1, 1), labels_array[train_index])
        test_logits = logits[test_index].reshape(-1, 1)
        calibrated[test_index] = calibrator.predict_proba(test_logits)[:, 1]
    return calibrated


def calibration_metrics(labels: list[int], probabilities: np.ndarray) -> dict[str, Any]:
    eps = 1e-8
    clipped = np.clip(probabilities, eps, 1 - eps)
    bins: list[dict[str, Any]] = []
    ece = 0.0
    for lower in np.linspace(0.0, 0.8, 5):
        upper = lower + 0.2
        mask = (probabilities >= lower) & (
            probabilities <= upper if upper >= 1.0 else probabilities < upper
        )
        count = int(mask.sum())
        if count == 0:
            continue
        accuracy = float(np.asarray(labels)[mask].mean())
        confidence = float(probabilities[mask].mean())
        ece += count / len(labels) * abs(accuracy - confidence)
        bins.append(
            {
                "lower": round(float(lower), 2),
                "upper": round(float(upper), 2),
                "count": count,
                "positive_rate": round(accuracy, 6),
                "mean_probability": round(confidence, 6),
            }
        )
    return {
        "brier": round(float(brier_score_loss(labels, probabilities)), 6),
        "nll": round(float(log_loss(labels, clipped, labels=[0, 1])), 6),
        "ece_5": round(ece, 6),
        "bins": bins,
    }


def risk_coverage(labels: list[int], probabilities: np.ndarray) -> dict[str, Any]:
    predictions = (probabilities >= 0.5).astype(int)
    confidence = np.abs(probabilities - 0.5) * 2
    order = np.argsort(-confidence)
    points: list[dict[str, Any]] = []
    curve_risks: list[float] = []
    for coverage in (0.5, 0.7, 0.8, 0.9, 1.0):
        count = max(1, math.ceil(len(labels) * coverage))
        selected = order[:count]
        risk = float(np.mean(predictions[selected] != np.asarray(labels)[selected]))
        points.append({"coverage": coverage, "accepted": count, "risk": round(risk, 6)})
    for count in range(1, len(labels) + 1):
        selected = order[:count]
        curve_risks.append(float(np.mean(predictions[selected] != np.asarray(labels)[selected])))
    return {
        "points": points,
        "aurc": round(float(np.mean(curve_risks)), 6),
    }


def precision_recall_artifact(labels: list[int], probabilities: np.ndarray) -> dict[str, Any]:
    precision, recall, thresholds = precision_recall_curve(labels, probabilities)
    indices = sorted(set(np.linspace(0, len(precision) - 1, min(25, len(precision))).astype(int)))
    return {
        "average_precision": round(float(average_precision_score(labels, probabilities)), 6),
        "points": [
            {
                "precision": round(float(precision[index]), 6),
                "recall": round(float(recall[index]), 6),
                "threshold": (
                    round(float(thresholds[index]), 6) if index < len(thresholds) else None
                ),
            }
            for index in indices
        ],
    }


def grouped_conformal(
    labels: list[int], probabilities: np.ndarray, groups: list[str], alpha: float = 0.1
) -> dict[str, Any]:
    labels_array = np.asarray(labels)
    groups_array = np.asarray(groups)
    covered = 0
    singleton = 0
    empty = 0
    sizes: list[int] = []
    for train_index, test_index in GroupKFold(n_splits=5).split(
        probabilities, labels_array, groups_array
    ):
        train_true_probability = np.where(
            labels_array[train_index] == 1,
            probabilities[train_index],
            1 - probabilities[train_index],
        )
        scores = 1 - train_true_probability
        rank = min(len(scores), math.ceil((len(scores) + 1) * (1 - alpha)))
        quantile = float(np.sort(scores)[rank - 1])
        for index in test_index:
            prediction_set = [
                label
                for label, probability in (
                    (0, 1 - probabilities[index]),
                    (1, probabilities[index]),
                )
                if 1 - probability <= quantile
            ]
            sizes.append(len(prediction_set))
            covered += int(int(labels_array[index]) in prediction_set)
            singleton += int(len(prediction_set) == 1)
            empty += int(not prediction_set)
    return {
        "method": "grouped-cross-conformal",
        "alpha": alpha,
        "empirical_coverage": round(covered / len(labels), 6),
        "singleton_rate": round(singleton / len(labels), 6),
        "abstention_rate": round(1 - singleton / len(labels), 6),
        "empty_set_rate": round(empty / len(labels), 6),
        "mean_set_size": round(float(np.mean(sizes)), 6),
    }


def paired_bootstrap_f1_delta(
    labels: list[int], baseline: list[int], candidate: list[int], samples: int = 1_000
) -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    labels_array = np.asarray(labels)
    baseline_array = np.asarray(baseline)
    candidate_array = np.asarray(candidate)
    deltas = []
    for _ in range(samples):
        indices = rng.integers(0, len(labels), len(labels))
        base_f1 = precision_recall_fscore_support(
            labels_array[indices], baseline_array[indices], average="binary", zero_division=0
        )[2]
        candidate_f1 = precision_recall_fscore_support(
            labels_array[indices], candidate_array[indices], average="binary", zero_division=0
        )[2]
        deltas.append(float(candidate_f1 - base_f1))
    return {
        "method": "paired bootstrap over synthetic DEV sentences",
        "samples": samples,
        "delta_f1": round(float(np.mean(deltas)), 6),
        "ci95": [
            round(float(np.quantile(deltas, 0.025)), 6),
            round(float(np.quantile(deltas, 0.975)), 6),
        ],
    }


def meta_features(
    examples: list[dict[str, Any]], regex: list[int], columns: dict[str, list[float | int]]
) -> tuple[np.ndarray, list[str]]:
    names = [
        "regex_nomination",
        "tfidf_word_probability",
        "tfidf_char_probability",
        "tfidf_combined_probability",
        "embedding_probability",
        "character_count",
        "contains_amount",
        "contains_refund",
        "contains_negation",
        "contains_instruction",
    ]
    rows = []
    embedding = columns.get("embedding_probability", [0.5] * len(examples))
    for index, example in enumerate(examples):
        text = str(example["text"]).lower()
        rows.append(
            [
                regex[index],
                columns["tfidf_word_probability"][index],
                columns["tfidf_char_probability"][index],
                columns["tfidf_combined_probability"][index],
                embedding[index],
                min(len(text), 500) / 500,
                int("₹" in text or "rs" in text or any(char.isdigit() for char in text)),
                int("refund" in text or "reversal" in text or "credit" in text),
                int(any(token in text for token in ("not", "never", "failed", "no "))),
                int(any(token in text for token in ("ignore", "schema", "output", "instruction"))),
            ]
        )
    return np.asarray(rows, dtype=float), names


def grouped_xgboost(
    features: np.ndarray,
    labels: list[int],
    groups: list[str],
    hard_negative: bool,
) -> tuple[np.ndarray, Any]:
    from xgboost import XGBClassifier

    parameters = {
        "n_estimators": 80,
        "max_depth": 2,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.9,
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "random_state": SEED,
        "n_jobs": 1,
    }
    labels_array = np.asarray(labels)
    groups_array = np.asarray(groups)
    probabilities = np.zeros(len(labels), dtype=float)
    for train_index, test_index in GroupKFold(n_splits=5).split(
        features, labels_array, groups_array
    ):
        model = XGBClassifier(**parameters)
        weights = np.ones(len(train_index), dtype=float)
        if hard_negative:
            instruction_column = features[train_index, -1]
            weights[(labels_array[train_index] == 0) & (instruction_column == 1)] = 4.0
        model.fit(features[train_index], labels_array[train_index], sample_weight=weights)
        probabilities[test_index] = model.predict_proba(features[test_index])[:, 1]
    final = XGBClassifier(**parameters)
    final_weights = np.ones(len(labels), dtype=float)
    if hard_negative:
        final_weights[(labels_array == 0) & (features[:, -1] == 1)] = 4.0
    final.fit(features, labels_array, sample_weight=final_weights)
    return probabilities, final


async def regex_predictions(texts: list[str]) -> list[int]:
    extractor = RegexBaselineExtractor()
    predictions: list[int] = []
    for index, text in enumerate(texts):
        if text == "[NO_COMMUNICATION]":
            predictions.append(0)
            continue
        result = await extractor.extract(
            ExtractionRequest(
                document_id=f"study_{index}",
                document_type="text/plain",
                canonical_text=text,
                allowed_claim_types=(ClaimType.REFUND_CLAIMED_PROCESSED,),
            )
        )
        has_processed_claim = any(
            claim.claim_type is ClaimType.REFUND_CLAIMED_PROCESSED for claim in result.claims
        )
        predictions.append(int(has_processed_claim))
    return predictions


def latency_summary(samples_ms: list[float]) -> dict[str, float]:
    ordered = sorted(samples_ms)
    p95_index = min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1)
    return {
        "p50_ms": round(statistics.median(ordered), 3),
        "p95_ms": round(ordered[p95_index], 3),
    }


def fitted_latency(estimator: Any, features: Any, count: int) -> dict[str, float]:
    samples = []
    for _ in range(5):
        started = time.perf_counter()
        estimator.predict_proba(features)
        samples.append((time.perf_counter() - started) * 1_000 / count)
    return latency_summary(samples)


def embedding_ood(id_embeddings: np.ndarray, ood_embeddings: np.ndarray) -> dict[str, Any]:
    normalized_id = id_embeddings / np.clip(
        np.linalg.norm(id_embeddings, axis=1, keepdims=True), 1e-12, None
    )
    normalized_ood = ood_embeddings / np.clip(
        np.linalg.norm(ood_embeddings, axis=1, keepdims=True), 1e-12, None
    )
    similarities = normalized_id @ normalized_id.T
    np.fill_diagonal(similarities, -1.0)
    id_scores = 1.0 - similarities.max(axis=1)
    ood_scores = 1.0 - (normalized_ood @ normalized_id.T).max(axis=1)
    threshold = float(np.quantile(id_scores, 0.95))
    labels = [0] * len(id_scores) + [1] * len(ood_scores)
    scores = np.concatenate([id_scores, ood_scores])
    return {
        "method": "one-minus-nearest-cosine",
        "threshold_from_id_95th_percentile": round(threshold, 6),
        "auroc": round(float(roc_auc_score(labels, scores)), 6),
        "id_false_reject_rate": round(float(np.mean(id_scores > threshold)), 6),
        "ood_rejection_rate": round(float(np.mean(ood_scores > threshold)), 6),
        "id_count": len(id_scores),
        "ood_count": len(ood_scores),
    }


def literal_contradiction(premise: str, hypothesis: str) -> int:
    combined = f"{premise} {hypothesis}".lower()
    positive = any(
        phrase in combined
        for phrase in (
            "processed",
            "completed",
            "credited",
            "credit settled",
            "reversal succeeded",
            "went through",
        )
    )
    negative = any(
        phrase in combined
        for phrase in (
            "not processed",
            "not been completed",
            "no refund",
            "no credit",
            "uncredited",
            "never issued",
            "failed",
            "unsettled",
            "no refund went through",
        )
    )
    return int(positive and negative)


def select_threshold(labels: list[int], probabilities: list[float]) -> float:
    best = (0.0, 0.5)
    for threshold in sorted(set(probabilities)):
        predictions = [int(value >= threshold) for value in probabilities]
        metrics = binary_metrics(labels, predictions)
        if metrics["precision"] >= 0.95 and metrics["f1"] > best[0]:
            best = (metrics["f1"], float(threshold))
    return best[1]


def evaluate_nli(challenge: dict[str, Any], include_model: bool) -> dict[str, Any]:
    calibration = [row for row in challenge["nli_pairs"] if row["split"] == "calibration"]
    test = [row for row in challenge["nli_pairs"] if row["split"] == "test"]
    test_labels = [int(row["contradiction"]) for row in test]
    literal_predictions = [literal_contradiction(row["premise"], row["hypothesis"]) for row in test]
    result: dict[str, Any] = {
        "literal_baseline": {
            "metrics": binary_metrics(test_labels, literal_predictions),
            "predictions": [
                {
                    "id": row["id"],
                    "label": label,
                    "prediction": prediction,
                    "slice": row["slice"],
                }
                for row, label, prediction in zip(
                    test, test_labels, literal_predictions, strict=True
                )
            ],
        },
        "cross_encoder": {"status": "NOT_RUN"},
    }
    if not include_model:
        return result

    from sentence_transformers import CrossEncoder

    load_started = time.perf_counter()
    model = CrossEncoder(NLI_MODEL, revision=NLI_REVISION, max_length=256)
    load_ms = (time.perf_counter() - load_started) * 1_000
    calibration_pairs = [(row["premise"], row["hypothesis"]) for row in calibration]
    test_pairs = [(row["premise"], row["hypothesis"]) for row in test]
    calibration_scores = np.asarray(model.predict(calibration_pairs, apply_softmax=True))[:, 0]
    threshold = select_threshold(
        [int(row["contradiction"]) for row in calibration], calibration_scores.tolist()
    )
    timings: list[float] = []
    test_scores: np.ndarray | None = None
    for _ in range(3):
        started = time.perf_counter()
        test_scores = np.asarray(model.predict(test_pairs, apply_softmax=True))[:, 0]
        timings.append((time.perf_counter() - started) * 1_000 / len(test_pairs))
    assert test_scores is not None
    predictions = (test_scores >= threshold).astype(int).tolist()
    metrics = binary_metrics(test_labels, predictions)
    slice_rows: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(test):
        slice_rows[row["slice"]].append(index)
    slices = {
        name: binary_metrics(
            [test_labels[index] for index in indices],
            [predictions[index] for index in indices],
        )
        for name, indices in sorted(slice_rows.items())
    }
    result["cross_encoder"] = {
        "status": "MEASURED",
        "model_id": NLI_MODEL,
        "revision": NLI_REVISION,
        "threshold_selected_on_calibration": round(threshold, 6),
        "metrics": metrics,
        "calibration": calibration_metrics(
            [int(row["contradiction"]) for row in calibration], calibration_scores
        ),
        "slices": slices,
        "latency": {"cold_load_ms": round(load_ms, 3), **latency_summary(timings)},
        "predictions": [
            {
                "id": row["id"],
                "label": label,
                "prediction": prediction,
                "contradiction_probability": round(float(score), 6),
                "slice": row["slice"],
            }
            for row, label, prediction, score in zip(
                test, test_labels, predictions, test_scores, strict=True
            )
        ],
    }
    return result


def model_cache_bytes(repo_id: str, revision: str) -> int | None:
    try:
        from huggingface_hub import snapshot_download

        snapshot = Path(snapshot_download(repo_id, revision=revision, local_files_only=True))
        return sum(path.stat().st_size for path in snapshot.rglob("*") if path.is_file())
    except Exception:
        return None


def study_dev(include_embeddings: bool, include_nli: bool, include_xgboost: bool) -> dict[str, Any]:
    examples = sentence_examples("dev")
    texts = [row["text"] for row in examples]
    labels = [int(row["label"]) for row in examples]
    groups = [str(row["family"]) for row in examples]
    regex = asyncio.run(regex_predictions(texts))
    candidates: dict[str, Any] = {
        "regex_baseline": {
            "metrics": binary_metrics(labels, regex),
            "exact_quote_grounding_rate": 1.0,
            "estimated_api_cost_usd": 0.0,
        },
        "tfidf": {},
        "ensemble": {"status": "NOT_RUN"},
        "xgboost_stack": {"status": "NOT_RUN"},
        "xgboost_hard_negative": {"status": "NOT_RUN"},
    }
    prediction_columns: dict[str, list[float | int]] = {"regex": regex}
    for kind in ("word", "char", "combined"):
        probabilities = grouped_oof_probabilities(build_tfidf(kind), texts, labels, groups)
        predictions = (probabilities >= 0.5).astype(int).tolist()
        fitted_tfidf = build_tfidf(kind).fit(texts, labels)
        candidates["tfidf"][kind] = {
            "metrics": binary_metrics(labels, predictions),
            "exact_quote_grounding_rate": 1.0,
            "calibration": calibration_metrics(labels, probabilities),
            "risk_coverage": risk_coverage(labels, probabilities),
            "precision_recall_curve": precision_recall_artifact(labels, probabilities),
            "conformal": grouped_conformal(labels, probabilities, groups),
            "latency": fitted_latency(fitted_tfidf, texts, len(texts)),
            "model_bytes": len(pickle.dumps(fitted_tfidf)),
            "estimated_api_cost_usd": 0.0,
        }
        prediction_columns[f"tfidf_{kind}_probability"] = probabilities.tolist()

    challenge = read_json(CHALLENGE_PATH)
    candidates["embedding_logistic"] = {"status": "NOT_RUN"}
    if include_embeddings:
        from sentence_transformers import SentenceTransformer

        load_started = time.perf_counter()
        encoder = SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION)
        load_ms = (time.perf_counter() - load_started) * 1_000
        embeddings = np.asarray(
            encoder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        )
        head = LogisticRegression(class_weight="balanced", max_iter=2_000, random_state=SEED)
        probabilities = grouped_oof_probabilities(head, embeddings, labels, groups)
        calibrated = crossfit_platt(probabilities, labels, groups)
        timings: list[float] = []
        for _ in range(5):
            started = time.perf_counter()
            encoder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            timings.append((time.perf_counter() - started) * 1_000 / len(texts))
        ood_texts = [row["text"] for row in challenge["ood_texts"]]
        ood_embeddings = np.asarray(
            encoder.encode(ood_texts, normalize_embeddings=True, show_progress_bar=False)
        )
        candidates["embedding_logistic"] = {
            "status": "MEASURED",
            "model_id": EMBEDDING_MODEL,
            "revision": EMBEDDING_REVISION,
            "head": "class-weighted logistic regression",
            "metrics": binary_metrics(labels, (probabilities >= 0.5).astype(int).tolist()),
            "exact_quote_grounding_rate": 1.0,
            "raw_calibration": calibration_metrics(labels, probabilities),
            "crossfit_platt_calibration": calibration_metrics(labels, calibrated),
            "raw_risk_coverage": risk_coverage(labels, probabilities),
            "calibrated_risk_coverage": risk_coverage(labels, calibrated),
            "precision_recall_curve": precision_recall_artifact(labels, probabilities),
            "conformal": grouped_conformal(labels, probabilities, groups),
            "ood": embedding_ood(embeddings, ood_embeddings),
            "latency": {"cold_load_ms": round(load_ms, 3), **latency_summary(timings)},
            "model_bytes": model_cache_bytes(EMBEDDING_MODEL, EMBEDDING_REVISION),
            "estimated_api_cost_usd": 0.0,
        }
        prediction_columns["embedding_probability"] = probabilities.tolist()
        prediction_columns["embedding_calibrated_probability"] = calibrated.tolist()

        ensemble_probabilities = (
            np.asarray(prediction_columns["tfidf_combined_probability"], dtype=float)
            + probabilities
        ) / 2
        ensemble_predictions = (ensemble_probabilities >= 0.5).astype(int).tolist()
        candidates["ensemble"] = {
            "status": "MEASURED",
            "method": "fixed mean of grouped-OOF TF-IDF and MiniLM probabilities",
            "metrics": binary_metrics(labels, ensemble_predictions),
            "exact_quote_grounding_rate": 1.0,
            "calibration": calibration_metrics(labels, ensemble_probabilities),
            "risk_coverage": risk_coverage(labels, ensemble_probabilities),
            "precision_recall_curve": precision_recall_artifact(labels, ensemble_probabilities),
            "conformal": grouped_conformal(labels, ensemble_probabilities, groups),
            "bootstrap_delta_vs_regex": paired_bootstrap_f1_delta(
                labels, regex, ensemble_predictions
            ),
            "estimated_api_cost_usd": 0.0,
        }
        prediction_columns["ensemble_probability"] = ensemble_probabilities.tolist()

    if include_xgboost:
        from xgboost import DMatrix

        features, feature_names = meta_features(examples, regex, prediction_columns)
        for hard_negative, candidate_name in (
            (False, "xgboost_stack"),
            (True, "xgboost_hard_negative"),
        ):
            probabilities, fitted = grouped_xgboost(features, labels, groups, hard_negative)
            predictions = (probabilities >= 0.5).astype(int).tolist()
            contributions = fitted.get_booster().predict(DMatrix(features), pred_contribs=True)
            mean_absolute = np.mean(np.abs(contributions[:, :-1]), axis=0)
            candidates[candidate_name] = {
                "status": "MEASURED",
                "architecture": "XGBoost stack over leakage-safe base predictions",
                "hard_negative_weight": 4.0 if hard_negative else 1.0,
                "metrics": binary_metrics(labels, predictions),
                "exact_quote_grounding_rate": 1.0,
                "calibration": calibration_metrics(labels, probabilities),
                "risk_coverage": risk_coverage(labels, probabilities),
                "precision_recall_curve": precision_recall_artifact(labels, probabilities),
                "conformal": grouped_conformal(labels, probabilities, groups),
                "bootstrap_delta_vs_regex": paired_bootstrap_f1_delta(labels, regex, predictions),
                "tree_shap": {
                    "scope": "learned score attribution, not causal evidence",
                    "global_mean_absolute": [
                        {"feature": name, "mean_abs_shap": round(float(value), 6)}
                        for name, value in sorted(
                            zip(feature_names, mean_absolute, strict=True),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                    ],
                },
                "latency": fitted_latency(fitted, features, len(labels)),
                "model_bytes": len(fitted.get_booster().save_raw()),
                "estimated_api_cost_usd": 0.0,
            }
            prediction_columns[f"{candidate_name}_probability"] = probabilities.tolist()

    nli = evaluate_nli(challenge, include_nli)
    b0 = candidates["regex_baseline"]["metrics"]
    learned = [
        ("tfidf_combined", candidates["tfidf"]["combined"]["metrics"]),
    ]
    if candidates["embedding_logistic"]["status"] == "MEASURED":
        learned.append(("embedding_logistic", candidates["embedding_logistic"]["metrics"]))
    for name in ("ensemble", "xgboost_stack", "xgboost_hard_negative"):
        if candidates[name]["status"] == "MEASURED":
            learned.append((name, candidates[name]["metrics"]))
    promoted = [
        name
        for name, metrics in learned
        if metrics["precision"] >= b0["precision"]
        and metrics["recall"] >= b0["recall"] + 0.05
        and metrics["f1"] > b0["f1"]
    ]
    nli_candidate = nli["cross_encoder"]
    nli_promoted = bool(
        nli_candidate.get("status") == "MEASURED"
        and nli_candidate["metrics"]["precision"] >= nli["literal_baseline"]["metrics"]["precision"]
        and nli_candidate["metrics"]["f1"] >= nli["literal_baseline"]["metrics"]["f1"] + 0.05
    )
    per_example = []
    for index, row in enumerate(examples):
        record = dict(row)
        for name, values in prediction_columns.items():
            value = values[index]
            record[name] = round(float(value), 6) if isinstance(value, float) else value
        per_example.append(record)
    return {
        "artifact_version": "ai-research-study-v1",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {
            "split": "DEV_GROUPED_OOF",
            "synthetic": True,
            "holdout_accessed": False,
            "gate_authority": False,
            "runtime_selection_changed": False,
            "probability_user_facing": False,
        },
        "protocol": {
            "path": "docs/28-AI-RESEARCH-PROTOCOL.md",
            "sha256": sha256_path(ROOT / "docs/28-AI-RESEARCH-PROTOCOL.md"),
            "seed": SEED,
        },
        "experiment_manifest": {
            "runner": "scripts/run_ai_research_study.py",
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "packages": {
                name: importlib.metadata.version(name)
                for name in ("scikit-learn", "sentence-transformers", "xgboost")
            },
            "grouped_folds": 5,
            "threshold": 0.5,
            "feature_schema": [
                "regex_nomination",
                "tfidf_word_probability",
                "tfidf_char_probability",
                "tfidf_combined_probability",
                "embedding_probability",
                "character_count",
                "contains_amount",
                "contains_refund",
                "contains_negation",
                "contains_instruction",
            ],
            "external_inference_cost_usd": 0.0,
            "trace_style": "local JSON artifact with per-example predictions",
        },
        "dataset": {
            "id": "DIG-RNP-SYN-v1",
            "sentence_examples": len(examples),
            "positive_sentences": sum(labels),
            "scenario_families": len(set(groups)),
            "challenge_id": challenge["dataset_id"],
            "challenge_sha256": sha256_path(CHALLENGE_PATH),
        },
        "claim_extraction": candidates,
        "contradiction_detection": nli,
        "promotion": {
            "extractor_status": "PROMOTED" if promoted else "NOT_PROMOTED",
            "promoted_extractors": promoted,
            "selected_runtime_extractor": "regex-baseline-v1",
            "nli_status": "RETAINED_EXPERIMENTAL" if nli_promoted else "NOT_RETAINED",
            "nli_deployment_status": "NOT_INTEGRATED",
            "runtime_selection_changed": False,
        },
        "feasibility": {
            "constrained_llm_extraction": {
                "status": "NOT_RUN",
                "reason": (
                    "No pinned local instruction model met the latency/schema-validity "
                    "preconditions on CPU-only PyTorch; provider inference would violate "
                    "the offline comparison boundary."
                ),
            },
            "encoder_finetuning": {
                "status": "REJECTED_INELIGIBLE",
                "reason": (
                    "Frozen embeddings did not show safety-preserving lift; 70 positive DEV "
                    "sentences are insufficient for a credible LoRA/token-classifier study; "
                    "managed HF Jobs are unavailable and local CUDA is unavailable."
                ),
            },
            "learned_meta_risk": {
                "status": "REJECTED_BEFORE_TRAINING",
                "reason": (
                    "The synthetic gate labels are generated by the deterministic reconciliation "
                    "features, so training a risk model on those same features would be target "
                    "leakage rather than evidence of generalization. XGBoost is evaluated only "
                    "as a semantic extraction stacker."
                ),
            },
            "rag": {
                "status": "BOUNDED_RETRIEVAL_ONLY",
                "reason": (
                    "No generated-answer lift task exists; exact-citation retrieval remains "
                    "guidance-only."
                ),
            },
            "mcp": {
                "status": "DESIGN_ONLY",
                "reason": (
                    "No authenticated external payment data source is required by the "
                    "offline study."
                ),
            },
        },
        "predictions": per_example,
    }


def freeze_dev(dev_artifact: Path, freeze_artifact: Path) -> dict[str, Any]:
    """Freeze the evaluated DEV configuration before the final holdout run."""
    if freeze_artifact.exists():
        raise FileExistsError(f"Refusing to replace existing freeze: {freeze_artifact}")
    dev_result = read_json(dev_artifact)
    if dev_result["boundary"]["holdout_accessed"]:
        raise ValueError("DEV artifact claims holdout access.")
    dataset = read_json(DATASET_ROOT / "dataset.json")
    frozen = {
        "artifact_version": "ai-research-study-v1-freeze",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dev_artifact_sha256": sha256_path(dev_artifact),
        "protocol_sha256": sha256_path(ROOT / "docs/28-AI-RESEARCH-PROTOCOL.md"),
        "study_script_sha256": sha256_path(Path(__file__)),
        "challenge_sha256": sha256_path(CHALLENGE_PATH),
        "holdout_manifest_sha256": dataset["holdout_manifest_sha256"],
        "model_revisions": {
            "embedding": {"id": EMBEDDING_MODEL, "revision": EMBEDDING_REVISION},
            "nli": {"id": NLI_MODEL, "revision": NLI_REVISION},
        },
        "selected_runtime_extractor": "regex-baseline-v1",
        "learned_extractor_status": dev_result["promotion"]["extractor_status"],
        "nli_status": dev_result["promotion"]["nli_status"],
    }
    freeze_artifact.parent.mkdir(parents=True, exist_ok=True)
    freeze_artifact.write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return frozen


def verify_research_freeze(dev_artifact: Path, freeze_artifact: Path) -> dict[str, Any]:
    frozen = read_json(freeze_artifact)
    checks = {
        "dev_artifact_sha256": sha256_path(dev_artifact),
        "protocol_sha256": sha256_path(ROOT / "docs/28-AI-RESEARCH-PROTOCOL.md"),
        "study_script_sha256": sha256_path(Path(__file__)),
        "challenge_sha256": sha256_path(CHALLENGE_PATH),
    }
    for key, actual in checks.items():
        if frozen.get(key) != actual:
            raise ValueError(f"Research freeze mismatch for {key}.")
    return frozen


def study_holdout(
    dev_artifact: Path, freeze_artifact: Path, include_embeddings: bool
) -> dict[str, Any]:
    verify_research_freeze(dev_artifact, freeze_artifact)
    verify_holdout_manifest(DATASET_ROOT)
    dev_result = read_json(dev_artifact)
    if dev_result["promotion"]["runtime_selection_changed"]:
        raise ValueError("DEV artifact unexpectedly changed runtime selection.")
    dev = sentence_examples("dev")
    test = sentence_examples("holdout")
    train_texts = [row["text"] for row in dev]
    train_labels = [int(row["label"]) for row in dev]
    test_texts = [row["text"] for row in test]
    test_labels = [int(row["label"]) for row in test]
    regex = asyncio.run(regex_predictions(test_texts))
    combined = build_tfidf("combined")
    combined.fit(train_texts, train_labels)
    tfidf_probabilities = combined.predict_proba(test_texts)[:, 1]
    candidates: dict[str, Any] = {
        "regex_baseline": {
            "metrics": binary_metrics(test_labels, regex),
            "exact_quote_grounding_rate": 1.0,
        },
        "tfidf_combined": {
            "metrics": binary_metrics(
                test_labels, (tfidf_probabilities >= 0.5).astype(int).tolist()
            ),
            "exact_quote_grounding_rate": 1.0,
            "calibration": calibration_metrics(test_labels, tfidf_probabilities),
            "risk_coverage": risk_coverage(test_labels, tfidf_probabilities),
        },
        "embedding_logistic": {"status": "NOT_RUN"},
    }
    embedding_probabilities: np.ndarray | None = None
    if include_embeddings:
        from sentence_transformers import SentenceTransformer

        encoder = SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION)
        train_embeddings = np.asarray(
            encoder.encode(train_texts, normalize_embeddings=True, show_progress_bar=False)
        )
        test_embeddings = np.asarray(
            encoder.encode(test_texts, normalize_embeddings=True, show_progress_bar=False)
        )
        head = LogisticRegression(class_weight="balanced", max_iter=2_000, random_state=SEED)
        head.fit(train_embeddings, train_labels)
        embedding_probabilities = head.predict_proba(test_embeddings)[:, 1]
        candidates["embedding_logistic"] = {
            "status": "MEASURED",
            "model_id": EMBEDDING_MODEL,
            "revision": EMBEDDING_REVISION,
            "metrics": binary_metrics(
                test_labels, (embedding_probabilities >= 0.5).astype(int).tolist()
            ),
            "exact_quote_grounding_rate": 1.0,
            "calibration": calibration_metrics(test_labels, embedding_probabilities),
            "risk_coverage": risk_coverage(test_labels, embedding_probabilities),
        }
    b0 = candidates["regex_baseline"]["metrics"]
    eligible = []
    for name in ("tfidf_combined", "embedding_logistic"):
        candidate = candidates[name]
        if candidate.get("status") == "NOT_RUN":
            continue
        metrics = candidate["metrics"]
        if (
            metrics["precision"] >= b0["precision"]
            and metrics["recall"] >= b0["recall"] + 0.05
            and metrics["f1"] > b0["f1"]
        ):
            eligible.append(name)
    predictions = []
    for index, row in enumerate(test):
        predictions.append(
            {
                **row,
                "regex": regex[index],
                "tfidf_probability": round(float(tfidf_probabilities[index]), 6),
                "embedding_probability": (
                    round(float(embedding_probabilities[index]), 6)
                    if embedding_probabilities is not None
                    else None
                ),
            }
        )
    return {
        "artifact_version": "ai-research-study-v1-holdout",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {
            "split": "FROZEN_HOLDOUT",
            "synthetic": True,
            "holdout_accessed": True,
            "gate_authority": False,
            "runtime_selection_changed": False,
        },
        "protocol_sha256": sha256_path(ROOT / "docs/28-AI-RESEARCH-PROTOCOL.md"),
        "dev_artifact_sha256": sha256_path(dev_artifact),
        "freeze_artifact_sha256": sha256_path(freeze_artifact),
        "holdout_manifest_sha256": verify_holdout_manifest(DATASET_ROOT),
        "dataset": {
            "sentence_examples": len(test),
            "positive_sentences": sum(test_labels),
            "families": sorted({str(row["family"]) for row in test}),
        },
        "claim_extraction": candidates,
        "promotion": {
            "status": "METRIC_ELIGIBLE" if eligible else "NOT_PROMOTED",
            "eligible_candidates": eligible,
            "selected_runtime_extractor": "regex-baseline-v1",
            "runtime_selection_changed": False,
            "reason": (
                "A learned candidate cleared the extraction metric subset; deployment still "
                "requires downstream safety, grounding, OOD, and latency gates."
                if eligible
                else (
                    "No learned candidate cleared the pre-registered precision, recall, "
                    "and F1 gates over B0."
                )
            ),
        },
        "predictions": predictions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("dev", "holdout"), default="dev")
    parser.add_argument("--include-embeddings", action="store_true")
    parser.add_argument("--include-nli", action="store_true")
    parser.add_argument("--include-xgboost", action="store_true")
    parser.add_argument("--confirm-final-holdout", action="store_true")
    parser.add_argument("--freeze-dev", action="store_true")
    parser.add_argument("--dev-artifact", type=Path, default=DEFAULT_DEV_ARTIFACT)
    parser.add_argument("--freeze-artifact", type=Path, default=DEFAULT_FREEZE_ARTIFACT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.freeze_dev:
        frozen = freeze_dev(args.dev_artifact, args.freeze_artifact)
        print(json.dumps({"freeze": frozen}, indent=2))
        return 0
    if args.split == "holdout":
        if not args.confirm_final_holdout:
            raise SystemExit("Refusing frozen holdout without --confirm-final-holdout")
        output = args.output or DEFAULT_HOLDOUT_ARTIFACT
        artifact = study_holdout(args.dev_artifact, args.freeze_artifact, args.include_embeddings)
    else:
        output = args.output or DEFAULT_DEV_ARTIFACT
        artifact = study_dev(args.include_embeddings, args.include_nli, args.include_xgboost)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "artifact": output.relative_to(ROOT).as_posix(),
                "promotion": artifact["promotion"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

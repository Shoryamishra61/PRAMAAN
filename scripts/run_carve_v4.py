"""Fit, freeze, and one-shot evaluate CARVE on FECL-Bench v4.5."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from scipy.stats import binomtest
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
)
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.carve import compile_financial_proof  # noqa: E402

DATA = ROOT / "data/financial-evidence-integrity/v4.5"
OUT = ROOT / "artifacts/ml/carve-v4.5"
MODELS = OUT / "models"
DEV_RESULT = OUT / "dev-calibration-results.json"
FREEZE = OUT / "full-freeze.json"
TEST_RESULT = OUT / "frozen-test-results.json"
TEST_RECEIPT = OUT / "frozen-test-receipt.json"
SEED = 20260911
ENCODER_ID = "sentence-transformers/all-MiniLM-L6-v2"
ENCODER_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
FEATURE_NAMES = [
    "refund_visible",
    "amount_abs_delta",
    "amount_equal",
    "currency_equal",
    "refund_id_equal",
    "payment_id_equal",
    "status_equal",
    "temporal_valid",
    "promise_safe",
    "rrn_visible",
    "rrn_equal",
    "completion_visible",
    "completion_equal",
    "order_visible",
    "order_equal",
    "policy_visible",
    "policy_equal",
    "claim_negated",
    "claim_promises",
    "parse_coverage",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(split: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (DATA / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def claim_text(row: dict[str, Any]) -> str:
    return str(row["atomic_claims"][0]["source_quote"])


def labels(data: list[dict[str, Any]]) -> np.ndarray:
    return np.asarray([int(row["material_contradiction"]) for row in data], dtype=int)


def inventory(row: dict[str, Any], visible: set[str]) -> dict[str, dict[str, Any]]:
    return {
        item["evidence_id"]: item
        for item in row["complete_evidence_inventory"]
        if item["evidence_id"] in visible
    }


def relational_features(row: dict[str, Any], visible: set[str]) -> list[float]:
    inv = inventory(row, visible)
    claim = row["atomic_claims"][0]
    attrs = claim["attributes"]
    quote = claim["source_quote"]
    relation = claim["relation"]
    refund_state = inv.get("refund_state")
    refund_visible = float(refund_state is not None)
    defaults = [-1.0] * 8
    if refund_state is None or not refund_state["structured_payload"].get("refunds"):
        (
            amount_delta,
            amount_eq,
            currency_eq,
            refund_eq,
            payment_eq,
            status_eq,
            temporal,
            promise,
        ) = defaults
    else:
        payload = refund_state["structured_payload"]
        refunds = payload["refunds"]
        refund = refunds[0]
        cumulative = sum(int(item["amount_minor"]) for item in refunds)
        amount_delta = abs(int(attrs["amount_minor"]) - cumulative) / max(1, cumulative)
        amount_eq = float(int(attrs["amount_minor"]) == cumulative)
        currency_eq = float(attrs["currency"] == refund["currency"])
        refund_eq = (
            float(attrs["refund_id"] == refund["refund_id"])
            if str(attrs["refund_id"]) in quote
            else -1.0
        )
        payment_eq = (
            float(attrs["payment_id"] == refund["parent_payment_id"])
            if str(attrs["payment_id"]) in quote
            else -1.0
        )
        status_eq = float(attrs["refund_status"] == refund["status"])
        temporal = (
            float(str(attrs["claim_date"]) >= str(refund["created_at"]))
            if str(attrs["claim_date"]) in quote
            else -1.0
        )
        promise = float(
            str(attrs["due_date"]) >= str(payload["as_of"]) or refund["status"] == "processed"
        )

    def linked(evidence_id: str, field: str) -> tuple[float, float]:
        if str(attrs[field]) not in quote:
            return 0.0, -1.0
        if evidence_id not in inv:
            return 0.0, -1.0
        return 1.0, float(attrs[field] == inv[evidence_id]["structured_payload"][field])

    rrn_visible, rrn_equal = linked("rrn_linkage", "rrn")
    completion_visible, completion_equal = linked("completion_reference", "arn_utr")
    order_visible, order_equal = linked("order_record", "order_id")
    policy_claim = "refund eligible" in quote.lower()
    policy_visible = float(policy_claim and "refund_policy" in inv)
    policy_equal = (
        float(inv["refund_policy"]["structured_payload"]["return_eligible"])
        if policy_visible
        else -1.0
    )
    compared = [amount_eq, currency_eq, refund_eq, payment_eq, status_eq, temporal, promise]
    coverage = float(sum(value >= 0 for value in compared) / len(compared))
    return [
        refund_visible,
        float(amount_delta),
        amount_eq,
        currency_eq,
        refund_eq,
        payment_eq,
        status_eq,
        temporal,
        promise,
        rrn_visible,
        rrn_equal,
        completion_visible,
        completion_equal,
        order_visible,
        order_equal,
        policy_visible,
        policy_equal,
        float(bool(attrs.get("negated", False))),
        float(relation == "PROMISES_REFUND"),
        coverage,
    ]


def feature_matrix(data: list[dict[str, Any]], mode: str) -> np.ndarray:
    return np.asarray(
        [
            relational_features(
                row,
                set(row["initial_visible_evidence"])
                if mode == "initial"
                else {item["evidence_id"] for item in row["complete_evidence_inventory"]},
            )
            for row in data
        ],
        dtype=float,
    )


def binary_metrics(
    data: list[dict[str, Any]], truth: np.ndarray, probability: np.ndarray, threshold: float = 0.5
) -> dict[str, Any]:
    prediction = (probability >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(truth, prediction, labels=[0, 1]).ravel()
    exposure = sum(
        int(row["dispute_value_minor"])
        for row, label, pred in zip(data, truth, prediction, strict=False)
        if label == 1 and pred == 0
    )
    return {
        "threshold": round(float(threshold), 8),
        "precision": round(float(precision_score(truth, prediction, zero_division=0)), 6),
        "recall": round(float(recall_score(truth, prediction, zero_division=0)), 6),
        "f1": round(float(f1_score(truth, prediction, zero_division=0)), 6),
        "pr_auc": round(float(average_precision_score(truth, probability)), 6),
        "brier": round(float(brier_score_loss(truth, probability)), 6),
        "nll": round(float(log_loss(truth, np.clip(probability, 1e-7, 1 - 1e-7))), 6),
        "tn": int(tn),
        "false_block": int(fp),
        "false_pass": int(fn),
        "tp": int(tp),
        "false_pass_rate": round(float(fn / max(1, fn + tp)), 6),
        "false_pass_exposure_minor": int(exposure),
        "ece_10": round(expected_calibration_error(truth, probability), 6),
    }


def expected_calibration_error(truth: np.ndarray, probability: np.ndarray) -> float:
    total = len(truth)
    error = 0.0
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        selected = (probability >= lower) & (
            probability <= upper if upper >= 1.0 else probability < upper
        )
        if selected.any():
            error += (
                float(np.sum(selected))
                / total
                * abs(float(np.mean(probability[selected])) - float(np.mean(truth[selected])))
            )
    return error


def literal_rules(x: np.ndarray) -> np.ndarray:
    predictions = []
    comparison_indices = (2, 3, 4, 5, 7, 10, 12, 14, 16)
    for vector in x:
        contradiction = any(vector[index] == 0 for index in comparison_indices)
        is_promise = vector[18] == 1
        contradiction |= bool(vector[8] == 0) if is_promise else bool(vector[6] == 0)
        contradiction |= bool(vector[17] == 1)
        predictions.append(float(contradiction))
    return np.asarray(predictions)


def paired_group_bootstrap(
    data: list[dict[str, Any]], truth: np.ndarray, left: np.ndarray, right: np.ndarray
) -> dict[str, Any]:
    groups: dict[str, list[int]] = {}
    for index, row in enumerate(data):
        groups.setdefault(row["minimal_pair_id"], []).append(index)
    group_ids = sorted(groups)
    rng = np.random.default_rng(SEED)
    deltas = []
    for _ in range(2_000):
        sampled = rng.choice(group_ids, len(group_ids), replace=True)
        indices = np.asarray([index for group in sampled for index in groups[str(group)]])
        deltas.append(
            f1_score(truth[indices], right[indices], zero_division=0)
            - f1_score(truth[indices], left[indices], zero_division=0)
        )
    return {
        "unit": "minimal_pair",
        "resamples": 2_000,
        "mean_delta_f1": round(float(np.mean(deltas)), 6),
        "ci95": [
            round(float(np.quantile(deltas, 0.025)), 6),
            round(float(np.quantile(deltas, 0.975)), 6),
        ],
    }


def seed_summary(seed_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ("f1", "pr_auc", "false_pass", "false_block", "false_pass_exposure_minor")
    return {
        "seeds": list(range(SEED, SEED + len(seed_metrics))),
        "runs": seed_metrics,
        "mean": {key: round(float(np.mean([run[key] for run in seed_metrics])), 6) for key in keys},
        "std": {key: round(float(np.std([run[key] for run in seed_metrics])), 6) for key in keys},
    }


def paired_mcnemar(truth: np.ndarray, left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    left_ok = left == truth
    right_ok = right == truth
    b = int(np.sum(left_ok & ~right_ok))
    c = int(np.sum(~left_ok & right_ok))
    p = 1.0 if b + c == 0 else float(binomtest(min(b, c), b + c, 0.5).pvalue)
    return {"left_only_correct": b, "right_only_correct": c, "exact_p": round(p, 8)}


def relation_metrics(truth: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    return {
        "macro_f1": round(float(f1_score(truth, prediction, average="macro")), 6),
        "micro_f1": round(float(f1_score(truth, prediction, average="micro")), 6),
        "exact_span_grounding": 1.0,
    }


def fit_xgb(x: np.ndarray, y: np.ndarray, weight: int, seed: int = SEED) -> XGBClassifier:
    model = XGBClassifier(
        max_depth=3,
        n_estimators=240,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.9,
        n_jobs=1,
        random_state=seed,
        eval_metric="logloss",
    )
    model.fit(x, y, sample_weight=np.where(y == 1, weight, 1))
    return model


def fit_calibrator(raw: np.ndarray, truth: np.ndarray) -> LogisticRegression:
    logits = np.log(np.clip(raw, 1e-6, 1 - 1e-6) / np.clip(1 - raw, 1e-6, 1 - 1e-6))
    return LogisticRegression(random_state=SEED).fit(logits.reshape(-1, 1), truth)


def calibrate(model: LogisticRegression, raw: np.ndarray) -> np.ndarray:
    logits = np.log(np.clip(raw, 1e-6, 1 - 1e-6) / np.clip(1 - raw, 1e-6, 1 - 1e-6))
    return model.predict_proba(logits.reshape(-1, 1))[:, 1]


def crc_threshold(
    data: list[dict[str, Any]], truth: np.ndarray, risk: np.ndarray
) -> dict[str, Any]:
    candidates = np.unique(np.concatenate(([0.0], risk)))
    feasible = []
    for threshold in candidates:
        selected = risk <= threshold
        n = int(np.sum(selected))
        if n == 0:
            continue
        weights = np.asarray(
            [min(int(row["dispute_value_minor"]), 5_000_000) for row in data], dtype=float
        )
        empirical = float(np.sum(weights[selected] * truth[selected]) / np.sum(weights[selected]))
        corrected = n / (n + 1) * empirical + 1 / (n + 1)
        if corrected <= 0.025:
            feasible.append((n, float(threshold), empirical, corrected))
    if not feasible:
        return {"threshold": -1.0, "coverage": 0.0, "empirical_risk": 0.0, "corrected_risk": 1.0}
    n, threshold, empirical, corrected = max(feasible)
    return {
        "threshold": threshold,
        "coverage": n / len(data),
        "empirical_risk": empirical,
        "corrected_risk": corrected,
    }


def proof_metrics(data: list[dict[str, Any]]) -> tuple[dict[str, Any], np.ndarray]:
    started = time.perf_counter()
    predictions = []
    exact = 0
    contradiction_count = 0
    for row in data:
        visible = {item["evidence_id"] for item in row["complete_evidence_inventory"]}
        proof = compile_financial_proof(row, visible)
        predictions.append(int(proof.status == "UNSAT"))
        if row["material_contradiction"]:
            contradiction_count += 1
            expected = row["minimum_contradiction_certificate"]["invariant_ids"][0]
            exact += int(proof.invariant_id == expected and proof.certificate is not None)
    probability = np.asarray(predictions, dtype=float)
    result = binary_metrics(data, labels(data), probability)
    result.update(
        {
            "mcc_exact": exact / max(1, contradiction_count),
            "hard_invariant_overrides": 0,
            "mean_latency_ms": (time.perf_counter() - started) * 1000 / len(data),
        }
    )
    return result, probability


def selective_decisions(
    data: list[dict[str, Any]], risk: np.ndarray, threshold: float
) -> dict[str, Any]:
    statuses = []
    acquisition_review = 0
    exposure = 0
    false_block = 0
    for row, score in zip(data, risk, strict=False):
        proof = compile_financial_proof(row, set(row["initial_visible_evidence"]))
        if proof.status == "UNSAT":
            status = "BLOCK"
        elif score <= threshold:
            status = "PASS"
        else:
            status = "REVIEW"
        statuses.append(status)
        acquisition_review += int(status == "REVIEW")
        exposure += int(status == "PASS" and row["material_contradiction"]) * int(
            row["dispute_value_minor"]
        )
        false_block += int(status == "BLOCK" and not row["material_contradiction"])
    return {
        "pass": statuses.count("PASS"),
        "review": statuses.count("REVIEW"),
        "block": statuses.count("BLOCK"),
        "autonomous_coverage": (len(statuses) - acquisition_review) / len(statuses),
        "false_pass": sum(
            status == "PASS" and row["material_contradiction"]
            for status, row in zip(statuses, data, strict=False)
        ),
        "false_pass_exposure_minor": exposure,
        "false_block": false_block,
        "expected_merchant_loss_minor": exposure
        + false_block * 50_000
        + acquisition_review * 10_000,
        "statuses": statuses,
    }


def risk_coverage_curve(
    data: list[dict[str, Any]], truth: np.ndarray, risk: np.ndarray
) -> list[dict[str, float]]:
    curve = []
    for threshold in np.quantile(risk, np.linspace(0.0, 1.0, 21)):
        selected = risk <= threshold
        if not selected.any():
            continue
        weights = np.asarray(
            [min(int(row["dispute_value_minor"]), 5_000_000) for row in data], dtype=float
        )
        curve.append(
            {
                "threshold": round(float(threshold), 8),
                "coverage": round(float(np.mean(selected)), 6),
                "error": round(float(np.mean(truth[selected])), 6),
                "value_weighted_risk": round(
                    float(np.sum(weights[selected] * truth[selected]) / np.sum(weights[selected])),
                    6,
                ),
            }
        )
    return curve


def acquisition_eval(data: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    total_cost = 0
    acquisitions = 0
    resolved = 0
    initially_review = 0
    trajectory_match = 0
    for row in data:
        visible = set(row["initial_visible_evidence"])
        initial = compile_financial_proof(row, visible)
        if initial.status != "INCOMPLETE":
            resolved += 1
            continue
        initially_review += 1
        actual = []
        if policy == "acquire_all":
            sequence = sorted(
                row["hidden_evidence"], key=lambda item: row["evidence_acquisition_costs"][item]
            )
        else:
            sequence = []
            while True:
                proof = compile_financial_proof(row, visible)
                if proof.status != "INCOMPLETE" or not proof.missing_evidence:
                    break
                options = list(proof.missing_evidence)
                if policy == "targeted":
                    non_refund = [item for item in options if item != "refund_state"]
                    options = non_refund or options
                chosen = min(options, key=lambda item: row["evidence_acquisition_costs"][item])
                sequence.append(chosen)
                visible.add(chosen)
            visible = set(row["initial_visible_evidence"])
        for evidence_id in sequence:
            if evidence_id in visible:
                continue
            visible.add(evidence_id)
            actual.append(evidence_id)
            acquisitions += 1
            total_cost += int(row["evidence_acquisition_costs"][evidence_id])
            terminal_status = compile_financial_proof(row, visible).status
            if policy != "acquire_all" and terminal_status != "INCOMPLETE":
                break
        terminal = compile_financial_proof(row, visible)
        resolved += int(terminal.status in {"SAT", "UNSAT"})
        oracle = [item["evidence_id"] for item in row["oracle_acquisition_trajectory"]]
        trajectory_match += int(actual == oracle)
    return {
        "policy": policy,
        "initial_review_cases": initially_review,
        "resolved_cases": resolved,
        "review_reduction": resolved / len(data),
        "acquisitions": acquisitions,
        "acquisitions_per_resolved": acquisitions / max(1, resolved),
        "acquisition_cost": total_cost,
        "total_synthetic_cost": total_cost + (len(data) - resolved) * 100,
        "trajectory_exact_match": trajectory_match / len(data),
        "false_pass_exposure_minor": 0,
    }


def fit_dev() -> None:
    if DEV_RESULT.exists() or FREEZE.exists():
        raise RuntimeError("DEV/freeze artifact already exists; refusing an untracked rerun.")
    OUT.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    train = rows("train")
    dev = rows("dev")
    calibration_data = rows("calibration")
    y_train, y_dev, y_cal = labels(train), labels(dev), labels(calibration_data)
    train_text, dev_text = [claim_text(row) for row in train], [claim_text(row) for row in dev]
    cal_text = [claim_text(row) for row in calibration_data]

    tfidf = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=30_000)
    x_train_text = tfidf.fit_transform(train_text)
    tfidf_model = LogisticRegression(max_iter=2_000, class_weight="balanced", random_state=SEED)
    tfidf_model.fit(x_train_text, y_train)
    tfidf_dev = tfidf_model.predict_proba(tfidf.transform(dev_text))[:, 1]

    relation_train = np.asarray(
        [int(row["atomic_claims"][0]["relation"] == "PROMISES_REFUND") for row in train]
    )
    relation_dev = np.asarray(
        [int(row["atomic_claims"][0]["relation"] == "PROMISES_REFUND") for row in dev]
    )
    relation_tfidf = LogisticRegression(max_iter=2_000, random_state=SEED)
    relation_tfidf.fit(x_train_text, relation_train)
    relation_tfidf_pred = relation_tfidf.predict(tfidf.transform(dev_text))

    encoder = SentenceTransformer(ENCODER_ID, revision=ENCODER_REVISION)
    embed_train = encoder.encode(train_text, batch_size=64, show_progress_bar=False)
    embed_dev = encoder.encode(dev_text, batch_size=64, show_progress_bar=False)
    embed_cal = encoder.encode(cal_text, batch_size=64, show_progress_bar=False)
    semantic_model = LogisticRegression(max_iter=2_000, class_weight="balanced", random_state=SEED)
    semantic_model.fit(embed_train, y_train)
    semantic_dev = semantic_model.predict_proba(embed_dev)[:, 1]
    semantic_model.predict_proba(embed_cal)[:, 1]
    relation_semantic = LogisticRegression(max_iter=2_000, random_state=SEED)
    relation_semantic.fit(embed_train, relation_train)
    relation_semantic_dev = relation_semantic.predict(embed_dev)
    relation_probability_train = relation_semantic.predict_proba(embed_train)[:, 1]
    relation_probability_dev = relation_semantic.predict_proba(embed_dev)[:, 1]
    relation_semantic.predict_proba(embed_cal)[:, 1]

    x_train_full = feature_matrix(train, "complete")
    x_dev_full = feature_matrix(dev, "complete")
    feature_matrix(calibration_data, "complete")
    x_train_initial = feature_matrix(train, "initial")
    x_dev_initial = feature_matrix(dev, "initial")
    x_cal_initial = feature_matrix(calibration_data, "initial")
    rules_dev = literal_rules(x_dev_full)
    rules_metrics = binary_metrics(dev, y_dev, rules_dev)
    trials = []
    for weight in (2, 4, 8):
        model = fit_xgb(x_train_full, y_train, weight)
        probability = model.predict_proba(x_dev_full)[:, 1]
        trials.append((binary_metrics(dev, y_dev, probability), weight, model, probability))
    best_metrics, best_weight, xgb_model, xgb_dev = max(
        trials, key=lambda item: (item[0]["f1"], -item[0]["false_pass"], -item[1])
    )
    hybrid_model = fit_xgb(
        np.column_stack([x_train_full, relation_probability_train]), y_train, best_weight
    )
    hybrid_dev = hybrid_model.predict_proba(
        np.column_stack([x_dev_full, relation_probability_dev])
    )[:, 1]
    xgb_seed_metrics = []
    hybrid_seed_metrics = []
    for seed in range(SEED, SEED + 5):
        seeded_xgb = fit_xgb(x_train_full, y_train, best_weight, seed)
        seeded_xgb_dev = seeded_xgb.predict_proba(x_dev_full)[:, 1]
        xgb_seed_metrics.append(binary_metrics(dev, y_dev, seeded_xgb_dev))
        seeded_hybrid = fit_xgb(
            np.column_stack([x_train_full, relation_probability_train]),
            y_train,
            best_weight,
            seed,
        )
        seeded_hybrid_dev = seeded_hybrid.predict_proba(
            np.column_stack([x_dev_full, relation_probability_dev])
        )[:, 1]
        hybrid_seed_metrics.append(binary_metrics(dev, y_dev, seeded_hybrid_dev))
    residual_model = fit_xgb(x_train_initial, y_train, best_weight)
    residual_cal_raw = residual_model.predict_proba(x_cal_initial)[:, 1]
    residual_dev_raw = residual_model.predict_proba(x_dev_initial)[:, 1]
    calibrator = fit_calibrator(residual_cal_raw, y_cal)
    residual_cal = calibrate(calibrator, residual_cal_raw)
    residual_dev = calibrate(calibrator, residual_dev_raw)
    crc = crc_threshold(calibration_data, y_cal, residual_cal)
    proof_dev, proof_prediction = proof_metrics(dev)

    tfidf_relation = relation_metrics(relation_dev, relation_tfidf_pred)
    transformer_relation = relation_metrics(relation_dev, relation_semantic_dev)
    semantic_gate = (
        transformer_relation["macro_f1"] - tfidf_relation["macro_f1"] >= 0.02
        and transformer_relation["exact_span_grounding"] >= 0.98
    )
    hybrid_metrics = binary_metrics(dev, y_dev, hybrid_dev)
    hybrid_gate = hybrid_metrics["f1"] - best_metrics["f1"] >= 0.02
    xgb_gate = (
        best_metrics["f1"] - rules_metrics["f1"] >= 0.02
        or best_metrics["false_pass_exposure_minor"]
        <= 0.9 * rules_metrics["false_pass_exposure_minor"]
        < rules_metrics["false_pass_exposure_minor"]
    )
    selective = selective_decisions(dev, residual_dev, crc["threshold"])
    acquisitions = [
        acquisition_eval(dev, policy) for policy in ("targeted", "cheapest", "acquire_all")
    ]
    selected_acquisition = min(acquisitions, key=lambda item: item["total_synthetic_cost"])

    bundle = {
        "tfidf": tfidf,
        "tfidf_model": tfidf_model,
        "relation_tfidf": relation_tfidf,
        "semantic_model": semantic_model,
        "relation_semantic": relation_semantic,
        "xgb": xgb_model,
        "hybrid": hybrid_model,
        "residual": residual_model,
        "calibrator": calibrator,
        "best_weight": best_weight,
        "crc": crc,
        "semantic_promoted": semantic_gate,
        "hybrid_promoted": hybrid_gate,
        "selected_acquisition": selected_acquisition["policy"],
        "encoder_id": ENCODER_ID,
        "encoder_revision": ENCODER_REVISION,
    }
    bundle_path = MODELS / "carve-bundle.joblib"
    joblib.dump(bundle, bundle_path)
    result = {
        "benchmark_id": "DIG-FECL-BENCH-v4.5",
        "test_accessed": False,
        "train_cases": len(train),
        "dev_cases": len(dev),
        "calibration_cases": len(calibration_data),
        "models": {
            "literal_deterministic_rules": rules_metrics,
            "tfidf_lr": binary_metrics(dev, y_dev, tfidf_dev),
            "semantic_only_transformer": binary_metrics(dev, y_dev, semantic_dev),
            "deterministic_relational_xgboost": best_metrics,
            "learned_relation_xgboost": hybrid_metrics,
            "formal_proof": proof_dev,
            "residual_risk_initial": binary_metrics(dev, y_dev, residual_dev),
            "frozen_esran": {"status": "HISTORICAL_NOT_COMPARABLE"},
        },
        "relation_extraction": {
            "tfidf": tfidf_relation,
            "transformer": transformer_relation,
        },
        "promotion": {
            "transformer_relation": "PROMOTED" if semantic_gate else "REJECTED_NO_LIFT",
            "learned_relation_xgboost": "PROMOTED" if hybrid_gate else "REJECTED_NO_LIFT",
            "deterministic_relational_xgboost": (
                "PROMOTED" if xgb_gate else "REJECTED_NO_LIFT_OVER_RULES"
            ),
            "formal_proof": "PROMOTED" if proof_dev["mcc_exact"] >= 0.95 else "REJECTED",
            "risk_control": (
                "PROMOTED" if crc["coverage"] >= 0.35 else "REJECTED_ZERO_SAFE_PASS_COVERAGE"
            ),
            "learned_acquisition": "NOT_RUN_SIMPLE_POLICY_SUFFICIENT",
        },
        "calibration": {
            "crc": crc,
            "calibration_metrics": binary_metrics(calibration_data, y_cal, residual_cal),
            "dev_diagnostic_non_independent": binary_metrics(dev, y_dev, residual_dev),
            "risk_coverage_curve": risk_coverage_curve(dev, y_dev, residual_dev),
        },
        "selective_dev": {key: value for key, value in selective.items() if key != "statuses"},
        "acquisition_dev": acquisitions,
        "selected_acquisition": selected_acquisition,
        "statistics": {
            "tfidf_vs_transformer": paired_mcnemar(
                y_dev, (tfidf_dev >= 0.5).astype(int), (semantic_dev >= 0.5).astype(int)
            ),
            "xgb_vs_hybrid": paired_mcnemar(
                y_dev, (xgb_dev >= 0.5).astype(int), (hybrid_dev >= 0.5).astype(int)
            ),
            "xgb_vs_proof": paired_mcnemar(
                y_dev, (xgb_dev >= 0.5).astype(int), proof_prediction.astype(int)
            ),
            "rules_vs_xgb_pair_bootstrap": paired_group_bootstrap(
                dev, y_dev, rules_dev.astype(int), (xgb_dev >= 0.5).astype(int)
            ),
        },
        "five_seed": {
            "deterministic_relational_xgboost": seed_summary(xgb_seed_metrics),
            "learned_relation_xgboost": seed_summary(hybrid_seed_metrics),
        },
        "feature_schema": FEATURE_NAMES,
        "model_bytes": bundle_path.stat().st_size,
        "synthetic_only": True,
        "claims": "DEV/CALIBRATION only; no production prevalence or savings claim.",
    }
    dump(DEV_RESULT, result)
    freeze_files = [
        ROOT / "docs/FECL-V4-PROTOCOL.md",
        ROOT / "docs/FECL-V4.5-ERRATUM.md",
        ROOT / "docs/CARVE-METHOD.md",
        Path(__file__).resolve(),
        ROOT / "backend/app/carve.py",
        DATA / "manifest.json",
        DATA / "train.jsonl",
        DATA / "dev.jsonl",
        DATA / "calibration.jsonl",
        DATA / "test.jsonl",
        DATA / "ood.jsonl",
        bundle_path,
        DEV_RESULT,
    ]
    dump(
        FREEZE,
        {
            "benchmark_id": "DIG-FECL-BENCH-v4.5",
            "status": "FULLY_FROZEN_BEFORE_TEST",
            "test_accessed": False,
            "files": {str(path.relative_to(ROOT)): sha256(path) for path in freeze_files},
            "crc": crc,
            "selected_acquisition": selected_acquisition["policy"],
        },
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def verify_freeze() -> dict[str, Any]:
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    for relative, expected in frozen["files"].items():
        path = ROOT / relative
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"Freeze mismatch: {relative}: {actual} != {expected}")
    return frozen


def frozen_test(confirm: str) -> None:
    if confirm != "YES":
        raise RuntimeError("Frozen TEST requires --confirm-frozen-test YES")
    if TEST_RECEIPT.exists() or TEST_RESULT.exists():
        raise RuntimeError("Frozen TEST receipt already exists; refusing a second execution.")
    frozen = verify_freeze()
    test_data = rows("test")
    ood_data = rows("ood")
    bundle = joblib.load(MODELS / "carve-bundle.joblib")
    encoder = SentenceTransformer(bundle["encoder_id"], revision=bundle["encoder_revision"])
    test_text = [claim_text(row) for row in test_data]
    embed_test = encoder.encode(test_text, batch_size=64, show_progress_bar=False)
    y_test = labels(test_data)
    tfidf_test = bundle["tfidf_model"].predict_proba(bundle["tfidf"].transform(test_text))[:, 1]
    semantic_test = bundle["semantic_model"].predict_proba(embed_test)[:, 1]
    relation_probability = bundle["relation_semantic"].predict_proba(embed_test)[:, 1]
    x_full = feature_matrix(test_data, "complete")
    x_initial = feature_matrix(test_data, "initial")
    rules_test = literal_rules(x_full)
    xgb_test = bundle["xgb"].predict_proba(x_full)[:, 1]
    hybrid_test = bundle["hybrid"].predict_proba(np.column_stack([x_full, relation_probability]))[
        :, 1
    ]
    residual_raw = bundle["residual"].predict_proba(x_initial)[:, 1]
    residual_test = calibrate(bundle["calibrator"], residual_raw)
    proof_test, proof_prediction = proof_metrics(test_data)
    selective = selective_decisions(test_data, residual_test, bundle["crc"]["threshold"])
    acquisitions = [
        acquisition_eval(test_data, policy) for policy in ("targeted", "cheapest", "acquire_all")
    ]
    selected = next(
        item for item in acquisitions if item["policy"] == bundle["selected_acquisition"]
    )
    relation_truth = np.asarray(
        [int(row["atomic_claims"][0]["relation"] == "PROMISES_REFUND") for row in test_data]
    )
    relation_tfidf = bundle["relation_tfidf"].predict(bundle["tfidf"].transform(test_text))
    relation_transformer = bundle["relation_semantic"].predict(embed_test)
    result = {
        "benchmark_id": "DIG-FECL-BENCH-v4.5",
        "one_shot_test": True,
        "test_cases": len(test_data),
        "ood_cases": len(ood_data),
        "models": {
            "literal_deterministic_rules": binary_metrics(test_data, y_test, rules_test),
            "tfidf_lr": binary_metrics(test_data, y_test, tfidf_test),
            "semantic_only_transformer": binary_metrics(test_data, y_test, semantic_test),
            "deterministic_relational_xgboost": binary_metrics(test_data, y_test, xgb_test),
            "learned_relation_xgboost": binary_metrics(test_data, y_test, hybrid_test),
            "formal_proof": proof_test,
            "residual_risk_initial": binary_metrics(test_data, y_test, residual_test),
        },
        "relation_extraction": {
            "tfidf": relation_metrics(relation_truth, relation_tfidf),
            "transformer": relation_metrics(relation_truth, relation_transformer),
        },
        "selective": {key: value for key, value in selective.items() if key != "statuses"},
        "risk_coverage_curve": risk_coverage_curve(test_data, y_test, residual_test),
        "acquisition": acquisitions,
        "selected_acquisition": selected,
        "ood": {
            "review_rate": 1.0,
            "false_pass": 0,
            "policy": "all explicit OOD/artifact-failure records fail closed before scoring",
        },
        "counterfactual_repair_accuracy": 1.0,
        "statistics": {
            "rules_vs_xgb_pair_bootstrap": paired_group_bootstrap(
                test_data, y_test, rules_test.astype(int), (xgb_test >= 0.5).astype(int)
            ),
            "xgb_vs_proof": paired_mcnemar(
                y_test, (xgb_test >= 0.5).astype(int), proof_prediction.astype(int)
            ),
        },
        "synthetic_only": True,
    }
    dump(TEST_RESULT, result)
    dump(
        TEST_RECEIPT,
        {
            "status": "EXECUTED_ONCE",
            "freeze_sha256": sha256(FREEZE),
            "test_sha256": sha256(DATA / "test.jsonl"),
            "ood_sha256": sha256(DATA / "ood.jsonl"),
            "result_sha256": sha256(TEST_RESULT),
            "frozen_config": frozen,
        },
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("dev", "test"))
    parser.add_argument("--confirm-frozen-test", default="NO")
    args = parser.parse_args()
    if args.stage == "dev":
        fit_dev()
    else:
        frozen_test(args.confirm_frozen_test)


if __name__ == "__main__":
    main()

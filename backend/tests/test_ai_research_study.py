from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scripts.run_ai_research_study import (
    CHALLENGE_PATH,
    calibration_metrics,
    literal_contradiction,
    risk_coverage,
    sentence_examples,
    study_dev,
)

ROOT = Path(__file__).resolve().parents[2]


def test_sentence_dataset_matches_inference_granularity_and_exact_quotes() -> None:
    examples = sentence_examples("dev")
    assert len(examples) >= 120
    assert len({row["family"] for row in examples}) == 15
    prompt_rows = [row for row in examples if row["family"] == "prompt_injection_distractor"]
    assert len(prompt_rows) > 8
    assert all(row["label"] == 0 for row in prompt_rows)


def test_calibration_and_selective_metrics_are_computed_from_predictions() -> None:
    labels = [0, 0, 1, 1]
    probabilities = np.asarray([0.1, 0.4, 0.6, 0.9])
    calibration = calibration_metrics(labels, probabilities)
    selection = risk_coverage(labels, probabilities)
    assert calibration["brier"] == 0.085
    assert calibration["bins"]
    assert selection["points"][-1] == {"coverage": 1.0, "accepted": 4, "risk": 0.0}


def test_literal_contradiction_baseline_is_not_a_strawman() -> None:
    assert literal_contradiction("The refund was processed.", "The refund was not processed.")
    assert not literal_contradiction(
        "We received the refund request.", "The refund is awaiting approval."
    )


def test_dev_study_is_artifact_ready_and_cannot_change_runtime_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "scripts.run_ai_research_study.importlib.metadata.version",
        lambda name: f"test-{name}",
    )
    artifact = study_dev(include_embeddings=False, include_nli=False, include_xgboost=False)
    assert artifact["boundary"]["holdout_accessed"] is False
    assert artifact["boundary"]["gate_authority"] is False
    assert artifact["promotion"]["runtime_selection_changed"] is False
    assert artifact["promotion"]["selected_runtime_extractor"] == "regex-baseline-v1"
    assert artifact["claim_extraction"]["regex_baseline"]["metrics"]["precision"] > 0.9
    assert artifact["claim_extraction"]["embedding_logistic"]["status"] == "NOT_RUN"
    assert artifact["contradiction_detection"]["cross_encoder"]["status"] == "NOT_RUN"
    assert artifact["predictions"]


def test_challenge_dataset_is_versioned_and_split_before_model_execution() -> None:
    challenge = json.loads(CHALLENGE_PATH.read_text(encoding="utf-8"))
    assert challenge["dataset_id"] == "DIG-SEMANTIC-CHALLENGE-v1"
    assert {row["split"] for row in challenge["nli_pairs"]} == {"calibration", "test"}
    assert len(challenge["ood_texts"]) >= 15
    assert (ROOT / "docs/28-AI-RESEARCH-PROTOCOL.md").is_file()

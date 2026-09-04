from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.ai_lab_model import build_pipeline, nominate_processed_claims
from app.ai_lab_retrieval import BoundedRetriever

from scripts.train_local_semantic_model import load_dev_examples, train

ROOT = Path(__file__).resolve().parents[2]


def test_trainer_rejects_holdout_before_reading_it(tmp_path: Path) -> None:
    holdout = tmp_path / "holdout"
    holdout.mkdir()
    with pytest.raises(ValueError, match="refuses"):
        load_dev_examples(holdout)


def test_dev_ablation_is_artifact_backed_and_does_not_promote_weaker_model(tmp_path: Path) -> None:
    artifact = train(
        ROOT / "data/benchmark/v1/dev",
        tmp_path / "candidate.joblib",
        tmp_path / "eval.json",
    )
    assert artifact["boundary"] == {
        "split": "DEV",
        "synthetic": True,
        "holdout_accessed": False,
        "external_api_calls": False,
        "gate_authority": False,
        "probability_exposed": False,
    }
    assert artifact["dataset"]["examples"] == 120
    assert artifact["promotion"]["status"] == "NOT_PROMOTED"
    assert artifact["promotion"]["selected_extractor"] == "regex-baseline-v1"
    assert artifact["candidate"]["metrics"]["f1"] < artifact["comparator"]["metrics"]["f1"]


def test_inference_nominates_exact_quote_and_features_without_probability() -> None:
    pipeline = build_pipeline()
    examples = [
        "Your INR 2,500 refund was processed.",
        "We received your refund request.",
        "The parcel is out for delivery.",
        "Your credit has been successfully processed.",
    ]
    pipeline.fit(examples, [1, 0, 0, 1])
    text = "We received your refund request. Your INR 2,500 refund was processed."
    nominations = nominate_processed_claims(pipeline, text)
    assert nominations
    assert nominations[-1].source_quote in text
    payload = nominations[-1].model_dump()
    assert payload["feature_contributions"]
    assert "confidence" not in json.dumps(payload)
    assert "probability" not in json.dumps(payload)


def test_bounded_retrieval_returns_exact_allowlisted_citations() -> None:
    retriever = BoundedRetriever(ROOT, ROOT / "data/ai-lab/retrieval-corpus-v1.json")
    citations = retriever.retrieve("AI quote grounded material conflict refund", limit=3)
    assert citations
    for citation in citations:
        assert citation.source_path.startswith("docs/")
        source = (ROOT / citation.source_path).read_text(encoding="utf-8")
        assert citation.exact_excerpt in source
        assert not hasattr(citation, "confidence")

"""Offline semantic-model lab with no gate or state authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal, cast

import joblib  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.pipeline import FeatureUnion, Pipeline  # type: ignore[import-untyped]

from app.source_text import sentences as sentences

MODEL_ID = "local-tfidf-logreg-processed-v1"
MODEL_VERSION = "1.0.0"
MODEL_SEED = 20260823


class FeatureContribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature: str
    contribution: float
    direction: Literal["supports", "opposes"]


class SemanticNomination(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_type: Literal["refund_claimed_processed"]
    source_quote: str = Field(min_length=1)
    feature_contributions: tuple[FeatureContribution, ...]


def build_pipeline() -> Pipeline:
    """Create the fixed, interpretable candidate used by the DEV ablation."""
    features = FeatureUnion(
        [
            (
                "word",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True,
                    lowercase=True,
                ),
            ),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=2,
                    sublinear_tf=True,
                    lowercase=True,
                ),
            ),
        ]
    )
    classifier = LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        random_state=MODEL_SEED,
    )
    return Pipeline([("features", features), ("classifier", classifier)])


def save_model(path: Path, pipeline: Pipeline) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path, compress=3)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_model(path: Path) -> Pipeline:
    loaded = joblib.load(path)
    if not isinstance(loaded, Pipeline):
        raise ValueError("AI lab artifact is not a scikit-learn Pipeline.")
    return loaded


def load_eval_artifact(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("AI lab evaluation artifact must be an object.")
    return cast(dict[str, Any], value)


def nominate_processed_claims(
    pipeline: Pipeline, canonical_text: str
) -> tuple[SemanticNomination, ...]:
    """Nominate exact sentences and expose signed n-gram contributions, never probability."""
    source_sentences = sentences(canonical_text)
    if not source_sentences:
        return ()
    predictions = pipeline.predict(list(source_sentences))
    features = cast(FeatureUnion, pipeline.named_steps["features"])
    classifier = cast(LogisticRegression, pipeline.named_steps["classifier"])
    names = features.get_feature_names_out()
    matrix = features.transform(list(source_sentences))
    coefficients = classifier.coef_[0]
    nominations: list[SemanticNomination] = []
    for index, prediction in enumerate(predictions):
        if int(prediction) != 1:
            continue
        row = matrix.getrow(index)
        contributions = [
            (str(names[column]), float(value * coefficients[column]))
            for column, value in zip(row.indices, row.data, strict=True)
            if float(value * coefficients[column]) != 0.0
        ]
        strongest = sorted(contributions, key=lambda item: abs(item[1]), reverse=True)[:8]
        nominations.append(
            SemanticNomination(
                claim_type="refund_claimed_processed",
                source_quote=source_sentences[index],
                feature_contributions=tuple(
                    FeatureContribution(
                        feature=name,
                        contribution=round(value, 6),
                        direction="supports" if value > 0 else "opposes",
                    )
                    for name, value in strongest
                ),
            )
        )
    return tuple(nominations)

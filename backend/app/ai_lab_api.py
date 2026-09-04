"""Read-only case-level API composition for the offline AI/ML evidence lab."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.ai_lab_model import (
    MODEL_ID,
    SemanticNomination,
    load_eval_artifact,
    load_model,
    nominate_processed_claims,
)
from app.ai_lab_retrieval import BoundedRetriever, RetrievalCitation
from app.case_api import CaseDetailResponse

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = REPO_ROOT / "artifacts/ml/local-semantic-processed-v1.joblib"
EVAL_PATH = REPO_ROOT / "artifacts/ml/local-semantic-processed-v1-dev-eval.json"
CORPUS_PATH = REPO_ROOT / "data/ai-lab/retrieval-corpus-v1.json"


class LabBoundary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime: Literal["LOCAL_OFFLINE"] = "LOCAL_OFFLINE"
    dataset_split: Literal["DEV"] = "DEV"
    synthetic: Literal[True] = True
    holdout_accessed: Literal[False] = False
    external_api_calls: Literal[False] = False
    gate_authority: Literal[False] = False
    probability_exposed: Literal[False] = False


class MetricSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    precision: float
    recall: float
    f1: float
    confusion: dict[str, int]


class LabModelSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    architecture: str
    evaluation: str
    promotion_status: Literal["PROMOTED", "NOT_PROMOTED"]
    promotion_rule: str
    selected_extractor: str
    candidate_metrics: MetricSummary
    comparator_metrics: MetricSummary
    nominations: tuple[SemanticNomination, ...]


class RetrievalSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["LOCAL_TFIDF_EXACT_CITATIONS"] = "LOCAL_TFIDF_EXACT_CITATIONS"
    corpus_sha256: str
    guidance_only: Literal[True] = True
    citations: tuple[RetrievalCitation, ...]


class AiLabCaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    boundary: LabBoundary
    model: LabModelSummary
    retrieval: RetrievalSummary


class AiLabArtifactError(ValueError):
    pass


def _metric(value: Any) -> MetricSummary:
    return MetricSummary.model_validate(value)


@functools.lru_cache(maxsize=8)
def _cached_eval_artifact(path_str: str) -> dict[str, Any]:
    return load_eval_artifact(Path(path_str))


@functools.lru_cache(maxsize=8)
def _cached_model(path_str: str) -> Any:
    return load_model(Path(path_str))


@functools.lru_cache(maxsize=8)
def _cached_retriever(repo_root_str: str, corpus_path_str: str) -> BoundedRetriever:
    return BoundedRetriever(Path(repo_root_str), Path(corpus_path_str))


def build_case_ai_lab(
    detail: CaseDetailResponse,
    *,
    repo_root: Path = REPO_ROOT,
    model_path: Path = MODEL_PATH,
    eval_path: Path = EVAL_PATH,
    corpus_path: Path = CORPUS_PATH,
) -> AiLabCaseResponse:
    """Analyze only already-ingested local evidence; no mutation or network access."""
    try:
        artifact = _cached_eval_artifact(str(eval_path.resolve()))
        pipeline = _cached_model(str(model_path.resolve()))
        retriever = _cached_retriever(str(repo_root.resolve()), str(corpus_path.resolve()))
    except (OSError, ValueError) as error:
        raise AiLabArtifactError(str(error)) from error

    canonical_text = "\n".join(
        document.canonical_text
        for document in detail.evidence_documents
        if document.source_type == "customer_communication" and document.canonical_text.strip()
    )
    query = "\n".join(
        value
        for value in [
            canonical_text,
            *[finding.explanation for finding in detail.findings],
            detail.case.reason_profile,
        ]
        if value.strip()
    )
    candidate = artifact["candidate"]
    comparator = artifact["comparator"]
    promotion = artifact["promotion"]
    return AiLabCaseResponse(
        case_id=detail.case.case_id,
        boundary=LabBoundary(),
        model=LabModelSummary(
            model_id=MODEL_ID,
            architecture=str(candidate["architecture"]),
            evaluation=str(candidate["evaluation"]),
            promotion_status=promotion["status"],
            promotion_rule=str(promotion["rule"]),
            selected_extractor=str(promotion["selected_extractor"]),
            candidate_metrics=_metric(candidate["metrics"]),
            comparator_metrics=_metric(comparator["metrics"]),
            nominations=nominate_processed_claims(pipeline, canonical_text),
        ),
        retrieval=RetrievalSummary(
            corpus_sha256=retriever.corpus_sha256,
            citations=retriever.retrieve(query, limit=3),
        ),
    )

"""Leakage-resistant case-level synthetic benchmark evaluator."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, cast

from pydantic import JsonValue

from app.benchmark_integrity import HoldoutAccessError, load_benchmark_case_paths
from app.case_pipeline import CaseEvaluationInput, evaluate_case
from app.decision import ENGINE_VERSION, GateStatus
from app.evaluation_artifact import (
    CasePrediction,
    ClaimEvaluationRecord,
    EvaluationResultArtifact,
    SystemProvenance,
    compute_config_sha256,
    read_dataset_provenance,
)
from app.evaluation_metrics import (
    ILLUSTRATIVE_COST_SCENARIOS,
    compute_baseline_delta,
    compute_cost_sensitivity,
    compute_evaluation_metrics,
)
from app.extraction import (
    CLAIM_SCHEMA_VERSION,
    ClaimModality,
    ClaimType,
    ExtractedClaim,
    ExtractionRequest,
    ExtractionResult,
)
from app.grounding import GroundedNormalizedClaim, ground_and_normalize_claim
from app.regex_baseline import RegexBaselineExtractor
from app.release_freeze import (
    CODE_COMMIT_UNAVAILABLE,
    CONFIG_PATHS,
    ReleaseFreeze,
    verify_release_freeze,
)
from app.verification import GroundingStatus, RefundRecord


class TimedRegexExtractor:
    """Measure the exact regex extraction call without changing its output."""

    def __init__(self) -> None:
        self._extractor = RegexBaselineExtractor()
        self.latencies_ms: list[float] = []

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        started = perf_counter()
        try:
            return await self._extractor.extract(request)
        finally:
            self.latencies_ms.append((perf_counter() - started) * 1000)


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return cast(dict[str, Any], value)


def _read_array(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"Expected JSON object array: {path}")
    return cast(list[dict[str, Any]], value)


def _normalized_value(claim: GroundedNormalizedClaim) -> JsonValue:
    normalized: dict[str, JsonValue] = {}
    if claim.amount_minor is not None:
        normalized["amount_minor"] = claim.amount_minor
    if claim.currency is not None:
        normalized["currency"] = claim.currency
    if claim.normalized_timestamp is not None:
        normalized["timestamp"] = claim.normalized_timestamp.isoformat().replace("+00:00", "Z")
    if claim.refund_reference is not None:
        normalized["refund_reference"] = claim.refund_reference
    return normalized or claim.raw_value


def _claim_record(claim: GroundedNormalizedClaim) -> ClaimEvaluationRecord | None:
    if (
        claim.grounding_status is not GroundingStatus.GROUNDED
        or claim.span_start is None
        or claim.span_end is None
    ):
        return None
    return ClaimEvaluationRecord(
        claim_type=claim.claim_type.value,
        quote=claim.source_quote,
        start=claim.span_start,
        end=claim.span_end,
        normalized_value=_normalized_value(claim),
    )


def _expected_claim_record(value: dict[str, Any], canonical_text: str) -> ClaimEvaluationRecord:
    extracted = ExtractedClaim(
        claim_id=str(value["claim_id"]),
        document_id=str(value["document_id"]),
        claim_type=ClaimType(value["claim_type"]),
        quote=str(value["quote"]),
        value=cast(JsonValue, value.get("value")),
        currency=cast(str | None, value.get("currency")),
        raw_date_text=cast(str | None, value.get("raw_date_text")),
        modality=(ClaimModality(value["modality"]) if value.get("modality") is not None else None),
        subject_ref=cast(str | None, value.get("subject_ref")),
    )
    grounded = ground_and_normalize_claim(extracted, canonical_text)
    return ClaimEvaluationRecord(
        claim_type=extracted.claim_type.value,
        quote=extracted.quote,
        start=int(value["start"]),
        end=int(value["end"]),
        normalized_value=_normalized_value(grounded),
    )


def _runtime_input(case_root: Path) -> tuple[CaseEvaluationInput, str]:
    """Read only detector-visible files; ground_truth is intentionally excluded."""
    manifest = _read_object(case_root / "manifest.json")
    payment = _read_object(case_root / "payment_snapshot.json")
    ledger = _read_object(case_root / "refunds.json")
    communication_path = case_root / "evidence" / "customer_communication.txt"
    canonical_text = (
        communication_path.read_text(encoding="utf-8").strip()
        if communication_path.is_file()
        else ""
    )
    return (
        CaseEvaluationInput(
            case_id=str(manifest["case_id"]),
            reason_profile=str(manifest["reason_profile"]),
            payment_id=str(payment["payment_id"]),
            captured_amount_minor=int(payment["captured_amount_minor"]),
            payment_currency=str(payment["currency"]),
            payment_snapshot_complete=bool(payment["snapshot_complete"]),
            refund_ledger_complete=bool(ledger["ledger_complete"]),
            document_id=str(manifest["document_id"]),
            canonical_text=canonical_text,
            input_supported=bool(manifest["input_supported"]),
            refunds=tuple(RefundRecord.model_validate(record) for record in ledger["records"]),
        ),
        canonical_text,
    )


async def _predict_case(
    case_root: Path,
    extractor: TimedRegexExtractor,
    evaluated_at: datetime,
) -> CasePrediction:
    runtime_input, canonical_text = _runtime_input(case_root)
    outcome = await evaluate_case(runtime_input, extractor, evaluated_at)

    # Labels are loaded only after the detector output is fixed for this case.
    label = _read_object(case_root / "ground_truth" / "gate_label.json")
    scenario = _read_object(case_root / "ground_truth" / "scenario.json")
    expected_claim_values = _read_array(case_root / "ground_truth" / "claims.json")
    predicted_claims = tuple(
        record for claim in outcome.semantic.claims if (record := _claim_record(claim)) is not None
    )
    expected_claims = tuple(
        _expected_claim_record(claim, canonical_text) for claim in expected_claim_values
    )
    return CasePrediction(
        case_id=runtime_input.case_id,
        predicted_status=outcome.decision.status,
        expected_status=GateStatus(str(label["status"])),
        finding_codes=tuple(finding.code for finding in outcome.verification.findings),
        review_reasons=outcome.decision.review_reasons,
        predicted_claims=predicted_claims,
        expected_claims=expected_claims,
        slice=str(scenario["slice"]),
    )


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _latency_summary(values: list[float]) -> dict[str, JsonValue]:
    return {
        "count": len(values),
        "unit": "milliseconds",
        "p50": _percentile(values, 0.50),
        "p95": _percentile(values, 0.95),
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
    }


async def evaluate_benchmark(
    repo_root: Path,
    dataset_root: Path,
    *,
    split: Literal["dev", "holdout"],
    run_id: str,
    created_at: datetime,
    confirm_frozen: bool = False,
    release_freeze_path: Path | None = None,
) -> EvaluationResultArtifact:
    """Evaluate one split without exposing labels to the runtime detector."""
    freeze: ReleaseFreeze | None = None
    if split == "holdout":
        if not confirm_frozen or release_freeze_path is None:
            raise HoldoutAccessError(
                "HOLDOUT requires --confirm-frozen and a verified release freeze."
            )
        freeze = verify_release_freeze(repo_root, release_freeze_path)
    case_paths = load_benchmark_case_paths(
        dataset_root,
        split=split,
        confirm_frozen=confirm_frozen,
    )
    extractor = TimedRegexExtractor()
    case_latencies: list[float] = []
    predictions: list[CasePrediction] = []
    for case_path in case_paths:
        started = perf_counter()
        predictions.append(await _predict_case(case_path, extractor, created_at))
        case_latencies.append((perf_counter() - started) * 1000)
    prediction_tuple = tuple(predictions)
    proposed = compute_evaluation_metrics(prediction_tuple)
    baseline = compute_evaluation_metrics(prediction_tuple)
    metrics = cast(
        dict[str, JsonValue],
        {
            **proposed.model_dump(mode="json"),
            "baseline": baseline.model_dump(mode="json"),
            "baseline_delta": compute_baseline_delta(proposed, baseline).model_dump(mode="json"),
            "cost_sensitivity": [
                result.model_dump(mode="json")
                for result in compute_cost_sensitivity(proposed, ILLUSTRATIVE_COST_SCENARIOS)
            ],
            "timing": {
                "case_end_to_end": _latency_summary(case_latencies),
                "regex_extraction": _latency_summary(extractor.latencies_ms),
            },
            "evaluation_boundary": {
                "synthetic": True,
                "production_prevalence": False,
                "selected_system": "B0 regex extractor plus deterministic verifier",
                "baseline_comparison": (
                    "Identical B0 comparator because offline/regex-only mode was selected; "
                    "no model-backed B1 result is claimed."
                ),
                "pass_is_not_win_prediction": True,
                "block_is_not_legal_verdict": True,
            },
            "release_freeze": (
                {
                    "code_bundle_sha256": freeze.code_bundle_sha256,
                    "created_at": freeze.created_at.isoformat().replace("+00:00", "Z"),
                }
                if freeze is not None
                else None
            ),
        },
    )
    root = repo_root.resolve()
    config_sha256 = (
        freeze.config_sha256
        if freeze is not None
        else compute_config_sha256(root, tuple(root / path for path in CONFIG_PATHS))
    )
    return EvaluationResultArtifact(
        run_id=run_id,
        created_at=created_at,
        system=SystemProvenance(
            system_version=ENGINE_VERSION,
            extractor_id="regex-baseline-v1",
            model_id=None,
            prompt_version="not-applicable-regex-v1",
            claim_schema_version=CLAIM_SCHEMA_VERSION,
            config_sha256=config_sha256,
            code_commit=CODE_COMMIT_UNAVAILABLE,
        ),
        dataset=read_dataset_provenance(dataset_root, split),
        predictions=prediction_tuple,
        metrics=metrics,
    )

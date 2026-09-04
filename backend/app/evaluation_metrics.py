"""Artifact-backed case, claim, slice, baseline, and cost metrics."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from app.decision import GateStatus
from app.evaluation_artifact import CasePrediction, ClaimEvaluationRecord


class RatioMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    value: float | None


class PRFMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    true_positive: int = Field(ge=0)
    false_positive: int = Field(ge=0)
    false_negative: int = Field(ge=0)
    precision: RatioMetric
    recall: RatioMetric
    f1: float | None


class ClassMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    support: int = Field(ge=0)
    predicted: int = Field(ge=0)
    scores: PRFMetric


class SliceCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    correct: int = Field(ge=0)
    expected: dict[str, int]
    predicted: dict[str, int]


class OperationalMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_cases: int = Field(ge=1)
    false_pass_block_cases: int = Field(ge=0)
    false_block_nonblock_cases: int = Field(ge=0)
    review_rate: RatioMetric
    auto_decision_coverage: RatioMetric


class ClaimMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    micro: PRFMetric
    macro_f1: float | None
    by_type: dict[str, ClassMetric]
    exact_grounding_rate: RatioMetric
    normalized_value_accuracy: RatioMetric


class EvaluationMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_conflict: PRFMetric
    operational: OperationalMetrics
    three_class_macro_f1: float
    by_gate_status: dict[str, ClassMetric]
    confusion_matrix: dict[str, dict[str, int]]
    claims: ClaimMetrics
    slices: dict[str, SliceCounts]


class CostScenarioInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    unit: str = "illustrative_cost_units"
    c_false_pass: int = Field(ge=0)
    c_false_block: int = Field(ge=0)
    c_review: int = Field(ge=0)


class CostScenarioResult(CostScenarioInput):
    n_false_pass: int = Field(ge=0)
    n_false_block: int = Field(ge=0)
    n_review: int = Field(ge=0)
    total_cost: int = Field(ge=0)


class BaselineDelta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposed_minus_baseline: dict[str, float | int | None]


ILLUSTRATIVE_COST_SCENARIOS = (
    CostScenarioInput(label="review-cheap", c_false_pass=10, c_false_block=3, c_review=1),
    CostScenarioInput(label="balanced", c_false_pass=10, c_false_block=10, c_review=3),
    CostScenarioInput(label="false-pass-expensive", c_false_pass=30, c_false_block=5, c_review=2),
)


def _ratio(numerator: int, denominator: int) -> RatioMetric:
    return RatioMetric(
        numerator=numerator,
        denominator=denominator,
        value=numerator / denominator if denominator else None,
    )


def _prf(true_positive: int, false_positive: int, false_negative: int) -> PRFMetric:
    f1_denominator = 2 * true_positive + false_positive + false_negative
    return PRFMetric(
        true_positive=true_positive,
        false_positive=false_positive,
        false_negative=false_negative,
        precision=_ratio(true_positive, true_positive + false_positive),
        recall=_ratio(true_positive, true_positive + false_negative),
        f1=(2 * true_positive / f1_denominator if f1_denominator else None),
    )


def _status_counts(values: Iterable[GateStatus]) -> dict[str, int]:
    counter = Counter(value.value for value in values)
    return {status.value: counter[status.value] for status in GateStatus}


def _claim_identity(claim: ClaimEvaluationRecord) -> tuple[str, str, int, int]:
    return claim.claim_type, claim.quote, claim.start, claim.end


def _grounding_identity(claim: ClaimEvaluationRecord) -> tuple[str, int, int]:
    return claim.quote, claim.start, claim.end


def _claim_prf(
    predicted: Iterable[ClaimEvaluationRecord], expected: Iterable[ClaimEvaluationRecord]
) -> PRFMetric:
    predicted_counter = Counter(_claim_identity(claim) for claim in predicted)
    expected_counter = Counter(_claim_identity(claim) for claim in expected)
    true_positive = sum((predicted_counter & expected_counter).values())
    return _prf(
        true_positive,
        sum(predicted_counter.values()) - true_positive,
        sum(expected_counter.values()) - true_positive,
    )


def _normalized_accuracy(
    predicted: Iterable[ClaimEvaluationRecord], expected: Iterable[ClaimEvaluationRecord]
) -> RatioMetric:
    predicted_by_identity: dict[tuple[str, str, int, int], Counter[str]] = defaultdict(Counter)
    expected_by_identity: dict[tuple[str, str, int, int], Counter[str]] = defaultdict(Counter)
    for claim in predicted:
        if claim.normalized_value is not None:
            value = json.dumps(claim.normalized_value, sort_keys=True, separators=(",", ":"))
            predicted_by_identity[_claim_identity(claim)][value] += 1
    for claim in expected:
        if claim.normalized_value is not None:
            value = json.dumps(claim.normalized_value, sort_keys=True, separators=(",", ":"))
            expected_by_identity[_claim_identity(claim)][value] += 1
    denominator = 0
    correct = 0
    for identity, expected_values in expected_by_identity.items():
        predicted_count = sum(predicted_by_identity[identity].values())
        expected_count = sum(expected_values.values())
        denominator += min(predicted_count, expected_count)
        correct += sum((predicted_by_identity[identity] & expected_values).values())
    return _ratio(correct, denominator)


def compute_evaluation_metrics(predictions: tuple[CasePrediction, ...]) -> EvaluationMetrics:
    """Compute all reported values from case-level prediction records."""
    if not predictions:
        raise ValueError("At least one prediction is required.")
    total = len(predictions)
    statuses = tuple(GateStatus)
    confusion = {
        expected.value: {predicted.value: 0 for predicted in statuses} for expected in statuses
    }
    for prediction in predictions:
        confusion[prediction.expected_status.value][prediction.predicted_status.value] += 1

    by_status: dict[str, ClassMetric] = {}
    status_f1: list[float] = []
    for status in statuses:
        true_positive = confusion[status.value][status.value]
        false_positive = sum(
            confusion[expected.value][status.value]
            for expected in statuses
            if expected is not status
        )
        false_negative = sum(
            confusion[status.value][predicted.value]
            for predicted in statuses
            if predicted is not status
        )
        scores = _prf(true_positive, false_positive, false_negative)
        by_status[status.value] = ClassMetric(
            label=status.value,
            support=sum(confusion[status.value].values()),
            predicted=sum(confusion[expected.value][status.value] for expected in statuses),
            scores=scores,
        )
        status_f1.append(scores.f1 or 0.0)

    block_scores = by_status[GateStatus.BLOCK.value].scores
    false_pass = sum(
        1
        for prediction in predictions
        if prediction.expected_status is GateStatus.BLOCK
        and prediction.predicted_status is GateStatus.PASS
    )
    false_block = sum(
        1
        for prediction in predictions
        if prediction.expected_status is not GateStatus.BLOCK
        and prediction.predicted_status is GateStatus.BLOCK
    )
    review_count = sum(
        prediction.predicted_status is GateStatus.REVIEW for prediction in predictions
    )

    all_predicted_claims = tuple(
        claim for prediction in predictions for claim in prediction.predicted_claims
    )
    all_expected_claims = tuple(
        claim for prediction in predictions for claim in prediction.expected_claims
    )
    claim_types = sorted({claim.claim_type for claim in all_predicted_claims + all_expected_claims})
    by_claim_type: dict[str, ClassMetric] = {}
    claim_type_f1: list[float] = []
    for claim_type in claim_types:
        predicted_claims = tuple(
            claim for claim in all_predicted_claims if claim.claim_type == claim_type
        )
        expected_claims = tuple(
            claim for claim in all_expected_claims if claim.claim_type == claim_type
        )
        scores = _claim_prf(predicted_claims, expected_claims)
        by_claim_type[claim_type] = ClassMetric(
            label=claim_type,
            support=len(expected_claims),
            predicted=len(predicted_claims),
            scores=scores,
        )
        claim_type_f1.append(scores.f1 or 0.0)

    predicted_groundings = Counter(_grounding_identity(claim) for claim in all_predicted_claims)
    expected_groundings = Counter(_grounding_identity(claim) for claim in all_expected_claims)
    exact_groundings = sum((predicted_groundings & expected_groundings).values())

    slice_groups: dict[str, list[CasePrediction]] = defaultdict(list)
    for prediction in predictions:
        slice_groups[prediction.slice].append(prediction)
    slices = {
        slice_name: SliceCounts(
            total=len(group),
            correct=sum(item.predicted_status is item.expected_status for item in group),
            expected=_status_counts(item.expected_status for item in group),
            predicted=_status_counts(item.predicted_status for item in group),
        )
        for slice_name, group in sorted(slice_groups.items())
    }

    return EvaluationMetrics(
        material_conflict=block_scores,
        operational=OperationalMetrics(
            total_cases=total,
            false_pass_block_cases=false_pass,
            false_block_nonblock_cases=false_block,
            review_rate=_ratio(review_count, total),
            auto_decision_coverage=_ratio(total - review_count, total),
        ),
        three_class_macro_f1=sum(status_f1) / len(status_f1),
        by_gate_status=by_status,
        confusion_matrix=confusion,
        claims=ClaimMetrics(
            micro=_claim_prf(all_predicted_claims, all_expected_claims),
            macro_f1=(sum(claim_type_f1) / len(claim_type_f1) if claim_type_f1 else None),
            by_type=by_claim_type,
            exact_grounding_rate=_ratio(exact_groundings, len(all_predicted_claims)),
            normalized_value_accuracy=_normalized_accuracy(
                all_predicted_claims, all_expected_claims
            ),
        ),
        slices=slices,
    )


def compute_cost_sensitivity(
    metrics: EvaluationMetrics,
    scenarios: tuple[CostScenarioInput, ...],
) -> tuple[CostScenarioResult, ...]:
    """Apply caller-visible unitless parameters; do not infer fees or savings."""
    if not scenarios:
        raise ValueError("At least one cost scenario is required.")
    operational = metrics.operational
    n_review = operational.review_rate.numerator
    return tuple(
        CostScenarioResult(
            **scenario.model_dump(),
            n_false_pass=operational.false_pass_block_cases,
            n_false_block=operational.false_block_nonblock_cases,
            n_review=n_review,
            total_cost=(
                operational.false_pass_block_cases * scenario.c_false_pass
                + operational.false_block_nonblock_cases * scenario.c_false_block
                + n_review * scenario.c_review
            ),
        )
        for scenario in scenarios
    )


def compute_baseline_delta(
    proposed: EvaluationMetrics, baseline: EvaluationMetrics
) -> BaselineDelta:
    """Return proposed-minus-baseline values from two identically computed protocols."""
    proposed_values: dict[str, float | int | None] = {
        "material_precision": proposed.material_conflict.precision.value,
        "material_recall": proposed.material_conflict.recall.value,
        "material_f1": proposed.material_conflict.f1,
        "false_pass_block_cases": proposed.operational.false_pass_block_cases,
        "false_block_nonblock_cases": proposed.operational.false_block_nonblock_cases,
        "review_rate": proposed.operational.review_rate.value,
        "auto_decision_coverage": proposed.operational.auto_decision_coverage.value,
        "claim_micro_f1": proposed.claims.micro.f1,
        "exact_grounding_rate": proposed.claims.exact_grounding_rate.value,
    }
    baseline_values: dict[str, float | int | None] = {
        "material_precision": baseline.material_conflict.precision.value,
        "material_recall": baseline.material_conflict.recall.value,
        "material_f1": baseline.material_conflict.f1,
        "false_pass_block_cases": baseline.operational.false_pass_block_cases,
        "false_block_nonblock_cases": baseline.operational.false_block_nonblock_cases,
        "review_rate": baseline.operational.review_rate.value,
        "auto_decision_coverage": baseline.operational.auto_decision_coverage.value,
        "claim_micro_f1": baseline.claims.micro.f1,
        "exact_grounding_rate": baseline.claims.exact_grounding_rate.value,
    }
    differences: dict[str, float | int | None] = {}
    for key, proposed_value in proposed_values.items():
        baseline_value = baseline_values[key]
        differences[key] = (
            proposed_value - baseline_value
            if proposed_value is not None and baseline_value is not None
            else None
        )
    return BaselineDelta(proposed_minus_baseline=differences)

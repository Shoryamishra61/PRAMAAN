from __future__ import annotations

import math

from app.decision import GateStatus
from app.evaluation_artifact import CasePrediction, ClaimEvaluationRecord
from app.evaluation_metrics import (
    ILLUSTRATIVE_COST_SCENARIOS,
    compute_baseline_delta,
    compute_cost_sensitivity,
    compute_evaluation_metrics,
)
from hypothesis import given
from hypothesis import strategies as st


def claim(name: str, normalized: object) -> ClaimEvaluationRecord:
    return ClaimEvaluationRecord(
        claim_type=name,
        quote=f"quote-{name}",
        start=0,
        end=len(f"quote-{name}"),
        normalized_value=normalized,
    )


def sample_predictions() -> tuple[CasePrediction, ...]:
    return (
        CasePrediction(
            case_id="one",
            predicted_status=GateStatus.BLOCK,
            expected_status=GateStatus.BLOCK,
            predicted_claims=(claim("a", 100),),
            expected_claims=(claim("a", 100),),
            slice="ledger",
        ),
        CasePrediction(
            case_id="two",
            predicted_status=GateStatus.PASS,
            expected_status=GateStatus.BLOCK,
            expected_claims=(claim("b", "ref"),),
            slice="ledger",
        ),
        CasePrediction(
            case_id="three",
            predicted_status=GateStatus.BLOCK,
            expected_status=GateStatus.PASS,
            predicted_claims=(claim("c", None),),
            slice="hard-negative",
        ),
        CasePrediction(
            case_id="four",
            predicted_status=GateStatus.REVIEW,
            expected_status=GateStatus.REVIEW,
            predicted_claims=(claim("d", "wrong"),),
            expected_claims=(claim("d", "right"),),
            slice="grounding",
        ),
    )


def test_gate_counts_ratios_confusion_and_slices_are_computed() -> None:
    metrics = compute_evaluation_metrics(sample_predictions())

    assert metrics.material_conflict.true_positive == 1
    assert metrics.material_conflict.precision.model_dump() == {
        "numerator": 1,
        "denominator": 2,
        "value": 0.5,
    }
    assert metrics.material_conflict.recall.value == 0.5
    assert metrics.material_conflict.f1 == 0.5
    assert metrics.operational.false_pass_block_cases == 1
    assert metrics.operational.false_block_nonblock_cases == 1
    assert metrics.operational.review_rate.value == 0.25
    assert metrics.operational.auto_decision_coverage.value == 0.75
    assert metrics.three_class_macro_f1 == 0.5
    assert metrics.confusion_matrix["BLOCK"] == {"PASS": 1, "REVIEW": 0, "BLOCK": 1}
    assert metrics.slices["ledger"].model_dump() == {
        "total": 2,
        "correct": 1,
        "expected": {"PASS": 0, "REVIEW": 0, "BLOCK": 2},
        "predicted": {"PASS": 1, "REVIEW": 0, "BLOCK": 1},
    }


def test_claim_metrics_use_exact_type_quote_span_and_normalized_values() -> None:
    metrics = compute_evaluation_metrics(sample_predictions()).claims

    assert math.isclose(metrics.micro.precision.value or 0, 2 / 3)
    assert math.isclose(metrics.micro.recall.value or 0, 2 / 3)
    assert math.isclose(metrics.micro.f1 or 0, 2 / 3)
    assert metrics.macro_f1 == 0.5
    assert metrics.exact_grounding_rate.model_dump() == {
        "numerator": 2,
        "denominator": 3,
        "value": 2 / 3,
    }
    assert metrics.normalized_value_accuracy.model_dump() == {
        "numerator": 1,
        "denominator": 2,
        "value": 0.5,
    }


def test_cost_sensitivity_uses_visible_unitless_inputs() -> None:
    metrics = compute_evaluation_metrics(sample_predictions())
    results = compute_cost_sensitivity(metrics, ILLUSTRATIVE_COST_SCENARIOS)

    assert [result.label for result in results] == [
        "review-cheap",
        "balanced",
        "false-pass-expensive",
    ]
    assert results[0].unit == "illustrative_cost_units"
    assert results[0].total_cost == 14
    assert results[1].total_cost == 23
    assert results[2].total_cost == 37


def test_baseline_delta_is_derived_from_same_metric_contract() -> None:
    proposed = compute_evaluation_metrics(sample_predictions())
    baseline_predictions = tuple(
        item.model_copy(update={"predicted_status": GateStatus.REVIEW})
        for item in sample_predictions()
    )
    baseline = compute_evaluation_metrics(baseline_predictions)
    delta = compute_baseline_delta(proposed, baseline).proposed_minus_baseline

    assert delta["material_recall"] == 0.5
    assert delta["false_pass_block_cases"] == 1
    assert delta["review_rate"] == -0.75
    assert delta["auto_decision_coverage"] == 0.75


@given(st.lists(st.sampled_from(tuple(GateStatus)), min_size=1, max_size=50))
def test_perfect_predictions_are_permutation_invariant(labels: list[GateStatus]) -> None:
    predictions = tuple(
        CasePrediction(
            case_id=f"case-{index}",
            predicted_status=label,
            expected_status=label,
            slice="property",
        )
        for index, label in enumerate(labels)
    )
    metrics = compute_evaluation_metrics(predictions)
    reversed_metrics = compute_evaluation_metrics(tuple(reversed(predictions)))

    assert metrics.model_dump() == reversed_metrics.model_dump()
    assert metrics.operational.false_pass_block_cases == 0
    assert metrics.operational.false_block_nonblock_cases == 0

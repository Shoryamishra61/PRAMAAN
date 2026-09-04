from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from app.carve import (
    AutomationRiskBudget,
    CircuitBreakerState,
    DecisionStatus,
    RiskCertificate,
    RiskPrediction,
    SourceAuthorityTier,
    apply_hard_precedence,
    compile_financial_proof,
    point_in_time_snapshot,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/financial-evidence-integrity/v4.5"


def _rows(split: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (DATA / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def _all_evidence(row: dict[str, Any]) -> set[str]:
    return {item["evidence_id"] for item in row["complete_evidence_inventory"]}


def test_proof_compiler_matches_every_train_dev_and_calibration_label() -> None:
    for split in ("train", "dev", "calibration"):
        for row in _rows(split):
            result = compile_financial_proof(row, _all_evidence(row))
            assert result.status == ("UNSAT" if row["material_contradiction"] else "SAT")
            if result.status == "UNSAT":
                assert result.certificate is not None
                assert result.certificate.minimal_relative_to_compiled_constraints is True
                assert len(result.certificate.facts) == 3
                assert result.model_override_allowed is False


def test_initially_incomplete_case_fails_closed_with_specific_evidence() -> None:
    row = next(
        row
        for row in _rows("dev")
        if set(row["required_for_resolution"]) - set(row["initial_visible_evidence"])
    )
    result = compile_financial_proof(row, set(row["initial_visible_evidence"]))
    assert result.status == "INCOMPLETE"
    assert result.missing_evidence
    assert apply_hard_precedence(result, None, None).status is DecisionStatus.REVIEW


def test_model_score_cannot_override_formal_contradiction() -> None:
    row = next(row for row in _rows("dev") if row["material_contradiction"] == 1)
    proof = compile_financial_proof(row, _all_evidence(row))
    risk = RiskPrediction(model_id="hostile-model", residual_risk=0.0, artifact_sha256="0" * 64)
    certificate = RiskCertificate(
        calibration_id="cal-v4",
        pass_threshold=1.0,
        normalized_risk_bound=0.025,
        assumptions=("synthetic",),
        valid_for_case=True,
    )
    decision = apply_hard_precedence(proof, risk, certificate)
    assert decision.status is DecisionStatus.BLOCK
    assert decision.razorpay_write_performed is False


def test_corrupt_evidence_hash_routes_to_review() -> None:
    row = copy.deepcopy(next(row for row in _rows("dev") if row["material_contradiction"] == 0))
    row["complete_evidence_inventory"][0]["content_sha256"] = "0" * 64
    proof = compile_financial_proof(row, _all_evidence(row))
    assert proof.status == "INCOMPLETE"
    assert "digest mismatch" in proof.reason.lower()
    assert apply_hard_precedence(proof, None, None).status is DecisionStatus.REVIEW


def test_ood_and_missing_authoritative_state_route_to_review() -> None:
    for row in _rows("ood"):
        proof = compile_financial_proof(row, set(row["initial_visible_evidence"]))
        decision = apply_hard_precedence(proof, None, None)
        assert decision.status is DecisionStatus.REVIEW


def test_point_in_time_snapshot_filters_future_evidence() -> None:
    row = copy.deepcopy(next(row for row in _rows("dev") if row["material_contradiction"] == 0))
    row["complete_evidence_inventory"][0]["available_time"] = "2026-03-01T10:00:00Z"
    row["complete_evidence_inventory"][1]["available_time"] = "2026-03-01T12:00:00Z"

    # Decision at 11:00:00Z should only see item 0, not item 1
    snap = point_in_time_snapshot(row, "2026-03-01T11:00:00Z")
    visible_ids = {i["evidence_id"] for i in snap["complete_evidence_inventory"]}
    assert row["complete_evidence_inventory"][0]["evidence_id"] in visible_ids
    assert row["complete_evidence_inventory"][1]["evidence_id"] not in visible_ids


def test_automation_risk_budget_and_circuit_breaker() -> None:
    budget = AutomationRiskBudget(daily_risk_budget=10.0, daily_review_capacity=2)
    assert budget.circuit_breaker_state == CircuitBreakerState.AUTOMATION_ENABLED

    # Safe low risk automation
    assert budget.can_automate(estimated_error_prob=0.05, economic_loss_if_wrong=10.0) is True
    budget.record_decision(
        DecisionStatus.PASS,
        estimated_error_prob=0.05,
        economic_loss_if_wrong=10.0,
    )
    assert budget.consumed_risk == 0.5

    # Reviews increment towards capacity
    budget.record_decision(DecisionStatus.REVIEW, estimated_error_prob=0.5)
    budget.record_decision(DecisionStatus.REVIEW, estimated_error_prob=0.5)
    deg_state: CircuitBreakerState = budget.circuit_breaker_state
    assert deg_state == CircuitBreakerState.DEGRADED

    # Exhausting risk budget triggers REVIEW_ONLY
    budget.record_decision(
        DecisionStatus.PASS,
        estimated_error_prob=0.96,
        economic_loss_if_wrong=10.0,
    )
    final_state: CircuitBreakerState = budget.circuit_breaker_state
    assert final_state == CircuitBreakerState.REVIEW_ONLY
    assert budget.can_automate(estimated_error_prob=0.01) is False
    assert SourceAuthorityTier.TIER_0.value == "TIER_0"

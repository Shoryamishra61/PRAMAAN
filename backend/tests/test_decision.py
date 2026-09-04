from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

from app.decision import (
    DECISION_DISCLAIMER,
    STATUS_COPY,
    GateDecision,
    GateStatus,
    decide,
)
from app.verification import Finding, FindingEffect, VerificationResult
from hypothesis import given
from hypothesis import strategies as st
from jsonschema import Draft202012Validator, FormatChecker

CONTRACT_PATH = Path(__file__).parents[2] / "contracts" / "gate-decision.schema.json"


def finding(effect: FindingEffect, code: str) -> Finding:
    return Finding(
        code=code,
        effect=effect,
        summary=f"Synthetic {effect.value.lower()} reason.",
        evidence_refs=("case:case_1",),
    )


def decision_for(*findings: Finding) -> GateDecision:
    return decide(
        "case_1",
        VerificationResult(findings=findings),
        datetime(2026, 8, 23, 10, tzinfo=timezone(timedelta(hours=5, minutes=30))),
    )


def test_no_findings_is_pass_with_canonical_boundary_copy() -> None:
    decision = decision_for()

    assert decision.status is GateStatus.PASS
    assert decision.primary_reason_code is None
    assert STATUS_COPY["PASS"] == "Gate clear — no supported integrity issue detected."
    assert DECISION_DISCLAIMER == "Decision support only — not a dispute outcome prediction."


def test_review_finding_cannot_pass() -> None:
    decision = decision_for(finding(FindingEffect.REVIEW, "F_SOURCE_UNGROUNDED"))

    assert decision.status is GateStatus.REVIEW
    assert decision.primary_reason_code == "F_SOURCE_UNGROUNDED"


def test_verified_material_conflict_blocks_and_remains_local_language() -> None:
    decision = decision_for(
        finding(FindingEffect.REVIEW, "F_EVIDENCE_RECOMMENDED_MISSING"),
        finding(FindingEffect.BLOCK, "F_REFUND_CLAIM_NO_LEDGER_MATCH"),
    )

    assert decision.status is GateStatus.BLOCK
    assert decision.primary_reason_code == "F_REFUND_CLAIM_NO_LEDGER_MATCH"
    assert STATUS_COPY["BLOCK"].startswith("Local hold")


def test_decision_serialization_matches_closed_json_schema() -> None:
    decision = decide(
        "case_1",
        VerificationResult(
            findings=(finding(FindingEffect.REVIEW, "F_STRUCTURED_STATE_INCOMPLETE"),)
        ),
        datetime(2026, 8, 23, 10, tzinfo=timezone.utc),
    )
    schema = cast(dict[str, Any], json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
    payload = decision.model_dump(mode="json")

    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
    assert payload["evaluated_at"] == "2026-08-23T10:00:00Z"
    assert "primary_reason_code" not in payload
    assert "disclaimer" not in payload


@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_any_review_only_result_never_passes(codes: list[str]) -> None:
    result = VerificationResult(
        findings=tuple(finding(FindingEffect.REVIEW, code) for code in codes)
    )

    decision = decide("case_property", result, datetime.now(timezone.utc))

    assert decision.status is GateStatus.REVIEW

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pytest
from app.case_pipeline import CaseEvaluationInput, evaluate_case
from app.decision import GateStatus
from app.extraction import ExtractionRequest, ExtractionResult
from app.regex_baseline import RegexBaselineExtractor
from app.semantic_pipeline import TransientExtractorError
from app.verification import RefundRecord

DEMO_ROOT = Path(__file__).parents[2] / "data" / "demo"
EVALUATED_AT = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def load_fixture(name: str) -> tuple[CaseEvaluationInput, dict[str, Any]]:
    root = DEMO_ROOT / name
    manifest = read_json(root / "manifest.json")
    payment = read_json(root / "payment_snapshot.json")
    ledger = read_json(root / "refunds.json")
    text = (root / "evidence" / "customer_communication.txt").read_text(encoding="utf-8").strip()
    return (
        CaseEvaluationInput(
            case_id=manifest["case_id"],
            payment_id=payment["payment_id"],
            captured_amount_minor=payment["captured_amount_minor"],
            payment_currency=payment["currency"],
            payment_snapshot_complete=payment["snapshot_complete"],
            refund_ledger_complete=ledger["ledger_complete"],
            document_id=f"doc_{name}",
            canonical_text=text,
            refunds=tuple(RefundRecord.model_validate(refund) for refund in ledger["records"]),
        ),
        manifest,
    )


@pytest.mark.parametrize("name", ["pass", "review", "block"])
@pytest.mark.asyncio
async def test_seeded_golden_cases_match_expected_gate_state(name: str) -> None:
    case, manifest = load_fixture(name)

    outcome = await evaluate_case(case, RegexBaselineExtractor(), EVALUATED_AT)

    assert outcome.decision.status.value == manifest["expected_gate_status"]
    assert outcome.decision.primary_reason_code == manifest["expected_primary_reason_code"]
    assert all(
        claim.span_start is not None and claim.span_end is not None
        for claim in outcome.semantic.claims
    )


@pytest.mark.asyncio
async def test_extractor_outage_is_review_and_never_pass() -> None:
    case, _ = load_fixture("pass")

    class UnavailableExtractor:
        async def extract(self, _: ExtractionRequest) -> ExtractionResult:
            raise TransientExtractorError("offline")

    outcome = await evaluate_case(
        case,
        UnavailableExtractor(),
        EVALUATED_AT,
        max_extraction_attempts=2,
    )

    assert outcome.decision.status is GateStatus.REVIEW
    assert outcome.decision.primary_reason_code == "F_MODEL_UNAVAILABLE"


@pytest.mark.asyncio
async def test_ambiguous_grounding_is_review_and_never_block() -> None:
    case, _ = load_fixture("block")
    repeated = case.model_copy(
        update={"canonical_text": f"{case.canonical_text} {case.canonical_text}"}
    )

    outcome = await evaluate_case(repeated, RegexBaselineExtractor(), EVALUATED_AT)

    assert outcome.decision.status is GateStatus.REVIEW
    assert "F_SOURCE_UNGROUNDED" in outcome.decision.review_reasons
    assert all(finding.materiality != "material" for finding in outcome.decision.findings)


@pytest.mark.asyncio
async def test_future_refund_promise_with_no_ledger_match_reviews_not_blocks() -> None:
    case, _ = load_fixture("block")
    promise = case.model_copy(
        update={"canonical_text": "We will process a refund within 5 business days."}
    )

    outcome = await evaluate_case(promise, RegexBaselineExtractor(), EVALUATED_AT)

    assert outcome.decision.status is GateStatus.REVIEW
    assert all(finding.materiality != "material" for finding in outcome.decision.findings)


@pytest.mark.asyncio
async def test_missing_communication_skips_extraction_and_routes_to_review() -> None:
    case, _ = load_fixture("pass")

    outcome = await evaluate_case(
        case.model_copy(update={"canonical_text": ""}),
        RegexBaselineExtractor(),
        EVALUATED_AT,
    )

    assert outcome.semantic.attempts == 0
    assert outcome.decision.status is GateStatus.REVIEW
    assert outcome.decision.primary_reason_code == "F_EVIDENCE_RECOMMENDED_MISSING"

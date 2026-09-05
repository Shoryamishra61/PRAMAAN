from __future__ import annotations

from app.verification import (
    FindingEffect,
    GroundingStatus,
    RefundRecord,
    ResolvedClaim,
    VerificationContext,
    verify_integrity,
)
from hypothesis import given
from hypothesis import strategies as st


def claim(**overrides: object) -> ResolvedClaim:
    values: dict[str, object] = {
        "id": "claim_1",
        "document_id": "doc_1",
        "claim_type": "refund_claimed_processed",
        "source_quote": "We processed a full refund of ₹2,500.",
        "grounding_status": "GROUNDED",
        "amount_minor": 250_000,
        "currency": "INR",
    }
    values.update(overrides)
    return ResolvedClaim.model_validate(values)


def refund(**overrides: object) -> RefundRecord:
    values: dict[str, object] = {
        "id": "rfnd_1",
        "payment_id": "pay_1",
        "amount_minor": 250_000,
        "currency": "INR",
        "local_status": "processed",
        "reference": "RF-101",
    }
    values.update(overrides)
    return RefundRecord.model_validate(values)


def context(**overrides: object) -> VerificationContext:
    values: dict[str, object] = {
        "case_id": "case_1",
        "payment_id": "pay_1",
        "captured_amount_minor": 250_000,
        "payment_currency": "INR",
        "payment_snapshot_complete": True,
        "refund_ledger_complete": True,
        "communication_present": True,
        "refunds": (),
        "claims": (),
    }
    values.update(overrides)
    return VerificationContext.model_validate(values)


def codes(result: object) -> set[str]:
    return {finding.code for finding in result.findings}  # type: ignore[attr-defined]


def test_processed_claim_without_complete_ledger_match_blocks() -> None:
    result = verify_integrity(context(claims=(claim(),)))

    assert codes(result) == {"F_REFUND_CLAIM_NO_LEDGER_MATCH"}
    assert result.findings[0].effect is FindingEffect.BLOCK


def test_matching_processed_refund_has_no_findings() -> None:
    result = verify_integrity(context(refunds=(refund(),), claims=(claim(),)))

    assert result.findings == ()


def test_incomplete_ledger_reviews_and_cannot_block() -> None:
    result = verify_integrity(context(refund_ledger_complete=False, claims=(claim(),)))

    assert codes(result) == {"F_STRUCTURED_STATE_INCOMPLETE"}
    assert all(finding.effect is FindingEffect.REVIEW for finding in result.findings)


def test_final_partial_refund_conflicts_with_grounded_full_amount() -> None:
    result = verify_integrity(context(refunds=(refund(amount_minor=100_000),), claims=(claim(),)))

    assert "F_REFUND_AMOUNT_MISMATCH" in codes(result)


def test_currency_mismatch_blocks_without_cross_currency_amount_comparison() -> None:
    result = verify_integrity(context(refunds=(refund(currency="USD"),), claims=(claim(),)))

    assert "F_REFUND_CURRENCY_MISMATCH" in codes(result)
    assert "F_REFUND_AMOUNT_MISMATCH" not in codes(result)


def test_wrong_payment_linkage_blocks() -> None:
    result = verify_integrity(context(refunds=(refund(payment_id="pay_other"),)))

    assert codes(result) == {"F_REFUND_REFERENCE_PAYMENT_MISMATCH"}


def test_pending_refund_reviews_instead_of_contradicting() -> None:
    result = verify_integrity(context(refunds=(refund(local_status="pending"),), claims=(claim(),)))

    assert "F_STRUCTURED_STATE_INCOMPLETE" in codes(result)
    assert all(finding.effect is FindingEffect.REVIEW for finding in result.findings)


def test_future_promise_without_resolved_timing_reviews() -> None:
    result = verify_integrity(
        context(claims=(claim(claim_type="refund_promised", amount_minor=None),))
    )

    assert codes(result) == {"F_STRUCTURED_STATE_INCOMPLETE"}


def test_customer_non_receipt_and_policy_interpretation_review() -> None:
    result = verify_integrity(
        context(
            claims=(
                claim(claim_type="return_not_received_claim", amount_minor=None),
                claim(claim_type="policy_condition_reference", amount_minor=None),
            )
        )
    )

    assert codes(result) == {"F_SOURCE_UNSUPPORTED"}
    assert all(finding.effect is FindingEffect.REVIEW for finding in result.findings)


def test_terminal_failed_refund_conflicts_with_processed_claim() -> None:
    result = verify_integrity(context(refunds=(refund(local_status="failed"),), claims=(claim(),)))

    assert codes(result) == {"F_REFUND_FINAL_STATUS_CONFLICT"}


def test_missing_communication_or_suggested_evidence_reviews() -> None:
    result = verify_integrity(
        context(
            communication_present=False,
            missing_recommended_evidence=("refund_generation_or_ledger_state",),
        )
    )

    assert codes(result) == {"F_EVIDENCE_RECOMMENDED_MISSING"}
    assert all(finding.effect is FindingEffect.REVIEW for finding in result.findings)


@given(st.sampled_from([GroundingStatus.UNGROUNDED, GroundingStatus.AMBIGUOUS]))
def test_ungrounded_claim_can_never_block(status: GroundingStatus) -> None:
    result = verify_integrity(context(claims=(claim(grounding_status=status),)))

    assert "F_SOURCE_UNGROUNDED" in codes(result)
    assert all(finding.effect is not FindingEffect.BLOCK for finding in result.findings)


@given(st.integers(min_value=250_001, max_value=10_000_000))
def test_refund_above_payment_is_invalid_state_not_block(amount_minor: int) -> None:
    result = verify_integrity(context(refunds=(refund(amount_minor=amount_minor),)))

    assert codes(result) == {"F_STRUCTURED_STATE_INCOMPLETE"}
    assert all(finding.effect is FindingEffect.REVIEW for finding in result.findings)


def test_cumulative_processed_refunds_above_capture_fail_closed() -> None:
    result = verify_integrity(
        context(
            captured_amount_minor=10_000,
            refunds=(
                refund(id="rfnd_1", amount_minor=6_000),
                refund(id="rfnd_2", amount_minor=6_000),
            ),
        )
    )

    assert codes(result) == {"F_STRUCTURED_STATE_INCOMPLETE"}
    assert all(finding.effect is FindingEffect.REVIEW for finding in result.findings)


def test_full_refund_can_be_satisfied_by_multiple_final_refunds() -> None:
    refunds = (refund(id="a", amount_minor=100_000), refund(id="b", amount_minor=150_000))
    assert verify_integrity(context(refunds=refunds, claims=(claim(),))).findings == ()


def test_aggregate_cannot_replace_a_specific_refund_reference() -> None:
    refunds = (refund(id="a", amount_minor=100_000), refund(id="b", amount_minor=150_000))
    result = verify_integrity(context(refunds=refunds, claims=(claim(refund_reference="RF-101"),)))
    assert "F_REFUND_CLAIM_NO_LEDGER_MATCH" in codes(result)

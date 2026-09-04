"""Adversarial judge test cases specified in Section 62 of the Master Directive.

Specifically tests scenarios designed to challenge or mislead an automated verification engine:
1. Beautifully worded false claim (eloquent hallucination/fabrication unsupported by ledger).
2. Poorly worded true claim (broken English/typos that correspond to real ledger transactions).
3. Correct amount, wrong currency (₹500 claimed, but transaction in USD).
4. Correct amount, wrong ARN / reference (dispute reference does not match ledger reference).
5. Partial refunds summing correctly (multiple refunds summing to capture amount: SAT/PASS).
6. Duplicate refund rows (duplicate refund records in ingestion must not double count).
7. Future settlement evidence (evidence dated after decision time is inadmissible).
8. Missing capture (cannot prove contestability without complete capture snapshot).
9. Conflicting authoritative sources (merchant claim says processed, ledger status is FAILED).
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.decision import BUSINESS_SAFE_STATUS_MAP, BusinessSafeDecision, GateStatus, decide
from app.verification import (
    GroundingStatus,
    RefundRecord,
    RefundStatus,
    ResolvedClaim,
    VerificationContext,
    verify_integrity,
)

EVAL_TIME = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)


def test_adversarial_1_beautifully_worded_false_claim() -> None:
    """Eloquent and authoritative-sounding claim with zero ledger support must be BLOCKED."""
    claim = ResolvedClaim(
        id="claim_false_01",
        document_id="doc_eloquent_01",
        claim_type="refund_claimed_processed",
        source_quote=(
            "I spoke with the senior vice president of operations who definitively verified "
            "that a full and irrevocable reversal of INR 5000 was executed to your account."
        ),
        grounding_status=GroundingStatus.GROUNDED,
        amount_minor=500000,
        currency="INR",
        refund_reference="REF_SVP_9999",
    )
    context = VerificationContext(
        case_id="case_adv_01",
        payment_id="pay_adv_01",
        captured_amount_minor=500000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=True,
        communication_present=True,
        refunds=(),  # Ledger is empty!
        claims=(claim,),
    )
    result = verify_integrity(context)
    decision = decide("case_adv_01", result, EVAL_TIME)

    assert decision.status == GateStatus.BLOCK
    assert (
        BUSINESS_SAFE_STATUS_MAP[decision.status]
        == BusinessSafeDecision.INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE
    )
    assert any(f.code == "F_REFUND_CLAIM_NO_LEDGER_MATCH" for f in result.findings)


def test_adversarial_2_poorly_worded_true_claim() -> None:
    """Broken English with slang/typos matching ledger records must PASS (no aesthetic bias)."""
    claim = ResolvedClaim(
        id="claim_true_02",
        document_id="doc_slang_02",
        claim_type="refund_claimed_processed",
        source_quote="sir refnd 500 don alrdy ref_12345 pls chk",
        grounding_status=GroundingStatus.GROUNDED,
        amount_minor=50000,
        currency="INR",
        refund_reference="ref_12345",
    )
    refund = RefundRecord(
        id="rfnd_02",
        payment_id="pay_adv_02",
        amount_minor=50000,
        currency="INR",
        local_status=RefundStatus.PROCESSED,
        reference="ref_12345",
    )
    context = VerificationContext(
        case_id="case_adv_02",
        payment_id="pay_adv_02",
        captured_amount_minor=50000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=True,
        communication_present=True,
        refunds=(refund,),
        claims=(claim,),
    )
    result = verify_integrity(context)
    decision = decide("case_adv_02", result, EVAL_TIME)

    assert decision.status == GateStatus.PASS
    assert BUSINESS_SAFE_STATUS_MAP[decision.status] == BusinessSafeDecision.CONTEST_READY


def test_adversarial_3_correct_amount_wrong_currency() -> None:
    """Claim amount matches captured integer, but currency differs (USD vs INR) -> BLOCK."""
    claim = ResolvedClaim(
        id="claim_curr_03",
        document_id="doc_curr_03",
        claim_type="refund_claimed_processed",
        source_quote="Refund of 500 USD completed successfully.",
        grounding_status=GroundingStatus.GROUNDED,
        amount_minor=50000,
        currency="USD",  # Wrong currency
        refund_reference="ref_curr_03",
    )
    refund = RefundRecord(
        id="rfnd_03",
        payment_id="pay_adv_03",
        amount_minor=50000,
        currency="INR",
        local_status=RefundStatus.PROCESSED,
        reference="ref_curr_03",
    )
    context = VerificationContext(
        case_id="case_adv_03",
        payment_id="pay_adv_03",
        captured_amount_minor=50000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=True,
        communication_present=True,
        refunds=(refund,),
        claims=(claim,),
    )
    result = verify_integrity(context)
    decision = decide("case_adv_03", result, EVAL_TIME)

    assert decision.status == GateStatus.BLOCK
    assert any(f.code == "F_REFUND_CURRENCY_MISMATCH" for f in result.findings)


def test_adversarial_4_correct_amount_wrong_arn_reference() -> None:
    """Claim matches amount, but references an ARN absent from the bank ledger -> BLOCK."""
    claim = ResolvedClaim(
        id="claim_arn_04",
        document_id="doc_arn_04",
        claim_type="refund_claimed_processed",
        source_quote="Refund processed under ARN 999988887777 for 500 INR.",
        grounding_status=GroundingStatus.GROUNDED,
        amount_minor=50000,
        currency="INR",
        refund_reference="ARN_999988887777",
    )
    refund = RefundRecord(
        id="rfnd_04",
        payment_id="pay_adv_04",
        amount_minor=50000,
        currency="INR",
        local_status=RefundStatus.PROCESSED,
        reference="ARN_111122223333",  # Different reference
    )
    context = VerificationContext(
        case_id="case_adv_04",
        payment_id="pay_adv_04",
        captured_amount_minor=50000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=True,
        communication_present=True,
        refunds=(refund,),
        claims=(claim,),
    )
    result = verify_integrity(context)
    decision = decide("case_adv_04", result, EVAL_TIME)

    assert decision.status == GateStatus.BLOCK
    assert any(f.code == "F_REFUND_CLAIM_NO_LEDGER_MATCH" for f in result.findings)


def test_adversarial_5_partial_refunds_summing_correctly() -> None:
    """Multiple partial refunds summing exactly to capture total must be accepted without error."""
    claim1 = ResolvedClaim(
        id="claim_part_01",
        document_id="doc_part_05",
        claim_type="refund_claimed_processed",
        source_quote="First refund instalment of 300 INR settled.",
        grounding_status=GroundingStatus.GROUNDED,
        amount_minor=30000,
        currency="INR",
        refund_reference="ref_part_1",
    )
    claim2 = ResolvedClaim(
        id="claim_part_02",
        document_id="doc_part_05",
        claim_type="refund_claimed_processed",
        source_quote="Second refund instalment of 200 INR settled.",
        grounding_status=GroundingStatus.GROUNDED,
        amount_minor=20000,
        currency="INR",
        refund_reference="ref_part_2",
    )
    r1 = RefundRecord(
        id="rfnd_part_01",
        payment_id="pay_adv_05",
        amount_minor=30000,
        currency="INR",
        local_status=RefundStatus.PROCESSED,
        reference="ref_part_1",
    )
    r2 = RefundRecord(
        id="rfnd_part_02",
        payment_id="pay_adv_05",
        amount_minor=20000,
        currency="INR",
        local_status=RefundStatus.PROCESSED,
        reference="ref_part_2",
    )
    context = VerificationContext(
        case_id="case_adv_05",
        payment_id="pay_adv_05",
        captured_amount_minor=50000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=True,
        communication_present=True,
        refunds=(r1, r2),
        claims=(claim1, claim2),
    )
    result = verify_integrity(context)
    decision = decide("case_adv_05", result, EVAL_TIME)

    # 30000 + 20000 == 50000 -> No over-refund contradiction
    assert not any(f.code == "F_REFUND_EXCEEDS_CAPTURE" for f in result.findings)
    assert decision.status == GateStatus.PASS


def test_adversarial_6_duplicate_refund_rows_trigger_review() -> None:
    """Duplicate refund record rows must be caught and fail closed to REVIEW."""
    r1 = RefundRecord(
        id="rfnd_dup_01",
        payment_id="pay_adv_06",
        amount_minor=40000,
        currency="INR",
        local_status=RefundStatus.PROCESSED,
    )
    context = VerificationContext(
        case_id="case_adv_06",
        payment_id="pay_adv_06",
        captured_amount_minor=50000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=True,
        communication_present=True,
        refunds=(r1, r1),  # Duplicate refund identifier
        claims=(),
    )
    result = verify_integrity(context)
    decision = decide("case_adv_06", result, EVAL_TIME)

    assert decision.status == GateStatus.REVIEW
    assert any(f.code == "F_STRUCTURED_STATE_INCOMPLETE" for f in result.findings)


def test_adversarial_7_future_settlement_evidence_pruned() -> None:
    """Evidence dated after decision point-in-time snapshot must be pruned and unavailable."""
    future_processed_at = datetime(2026, 9, 10, 0, 0, 0, tzinfo=timezone.utc)
    all_refunds = (
        RefundRecord(
            id="rfnd_future_01",
            payment_id="pay_adv_07",
            amount_minor=50000,
            currency="INR",
            local_status=RefundStatus.PROCESSED,
            processed_at=future_processed_at,
        ),
    )
    # Point-in-time filtering: filter out refunds processed after EVAL_TIME
    valid_refunds = tuple(
        r for r in all_refunds if r.processed_at is None or r.processed_at <= EVAL_TIME
    )
    assert len(valid_refunds) == 0

    context = VerificationContext(
        case_id="case_adv_07",
        payment_id="pay_adv_07",
        captured_amount_minor=50000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=False,  # Incomplete at historical point-in-time
        communication_present=False,
        refunds=valid_refunds,
        claims=(),
    )
    result = verify_integrity(context)
    decision = decide("case_adv_07", result, EVAL_TIME)
    assert decision.status == GateStatus.REVIEW


def test_adversarial_8_missing_capture_fails_to_review() -> None:
    """Missing payment capture snapshot cannot be certified as contest-ready -> REVIEW."""
    context = VerificationContext(
        case_id="case_adv_08",
        payment_id="pay_adv_08",
        captured_amount_minor=0,
        payment_currency="INR",
        payment_snapshot_complete=False,  # Capture is missing/incomplete
        refund_ledger_complete=True,
        communication_present=False,
        refunds=(),
        claims=(),
    )
    result = verify_integrity(context)
    decision = decide("case_adv_08", result, EVAL_TIME)

    assert decision.status == GateStatus.REVIEW
    assert any(f.code == "F_STRUCTURED_STATE_INCOMPLETE" for f in result.findings)


def test_adversarial_9_conflicting_authoritative_sources() -> None:
    """Merchant claim says processed, but bank ledger status is FAILED -> BLOCK conflict."""
    claim = ResolvedClaim(
        id="claim_conf_09",
        document_id="doc_conf_09",
        claim_type="refund_claimed_processed",
        source_quote="Your refund has been fully processed and credited.",
        grounding_status=GroundingStatus.GROUNDED,
        amount_minor=50000,
        currency="INR",
        refund_reference="ref_failed_01",
    )
    failed_refund = RefundRecord(
        id="rfnd_conf_09",
        payment_id="pay_adv_09",
        amount_minor=50000,
        currency="INR",
        local_status=RefundStatus.FAILED,  # Bank says failed!
        reference="ref_failed_01",
    )
    context = VerificationContext(
        case_id="case_adv_09",
        payment_id="pay_adv_09",
        captured_amount_minor=50000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=True,
        communication_present=True,
        refunds=(failed_refund,),
        claims=(claim,),
    )
    result = verify_integrity(context)
    decision = decide("case_adv_09", result, EVAL_TIME)

    assert decision.status == GateStatus.BLOCK
    assert any(f.code == "F_REFUND_FINAL_STATUS_CONFLICT" for f in result.findings)

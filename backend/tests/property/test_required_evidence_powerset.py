"""Required-evidence powerset testing for PRAMAAN.

Validates the Required-Evidence Tests:
1. For required categories (payment snapshot, refund ledger, communication), tests all 2^N subsets.
2. Any subset missing required trusted evidence emits REVIEW, never PASS.
3. Differentiates between 'file exists' vs 'evidence valid and authoritative'.
"""

from __future__ import annotations

from itertools import combinations

from app.verification import (
    FindingEffect,
    RefundRecord,
    RefundStatus,
    ResolvedClaim,
    VerificationContext,
    verify_integrity,
)


def _build_context(
    has_payment: bool,
    has_refunds: bool,
    has_comm: bool,
) -> VerificationContext:
    claim = ResolvedClaim(
        id="clm_1",
        document_id="doc_1",
        claim_type="refund_claimed_processed",
        source_quote="Refund processed for ₹2,500",
        grounding_status="GROUNDED",
        amount_minor=250_000,
        currency="INR",
    )
    refund = RefundRecord(
        id="rfnd_1",
        payment_id="pay_1",
        amount_minor=250_000,
        currency="INR",
        local_status=RefundStatus.PROCESSED,
    )

    return VerificationContext(
        case_id="case_powerset_test",
        payment_id="pay_1",
        captured_amount_minor=250_000,
        payment_currency="INR",
        payment_snapshot_complete=has_payment,
        refund_ledger_complete=has_refunds,
        communication_present=has_comm,
        claims=(claim,) if has_comm else (),
        refunds=(refund,) if has_refunds else (),
    )


def test_required_evidence_all_subsets_fail_closed_unless_complete() -> None:
    """Test all 2^3 = 8 subsets of {payment_snapshot, refund_ledger, communication}.

    Only the complete set {payment, refund, communication} may proceed without
    F_STRUCTURED_STATE_INCOMPLETE or missing findings.
    """
    categories = ["payment", "refund", "communication"]

    # Generate powerset: all combinations of length 0 to 3
    powerset: list[tuple[str, ...]] = []
    for r in range(len(categories) + 1):
        powerset.extend(combinations(categories, r))

    assert len(powerset) == 8

    for subset in powerset:
        has_pay = "payment" in subset
        has_rfnd = "refund" in subset
        has_comm = "communication" in subset

        ctx = _build_context(has_payment=has_pay, has_refunds=has_rfnd, has_comm=has_comm)
        result = verify_integrity(ctx)

        is_complete = has_pay and has_rfnd and has_comm

        if not is_complete:
            # Invariant: Any incomplete subset MUST emit findings requiring REVIEW
            assert len(result.findings) > 0
            codes = {f.code for f in result.findings}
            # Must have either incomplete state or missing claim/ledger findings
            assert any(
                code in codes
                for code in {
                    "F_STRUCTURED_STATE_INCOMPLETE",
                    "F_EVIDENCE_RECOMMENDED_MISSING",
                    "F_REFUND_CLAIM_NO_LEDGER_MATCH",
                }
            )
            assert any(f.effect == FindingEffect.REVIEW for f in result.findings)
        else:
            # When fully complete and matching, no blocking/review findings
            assert len(result.findings) == 0

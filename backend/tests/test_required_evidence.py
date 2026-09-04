"""Tests for reason-code-aware Required Evidence Schema and active acquisition logic."""

from datetime import datetime, timedelta, timezone

from app.required_evidence import (
    EvidenceCategory,
    audit_dispute_evidence,
)


def test_required_evidence_audit_complete_package() -> None:
    future_deadline = datetime.now(timezone.utc) + timedelta(days=5)
    audit = audit_dispute_evidence(
        dispute_id="disp_101",
        payment_id="pay_999",
        reason_code_str="CREDIT_NOT_PROCESSED",
        respond_by=future_deadline,
        existing_evidence_categories=[
            EvidenceCategory.REFUND_LEDGER,
            EvidenceCategory.CUSTOMER_COMMUNICATION,
        ],
        detected_conflicts=[],
        has_smt_unsat=False,
        neural_uncertainty_high=False,
    )
    assert audit.is_defensively_sufficient is True
    assert audit.recommended_action == "CONTEST_READY"
    assert len(audit.missing_mandatory_categories) == 0
    assert audit.is_expired is False


def test_required_evidence_audit_missing_mandatory() -> None:
    future_deadline = datetime.now(timezone.utc) + timedelta(days=3)
    audit = audit_dispute_evidence(
        dispute_id="disp_102",
        payment_id="pay_998",
        reason_code_str="GOODS_SERVICES_NOT_RECEIVED",
        respond_by=future_deadline,
        existing_evidence_categories=[EvidenceCategory.CUSTOMER_COMMUNICATION],
        detected_conflicts=[],
        has_smt_unsat=False,
        neural_uncertainty_high=False,
    )
    assert audit.is_defensively_sufficient is False
    assert audit.recommended_action == "REVIEW_REQUIRED"
    assert EvidenceCategory.PROOF_OF_DELIVERY in audit.missing_mandatory_categories
    assert "Proof Of Delivery" in (audit.next_best_evidence_acquisition or "")


def test_required_evidence_audit_smt_conflict() -> None:
    future_deadline = datetime.now(timezone.utc) + timedelta(days=2)
    audit = audit_dispute_evidence(
        dispute_id="disp_103",
        payment_id="pay_997",
        reason_code_str="CREDIT_NOT_PROCESSED",
        respond_by=future_deadline,
        existing_evidence_categories=[
            EvidenceCategory.REFUND_LEDGER,
            EvidenceCategory.CUSTOMER_COMMUNICATION,
        ],
        detected_conflicts=["REFUND_AMOUNT_MISMATCH: refund 5000 != transacted 2000"],
        has_smt_unsat=True,
        neural_uncertainty_high=False,
    )
    assert audit.is_defensively_sufficient is False
    assert audit.recommended_action == "INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE"

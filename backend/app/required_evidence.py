"""Reason-Code-Aware Required Evidence Schema and Sufficiency Evaluation.

Satisfies Section 4 of the Master Directive:
For every dispute:
1. What evidence is required?
2. What evidence exists?
3. What is missing?
4. What conflicts?
5. Which facts are authoritative?
6. Is evidence sufficient to prepare a defensive contest?
7. What is the response deadline?
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DisputeReasonCode(str, Enum):
    CREDIT_NOT_PROCESSED = "CREDIT_NOT_PROCESSED"
    GOODS_SERVICES_NOT_RECEIVED = "GOODS_SERVICES_NOT_RECEIVED"
    GOODS_SERVICES_NOT_AS_DESCRIBED = "GOODS_SERVICES_NOT_AS_DESCRIBED"
    DUPLICATE_CHARGE = "DUPLICATE_CHARGE"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"


class EvidenceCategory(str, Enum):
    REFUND_LEDGER = "refund_ledger"
    CUSTOMER_COMMUNICATION = "customer_communication"
    MERCHANT_POLICY = "merchant_policy"
    PROOF_OF_DELIVERY = "proof_of_delivery"
    ORDER_INVOICE = "order_invoice"
    PRODUCT_CATALOG_SPEC = "product_catalog_spec"
    DUAL_ORDER_RECEIPT = "dual_order_receipt"
    GATEWAY_CAPTURE_RECORD = "gateway_capture_record"
    CURRENCY_SETTLEMENT_STATEMENT = "currency_settlement_statement"


class EvidenceAuthorityTier(str, Enum):
    TIER_1_IMMUTABLE_BANK_LEDGER = "TIER_1_IMMUTABLE_BANK_LEDGER"
    TIER_2_CARRIER_CONFIRMATION = "TIER_2_CARRIER_CONFIRMATION"
    TIER_3_MERCHANT_SYSTEM_RECORD = "TIER_3_MERCHANT_SYSTEM_RECORD"
    TIER_4_UNVERIFIED_PARTY_COMMUNICATION = "TIER_4_UNVERIFIED_PARTY_COMMUNICATION"


class EvidenceRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: EvidenceCategory
    name: str
    description: str
    authority_tier: EvidenceAuthorityTier
    is_mandatory: bool


# Canonical evidence requirements per dispute reason family
REQUIRED_EVIDENCE_MAP: dict[DisputeReasonCode, tuple[EvidenceRequirement, ...]] = {
    DisputeReasonCode.CREDIT_NOT_PROCESSED: (
        EvidenceRequirement(
            category=EvidenceCategory.REFUND_LEDGER,
            name="Bank Refund Settlement Ledger",
            description="Authoritative bank settlement ARN proving refund disbursement",
            authority_tier=EvidenceAuthorityTier.TIER_1_IMMUTABLE_BANK_LEDGER,
            is_mandatory=True,
        ),
        EvidenceRequirement(
            category=EvidenceCategory.CUSTOMER_COMMUNICATION,
            name="Customer Communication Log",
            description="Email, chat, or WhatsApp correspondence regarding refund requests",
            authority_tier=EvidenceAuthorityTier.TIER_4_UNVERIFIED_PARTY_COMMUNICATION,
            is_mandatory=True,
        ),
        EvidenceRequirement(
            category=EvidenceCategory.MERCHANT_POLICY,
            name="Refund and Cancellation Policy",
            description="Published merchant policy terms accepted by customer during checkout",
            authority_tier=EvidenceAuthorityTier.TIER_3_MERCHANT_SYSTEM_RECORD,
            is_mandatory=False,
        ),
    ),
    DisputeReasonCode.GOODS_SERVICES_NOT_RECEIVED: (
        EvidenceRequirement(
            category=EvidenceCategory.PROOF_OF_DELIVERY,
            name="Carrier Delivery Confirmation",
            description=(
                "Tracking URL, AWB, and carrier signed proof of delivery or OTP confirmation"
            ),
            authority_tier=EvidenceAuthorityTier.TIER_2_CARRIER_CONFIRMATION,
            is_mandatory=True,
        ),
        EvidenceRequirement(
            category=EvidenceCategory.ORDER_INVOICE,
            name="Tax Invoice & Shipping Address",
            description="Order invoice verifying shipping address matching customer billing",
            authority_tier=EvidenceAuthorityTier.TIER_3_MERCHANT_SYSTEM_RECORD,
            is_mandatory=True,
        ),
        EvidenceRequirement(
            category=EvidenceCategory.CUSTOMER_COMMUNICATION,
            name="Delivery Inquiry Correspondence",
            description="Customer inquiries or carrier status updates",
            authority_tier=EvidenceAuthorityTier.TIER_4_UNVERIFIED_PARTY_COMMUNICATION,
            is_mandatory=False,
        ),
    ),
    DisputeReasonCode.GOODS_SERVICES_NOT_AS_DESCRIBED: (
        EvidenceRequirement(
            category=EvidenceCategory.PRODUCT_CATALOG_SPEC,
            name="Product Specification & Description",
            description="Published product description, specifications, and pre-dispatch QC record",
            authority_tier=EvidenceAuthorityTier.TIER_3_MERCHANT_SYSTEM_RECORD,
            is_mandatory=True,
        ),
        EvidenceRequirement(
            category=EvidenceCategory.ORDER_INVOICE,
            name="Order Confirmation Invoice",
            description="Itemized receipt displaying exact SKU, dimensions, and customer selection",
            authority_tier=EvidenceAuthorityTier.TIER_3_MERCHANT_SYSTEM_RECORD,
            is_mandatory=True,
        ),
        EvidenceRequirement(
            category=EvidenceCategory.CUSTOMER_COMMUNICATION,
            name="Customer Complaint & RMA Correspondence",
            description="Customer defect notification and return merchandise authorization history",
            authority_tier=EvidenceAuthorityTier.TIER_4_UNVERIFIED_PARTY_COMMUNICATION,
            is_mandatory=True,
        ),
    ),
    DisputeReasonCode.DUPLICATE_CHARGE: (
        EvidenceRequirement(
            category=EvidenceCategory.GATEWAY_CAPTURE_RECORD,
            name="Gateway Authorization & Capture Ledger",
            description="Distinct gateway payment IDs and bank reference numbers (RRN)",
            authority_tier=EvidenceAuthorityTier.TIER_1_IMMUTABLE_BANK_LEDGER,
            is_mandatory=True,
        ),
        EvidenceRequirement(
            category=EvidenceCategory.DUAL_ORDER_RECEIPT,
            name="Separate Order Invoices",
            description="Proof of two distinct orders placed or evidence of auto-reversal",
            authority_tier=EvidenceAuthorityTier.TIER_3_MERCHANT_SYSTEM_RECORD,
            is_mandatory=True,
        ),
    ),
    DisputeReasonCode.PROCESSING_ERROR: (
        EvidenceRequirement(
            category=EvidenceCategory.CURRENCY_SETTLEMENT_STATEMENT,
            name="Settlement & Currency Reconciliation",
            description=(
                "Acquiring bank settlement statement verifying transacted vs captured amount"
            ),
            authority_tier=EvidenceAuthorityTier.TIER_1_IMMUTABLE_BANK_LEDGER,
            is_mandatory=True,
        ),
        EvidenceRequirement(
            category=EvidenceCategory.ORDER_INVOICE,
            name="Itemized Transaction Receipt",
            description="Checkout receipt displaying minor units, taxes, and applied discounts",
            authority_tier=EvidenceAuthorityTier.TIER_3_MERCHANT_SYSTEM_RECORD,
            is_mandatory=True,
        ),
    ),
    DisputeReasonCode.AUTHORIZATION_ERROR: (
        EvidenceRequirement(
            category=EvidenceCategory.GATEWAY_CAPTURE_RECORD,
            name="3DS / E-Mandate Authentication Log",
            description=(
                "3D-Secure liability shift token, OTP validation timestamp, or recurring mandate"
                " registration"
            ),
            authority_tier=EvidenceAuthorityTier.TIER_1_IMMUTABLE_BANK_LEDGER,
            is_mandatory=True,
        ),
    ),
}


class DisputeEvidenceAudit(BaseModel):
    """Answers all 7 core dispute evidence questions required by Razorpay Track 02."""

    model_config = ConfigDict(extra="forbid")

    dispute_id: str
    payment_id: str
    reason_code: DisputeReasonCode
    respond_by: datetime
    is_expired: bool

    # 1. What evidence is required?
    required_categories: tuple[EvidenceCategory, ...]

    # 2. What evidence exists?
    existing_categories: tuple[EvidenceCategory, ...]

    # 3. What evidence is missing?
    missing_mandatory_categories: tuple[EvidenceCategory, ...]
    missing_optional_categories: tuple[EvidenceCategory, ...]

    # 4. What evidence conflicts?
    conflicting_findings: tuple[str, ...]

    # 5. Which facts are authoritative?
    authoritative_sources: tuple[str, ...]

    # 6. Is evidence sufficient to prepare a defensive contest?
    is_defensively_sufficient: bool
    recommended_action: Literal[
        "CONTEST_READY", "REVIEW_REQUIRED", "INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE"
    ]

    # 7. Next priority evidence recommendation (Active Evidence Acquisition / VOI)
    next_best_evidence_acquisition: str | None


def audit_dispute_evidence(
    dispute_id: str,
    payment_id: str,
    reason_code_str: str,
    respond_by: datetime,
    existing_evidence_categories: list[EvidenceCategory],
    detected_conflicts: list[str],
    has_smt_unsat: bool,
    neural_uncertainty_high: bool,
) -> DisputeEvidenceAudit:
    """Evaluate evidence sufficiency, missing requirements, and active acquisition priority."""
    try:
        reason_code = DisputeReasonCode(reason_code_str)
    except ValueError:
        reason_code = DisputeReasonCode.CREDIT_NOT_PROCESSED

    requirements = REQUIRED_EVIDENCE_MAP.get(
        reason_code, REQUIRED_EVIDENCE_MAP[DisputeReasonCode.CREDIT_NOT_PROCESSED]
    )
    required_cats = tuple(req.category for req in requirements)
    existing_set = set(existing_evidence_categories)

    missing_mandatory = tuple(
        req.category
        for req in requirements
        if req.is_mandatory and req.category not in existing_set
    )
    missing_optional = tuple(
        req.category
        for req in requirements
        if not req.is_mandatory and req.category not in existing_set
    )

    now = datetime.now(timezone.utc)
    is_expired = respond_by < now

    # Authoritative facts
    authoritative: list[str] = []
    if (
        EvidenceCategory.REFUND_LEDGER in existing_set
        or EvidenceCategory.GATEWAY_CAPTURE_RECORD in existing_set
    ):
        authoritative.append("Gateway Settlement Ledger (Tier 1: Bank Verified)")
    if EvidenceCategory.PROOF_OF_DELIVERY in existing_set:
        authoritative.append("Logistics Carrier POD (Tier 2: Courier Verified)")

    # Sufficiency & Decisioning
    if has_smt_unsat or any(
        "REFUND_AMOUNT_MISMATCH" in c or "PROCESSED_NO_LEDGER" in c for c in detected_conflicts
    ):
        action = "INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE"
        sufficient = False
    elif missing_mandatory or neural_uncertainty_high or is_expired:
        action = "REVIEW_REQUIRED"
        sufficient = False
    else:
        action = "CONTEST_READY"
        sufficient = True

    # Active evidence acquisition recommendation (VOI)
    next_evidence: str | None = None
    if missing_mandatory:
        cat_title = missing_mandatory[0].value.replace("_", " ").title()
        next_evidence = f"Acquire mandatory {cat_title} to clear uncertainty"
    elif detected_conflicts:
        next_evidence = (
            "Request merchant ledger audit to reconcile conflicting settlement timestamps"
        )

    return DisputeEvidenceAudit(
        dispute_id=dispute_id,
        payment_id=payment_id,
        reason_code=reason_code,
        respond_by=respond_by,
        is_expired=is_expired,
        required_categories=required_cats,
        existing_categories=tuple(existing_evidence_categories),
        missing_mandatory_categories=missing_mandatory,
        missing_optional_categories=missing_optional,
        conflicting_findings=tuple(detected_conflicts),
        authoritative_sources=tuple(authoritative),
        is_defensively_sufficient=sufficient,
        recommended_action=action,
        next_best_evidence_acquisition=next_evidence,
    )

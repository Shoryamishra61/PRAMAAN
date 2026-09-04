"""Canonical PASS/REVIEW/BLOCK decision policy and closed output schema."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain import require_utc
from app.verification import FindingEffect, VerificationResult

ENGINE_VERSION = "deterministic-v1"

STATUS_COPY: dict[str, str] = {
    "PASS": "Gate clear — no supported integrity issue detected.",
    "REVIEW": "Review required — evidence could not be verified safely.",
    "BLOCK": "Local hold — a material evidence inconsistency was verified.",
}

DECISION_DISCLAIMER = "Decision support only — not a dispute outcome prediction."


class GateStatus(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class BusinessSafeDecision(str, Enum):
    CONTEST_READY = "CONTEST_READY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE = "INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE"


BUSINESS_SAFE_STATUS_MAP: dict[GateStatus, BusinessSafeDecision] = {
    GateStatus.PASS: BusinessSafeDecision.CONTEST_READY,
    GateStatus.REVIEW: BusinessSafeDecision.REVIEW_REQUIRED,
    GateStatus.BLOCK: BusinessSafeDecision.INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE,
}

BUSINESS_SAFE_COPY: dict[BusinessSafeDecision, str] = {
    BusinessSafeDecision.CONTEST_READY: (
        "Evidence consistent and complete — defensive contest package ready for preparation."
    ),
    BusinessSafeDecision.REVIEW_REQUIRED: (
        "Evidence requires human inspection or additional supporting documentation."
    ),
    BusinessSafeDecision.INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE: (
        "Material contradiction or critical insufficiency detected — hold contest preparation."
    ),
}


class DecisionFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    materiality: Literal["material", "non_material"]
    summary: str
    evidence_refs: tuple[str, ...]


class GateDecision(BaseModel):
    """Matches contracts/gate-decision.schema.json exactly."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    profile_id: Literal["refund_not_processed_v1"] = "refund_not_processed_v1"
    status: GateStatus
    findings: tuple[DecisionFinding, ...]
    review_reasons: tuple[str, ...]
    evaluated_at: datetime
    engine_version: str = ENGINE_VERSION

    @field_validator("evaluated_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return require_utc(value)

    @property
    def primary_reason_code(self) -> str | None:
        """Derive API/storage metadata without adding a field to the closed JSON contract."""
        if self.status is GateStatus.BLOCK:
            return next(
                (finding.code for finding in self.findings if finding.materiality == "material"),
                None,
            )
        return self.review_reasons[0] if self.review_reasons else None

    @property
    def business_decision(self) -> BusinessSafeDecision:
        """Map internal gate status to business-safe operational semantics."""
        return BUSINESS_SAFE_STATUS_MAP[self.status]

    @property
    def business_description(self) -> str:
        """Human-readable merchant risk guidance."""
        return BUSINESS_SAFE_COPY[self.business_decision]


def decide(case_id: str, verification: VerificationResult, evaluated_at: datetime) -> GateDecision:
    """Apply decision precedence after verifier completeness guards have run."""
    has_block = any(finding.effect is FindingEffect.BLOCK for finding in verification.findings)
    has_review = any(finding.effect is FindingEffect.REVIEW for finding in verification.findings)
    status = GateStatus.BLOCK if has_block else GateStatus.REVIEW if has_review else GateStatus.PASS

    findings = tuple(
        DecisionFinding(
            code=finding.code,
            materiality=("material" if finding.effect is FindingEffect.BLOCK else "non_material"),
            summary=finding.summary,
            evidence_refs=finding.evidence_refs,
        )
        for finding in verification.findings
    )
    review_reasons = tuple(
        dict.fromkeys(
            finding.code
            for finding in verification.findings
            if finding.effect is FindingEffect.REVIEW
        )
    )
    return GateDecision(
        case_id=case_id,
        status=status,
        findings=findings,
        review_reasons=review_reasons,
        evaluated_at=evaluated_at,
    )

"""End-to-end semantic-to-deterministic case evaluation slice."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.decision import GateDecision, decide
from app.domain import MoneyMinor
from app.extraction import (
    ExtractionRequest,
    SemanticExtractor,
    default_claim_allowlist,
)
from app.semantic_pipeline import (
    SemanticPipelineOutcome,
    SemanticPipelineStatus,
    run_semantic_pipeline,
)
from app.verification import (
    Finding,
    RefundRecord,
    VerificationContext,
    VerificationResult,
    verify_integrity,
)


class CaseEvaluationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    reason_profile: str = "refund_not_processed_v1"
    payment_id: str = Field(min_length=1)
    captured_amount_minor: MoneyMinor
    payment_currency: str = Field(pattern=r"^[A-Z]{3}$")
    payment_snapshot_complete: bool
    refund_ledger_complete: bool
    document_id: str = Field(min_length=1)
    canonical_text: str
    document_type: str = "text/plain"
    input_supported: bool = True
    missing_recommended_evidence: tuple[str, ...] = ()
    refunds: tuple[RefundRecord, ...] = ()
    pre_verification_findings: tuple[Finding, ...] = ()


class CaseEvaluationOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semantic: SemanticPipelineOutcome
    verification: VerificationResult
    decision: GateDecision


def _deduplicate_findings(findings: tuple[Finding, ...]) -> tuple[Finding, ...]:
    seen: set[tuple[str, tuple[str, ...], str]] = set()
    unique: list[Finding] = []
    for finding in findings:
        key = (finding.code, finding.evidence_refs, finding.summary)
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return tuple(unique)


async def evaluate_case(
    case: CaseEvaluationInput,
    extractor: SemanticExtractor,
    evaluated_at: datetime,
    *,
    max_extraction_attempts: int = 2,
) -> CaseEvaluationOutcome:
    """Evaluate one case without granting semantic output final-decision authority."""
    if case.canonical_text.strip():
        request = ExtractionRequest(
            document_id=case.document_id,
            document_type=case.document_type,
            canonical_text=case.canonical_text,
            allowed_claim_types=default_claim_allowlist(),
            reason_profile_id="refund_not_processed_v1",
        )
        semantic = await run_semantic_pipeline(
            extractor,
            request,
            max_attempts=max_extraction_attempts,
            input_supported=case.input_supported,
            case_id=case.case_id,
        )
    else:
        semantic = SemanticPipelineOutcome(
            status=SemanticPipelineStatus.REVIEW,
            attempts=0,
            claims=(),
            review_findings=(),
        )
    deterministic = verify_integrity(
        VerificationContext(
            case_id=case.case_id,
            reason_profile=case.reason_profile,
            payment_id=case.payment_id,
            captured_amount_minor=case.captured_amount_minor,
            payment_currency=case.payment_currency,
            payment_snapshot_complete=case.payment_snapshot_complete,
            refund_ledger_complete=case.refund_ledger_complete,
            communication_present=bool(case.canonical_text.strip()),
            missing_recommended_evidence=case.missing_recommended_evidence,
            refunds=case.refunds,
            claims=tuple(claim.to_resolved_claim() for claim in semantic.claims),
        )
    )
    combined = VerificationResult(
        findings=_deduplicate_findings(
            case.pre_verification_findings + semantic.review_findings + deterministic.findings
        )
    )
    return CaseEvaluationOutcome(
        semantic=semantic,
        verification=combined,
        decision=decide(case.case_id, combined, evaluated_at),
    )

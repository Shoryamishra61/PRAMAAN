from __future__ import annotations

from pathlib import Path

from app.ai_lab_api import build_case_ai_lab
from app.case_api import (
    CaseDetailResponse,
    ClaimResponse,
    EvidenceResponse,
    FindingResponse,
    QueueItem,
)
from app.decision import GateStatus
from app.domain import ProcessingStatus, WorkflowStatus

ROOT = Path(__file__).resolve().parents[2]


def _detail() -> CaseDetailResponse:
    return CaseDetailResponse(
        case=QueueItem(
            case_id="case_ai_lab",
            dispute_id="disp_ai_lab",
            payment_id="pay_ai_lab",
            amount_minor=250000,
            currency="INR",
            respond_by=None,
            raw_reason_code="raw_refund_reason",
            reason_profile="refund_not_processed_v1",
            processing_status=ProcessingStatus.READY,
            gate_status=GateStatus.BLOCK,
            primary_reason_code="F_REFUND_AMOUNT_MISMATCH",
        ),
        workflow_status=WorkflowStatus.REVIEW_PENDING,
        payment_snapshot=None,
        refunds=(),
        evidence_documents=(
            EvidenceResponse(
                id="doc_ai_lab",
                source_type="customer_communication",
                source_system="synthetic_fixture",
                media_type="text/plain",
                canonical_text="Your INR 2,500 refund was processed.",
                content_sha256="a" * 64,
                captured_at=None,
                ingested_at="2026-08-23T12:00:00Z",
                is_complete_source=True,
            ),
        ),
        grounded_claims=(
            ClaimResponse(
                id="claim_ai_lab",
                document_id="doc_ai_lab",
                claim_type="refund_claimed_processed",
                raw_value="INR 2,500",
                amount_minor=250000,
                currency="INR",
                refund_reference=None,
                modality="assertion",
                source_quote="Your INR 2,500 refund was processed.",
                span_start=0,
                span_end=36,
                grounding_status="GROUNDED",
            ),
        ),
        findings=(
            FindingResponse(
                id="finding_ai_lab",
                rule_code="F_REFUND_AMOUNT_MISMATCH",
                severity="material",
                decision_effect=GateStatus.BLOCK,
                explanation="A grounded processed amount conflicts with the trusted refund ledger.",
                structured_refs=("rfnd_1",),
                claim_refs=("claim_ai_lab",),
            ),
        ),
        gate_decision={"status": "BLOCK"},
        audit_events=(),
    )


def test_case_ai_lab_is_offline_explainable_and_advisory() -> None:
    response = build_case_ai_lab(_detail())
    assert response.boundary.holdout_accessed is False
    assert response.boundary.external_api_calls is False
    assert response.boundary.gate_authority is False
    assert response.model.promotion_status == "NOT_PROMOTED"
    assert response.model.selected_extractor == "regex-baseline-v1"
    assert response.model.nominations[0].source_quote == "Your INR 2,500 refund was processed."
    assert response.model.nominations[0].feature_contributions
    assert response.retrieval.guidance_only is True
    assert response.retrieval.citations
    serialized = response.model_dump_json()
    assert "confidence" not in serialized
    assert "predicted_probability" not in serialized

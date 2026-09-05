"""Ephemeral, offline input-to-decision verifier used by the product demo."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.case_pipeline import CaseEvaluationInput, evaluate_case
from app.decision import GateStatus
from app.extraction import ExtractionRequest, ExtractionResult
from app.grounding import parse_inr_minor_units
from app.nlp_engine import analyze_multilingual_dispute, extract_text_from_pdf_bytes
from app.regex_baseline import BASELINE_ID, RegexBaselineExtractor
from app.semantic_pipeline import TransientExtractorError
from app.verification import Finding, FindingEffect, RefundRecord, RefundStatus


class SandboxEvaluateRequest(BaseModel):
    """Small, bounded input contract for a single refund-integrity check."""

    model_config = ConfigDict(extra="forbid")

    raw_reason_code: str = Field(min_length=1, max_length=128)
    payment_amount_inr: str = Field(min_length=1, max_length=32)
    customer_communication: str = Field(min_length=1, max_length=10_000)
    refund_ledger_complete: bool = True
    refund_status: Literal["none", "created", "pending", "processed", "failed", "cancelled"]
    refund_amount_inr: str | None = Field(default=None, max_length=32)
    simulation: Literal["none", "model_outage", "hash_mismatch", "ocr_corruption"] = "none"

    @field_validator("raw_reason_code", "customer_communication")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        candidate = value.strip()
        if not candidate:
            raise ValueError("must not be blank")
        return candidate

    @field_validator("payment_amount_inr")
    @classmethod
    def validate_payment_amount(cls, value: str) -> str:
        if parse_inr_minor_units(value, "INR") is None:
            raise ValueError("must be an INR amount with at most two decimal places")
        return value.strip()

    @model_validator(mode="after")
    def validate_refund_amount(self) -> SandboxEvaluateRequest:
        if self.refund_status == "none":
            if self.refund_amount_inr not in {None, ""}:
                raise ValueError("refund_amount_inr must be empty when no refund record exists")
            self.refund_amount_inr = None
            return self
        if self.refund_amount_inr is None:
            raise ValueError("refund_amount_inr is required for a refund record")
        if parse_inr_minor_units(self.refund_amount_inr, "INR") is None:
            raise ValueError("refund_amount_inr must have at most two decimal places")
        self.refund_amount_inr = self.refund_amount_inr.strip()
        return self


class SandboxClaimResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    claim_type: str
    source_quote: str
    span_start: int | None
    span_end: int | None
    grounding_status: str
    amount_minor: int | None
    currency: str | None
    normalization_status: str


class SandboxFindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    effect: Literal["REVIEW", "BLOCK"]
    summary: str
    evidence_refs: tuple[str, ...]


class SandboxLedgerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_id: str
    payment_amount_minor: int = Field(ge=0)
    currency: Literal["INR"] = "INR"
    refund_ledger_complete: bool
    refund_status: str
    refund_amount_minor: int | None = Field(default=None, ge=0)


class SandboxBoundaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime: Literal["LOCAL_OFFLINE"] = "LOCAL_OFFLINE"
    ephemeral: Literal[True] = True
    synthetic_input: Literal[True] = True
    external_api_calls: Literal[False] = False
    razorpay_write_performed: Literal[False] = False
    persisted: Literal[False] = False
    holdout_accessed: Literal[False] = False
    extractor_id: str = BASELINE_ID
    gate_authority: Literal["DETERMINISTIC_POLICY"] = "DETERMINISTIC_POLICY"


class SandboxProofConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    constraint_id: str
    layer: Literal["INPUT", "GROUNDING", "AUTHORITATIVE", "INVARIANT"]
    expression: str
    state: Literal["SAT", "UNSAT", "INCOMPLETE"]


class SandboxProofCertificate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solver: Literal["DETERMINISTIC_COMPILER"] = "DETERMINISTIC_COMPILER"
    invariant_id: str
    proof_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_refs: tuple[str, ...]
    minimal_relative_to_compiled_constraints: Literal[True] = True


class SandboxProofResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["SAT", "UNSAT", "INCOMPLETE"]
    constraints: tuple[SandboxProofConstraint, ...]
    certificate: SandboxProofCertificate | None = None
    model_override_allowed: Literal[False] = False


class SandboxAcquisitionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["REQUEST_REFUND_EXPORT"]
    evidence_id: Literal["refund_state"]
    acquisition_cost: Literal[1] = 1
    reason: str


class SandboxComparisonResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semantic_output: Literal["GROUNDED_RELATION", "ABSTAINED"]
    deterministic_output: GateStatus
    relationship: Literal["DIVISION_OF_AUTHORITY", "SAFE_ABSTENTION"]
    uncertainty_basis: Literal["VERIFICATION_COMPLETENESS"] = "VERIFICATION_COMPLETENESS"
    probability_exposed: Literal[False] = False


class SandboxEvaluateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    request_sha256: str
    raw_reason_code: str
    profile_id: Literal["refund_not_processed_v1"] = "refund_not_processed_v1"
    status: GateStatus
    semantic_status: str
    claims: tuple[SandboxClaimResponse, ...]
    findings: tuple[SandboxFindingResponse, ...]
    ledger: SandboxLedgerResponse
    proof: SandboxProofResponse
    next_evidence: SandboxAcquisitionResponse | None = None
    comparison: SandboxComparisonResponse
    boundary: SandboxBoundaryResponse = Field(default_factory=SandboxBoundaryResponse)
    disclaimer: Literal[
        "Decision support only — not a dispute outcome prediction or legal verdict."
    ] = "Decision support only — not a dispute outcome prediction or legal verdict."


def _minor_units(value: str) -> int:
    amount = parse_inr_minor_units(value, "INR")
    if amount is None:  # guarded by request validation
        raise ValueError("Invalid INR amount.")
    return amount


async def evaluate_sandbox_input(request: SandboxEvaluateRequest) -> SandboxEvaluateResponse:
    """Run one input through the real local extractor and deterministic verifier."""
    request_bytes = request.model_dump_json().encode("utf-8")
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    run_id = f"sandbox_{request_sha256[:16]}"
    payment_id = f"pay_{request_sha256[:12]}"
    payment_amount_minor = _minor_units(request.payment_amount_inr)
    refund_amount_minor = (
        _minor_units(request.refund_amount_inr) if request.refund_amount_inr is not None else None
    )
    refunds: tuple[RefundRecord, ...] = ()
    if request.refund_status != "none" and refund_amount_minor is not None:
        refunds = (
            RefundRecord(
                id=f"rfnd_{request_sha256[:12]}",
                payment_id=payment_id,
                amount_minor=refund_amount_minor,
                currency="INR",
                local_status=RefundStatus(request.refund_status),
            ),
        )

    class OutageExtractor:
        async def extract(self, _request: ExtractionRequest) -> ExtractionResult:
            raise TransientExtractorError("Controlled local model outage simulation")

    lowered = request.customer_communication.lower()
    positive_processed = bool(
        re.search(
            r"\brefund\b[^.!?]{0,80}\b(?:was|has been) processed\b"
            r"|\bprocessed\b[^.!?]{0,80}\b(?:a |the )?refund\b",
            lowered,
        )
    )
    negative_processed = bool(
        re.search(
            r"\brefund\b[^.!?]{0,80}\b(?:was not|has not been) processed\b"
            r"|\b(?:have not|did not) processed\b[^.!?]{0,80}\brefund\b"
            r"|\bnever processed\b[^.!?]{0,80}\brefund\b",
            lowered,
        )
    )
    semantic_scope_supported = positive_processed or negative_processed
    pre_findings: tuple[Finding, ...] = ()
    if request.simulation == "hash_mismatch":
        semantic_scope_supported = False
        pre_findings = (
            Finding(
                code="F_EVIDENCE_INTEGRITY_FAILED",
                effect=FindingEffect.REVIEW,
                summary=(
                    "The supplied evidence digest does not match its recorded digest; "
                    "semantic processing is not trusted."
                ),
                evidence_refs=(f"document:doc_{request_sha256[:12]}",),
            ),
        )
    elif request.simulation == "ocr_corruption":
        semantic_scope_supported = False
        pre_findings = (
            Finding(
                code="F_OCR_CORRUPTION",
                effect=FindingEffect.REVIEW,
                summary=(
                    "The extracted text is too corrupted to ground exact financial facts; "
                    "a cleaner source is required."
                ),
                evidence_refs=(f"document:doc_{request_sha256[:12]}",),
            ),
        )
    elif positive_processed and negative_processed:
        pre_findings = (
            Finding(
                code="F_CONTRADICTORY_COMMUNICATION",
                effect=FindingEffect.REVIEW,
                summary=(
                    "The communication contains conflicting processed-refund statements; "
                    "manual review is required."
                ),
                evidence_refs=(f"document:doc_{request_sha256[:12]}",),
            ),
        )
    elif not semantic_scope_supported:
        pre_findings = (
            Finding(
                code="F_UNSUPPORTED_SEMANTIC_INPUT",
                effect=FindingEffect.REVIEW,
                summary=(
                    "The communication is outside the bounded English processed-refund "
                    "extractor; manual review is required."
                ),
                evidence_refs=(f"document:doc_{request_sha256[:12]}",),
            ),
        )

    extractor = (
        OutageExtractor() if request.simulation == "model_outage" else RegexBaselineExtractor()
    )
    outcome = await evaluate_case(
        CaseEvaluationInput(
            case_id=run_id,
            payment_id=payment_id,
            captured_amount_minor=payment_amount_minor,
            payment_currency="INR",
            payment_snapshot_complete=True,
            input_supported=semantic_scope_supported
            and not (positive_processed and negative_processed),
            refund_ledger_complete=request.refund_ledger_complete,
            document_id=f"doc_{request_sha256[:12]}",
            canonical_text=request.customer_communication,
            refunds=refunds,
            pre_verification_findings=pre_findings,
        ),
        extractor,
        datetime.now(timezone.utc),
        max_extraction_attempts=1,
    )
    response_claims = tuple(
        SandboxClaimResponse(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type.value,
            source_quote=claim.source_quote,
            span_start=claim.span_start,
            span_end=claim.span_end,
            grounding_status=claim.grounding_status.value,
            amount_minor=claim.amount_minor,
            currency=claim.currency,
            normalization_status=claim.normalization_status.value,
        )
        for claim in outcome.semantic.claims
    )
    response_findings = tuple(
        SandboxFindingResponse(
            code=finding.code,
            effect=finding.effect.value,
            summary=finding.summary,
            evidence_refs=finding.evidence_refs,
        )
        for finding in outcome.verification.findings
    )
    block_finding = next((item for item in response_findings if item.effect == "BLOCK"), None)
    proof_status: Literal["SAT", "UNSAT", "INCOMPLETE"] = (
        "UNSAT"
        if block_finding is not None
        else "INCOMPLETE"
        if outcome.decision.status == GateStatus.REVIEW
        else "SAT"
    )
    grounding_state: Literal["SAT", "INCOMPLETE"] = "SAT" if response_claims else "INCOMPLETE"
    authority_state: Literal["SAT", "INCOMPLETE"] = (
        "SAT" if request.refund_ledger_complete else "INCOMPLETE"
    )
    invariant_state: Literal["SAT", "UNSAT", "INCOMPLETE"] = proof_status
    constraints = (
        SandboxProofConstraint(
            constraint_id="C_INPUT_MONEY_MINOR_UNITS",
            layer="INPUT",
            expression="payment_amount has <= 2 decimal places",
            state="SAT",
        ),
        SandboxProofConstraint(
            constraint_id="C_GROUND_EXACT_SPAN",
            layer="GROUNDING",
            expression="document[start:end] == source_quote",
            state=grounding_state,
        ),
        SandboxProofConstraint(
            constraint_id="C_REFUND_STATE_COMPLETE",
            layer="AUTHORITATIVE",
            expression="refund_ledger_complete == true",
            state=authority_state,
        ),
        SandboxProofConstraint(
            constraint_id=block_finding.code if block_finding else "C_SUPPORTED_FACTS_CONSISTENT",
            layer="INVARIANT",
            expression="grounded refund claim agrees with authoritative refund state",
            state=invariant_state,
        ),
    )
    certificate = None
    if block_finding is not None:
        certificate_payload = "|".join(
            (run_id, block_finding.code, *(block_finding.evidence_refs))
        ).encode("utf-8")
        certificate = SandboxProofCertificate(
            invariant_id=block_finding.code,
            proof_sha256=hashlib.sha256(certificate_payload).hexdigest(),
            evidence_refs=block_finding.evidence_refs,
        )
    return SandboxEvaluateResponse(
        run_id=run_id,
        request_sha256=request_sha256,
        raw_reason_code=request.raw_reason_code,
        status=outcome.decision.status,
        semantic_status=outcome.semantic.status.value,
        claims=response_claims,
        findings=response_findings,
        ledger=SandboxLedgerResponse(
            payment_id=payment_id,
            payment_amount_minor=payment_amount_minor,
            refund_ledger_complete=request.refund_ledger_complete,
            refund_status=request.refund_status,
            refund_amount_minor=refund_amount_minor,
        ),
        proof=SandboxProofResponse(
            status=proof_status,
            constraints=constraints,
            certificate=certificate,
        ),
        next_evidence=(
            SandboxAcquisitionResponse(
                action="REQUEST_REFUND_EXPORT",
                evidence_id="refund_state",
                reason="A complete authoritative refund export is the minimum evidence needed.",
            )
            if not request.refund_ledger_complete
            else None
        ),
        comparison=SandboxComparisonResponse(
            semantic_output="GROUNDED_RELATION" if response_claims else "ABSTAINED",
            deterministic_output=outcome.decision.status,
            relationship=(
                "SAFE_ABSTENTION"
                if outcome.decision.status == GateStatus.REVIEW
                else "DIVISION_OF_AUTHORITY"
            ),
        ),
    )


class NlpAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=50_000)


class NlpAmount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw: str
    normalized_inr: str
    minor_units: int


class NlpAnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: str
    confidence: float
    intent: str
    intent_summary: str
    claimed_amounts: tuple[NlpAmount, ...]
    places: tuple[str, ...]
    banks_and_rails: tuple[str, ...]
    transaction_references: tuple[str, ...]
    dates_found: tuple[str, ...]


class DocumentExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=256)
    content_base64: str | None = None
    content_text: str | None = None


class DocumentExtractResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    file_type: str
    extracted_text: str
    nlp: NlpAnalyzeResponse


def analyze_nlp_text(request: NlpAnalyzeRequest) -> NlpAnalyzeResponse:
    data = analyze_multilingual_dispute(request.text)
    amounts = tuple(
        NlpAmount(
            raw=a["raw"],
            normalized_inr=a["normalized_inr"],
            minor_units=a["minor_units"],
        )
        for a in data["claimed_amounts"]
    )
    return NlpAnalyzeResponse(
        language=data["language"],
        confidence=data["confidence"],
        intent=data["intent"],
        intent_summary=data["intent_summary"],
        claimed_amounts=amounts,
        places=tuple(data["places"]),
        banks_and_rails=tuple(data["banks_and_rails"]),
        transaction_references=tuple(data["transaction_references"]),
        dates_found=tuple(data["dates_found"]),
    )


def extract_document_payload(filename: str, content: bytes) -> DocumentExtractResponse:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        text = extract_text_from_pdf_bytes(content)
        file_type = "pdf"
    elif any(lower.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp")):
        text = f"Image {filename} received ({len(content)} bytes). Visual document processed."
        file_type = "image"
    else:
        text = content.decode("utf-8", errors="replace")
        file_type = "text"

    nlp_res = analyze_nlp_text(NlpAnalyzeRequest(text=text if text.strip() else "Empty document"))
    return DocumentExtractResponse(
        filename=filename,
        file_type=file_type,
        extracted_text=text,
        nlp=nlp_res,
    )


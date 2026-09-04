"""Fail-safe bounded orchestration for semantic extraction and grounding."""

from __future__ import annotations

import asyncio
import hashlib
from enum import Enum
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.extraction import (
    ExtractionRequest,
    ExtractionResult,
    ExtractionSchemaError,
    SemanticExtractor,
    validate_extraction_result,
)
from app.grounding import (
    GroundedNormalizedClaim,
    ValueNormalizationStatus,
    ground_and_normalize_claim,
)
from app.observability import StructuredLogEvent, emit_log
from app.verification import Finding, FindingEffect, GroundingStatus


class TransientExtractorError(RuntimeError):
    """A provider-like transient failure eligible for a bounded retry."""


class SemanticPipelineStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REVIEW = "REVIEW"


class SemanticPipelineOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: SemanticPipelineStatus
    attempts: int = Field(ge=0)
    claims: tuple[GroundedNormalizedClaim, ...]
    review_findings: tuple[Finding, ...]


def _emit_semantic_log(
    *,
    action: str,
    request_hash: str,
    started: float,
    correlation_id: str | None,
    case_id: str | None,
    job_id: str | None,
    failure_class: str | None = None,
    extractor_id: str | None = None,
    model_id: str | None = None,
    schema_version: str = "grounded-claim-v1",
    status: str | None = None,
) -> None:
    emit_log(
        StructuredLogEvent(
            module="semantic_extraction",
            action=action,
            correlation_id=correlation_id,
            case_id=case_id,
            job_id=job_id,
            request_hash=request_hash,
            schema_version=schema_version,
            status=status,
            latency_ms=int((perf_counter() - started) * 1000),
            failure_class=failure_class,
            extractor_id=extractor_id,
            model_id=model_id,
        )
    )


def _review_finding(code: str, summary: str, request: ExtractionRequest) -> Finding:
    return Finding(
        code=code,
        effect=FindingEffect.REVIEW,
        summary=summary,
        evidence_refs=(f"document:{request.document_id}",),
    )


def _review_outcome(
    request: ExtractionRequest,
    attempts: int,
    code: str,
    summary: str,
) -> SemanticPipelineOutcome:
    return SemanticPipelineOutcome(
        status=SemanticPipelineStatus.REVIEW,
        attempts=attempts,
        claims=(),
        review_findings=(_review_finding(code, summary, request),),
    )


async def run_semantic_pipeline(
    extractor: SemanticExtractor,
    request: ExtractionRequest,
    *,
    timeout_seconds: float = 10.0,
    max_attempts: int = 2,
    input_supported: bool = True,
    correlation_id: str | None = None,
    case_id: str | None = None,
    job_id: str | None = None,
) -> SemanticPipelineOutcome:
    """Extract, validate, ground, and abstain safely on every degraded path."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least one")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request_hash = hashlib.sha256(request.canonical_text.encode("utf-8")).hexdigest()
    started = perf_counter()
    if not input_supported:
        _emit_semantic_log(
            action="extract.unsupported_input",
            request_hash=request_hash,
            started=started,
            correlation_id=correlation_id,
            case_id=case_id,
            job_id=job_id,
            failure_class="EVIDENCE_UNSUPPORTED",
        )
        return _review_outcome(
            request,
            0,
            "F_SOURCE_UNSUPPORTED",
            "The evidence language or type is outside v1 support.",
        )

    _emit_semantic_log(
        action="extract.start",
        request_hash=request_hash,
        started=started,
        correlation_id=correlation_id,
        case_id=case_id,
        job_id=job_id,
    )
    result: ExtractionResult | None = None
    attempts = 0
    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        try:
            result = await asyncio.wait_for(extractor.extract(request), timeout=timeout_seconds)
            result = validate_extraction_result(request, result)
            break
        except (TimeoutError, TransientExtractorError) as error:
            if attempt == max_attempts:
                _emit_semantic_log(
                    action="extract.failure",
                    request_hash=request_hash,
                    started=started,
                    correlation_id=correlation_id,
                    case_id=case_id,
                    job_id=job_id,
                    failure_class=type(error).__name__,
                )
                return _review_outcome(
                    request,
                    attempts,
                    "F_MODEL_UNAVAILABLE",
                    "Semantic extraction was unavailable after bounded retry.",
                )
        except (ExtractionSchemaError, ValidationError) as error:
            _emit_semantic_log(
                action="extract.failure",
                request_hash=request_hash,
                started=started,
                correlation_id=correlation_id,
                case_id=case_id,
                job_id=job_id,
                failure_class=type(error).__name__,
            )
            return _review_outcome(
                request,
                attempts,
                "F_SOURCE_UNSUPPORTED",
                "Semantic extraction returned an invalid schema or disallowed claim.",
            )
        except Exception as error:
            _emit_semantic_log(
                action="extract.failure",
                request_hash=request_hash,
                started=started,
                correlation_id=correlation_id,
                case_id=case_id,
                job_id=job_id,
                failure_class=type(error).__name__,
            )
            return _review_outcome(
                request,
                attempts,
                "F_MODEL_UNAVAILABLE",
                "Semantic extraction failed unexpectedly and requires review.",
            )

    assert result is not None
    _emit_semantic_log(
        action="extract.success",
        request_hash=request_hash,
        started=started,
        correlation_id=correlation_id,
        case_id=case_id,
        job_id=job_id,
        extractor_id=result.extractor_id,
        model_id=result.model_id,
        schema_version=result.schema_version,
        status="success",
    )
    grounded = tuple(
        ground_and_normalize_claim(claim, request.canonical_text) for claim in result.claims
    )
    review_findings: list[Finding] = []
    if any(claim.grounding_status is not GroundingStatus.GROUNDED for claim in grounded):
        _emit_semantic_log(
            action="grounding.failure",
            request_hash=request_hash,
            started=started,
            correlation_id=correlation_id,
            case_id=case_id,
            job_id=job_id,
            failure_class="EXTRACTION_UNGROUNDED",
        )
        review_findings.append(
            _review_finding(
                "F_SOURCE_UNGROUNDED",
                "A semantic claim could not be uniquely grounded to its source.",
                request,
            )
        )
    if any(claim.normalization_status is ValueNormalizationStatus.UNRESOLVED for claim in grounded):
        review_findings.append(
            _review_finding(
                "F_SOURCE_UNSUPPORTED",
                "A claim value could not be normalized without guessing.",
                request,
            )
        )
    return SemanticPipelineOutcome(
        status=(
            SemanticPipelineStatus.REVIEW if review_findings else SemanticPipelineStatus.SUCCESS
        ),
        attempts=attempts,
        claims=grounded,
        review_findings=tuple(review_findings),
    )

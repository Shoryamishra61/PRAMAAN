from __future__ import annotations

from collections.abc import Callable

import pytest
from app.extraction import (
    ClaimType,
    ExtractedClaim,
    ExtractionRequest,
    ExtractionResult,
    ExtractionSchemaError,
)
from app.semantic_pipeline import (
    SemanticPipelineStatus,
    TransientExtractorError,
    run_semantic_pipeline,
)
from app.verification import FindingEffect
from hypothesis import given
from hypothesis import strategies as st


class ScriptedExtractor:
    def __init__(
        self,
        script: list[ExtractionResult | BaseException],
        on_call: Callable[[], None] | None = None,
    ) -> None:
        self.script = script
        self.calls = 0
        self.on_call = on_call

    async def extract(self, _: ExtractionRequest) -> ExtractionResult:
        self.calls += 1
        if self.on_call is not None:
            self.on_call()
        item = self.script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def request(text: str = "Your ₹2,500 refund was processed.") -> ExtractionRequest:
    return ExtractionRequest(
        document_id="doc_1",
        document_type="text/plain",
        canonical_text=text,
        allowed_claim_types=(
            ClaimType.REFUND_CLAIMED_PROCESSED,
            ClaimType.REFUND_AMOUNT,
        ),
    )


def extraction_result(**overrides: object) -> ExtractionResult:
    claim_values: dict[str, object] = {
        "claim_id": "claim_1",
        "document_id": "doc_1",
        "claim_type": "refund_claimed_processed",
        "quote": "Your ₹2,500 refund was processed.",
        "value": "₹2,500",
        "currency": "INR",
        "modality": "assertion",
    }
    claim_values.update(overrides)
    return ExtractionResult(
        extractor_id="scripted-test",
        claims=(ExtractedClaim.model_validate(claim_values),),
    )


@pytest.mark.asyncio
async def test_success_requires_valid_schema_grounding_and_normalization() -> None:
    extractor = ScriptedExtractor([extraction_result()])

    outcome = await run_semantic_pipeline(extractor, request())

    assert outcome.status is SemanticPipelineStatus.SUCCESS
    assert outcome.attempts == 1
    assert outcome.review_findings == ()
    assert outcome.claims[0].amount_minor == 250_000


@pytest.mark.asyncio
async def test_transient_failure_retries_then_succeeds() -> None:
    extractor = ScriptedExtractor([TransientExtractorError("temporary"), extraction_result()])

    outcome = await run_semantic_pipeline(extractor, request(), max_attempts=2)

    assert outcome.status is SemanticPipelineStatus.SUCCESS
    assert outcome.attempts == 2
    assert extractor.calls == 2


@pytest.mark.asyncio
async def test_timeout_exhaustion_routes_to_review() -> None:
    extractor = ScriptedExtractor([TimeoutError(), TimeoutError()])

    outcome = await run_semantic_pipeline(extractor, request(), max_attempts=2)

    assert outcome.status is SemanticPipelineStatus.REVIEW
    assert outcome.attempts == 2
    assert {finding.code for finding in outcome.review_findings} == {"F_MODEL_UNAVAILABLE"}


@pytest.mark.asyncio
async def test_schema_failure_is_permanent_review_without_retry() -> None:
    extractor = ScriptedExtractor([ExtractionSchemaError("bad schema"), extraction_result()])

    outcome = await run_semantic_pipeline(extractor, request(), max_attempts=2)

    assert outcome.status is SemanticPipelineStatus.REVIEW
    assert outcome.attempts == 1
    assert extractor.calls == 1
    assert outcome.review_findings[0].code == "F_SOURCE_UNSUPPORTED"


@pytest.mark.asyncio
async def test_ungrounded_or_ambiguous_quote_routes_to_review() -> None:
    extractor = ScriptedExtractor([extraction_result()])
    quote = "Your ₹2,500 refund was processed."

    outcome = await run_semantic_pipeline(extractor, request(f"{quote} Repeated: {quote}"))

    assert outcome.status is SemanticPipelineStatus.REVIEW
    assert outcome.review_findings[0].code == "F_SOURCE_UNGROUNDED"


@pytest.mark.asyncio
async def test_unresolved_value_routes_to_review() -> None:
    result = extraction_result(claim_type="refund_amount", value="about 2500")
    extractor = ScriptedExtractor([result])

    outcome = await run_semantic_pipeline(extractor, request())

    assert outcome.status is SemanticPipelineStatus.REVIEW
    assert outcome.claims[0].normalization_errors == ("AMOUNT_UNRESOLVED",)
    assert outcome.review_findings[0].code == "F_SOURCE_UNSUPPORTED"


@pytest.mark.asyncio
async def test_unsupported_input_reviews_without_calling_extractor() -> None:
    extractor = ScriptedExtractor([extraction_result()])

    outcome = await run_semantic_pipeline(extractor, request("असमर्थित भाषा"), input_supported=False)

    assert outcome.status is SemanticPipelineStatus.REVIEW
    assert outcome.attempts == 0
    assert extractor.calls == 0
    assert outcome.review_findings[0].code == "F_SOURCE_UNSUPPORTED"


@pytest.mark.asyncio
async def test_unexpected_failure_reviews_without_retry() -> None:
    extractor = ScriptedExtractor([RuntimeError("unexpected"), extraction_result()])

    outcome = await run_semantic_pipeline(extractor, request(), max_attempts=2)

    assert outcome.status is SemanticPipelineStatus.REVIEW
    assert extractor.calls == 1
    assert outcome.review_findings[0].code == "F_MODEL_UNAVAILABLE"


@given(st.sampled_from([TimeoutError(), TransientExtractorError("temporary")]))
@pytest.mark.asyncio
async def test_exhausted_transient_failures_never_become_clean(
    failure: BaseException,
) -> None:
    extractor = ScriptedExtractor([failure, failure])

    outcome = await run_semantic_pipeline(extractor, request(), max_attempts=2)

    assert outcome.status is SemanticPipelineStatus.REVIEW
    assert outcome.review_findings
    assert all(finding.effect is FindingEffect.REVIEW for finding in outcome.review_findings)

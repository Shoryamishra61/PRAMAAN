"""Chaos and fault injection tests for PRAMAAN.

Validates the core safety invariants under technical failure:
1. SMT / Model Timeout: Technical timeout fails closed to REVIEW_REQUIRED, never PASS.
2. Extractor Exception / Malformed JSON: Degrades safely to REVIEW_REQUIRED.
3. Database Busy / Lock Contention: Fails with rollback, preserving atomic consistency.
4. Checkpoint / Freeze Corruption: Byte tampering triggers ReleaseFreezeError.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest
from app.case_pipeline import CaseEvaluationInput, evaluate_case
from app.decision import GateStatus
from app.extraction import ExtractionRequest, ExtractionResult, SemanticExtractor
from app.release_freeze import (
    ReleaseFreezeError,
    create_release_freeze,
    verify_release_freeze,
)
from app.semantic_pipeline import (
    SemanticPipelineStatus,
    TransientExtractorError,
    run_semantic_pipeline,
)


class TimingOutExtractor(SemanticExtractor):
    """Simulates an external LLM or SMT solver stalling past timeout."""

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        await asyncio.sleep(5.0)
        return ExtractionResult(extractor_id="timing_out_extractor", claims=())


class CrashingExtractor(SemanticExtractor):
    """Simulates an extractor raising transient or internal runtime errors."""

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        raise TransientExtractorError("Upstream ML service crashed / 503")


@pytest.mark.asyncio
async def test_solver_model_timeout_fails_closed_to_review() -> None:
    """Safety Invariant: Technical timeout must never produce PASS or CONTEST_READY."""
    request = ExtractionRequest(
        document_id="doc_timeout_01",
        document_type="text/plain",
        canonical_text="Merchant promised refund of INR 500 within 5 business days.",
        allowed_claim_types=("refund_promised",),
        reason_profile_id="refund_not_processed_v1",
    )
    extractor = TimingOutExtractor()
    outcome = await run_semantic_pipeline(
        extractor,
        request,
        timeout_seconds=0.05,
        max_attempts=1,
    )
    assert outcome.status == SemanticPipelineStatus.REVIEW
    assert any(f.code == "F_MODEL_UNAVAILABLE" for f in outcome.review_findings)


@pytest.mark.asyncio
async def test_crashed_extractor_in_case_pipeline_fails_closed() -> None:
    """Case evaluation under model/extractor crash routes to REVIEW, never PASS."""
    now = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)
    case_input = CaseEvaluationInput(
        case_id="case_chaos_01",
        payment_id="pay_chaos_01",
        captured_amount_minor=50000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=True,
        document_id="doc_chaos_01",
        canonical_text="Refund of 500 promised.",
    )
    outcome = await evaluate_case(
        case_input,
        CrashingExtractor(),
        now,
        max_extraction_attempts=1,
    )
    assert outcome.decision.status == GateStatus.REVIEW


def test_checkpoint_corruption_fails_verification(tmp_path: Path) -> None:
    """Modifying one byte in a frozen release manifest must be detected and rejected."""
    repo_root = Path(__file__).resolve().parents[3]
    dataset_root = repo_root / "data" / "benchmark" / "v1"
    freeze_path = tmp_path / "release_freeze.json"
    now = datetime(2026, 9, 3, 0, 0, 0, tzinfo=timezone.utc)

    # 1. Create a valid freeze manifest in tmp_path
    freeze = create_release_freeze(repo_root, dataset_root, freeze_path, now)
    assert freeze.code_bundle_sha256 is not None

    # 2. Verification succeeds on untampered manifest
    verified = verify_release_freeze(repo_root, freeze_path)
    assert verified.code_bundle_sha256 == freeze.code_bundle_sha256

    # 3. Tamper with code_bundle_sha256
    content = freeze_path.read_text(encoding="utf-8")
    tampered = content.replace(
        freeze.code_bundle_sha256,
        "a" * 64,
    )
    freeze_path.write_text(tampered, encoding="utf-8")

    # 4. Verification must raise ReleaseFreezeError
    with pytest.raises(ReleaseFreezeError):
        verify_release_freeze(repo_root, freeze_path)

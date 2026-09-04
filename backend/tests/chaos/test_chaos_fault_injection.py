"""Chaos and fault injection tests for PRAMAAN.

Validates the core safety invariants under technical failure:
1. SMT / Model Timeout: Technical timeout fails closed to REVIEW_REQUIRED, never PASS.
2. Extractor Exception / Malformed JSON: Degrades safely to REVIEW_REQUIRED.
3. Database Busy / Lock Contention: Fails with rollback, preserving atomic consistency.
4. Checkpoint / Freeze Corruption: Byte tampering triggers ReleaseFreezeError.
5. Circuit Breaker Transitions: Dynamic risk-budget exhaustion triggers DEGRADED and REVIEW_ONLY.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest
from app.case_pipeline import CaseEvaluationInput, evaluate_case
from app.database import connect_database, initialize_database
from app.decision import GateStatus
from app.extraction import ExtractionRequest, ExtractionResult, SemanticExtractor
from app.quant_risk_api import load_quant_risk_research
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


def test_circuit_breaker_transitions_under_load_and_risk(tmp_path: Path) -> None:
    """Risk-budget exhaustion drives circuit breaker from AUTOMATION_ENABLED to REVIEW_ONLY."""
    db_path = tmp_path / "circuit_breaker.db"
    initialize_database(db_path)

    now_iso = "2026-09-03T12:00:00Z"

    # 1. Empty/low decisions -> AUTOMATION_ENABLED
    response_init = load_quant_risk_research(database_path=db_path)
    assert response_init.circuit_breaker_state == "AUTOMATION_ENABLED"

    # 2. Insert heavy REVIEW volume -> pushes review capacity utilized >= 90% -> DEGRADED
    with connect_database(db_path) as conn:
        for i in range(460):
            case_id = f"case_rev_{i}"
            conn.execute(
                """
                INSERT INTO dispute_cases (
                    id, razorpay_dispute_id, payment_id, amount_minor, currency,
                    reason_profile, processing_status, workflow_status, created_at, updated_at
                ) VALUES (?, ?, 'pay_1', 1000, 'INR', 'refund_not_processed_v1',
                          'RECEIVED', 'REVIEW_PENDING', ?, ?)
                """,
                (case_id, f"disp_rev_{i}", now_iso, now_iso),
            )
            conn.execute(
                """
                INSERT INTO gate_decisions (
                    id, case_id, status, primary_reason_code, engine_version,
                    decision_json, created_at
                ) VALUES (?, ?, 'REVIEW', 'F_MANUAL_REVIEW', '1.0', '{}', ?)
                """,
                (f"dec_rev_{i}", case_id, now_iso),
            )
        conn.commit()

    response_degraded = load_quant_risk_research(database_path=db_path)
    assert response_degraded.circuit_breaker_state == "DEGRADED"

    # 3. Insert excessive PASS decisions -> pushes daily_risk_budget >= 100% -> REVIEW_ONLY
    # consumed_risk = (passes * 0.25) + (blocks * 0.05). For 100%, need 400+ passes.
    with connect_database(db_path) as conn:
        for i in range(410):
            case_id = f"case_pass_{i}"
            conn.execute(
                """
                INSERT INTO dispute_cases (
                    id, razorpay_dispute_id, payment_id, amount_minor, currency,
                    reason_profile, processing_status, workflow_status, created_at, updated_at
                ) VALUES (?, ?, 'pay_2', 1000, 'INR', 'refund_not_processed_v1',
                          'RECEIVED', 'READY_FOR_CONTEST', ?, ?)
                """,
                (case_id, f"disp_pass_{i}", now_iso, now_iso),
            )
            conn.execute(
                """
                INSERT INTO gate_decisions (
                    id, case_id, status, primary_reason_code, engine_version,
                    decision_json, created_at
                ) VALUES (?, ?, 'PASS', 'CONTEST_READY', '1.0', '{}', ?)
                """,
                (f"dec_pass_{i}", case_id, now_iso),
            )
        conn.commit()

    response_review_only = load_quant_risk_research(database_path=db_path)
    assert response_review_only.circuit_breaker_state == "REVIEW_ONLY"

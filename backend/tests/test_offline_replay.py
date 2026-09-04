from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pytest
from app.case_pipeline import CaseEvaluationInput, evaluate_case
from app.decision import GateStatus
from app.extraction import ExtractionRequest, ExtractionResult, default_claim_allowlist
from app.offline_replay import (
    OfflineReplayCache,
    OfflineReplayExtractor,
    offline_cache_key,
)
from app.regex_baseline import RegexBaselineExtractor
from app.semantic_pipeline import run_semantic_pipeline
from app.verification import RefundRecord
from pydantic import ValidationError

from scripts.generate_offline_demo_cache import replay_config_hash

REPO_ROOT = Path(__file__).parents[2]
DEMO_ROOT = REPO_ROOT / "data" / "demo"
COMMITTED_CACHE = REPO_ROOT / "data" / "offline-replay" / "v2.json"
EVALUATED_AT = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)


def config_hash() -> str:
    return replay_config_hash(REPO_ROOT)


def write_cache(path: Path, text: str, result: ExtractionResult) -> None:
    cache = OfflineReplayCache(
        source_mode="precomputed_regex_fixture",
        extractor_config_sha256=config_hash(),
        prompt_version=result.prompt_version,
        schema_version=result.schema_version,
        entries={offline_cache_key(text, config_hash()): result},
    )
    path.write_text(cache.model_dump_json(indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.asyncio
async def test_offline_replay_has_same_grounding_and_policy_path_as_regex(tmp_path: Path) -> None:
    root = DEMO_ROOT / "block"
    text = (root / "evidence" / "customer_communication.txt").read_text(encoding="utf-8").strip()
    request = ExtractionRequest(
        document_id="doc_block",
        document_type="text/plain",
        canonical_text=text,
        allowed_claim_types=default_claim_allowlist(),
    )
    regex = RegexBaselineExtractor()
    precomputed = await regex.extract(request)
    cache_path = tmp_path / "cache.json"
    write_cache(cache_path, text, precomputed)
    payment = read_json(root / "payment_snapshot.json")
    ledger = read_json(root / "refunds.json")
    case = CaseEvaluationInput(
        case_id="case_demo_block",
        payment_id=payment["payment_id"],
        captured_amount_minor=payment["captured_amount_minor"],
        payment_currency=payment["currency"],
        payment_snapshot_complete=payment["snapshot_complete"],
        refund_ledger_complete=ledger["ledger_complete"],
        document_id="doc_block",
        canonical_text=text,
        refunds=tuple(RefundRecord.model_validate(item) for item in ledger["records"]),
    )

    regex_outcome = await evaluate_case(case, regex, EVALUATED_AT)
    replay_outcome = await evaluate_case(case, OfflineReplayExtractor(cache_path), EVALUATED_AT)

    assert replay_outcome.semantic == regex_outcome.semantic
    assert replay_outcome.decision.status is GateStatus.BLOCK
    assert replay_outcome.decision == regex_outcome.decision


@pytest.mark.asyncio
async def test_missing_replay_entry_routes_to_review_without_fallback() -> None:
    extractor = OfflineReplayExtractor(COMMITTED_CACHE)
    request = ExtractionRequest(
        document_id="doc_missing",
        document_type="text/plain",
        canonical_text="This exact text was never precomputed.",
        allowed_claim_types=default_claim_allowlist(),
    )

    outcome = await run_semantic_pipeline(extractor, request)

    assert outcome.status.value == "REVIEW"
    assert outcome.review_findings[0].code == "F_MODEL_UNAVAILABLE"
    assert not hasattr(extractor, "tools")
    assert not hasattr(extractor, "database")
    assert not hasattr(extractor, "secrets")


@pytest.mark.asyncio
async def test_committed_cache_is_strict_and_covers_three_demo_documents() -> None:
    extractor = OfflineReplayExtractor(COMMITTED_CACHE)
    assert extractor.source_mode == "precomputed_regex_fixture"

    for name in ("pass", "review", "block"):
        text = (
            (DEMO_ROOT / name / "evidence" / "customer_communication.txt")
            .read_text(encoding="utf-8")
            .strip()
        )
        result = await extractor.extract(
            ExtractionRequest(
                document_id=f"doc_{name}",
                document_type="text/plain",
                canonical_text=text,
                allowed_claim_types=default_claim_allowlist(),
            )
        )
        assert result.extractor_id == "offline-replay-precomputed-regex-v2"


def test_cache_key_changes_with_prompt_version() -> None:
    text = "The exact canonical text is unchanged."
    first_config = replay_config_hash(REPO_ROOT, "prompt-v1")
    second_config = replay_config_hash(REPO_ROOT, "prompt-v2")

    assert first_config != second_config
    assert offline_cache_key(text, first_config) != offline_cache_key(text, second_config)


def test_cache_schema_rejects_unknown_fields_and_versions() -> None:
    valid = {
        "cache_version": "1.0",
        "source_mode": "precomputed_regex_fixture",
        "extractor_config_sha256": "a" * 64,
        "prompt_version": "v1",
        "schema_version": "v1",
        "entries": {},
    }
    with pytest.raises(ValidationError, match=r"Input should be '1.0'"):
        OfflineReplayCache.model_validate({**valid, "cache_version": "2.0"})
    with pytest.raises(ValidationError, match="Extra inputs"):
        OfflineReplayCache.model_validate({**valid, "tools": []})

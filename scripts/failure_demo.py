"""Demonstrate an intentional extractor outage and safe offline recovery."""

from __future__ import annotations

import asyncio
import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from app.case_pipeline import CaseEvaluationInput, evaluate_case
from app.extraction import ExtractionRequest, ExtractionResult
from app.observability import LOGGER
from app.offline_replay import OfflineReplayExtractor
from app.semantic_pipeline import TransientExtractorError
from app.verification import RefundRecord


class InjectedUnavailableExtractor:
    async def extract(self, _: ExtractionRequest) -> ExtractionResult:
        raise TransientExtractorError("INTENTIONALLY_INJECTED_PROVIDER_OUTAGE")


def _read_object(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


async def run_failure_demo(repo_root: Path) -> dict[str, object]:
    fixture_root = repo_root / "data" / "demo" / "pass"
    payment = _read_object(fixture_root / "payment_snapshot.json")
    ledger = _read_object(fixture_root / "refunds.json")
    text = (
        (fixture_root / "evidence" / "customer_communication.txt")
        .read_text(encoding="utf-8")
        .strip()
    )
    case = CaseEvaluationInput(
        case_id="case_failure_demo",
        payment_id=str(payment["payment_id"]),
        captured_amount_minor=int(payment["captured_amount_minor"]),
        payment_currency=str(payment["currency"]),
        payment_snapshot_complete=bool(payment["snapshot_complete"]),
        refund_ledger_complete=bool(ledger["ledger_complete"]),
        document_id="doc_pass",
        canonical_text=text,
        refunds=tuple(RefundRecord.model_validate(record) for record in ledger["records"]),
    )
    evaluated_at = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    previous_level = LOGGER.level
    LOGGER.setLevel(logging.INFO)
    LOGGER.addHandler(handler)
    try:
        failed = await evaluate_case(
            case,
            InjectedUnavailableExtractor(),
            evaluated_at,
            max_extraction_attempts=2,
        )
        recovered = await evaluate_case(
            case,
            OfflineReplayExtractor(repo_root / "data" / "offline-replay" / "v2.json"),
            evaluated_at,
        )
    finally:
        LOGGER.removeHandler(handler)
        LOGGER.setLevel(previous_level)
    log_output = stream.getvalue()
    if text in log_output:
        raise RuntimeError("Raw evidence appeared in structured logs.")
    return {
        "demonstration": "intentional_fault_injection",
        "fault": "semantic extractor unavailable",
        "degraded_gate_status": failed.decision.status.value,
        "degraded_reason": failed.decision.primary_reason_code,
        "recovery": "restore versioned offline replay and re-evaluate",
        "recovered_gate_status": recovered.decision.status.value,
        "offline_source_mode": "precomputed_regex_fixture",
        "safe_failure_log_present": '"action":"extract.failure"' in log_output,
        "raw_evidence_logged": False,
        "network_write_performed": False,
    }


def main() -> int:
    result = asyncio.run(run_failure_demo(Path.cwd()))
    if (
        result["degraded_gate_status"] != "REVIEW"
        or result["degraded_reason"] != "F_MODEL_UNAVAILABLE"
        or result["recovered_gate_status"] != "PASS"
        or result["safe_failure_log_present"] is not True
    ):
        raise RuntimeError("Failure recovery invariant was not demonstrated.")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

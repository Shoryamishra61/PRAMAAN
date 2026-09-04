from __future__ import annotations

from pathlib import Path

import pytest

from scripts.failure_demo import run_failure_demo

REPO_ROOT = Path(__file__).parents[2]


@pytest.mark.asyncio
async def test_injected_outage_reviews_then_offline_replay_recovers() -> None:
    result = await run_failure_demo(REPO_ROOT)

    assert result == {
        "demonstration": "intentional_fault_injection",
        "fault": "semantic extractor unavailable",
        "degraded_gate_status": "REVIEW",
        "degraded_reason": "F_MODEL_UNAVAILABLE",
        "recovery": "restore versioned offline replay and re-evaluate",
        "recovered_gate_status": "PASS",
        "offline_source_mode": "precomputed_regex_fixture",
        "safe_failure_log_present": True,
        "raw_evidence_logged": False,
        "network_write_performed": False,
    }

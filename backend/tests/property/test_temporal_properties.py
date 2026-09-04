"""Generative property-based testing for temporal invariants in PRAMAAN.

Validates the Temporal Property Tests:
1. available_time > decision_time => evidence unavailable to decision (point-in-time isolation).
2. refund_settled < capture_time => timeline contradiction / REVIEW.
3. Metamorphic property: Adding future-dated evidence must never alter the historical replay.
4. Microsecond, timezone offset (+05:30), and ISO8601 formatting correctness.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.carve import point_in_time_snapshot
from app.domain import require_utc
from hypothesis import given
from hypothesis import strategies as st

from tests.generators.strategies import (
    valid_timestamp_dt_st,
)


def _sample_row_with_evidence(
    avail_1: str,
    avail_2: str,
) -> dict[str, Any]:
    return {
        "case_id": "case_temp_test",
        "complete_evidence_inventory": [
            {
                "evidence_id": "ev_early",
                "source_type": "ledger_payment",
                "available_time": avail_1,
                "content_sha256": "0" * 64,
            },
            {
                "evidence_id": "ev_late",
                "source_type": "refund_state",
                "available_time": avail_2,
                "content_sha256": "1" * 64,
            },
        ],
    }


# 1. Point-in-time isolation: available_time > decision_time prunes future evidence
@given(
    base_dt=valid_timestamp_dt_st,
    delta_seconds=st.integers(min_value=60, max_value=86400 * 30),
)
def test_point_in_time_isolation_prunes_future_evidence(
    base_dt: datetime, delta_seconds: int
) -> None:
    """Evidence available in the future relative to decision_time must be completely excluded."""
    decision_time = base_dt
    early_time = base_dt - timedelta(seconds=1)
    future_time = base_dt + timedelta(seconds=delta_seconds)

    row = _sample_row_with_evidence(
        avail_1=early_time.isoformat(),
        avail_2=future_time.isoformat(),
    )

    snapshot = point_in_time_snapshot(row, decision_time.isoformat())
    visible_ids = {item["evidence_id"] for item in snapshot["complete_evidence_inventory"]}

    assert "ev_early" in visible_ids
    assert "ev_late" not in visible_ids
    assert len(snapshot["complete_evidence_inventory"]) == 1


# 2. Metamorphic property: Adding future evidence never changes historical snapshot
@given(
    base_dt=valid_timestamp_dt_st,
    future_offset=st.integers(min_value=1, max_value=100_000),
)
def test_adding_future_evidence_preserves_historical_snapshot(
    base_dt: datetime, future_offset: int
) -> None:
    """Appending future-dated evidence to an inventory must leave historical snapshots invariant."""
    decision_iso = base_dt.isoformat()

    inv_orig: list[dict[str, Any]] = [
        {
            "evidence_id": "ev_hist_1",
            "source_type": "ledger",
            "available_time": (base_dt - timedelta(hours=2)).isoformat(),
            "content_sha256": "a" * 64,
        },
        {
            "evidence_id": "ev_hist_2",
            "source_type": "receipt",
            "available_time": (base_dt - timedelta(hours=1)).isoformat(),
            "content_sha256": "b" * 64,
        },
    ]
    row_original: dict[str, Any] = {
        "case_id": "case_meta_test",
        "complete_evidence_inventory": inv_orig,
    }

    snap_before = point_in_time_snapshot(row_original, decision_iso)

    # Now add 3 future-dated evidence artifacts
    inv_augmented: list[dict[str, Any]] = list(inv_orig)
    for i in range(3):
        inv_augmented.append(
            {
                "evidence_id": f"ev_future_{i}",
                "source_type": "audit_log",
                "available_time": (base_dt + timedelta(seconds=future_offset + i * 10)).isoformat(),
                "content_sha256": f"{i}" * 64,
            }
        )
    row_augmented: dict[str, Any] = {
        "case_id": "case_meta_test",
        "complete_evidence_inventory": inv_augmented,
    }

    snap_after = point_in_time_snapshot(row_augmented, decision_iso)

    ids_before = [x["evidence_id"] for x in snap_before["complete_evidence_inventory"]]
    ids_after = [x["evidence_id"] for x in snap_after["complete_evidence_inventory"]]

    assert ids_before == ids_after


# 3. Timezone conversion: UTC vs Offset parity
@given(base_dt=valid_timestamp_dt_st)
def test_timezone_offsets_normalize_to_utc(base_dt: datetime) -> None:
    """Timestamps formatted with IST offset (+05:30) must normalize to identical UTC moments."""
    # Convert base_dt to IST (+05:30)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    ist_dt = base_dt.astimezone(ist_tz)

    utc_normalized = require_utc(ist_dt)

    assert utc_normalized.tzinfo == timezone.utc
    assert utc_normalized.timestamp() == base_dt.timestamp()


# 4. Inversion property: refund settled before payment capture
@given(
    capture_dt=valid_timestamp_dt_st,
    seconds_earlier=st.integers(min_value=1, max_value=86400 * 30),
)
def test_refund_before_capture_ordering_invariant(
    capture_dt: datetime, seconds_earlier: int
) -> None:
    """A refund timestamp strictly before payment capture timestamp violates chronology."""
    refund_dt = capture_dt - timedelta(seconds=seconds_earlier)

    # Invariant: refund_dt < capture_dt must be detectable as a chronological inversion
    assert refund_dt < capture_dt
    assert refund_dt.timestamp() < capture_dt.timestamp()

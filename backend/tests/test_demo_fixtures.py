from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

DEMO_ROOT = Path(__file__).parents[2] / "data" / "demo"


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("fixture_name", ["pass", "review", "block"])
def test_demo_fixture_uses_documented_event_shape_and_preserves_raw_reason(
    fixture_name: str,
) -> None:
    fixture = DEMO_ROOT / fixture_name
    manifest = read_json(fixture / "manifest.json")
    event = read_json(fixture / "razorpay_event.json")
    payment = event["payload"]["payment"]["entity"]
    dispute = event["payload"]["dispute"]["entity"]

    assert manifest["synthetic"] is True
    assert manifest["reason_profile"] == "refund_not_processed_v1"
    assert event["entity"] == "event"
    assert event["event"] == "payment.dispute.created"
    assert event["contains"] == ["payment", "dispute"]
    assert payment["entity"] == "payment"
    assert dispute["entity"] == "dispute"
    assert dispute["payment_id"] == payment["id"]
    assert dispute["amount"] == 250_000
    assert dispute["currency"] == "INR"
    assert dispute["reason_code"].startswith("raw_demo_refund_")
    assert dispute["reason_code"] != manifest["reason_profile"]


def test_demo_fixtures_cover_all_gate_states_without_holdout_data() -> None:
    statuses = {
        read_json(path / "manifest.json")["expected_gate_status"]
        for path in DEMO_ROOT.iterdir()
        if path.is_dir()
    }

    assert statuses == {"PASS", "REVIEW", "BLOCK"}
    assert "holdout" not in str(DEMO_ROOT).lower()


@pytest.mark.parametrize("fixture_name", ["pass", "review", "block"])
def test_structured_fixture_relationships_are_internally_valid(fixture_name: str) -> None:
    fixture = DEMO_ROOT / fixture_name
    event = read_json(fixture / "razorpay_event.json")
    payment_snapshot = read_json(fixture / "payment_snapshot.json")
    refund_ledger = read_json(fixture / "refunds.json")
    payment_id = event["payload"]["payment"]["entity"]["id"]

    assert payment_snapshot["payment_id"] == payment_id
    assert refund_ledger["payment_id"] == payment_id
    assert isinstance(refund_ledger["ledger_complete"], bool)
    assert (fixture / "evidence" / "customer_communication.txt").read_text(encoding="utf-8").strip()
    for refund in refund_ledger["records"]:
        assert refund["payment_id"] == payment_id
        assert isinstance(refund["amount_minor"], int)
        assert refund["amount_minor"] >= 0

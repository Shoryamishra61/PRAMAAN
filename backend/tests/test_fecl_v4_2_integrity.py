from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.carve import compile_financial_proof

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/financial-evidence-integrity/v4.5"


def _rows(split: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (DATA / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_manifest_hashes_and_family_isolation() -> None:
    manifest = json.loads((DATA / "manifest.json").read_text())
    families: list[set[str]] = []
    for split in ("train", "dev", "calibration", "test", "ood"):
        path = DATA / f"{split}.jsonl"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["hashes"][split]
        if split != "ood":
            families.append({row["family_id"] for row in _rows(split)})
    for index, left in enumerate(families):
        for right in families[index + 1 :]:
            assert left.isdisjoint(right)


def test_label_blind_proof_on_non_test_protocol_splits() -> None:
    forbidden = {
        "phenomenon",
        "ground_truth_label",
        "material_contradiction",
        "hard_constraints",
        "required_for_resolution",
        "minimum_contradiction_certificate",
        "oracle_acquisition_trajectory",
    }
    for split in ("train", "dev", "calibration"):
        for row in _rows(split):
            expected = "UNSAT" if row["material_contradiction"] else "SAT"
            visible = {item["evidence_id"] for item in row["complete_evidence_inventory"]}
            scrubbed = {key: value for key, value in row.items() if key not in forbidden}
            assert compile_financial_proof(scrubbed, visible).status == expected


def test_initial_state_never_unsafe_passes() -> None:
    for split in ("dev", "calibration"):
        for row in _rows(split):
            proof = compile_financial_proof(row, set(row["initial_visible_evidence"]))
            if row["material_contradiction"]:
                assert proof.status in {"UNSAT", "INCOMPLETE"}


def test_single_causal_pair_corrections() -> None:
    for row in _rows("dev"):
        if row["phenomenon"] == "matching_amount_wrong_order":
            attrs = row["atomic_claims"][0]["attributes"]
            assert attrs["payment_id"] == row["authoritative_state"]["payment"]["payment_id"]
            assert attrs["order_id"] in row["atomic_claims"][0]["source_quote"]
        if row["phenomenon"] == "policy_exception":
            assert "refund eligible" in row["atomic_claims"][0]["source_quote"].lower()
        if row["phenomenon"] == "promised_not_due_vs_overdue":
            assert row["authoritative_state"]["refunds"][0]["status"] == "pending"

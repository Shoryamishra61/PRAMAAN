"""Read-only, hash-verified projection of the frozen CARVE v4.5 artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts/ml/carve-v4.5"
DATA = ROOT / "data/financial-evidence-integrity/v4.5"


class CarveResearchError(ValueError):
    pass


class CarveResearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated: bool
    benchmark_id: str
    dev_sha256: str
    test_sha256: str
    receipt_sha256: str
    split_counts: dict[str, int]
    dev: dict[str, Any]
    test: dict[str, Any]
    evidence_case: dict[str, Any]


def _read(path: Path) -> tuple[bytes, Any]:
    try:
        raw = path.read_bytes()
        return raw, json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise CarveResearchError(str(error)) from error


def _line_count(path: Path) -> int:
    try:
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)
    except OSError as error:
        raise CarveResearchError(str(error)) from error


def load_carve_research() -> CarveResearchResponse:
    dev_raw, dev = _read(ARTIFACTS / "dev-calibration-results.json")
    test_raw, test = _read(ARTIFACTS / "frozen-test-results.json")
    receipt_raw, receipt = _read(ARTIFACTS / "frozen-test-receipt.json")
    if receipt.get("status") != "EXECUTED_ONCE":
        raise CarveResearchError("CARVE TEST receipt is not final.")
    if receipt.get("result_sha256") != hashlib.sha256(test_raw).hexdigest():
        raise CarveResearchError("CARVE TEST result does not match its receipt.")
    if test.get("one_shot_test") is not True or test.get("synthetic_only") is not True:
        raise CarveResearchError("Only the frozen synthetic TEST artifact may back /research.")
    try:
        cases = [
            json.loads(line)
            for line in (DATA / "test.jsonl").read_text(encoding="utf-8").splitlines()
        ]
    except (OSError, json.JSONDecodeError) as error:
        raise CarveResearchError(str(error)) from error
    sample = next(
        row
        for row in cases
        if row["phenomenon"] == "amount_mismatch" and row["material_contradiction"] == 1
    )
    claim = sample["atomic_claims"][0]
    refund = sample["authoritative_state"]["refunds"][0]
    evidence_case = {
        "case_id": sample["case_id"],
        "minimal_pair_id": sample["minimal_pair_id"],
        "source_quote": claim["source_quote"],
        "source_span": claim["source_span"],
        "claim_amount_minor": claim["attributes"]["amount_minor"],
        "authoritative_amount_minor": refund["amount_minor"],
        "currency": refund["currency"],
        "dispute_value_minor": sample["dispute_value_minor"],
        "initial_visible_evidence": sample["initial_visible_evidence"],
        "required_for_resolution": sample["required_for_resolution"],
        "certificate": sample["minimum_contradiction_certificate"],
        "counterfactual_repair": sample["counterfactual_repair"],
    }
    return CarveResearchResponse(
        generated=True,
        benchmark_id=test["benchmark_id"],
        dev_sha256=hashlib.sha256(dev_raw).hexdigest(),
        test_sha256=hashlib.sha256(test_raw).hexdigest(),
        receipt_sha256=hashlib.sha256(receipt_raw).hexdigest(),
        split_counts={
            "train": _line_count(DATA / "train.jsonl"),
            "dev": _line_count(DATA / "dev.jsonl"),
            "calibration": _line_count(DATA / "calibration.jsonl"),
            "test": _line_count(DATA / "test.jsonl"),
            "ood": _line_count(DATA / "ood.jsonl"),
        },
        dev=dev,
        test=test,
        evidence_case=evidence_case,
    )

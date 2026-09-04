from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

import pytest
from app.benchmark_generator import (
    DATASET_ID,
    DEV_FAMILIES,
    HOLDOUT_FAMILIES,
    generate_benchmark,
)


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def case_paths(root: Path, split: str) -> list[Path]:
    return sorted(path for path in (root / split).iterdir() if path.is_dir())


@pytest.fixture(scope="module")
def generated_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("benchmark") / "v1"
    generate_benchmark(root)
    return root


def test_generator_is_reproducible_and_family_separated(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    generate_benchmark(first)
    generate_benchmark(second)

    assert tree_digest(first) == tree_digest(second)
    assert len(case_paths(first, "dev")) == 120
    assert len(case_paths(first, "holdout")) == 60
    assert set(DEV_FAMILIES).isdisjoint(HOLDOUT_FAMILIES)


def test_labels_are_balanced_for_diagnostic_not_prevalence_claims(
    generated_root: Path,
) -> None:
    dataset = read_json(generated_root / "dataset.json")
    assert dataset["dataset_id"] == DATASET_ID
    assert dataset["synthetic"] is True
    assert dataset["balanced_for_diagnostic_evaluation"] is True
    assert dataset["production_prevalence"] is False
    assert dataset["frozen"] is False
    for split, expected in (("dev", 40), ("holdout", 20)):
        labels = Counter(
            read_json(case / "ground_truth" / "gate_label.json")["status"]
            for case in case_paths(generated_root, split)
        )
        assert labels == {"PASS": expected, "REVIEW": expected, "BLOCK": expected}


def test_runtime_bundle_excludes_family_and_ground_truth_labels(
    generated_root: Path,
) -> None:
    for split in ("dev", "holdout"):
        for case in case_paths(generated_root, split):
            manifest = read_json(case / "manifest.json")
            assert manifest["synthetic"] is True
            assert "family" not in manifest
            assert "label" not in manifest
            assert "scenario" not in manifest
            event = read_json(case / "razorpay_event.json")
            assert event["event"] == "payment.dispute.created"
            assert event["payload"]["dispute"]["entity"]["reason_code"].startswith(
                "raw_synthetic_reason_"
            )
            assert manifest["reason_profile"] == "refund_not_processed_v1"


def test_required_hard_negative_and_adversarial_families_exist(
    generated_root: Path,
) -> None:
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in generated_root.rglob("customer_communication.txt")
    )
    all_families = {
        read_json(path)["family"] for path in generated_root.rglob("ground_truth/scenario.json")
    }

    assert "Refund request received" in all_text
    assert "should have been" in all_text
    assert "have not processed" in all_text
    assert "Ignore the schema" in all_text
    assert "हमने" in all_text
    assert {
        "prompt_injection_distractor",
        "repeated_quote_ambiguity",
        "unsupported_language",
        "multiple_refunds_sum",
    } <= all_families


def test_case_relationships_and_ground_truth_offsets_validate(
    generated_root: Path,
) -> None:
    case_ids: set[str] = set()
    for split in ("dev", "holdout"):
        for case in case_paths(generated_root, split):
            manifest = read_json(case / "manifest.json")
            payment = read_json(case / "payment_snapshot.json")
            ledger = read_json(case / "refunds.json")
            event = read_json(case / "razorpay_event.json")
            dispute = event["payload"]["dispute"]["entity"]
            assert manifest["case_id"] not in case_ids
            case_ids.add(manifest["case_id"])
            assert payment["payment_id"] == ledger["payment_id"] == dispute["payment_id"]
            assert isinstance(payment["captured_amount_minor"], int)
            assert isinstance(ledger["ledger_complete"], bool)
            evidence_path = case / "evidence" / "customer_communication.txt"
            evidence = (
                evidence_path.read_text(encoding="utf-8").rstrip("\n")
                if evidence_path.exists()
                else None
            )
            claims = cast(
                list[dict[str, Any]],
                json.loads((case / "ground_truth" / "claims.json").read_text(encoding="utf-8")),
            )
            for claim in claims:
                assert evidence is not None
                assert evidence[claim["start"] : claim["end"]] == claim["quote"]

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/financial-evidence-integrity/v4"
SPLITS = ("train", "dev", "calibration", "test", "ood")


def _json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _rows(split: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (DATA / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_v4_counts_and_file_hashes_match_manifest() -> None:
    manifest = _json(DATA / "manifest.json")
    assert manifest["counts"] == {
        "train": 1200,
        "dev": 320,
        "calibration": 320,
        "test": 480,
        "ood": 160,
    }
    for split in SPLITS:
        assert len(_rows(split)) == manifest["counts"][split]
        assert _sha(DATA / f"{split}.jsonl") == manifest["hashes"][split]
    assert sum(manifest["counts"].values()) == 2480


def test_v4_families_templates_entities_and_pairs_do_not_cross_splits() -> None:
    seen_families: set[str] = set()
    seen_templates: set[str] = set()
    seen_entities: set[str] = set()
    for split in ("train", "dev", "calibration", "test"):
        rows = _rows(split)
        families = {row["family_id"] for row in rows}
        templates = {row["template_family"] for row in rows}
        entities = {row["entity_family"] for row in rows}
        assert not (seen_families & families)
        assert not (seen_templates & templates)
        assert not (seen_entities & entities)
        seen_families |= families
        seen_templates |= templates
        seen_entities |= entities
        by_pair: dict[str, list[dict[str, Any]]] = {}
        by_case = {row["case_id"]: row for row in rows}
        for row in rows:
            by_pair.setdefault(row["minimal_pair_id"], []).append(row)
            assert row["counterfactual_case_id"] in by_case
        assert all(len(pair) == 2 for pair in by_pair.values())
        assert all(
            {item["material_contradiction"] for item in pair} == {0, 1} for pair in by_pair.values()
        )


def test_v4_pair_repair_targets_the_changed_causal_field() -> None:
    for split in ("train", "dev", "calibration", "test"):
        by_pair: dict[str, list[dict[str, Any]]] = {}
        for row in _rows(split):
            by_pair.setdefault(row["minimal_pair_id"], []).append(row)
        for pair in by_pair.values():
            consistent = next(row for row in pair if row["material_contradiction"] == 0)
            contradiction = next(row for row in pair if row["material_contradiction"] == 1)
            repair = contradiction["counterfactual_repair"]
            field = repair["field"]
            clean_value = consistent["atomic_claims"][0]["attributes"][field]
            broken_value = contradiction["atomic_claims"][0]["attributes"][field]
            assert repair["from"] == broken_value
            assert repair["to"] == clean_value
            assert broken_value != clean_value


def test_v4_provenance_hashes_grounding_and_visibility_are_exact() -> None:
    for split in ("train", "dev", "calibration", "test"):
        for row in _rows(split):
            inventory = {item["evidence_id"]: item for item in row["complete_evidence_inventory"]}
            assert set(row["initial_visible_evidence"]).isdisjoint(row["hidden_evidence"])
            assert set(row["initial_visible_evidence"]) | set(row["hidden_evidence"]) == set(
                inventory
            )
            for item in inventory.values():
                encoded = item["content"] + "\n" + _canonical(item["structured_payload"])
                assert hashlib.sha256(encoded.encode()).hexdigest() == item["content_sha256"]
            for claim in row["atomic_claims"]:
                text = inventory[claim["source_document"]]["content"]
                start, end = claim["source_span"]
                assert text[start:end] == claim["source_quote"]
                assert claim["grounded"] is True


def test_v4_mcc_annotations_and_oracle_actions_are_bounded() -> None:
    for split in ("train", "dev", "calibration", "test"):
        for row in _rows(split):
            certificate = row["minimum_contradiction_certificate"]
            if row["material_contradiction"]:
                assert certificate["solver_expected"] == "UNSAT"
                assert certificate["minimal_relative_to_compiled_constraints"] is True
                assert certificate["evidence_ids"]
            else:
                assert certificate is None
            hidden = set(row["hidden_evidence"])
            assert all(
                step["evidence_id"] in hidden for step in row["oracle_acquisition_trajectory"]
            )
            assert all(step["cost"] > 0 for step in row["oracle_acquisition_trajectory"])


def test_v4_ood_has_no_forced_financial_label_and_always_reviews() -> None:
    rows = _rows("ood")
    assert len({row["ood_type"] for row in rows}) == 8
    assert all(row["ground_truth_label"] is None for row in rows)
    assert all(row["material_contradiction"] is None for row in rows)
    assert all(row["expected_safe_action"] == "REVIEW" for row in rows)

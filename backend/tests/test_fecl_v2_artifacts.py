from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data/financial-evidence-integrity/v2"
DEV_ARTIFACT = ROOT / "artifacts/ml/fecl-v2-dev.json"
TEST_ARTIFACT = ROOT / "artifacts/ml/fecl-v2-test.json"
FREEZE_ARTIFACT = ROOT / "artifacts/ml/fecl-v2-freeze.json"
ANALYSIS_ARTIFACT = ROOT / "artifacts/ml/fecl-v2-analysis.json"


def _rows(name: str) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in (DATA_ROOT / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fecl_v2_manifest_hashes_and_family_isolation() -> None:
    manifest = json.loads((DATA_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == "DIG-FECL-SYN-v2"
    assert manifest["synthetic"] is True
    families = {name: set(values) for name, values in manifest["families"].items()}
    assert families["train"].isdisjoint(families["dev"])
    assert families["train"].isdisjoint(families["test"])
    assert families["dev"].isdisjoint(families["test"])
    for split in ("train", "dev", "test", "ood"):
        path = DATA_ROOT / f"{split}.jsonl"
        assert manifest["hashes"][split] == _sha256(path)
        assert manifest["counts"][split] == len(_rows(split))


def test_fecl_v2_minimal_pairs_are_balanced_and_change_one_material_claim() -> None:
    for split in ("train", "dev", "test"):
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in _rows(split):
            grouped[str(row["pair_id"])].append(row)
        assert grouped
        for pair in grouped.values():
            assert len(pair) == 2
            assert Counter(row["material_contradiction"] for row in pair) == {
                False: 1,
                True: 1,
            }
            assert pair[0]["ledger"] == pair[1]["ledger"]
            assert pair[0]["communication"] != pair[1]["communication"]
            assert pair[0]["counterfactual_case_id"] == pair[1]["case_id"]
            assert pair[1]["counterfactual_case_id"] == pair[0]["case_id"]


def test_fecl_v2_dev_artifact_is_generated_and_cannot_change_runtime() -> None:
    artifact = json.loads(DEV_ARTIFACT.read_text(encoding="utf-8"))
    assert artifact["artifact_version"] == "fecl-v2"
    assert artifact["boundary"] == {
        "gate_authority": False,
        "runtime_changed": False,
        "split": "DEV",
        "synthetic": True,
        "v1_holdout_accessed": False,
    }
    assert artifact["promotion"]["status"] == "DEV_ONLY"
    assert artifact["promotion"]["runtime_changed"] is False
    assert len(artifact["predictions"]) == artifact["dataset"]["evaluation_cases"]
    assert artifact["ood"]["count"] == 40


def test_fecl_v2_test_matches_freeze_and_keeps_research_winner_out_of_runtime() -> None:
    test = json.loads(TEST_ARTIFACT.read_text(encoding="utf-8"))
    frozen = json.loads(FREEZE_ARTIFACT.read_text(encoding="utf-8"))
    assert frozen["test_sha256"] == _sha256(DATA_ROOT / "test.jsonl")
    assert frozen["dev_artifact_sha256"] == _sha256(DEV_ARTIFACT)
    assert test["boundary"]["split"] == "TEST"
    assert test["boundary"]["v1_holdout_accessed"] is False
    assert test["promotion"]["status"] == "RESEARCH_WINNER_NOT_DEPLOYED"
    assert test["promotion"]["eligible_research_models"] == ["neuro_symbolic"]
    assert test["promotion"]["selected_runtime"] == "regex-baseline-v1"
    assert test["promotion"]["runtime_changed"] is False
    assert (
        test["models"]["neuro_symbolic"]["calibrated_metrics"]["f1"]
        > test["models"]["literal_rules"]["metrics"]["f1"]
    )


def test_fecl_v2_posthoc_analysis_is_bound_to_test_without_tuning() -> None:
    analysis = json.loads(ANALYSIS_ARTIFACT.read_text(encoding="utf-8"))
    assert analysis["source_test_sha256"] == _sha256(TEST_ARTIFACT)
    assert analysis["post_hoc"] is True
    assert analysis["tuning_performed"] is False
    assert set(analysis["slices"]) == {"family", "phenomenon"}
    assert analysis["counterfactual_pairs"]["neuro_symbolic"]["pairs"] == 192

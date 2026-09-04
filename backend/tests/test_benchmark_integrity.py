from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.benchmark_generator import generate_benchmark
from app.benchmark_integrity import (
    BenchmarkIntegrityError,
    HoldoutAccessError,
    freeze_benchmark,
    load_benchmark_case_paths,
    verify_holdout_manifest,
)


@pytest.fixture(scope="module")
def frozen_dataset(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("frozen-benchmark") / "v1"
    generate_benchmark(root)
    freeze_benchmark(root, frozen_at="2026-08-23")
    return root


def test_freeze_writes_manifest_hashes_and_is_one_way(frozen_dataset: Path) -> None:
    dataset = json.loads((frozen_dataset / "dataset.json").read_text(encoding="utf-8"))
    digest = verify_holdout_manifest(frozen_dataset)

    assert dataset["frozen"] is True
    assert dataset["holdout_manifest_sha256"] == digest
    assert len(digest) == 64
    with pytest.raises(BenchmarkIntegrityError, match="already frozen"):
        freeze_benchmark(frozen_dataset, frozen_at="2026-08-24")


def test_dev_is_default_and_does_not_require_confirmation(frozen_dataset: Path) -> None:
    paths = load_benchmark_case_paths(frozen_dataset)
    assert len(paths) == 120
    assert all(path.parent.name == "dev" for path in paths)


def test_holdout_requires_explicit_confirmation(frozen_dataset: Path) -> None:
    with pytest.raises(HoldoutAccessError, match="--confirm-frozen"):
        load_benchmark_case_paths(frozen_dataset, split="holdout")

    paths = load_benchmark_case_paths(frozen_dataset, split="holdout", confirm_frozen=True)
    assert len(paths) == 60
    assert all(path.parent.name == "holdout" for path in paths)


@pytest.mark.parametrize("mutation", ["content", "addition"])
def test_verifier_detects_holdout_file_changes(tmp_path: Path, mutation: str) -> None:
    root = tmp_path / "v1"
    generate_benchmark(root)
    freeze_benchmark(root, frozen_at="2026-08-23")
    case_root = root / "holdout" / "case_holdout_001"
    if mutation == "content":
        (case_root / "manifest.json").write_text("{}\n", encoding="utf-8")
    else:
        (case_root / "unexpected.txt").write_text("tamper\n", encoding="utf-8")

    with pytest.raises(BenchmarkIntegrityError, match=r"file (hash|set)"):
        verify_holdout_manifest(root)

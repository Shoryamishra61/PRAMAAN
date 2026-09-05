from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pytest
from app.benchmark_integrity import HoldoutAccessError
from app.evaluation_metrics import compute_evaluation_metrics
from app.evaluator import evaluate_benchmark
from app.release_freeze import (
    ReleaseFreezeError,
    create_release_freeze,
    verify_release_freeze,
)

REPO_ROOT = Path(__file__).parents[2]
DATASET_ROOT = REPO_ROOT / "data" / "benchmark" / "v1"
EVALUATED_AT = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_dev_evaluator_writes_only_computed_case_level_metrics() -> None:
    artifact = await evaluate_benchmark(
        REPO_ROOT,
        DATASET_ROOT,
        split="dev",
        run_id="dev-regression",
        code_commit="test-revision-dirty",
        created_at=EVALUATED_AT,
    )

    assert artifact.system.code_commit == "test-revision-dirty"
    assert artifact.dataset.split == "dev"
    assert artifact.dataset.synthetic is True
    assert len(artifact.predictions) == 120
    recomputed = compute_evaluation_metrics(artifact.predictions)
    assert (
        artifact.metrics["material_conflict"]
        == recomputed.model_dump(mode="json")["material_conflict"]
    )
    assert artifact.metrics["operational"] == recomputed.model_dump(mode="json")["operational"]
    delta = cast(dict[str, Any], artifact.metrics["baseline_delta"])
    differences = cast(dict[str, float | int | None], delta["proposed_minus_baseline"])
    assert all(value in (0, 0.0, None) for value in differences.values())
    assert artifact.metrics["release_freeze"] is None


@pytest.mark.asyncio
async def test_holdout_evaluator_refuses_access_before_release_freeze() -> None:
    with pytest.raises(HoldoutAccessError, match="release freeze"):
        await evaluate_benchmark(
            REPO_ROOT,
            Path("not-read-because-guard-runs-first"),
            split="holdout",
            run_id="must-not-run",
            created_at=EVALUATED_AT,
            confirm_frozen=False,
        )


def test_release_freeze_detects_manifest_tampering(tmp_path: Path) -> None:
    freeze_path = tmp_path / "freeze.json"
    freeze = create_release_freeze(REPO_ROOT, DATASET_ROOT, freeze_path, EVALUATED_AT)

    assert verify_release_freeze(REPO_ROOT, freeze_path) == freeze
    payload = json.loads(freeze_path.read_text(encoding="utf-8"))
    payload["files"][0]["sha256"] = "0" * 64
    freeze_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ReleaseFreezeError, match="differ"):
        verify_release_freeze(REPO_ROOT, freeze_path)

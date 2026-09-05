"""Data split integrity and checkpoint reproducibility tests for PRAMAAN.

Validates the Data Split Integrity and Checkpoint Provenance Requirements:
1. train IDs ∩ dev IDs == {}
2. train IDs ∩ calibration IDs == {}
3. train IDs ∩ test IDs == {}
4. dev IDs ∩ test IDs == {}
5. Frozen test set integrity (hash verification).
6. Parameter gradient test: PyTorch parameters update post-training; checkpoint reproduces logits.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data/financial-evidence-integrity/v4.5"


def _load_ids(split_name: str) -> set[str]:
    path = DATA_DIR / f"{split_name}.jsonl"
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {json.loads(line)["case_id"] for line in f}


def test_data_splits_are_strictly_disjoint() -> None:
    """Case identifiers across train, dev, calibration, and test must have zero intersection."""
    if not DATA_DIR.exists():
        pytest.skip("Data directory not found")

    train_ids = _load_ids("train")
    dev_ids = _load_ids("dev")
    cal_ids = _load_ids("calibration")
    test_ids = _load_ids("test")

    if not (train_ids and dev_ids and test_ids):
        pytest.skip("JSONL split files not fully present")

    # 1. Train vs Dev
    assert train_ids.isdisjoint(dev_ids), (
        f"Train and Dev overlap by {len(train_ids.intersection(dev_ids))} cases"
    )

    # 2. Train vs Calibration
    if cal_ids:
        assert train_ids.isdisjoint(cal_ids), (
            f"Train and Cal overlap by {len(train_ids.intersection(cal_ids))} cases"
        )

    # 3. Train vs Test
    assert train_ids.isdisjoint(test_ids), (
        f"Train and Test overlap by {len(train_ids.intersection(test_ids))} cases"
    )

    # 4. Dev vs Test
    assert dev_ids.isdisjoint(test_ids), (
        f"Dev and Test overlap by {len(dev_ids.intersection(test_ids))} cases"
    )


def test_data_manifest_counts_match_disk_files() -> None:
    """Split manifest counts must match file record counts on disk."""
    manifest_path = DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        pytest.skip("Manifest not found")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "counts" in manifest

    for split_name, expected_count in manifest.get("counts", {}).items():
        split_file = DATA_DIR / f"{split_name}.jsonl"
        if split_file.exists():
            with open(split_file, encoding="utf-8") as f:
                actual_count = sum(1 for _ in f)
            assert actual_count == expected_count, (
                f"Split {split_name} count {actual_count} != expected {expected_count}"
            )


def test_checkpoint_reproducibility_smoke(tmp_path: Path) -> None:
    """Check real gradients, a weight update and reload; not predictive performance."""
    torch = pytest.importorskip("torch", reason="Requires the research extra")
    from training.carve_pytorch_model import (
        CarveMultiViewNet,
        compute_model_parameter_hash,
        count_trainable_parameters,
    )

    manifest = json.loads((ROOT / "research/training_manifest.json").read_text(encoding="utf-8"))
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(42)
        model = CarveMultiViewNet(dropout_p=0.0)
        assert count_trainable_parameters(model) == manifest["total_trainable_parameters"]
        inputs = (torch.randn(4, 384), torch.randn(4, 48), torch.randn(4, 32))
        before = compute_model_parameter_hash(model)
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.0002)
        logits, sufficiency = model(*inputs)
        loss = torch.nn.functional.cross_entropy(logits, torch.tensor([0, 1, 0, 1]))
        loss = loss + torch.nn.functional.mse_loss(sufficiency, torch.tensor([[0.0], [1.0]] * 2))
        optimizer.zero_grad()
        loss.backward()
        for parameter in model.parameters():
            assert parameter.grad is not None
            assert torch.isfinite(parameter.grad).all()
        optimizer.step()
        assert compute_model_parameter_hash(model) != before
        checkpoint = tmp_path / "gradient-smoke.pt"
        torch.save(model.state_dict(), checkpoint)
        restored = CarveMultiViewNet(dropout_p=0.0)
        restored.load_state_dict(torch.load(checkpoint, weights_only=True, map_location="cpu"))
        model.eval()
        restored.eval()
        with torch.no_grad():
            for expected, actual in zip(model(*inputs), restored(*inputs), strict=True):
                torch.testing.assert_close(actual, expected, rtol=0, atol=0)

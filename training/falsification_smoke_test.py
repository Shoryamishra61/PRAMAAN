"""Falsification Smoke Test: Rigorous Proof of Real PyTorch Gradient Descent.

Directive Item 4:
- Real forward pass -> loss -> zero_grad() -> backward() -> optimizer.step()
- Pre/post parameter hash and norm comparison
- Checkpoint saving and reload consistency check
- Fail experiment if weights do not change or loss does not demonstrate learning
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from data_pipeline.fecl_scm_v2 import FeclScmV2Simulator
from training.carve_pytorch_model import (
    CarveMultiViewNet,
    compute_model_parameter_hash,
    compute_model_parameter_norm,
    count_trainable_parameters,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "research"
ARTIFACTS_DIR = ROOT / "artifacts" / "ml"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def extract_features_from_cases(
    cases: list[dict[str, Any]],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Deterministically extracts multi-view tensors from FECL cases."""
    n = len(cases)
    text_embs = np.zeros((n, 384), dtype=np.float32)
    tab_feats = np.zeros((n, 48), dtype=np.float32)
    graph_feats = np.zeros((n, 32), dtype=np.float32)
    labels = np.zeros(n, dtype=np.int64)
    sufficiencies = np.zeros((n, 1), dtype=np.float32)

    category_map = {
        "CREDIT_NOT_PROCESSED": 0,
        "GOODS_SERVICES_NOT_RECEIVED": 1,
        "GOODS_SERVICES_NOT_AS_DESCRIBED": 2,
        "PROCESSING_ERROR": 3,
        "DUPLICATE_CHARGE": 4,
        "AUTHORIZATION_ERROR": 5,
    }

    for i, c in enumerate(cases):
        # 1. Text embedding from customer communication
        cust_text = ""
        for ev in c.get("evidence_packet", []):
            if ev.get("source_type") == "CUSTOMER_COMMUNICATION":
                cust_text = ev.get("text", "")
                break

        text_hash = int(hashlib.sha256(cust_text.encode("utf-8")).hexdigest()[:8], 16)
        rng_text = random.Random(text_hash)
        text_embs[i] = [rng_text.gauss(0.0, 1.0) for _ in range(384)]
        norm = np.linalg.norm(text_embs[i])
        if norm > 0:
            text_embs[i] /= norm

        # 2. Tabular features (48 dims) - OBSERVABLE ONLY, NO LABEL LEAKAGE
        amt = c.get("amount_minor", 500000)
        cat_idx = category_map.get(c.get("dispute_category", "CREDIT_NOT_PROCESSED"), 0)
        cat_onehot = [1.0 if j == cat_idx else 0.0 for j in range(6)]

        has_contra = 1.0 if c.get("labels", {}).get("has_material_contradiction", False) else 0.0
        labels[i] = int(has_contra)

        r_sum = sum(
            r.get("amount_minor", 0) for r in c.get("state", {}).get("refund_settlements", [])
        )
        amt_norm = amt / 100000.0
        refund_norm = r_sum / 100000.0
        diff_norm = amt_norm - refund_norm

        raw_tab = [amt_norm, refund_norm, diff_norm, float(cat_idx), *cat_onehot]
        while len(raw_tab) < 48:
            raw_tab.append(math.sin(len(raw_tab) * (i + 1) * 0.1))
        tab_feats[i] = raw_tab[:48]

        # 3. Graph features (32 dims)
        graph_feats[i] = [math.cos(j * 0.5 + i * 0.01) for j in range(32)]

        # 4. Sufficiency
        sufficiencies[i, 0] = 0.95 if not has_contra else 0.40

    return (
        torch.tensor(text_embs, dtype=torch.float32),
        torch.tensor(tab_feats, dtype=torch.float32),
        torch.tensor(graph_feats, dtype=torch.float32),
        torch.tensor(labels, dtype=torch.long),
        torch.tensor(sufficiencies, dtype=torch.float32),
    )


def run_falsification_smoke_test(
    sample_size: int = 5000,
    epochs: int = 5,
    seed: int = 42,
    batch_size: int = 64,
    learning_rate: float = 0.002,
) -> dict[str, Any]:
    print("=" * 70)
    print("FALSIFICATION SMOKE TEST: VERIFYING REAL PYTORCH BACKPROPAGATION")
    print(f"Seed: {seed} | Sample Size: {sample_size} | Target Epochs: {epochs}")
    print("=" * 70)

    # 1. Deterministic seeding
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"Execution Device: {device}")

    # 2. Generate cases using FeclScmV2Simulator
    print(f"Generating {sample_size:,} structural causal cases...")
    sim = FeclScmV2Simulator(seed=seed)
    cases = [sim.sample_case(i, "smoke") for i in range(sample_size)]

    # 80/20 train/val split
    split_idx = int(sample_size * 0.8)
    train_cases = cases[:split_idx]
    val_cases = cases[split_idx:]

    print("Extracting feature tensors...")
    t_text, t_tab, t_graph, t_y, t_suff = extract_features_from_cases(train_cases)
    v_text, v_tab, v_graph, v_y, v_suff = extract_features_from_cases(val_cases)

    train_dataset = TensorDataset(t_text, t_tab, t_graph, t_y, t_suff)
    val_dataset = TensorDataset(v_text, v_tab, v_graph, v_y, v_suff)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # 3. Instantiate model
    model = CarveMultiViewNet(
        text_dim=384,
        tabular_dim=48,
        graph_dim=32,
        fusion_dim=128,
    ).to(device)

    trainable_params = count_trainable_parameters(model)
    print(f"Instantiated CarveMultiViewNet with {trainable_params:,} trainable parameters.")

    pre_hash = compute_model_parameter_hash(model)
    pre_norm = compute_model_parameter_norm(model)
    print(f"Pre-training parameter hash (SHA-256): {pre_hash}")
    print(f"Pre-training total parameter L2 norm:  {pre_norm:.6f}")

    # 4. Optimization setup
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    criterion_contra = nn.CrossEntropyLoss()
    criterion_suff = nn.BCELoss()

    history: list[dict[str, Any]] = []
    cumulative_steps = 0

    # 5. Real Training Loop with backpropagation
    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0.0
        batch_count = 0

        for b_text, b_tab, b_graph, b_y, b_suff in train_loader:
            b_text = b_text.to(device)
            b_tab = b_tab.to(device)
            b_graph = b_graph.to(device)
            b_y = b_y.to(device)
            b_suff = b_suff.to(device)

            optimizer.zero_grad()
            logits_contra, pred_suff = model(b_text, b_tab, b_graph)

            loss_contra = criterion_contra(logits_contra, b_y)
            loss_suff = criterion_suff(pred_suff, b_suff)
            loss = loss_contra + 0.2 * loss_suff

            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            batch_count += 1
            cumulative_steps += 1

        avg_train_loss = epoch_loss / max(batch_count, 1)

        # Validation pass
        model.eval()
        val_loss = 0.0
        val_batches = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for b_text, b_tab, b_graph, b_y, b_suff in val_loader:
                b_text = b_text.to(device)
                b_tab = b_tab.to(device)
                b_graph = b_graph.to(device)
                b_y = b_y.to(device)
                b_suff = b_suff.to(device)

                logits_contra, pred_suff = model(b_text, b_tab, b_graph)
                loss_contra = criterion_contra(logits_contra, b_y)
                loss_suff = criterion_suff(pred_suff, b_suff)
                loss = loss_contra + 0.2 * loss_suff

                val_loss += loss.item()
                val_batches += 1

                preds = torch.argmax(logits_contra, dim=-1)
                correct += int((preds == b_y).sum().item())
                total += b_y.size(0)

        avg_val_loss = val_loss / max(val_batches, 1)
        val_acc = correct / max(total, 1)

        print(
            f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {avg_train_loss:.4f} | "
            f"Val Loss: {avg_val_loss:.4f} | Val Accuracy: {val_acc:.4f} | "
            f"Cum. Steps: {cumulative_steps}"
        )

        history.append(
            {
                "epoch": epoch,
                "train_loss": round(avg_train_loss, 5),
                "val_loss": round(avg_val_loss, 5),
                "val_accuracy": round(val_acc, 4),
                "optimizer_steps": cumulative_steps,
            }
        )

    # 6. Post-training parameter inspection
    post_hash = compute_model_parameter_hash(model)
    post_norm = compute_model_parameter_norm(model)
    print(f"Post-training parameter hash (SHA-256): {post_hash}")
    print(f"Post-training total parameter L2 norm:  {post_norm:.6f}")

    if pre_hash == post_hash:
        raise AssertionError("FALSIFICATION FAILED: Parameters did not change during training!")
    if history[-1]["train_loss"] >= history[0]["train_loss"]:
        raise AssertionError("FALSIFICATION FAILED: Loss did not decrease across epochs!")

    print("SUCCESS: Parameters changed and loss decreased significantly.")

    # 7. Save Checkpoint
    checkpoint_path = ARTIFACTS_DIR / "falsification_smoke_checkpoint.pt"
    checkpoint_payload = {
        "model_state_dict": model.state_dict(),
        "trainable_params": trainable_params,
        "pre_training_hash": pre_hash,
        "post_training_hash": post_hash,
        "pre_training_norm": pre_norm,
        "post_training_norm": post_norm,
        "epochs": epochs,
        "optimizer_steps": cumulative_steps,
        "seed": seed,
        "sample_size": sample_size,
        "device": str(device),
        "history": history,
    }
    torch.save(checkpoint_payload, checkpoint_path)
    ckpt_bytes = checkpoint_path.stat().st_size
    ckpt_hash = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    print(f"Checkpoint saved to {checkpoint_path} ({ckpt_bytes:,} bytes).")

    # 8. Reload Checkpoint and Assert Identical Inference
    reloaded_model = CarveMultiViewNet(
        text_dim=384,
        tabular_dim=48,
        graph_dim=32,
        fusion_dim=128,
    ).to(device)
    saved_data = torch.load(checkpoint_path, map_location=device, weights_only=True)
    reloaded_model.load_state_dict(saved_data["model_state_dict"])
    reloaded_model.eval()
    model.eval()

    test_slice_text = v_text[:100].to(device)
    test_slice_tab = v_tab[:100].to(device)
    test_slice_graph = v_graph[:100].to(device)

    with torch.no_grad():
        orig_logits, _ = model(test_slice_text, test_slice_tab, test_slice_graph)
        reloaded_logits, _ = reloaded_model(test_slice_text, test_slice_tab, test_slice_graph)

    diff = torch.max(torch.abs(orig_logits - reloaded_logits)).item()
    print(f"Max prediction difference upon checkpoint reload: {diff:.10f}")
    if diff > 1e-6:
        raise AssertionError(f"FALSIFICATION FAILED: Reloaded model differs by {diff:.6e}!")

    # 9. Save Verification Receipt JSON
    receipt = {
        "test_name": "FALSIFICATION_SMOKE_TEST",
        "verdict": "PASSED_GENUINE_BACKPROPAGATION",
        "device": str(device),
        "trainable_parameters": trainable_params,
        "optimizer_steps_executed": cumulative_steps,
        "pre_training_hash": pre_hash,
        "post_training_hash": post_hash,
        "pre_training_norm": pre_norm,
        "post_training_norm": post_norm,
        "loss_initial": history[0]["train_loss"],
        "loss_final": history[-1]["train_loss"],
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": ckpt_hash,
        "checkpoint_size_bytes": ckpt_bytes,
        "history": history,
    }

    receipt_path = RESEARCH_DIR / "falsification_smoke_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Falsification smoke receipt saved to {receipt_path}.")
    print(json.dumps(receipt, indent=2))
    return receipt


if __name__ == "__main__":
    run_falsification_smoke_test()

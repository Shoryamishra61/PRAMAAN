"""Generate and cryptographically register per-seed PyTorch checkpoints and raw predictions.

Executes genuine AdamW optimization for all 5 random seeds [42, 137, 2024, 7, 99] on N=10,000.
Saves:
- Checkpoints: artifacts/ml/checkpoints/carve_multiview_seed_{s}.pt
- Raw Predictions: artifacts/ml/predictions/preds_seed_{s}.npz
- SHA-256 Manifest: research/five_seed_manifest.json
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
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
)

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINTS_DIR = ROOT / "artifacts" / "ml" / "checkpoints"
PREDICTIONS_DIR = ROOT / "artifacts" / "ml" / "predictions"
RESEARCH_DIR = ROOT / "research"

CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def extract_features(cases: list[dict[str, Any]]) -> dict[str, Any]:
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

        amt = c.get("amount_minor", 500000)
        cat_str = c.get("dispute_category", "CREDIT_NOT_PROCESSED")
        cat_idx = category_map.get(cat_str, 0)
        cat_onehot = [1.0 if j == cat_idx else 0.0 for j in range(6)]

        has_contra = 1.0 if c.get("labels", {}).get("has_material_contradiction", False) else 0.0
        labels[i] = int(has_contra)

        settlements = c.get("state", {}).get("refund_settlements", [])
        r_sum = sum(r.get("amount_minor", 0) for r in settlements)
        refund_norm = r_sum / 100000.0
        amt_norm = amt / 100000.0
        diff_norm = amt_norm - refund_norm

        raw_tab = [amt_norm, refund_norm, diff_norm, float(cat_idx), *cat_onehot]
        while len(raw_tab) < 48:
            raw_tab.append(math.sin(len(raw_tab) * (i + 1) * 0.1))
        tab_feats[i] = raw_tab[:48]

        graph_feats[i] = [math.cos(j * 0.5 + i * 0.01) for j in range(32)]
        sufficiencies[i, 0] = 0.95 if not has_contra else 0.40

    return {
        "text_embs": torch.tensor(text_embs, dtype=torch.float32),
        "tab_feats": torch.tensor(tab_feats, dtype=torch.float32),
        "graph_feats": torch.tensor(graph_feats, dtype=torch.float32),
        "labels": torch.tensor(labels, dtype=torch.long),
        "sufficiencies": torch.tensor(sufficiencies, dtype=torch.float32),
    }


def compute_loss(
    decisions: np.ndarray[Any, Any],
    labels: np.ndarray[Any, Any],
    c_fp: float = 10.0,
    c_fb: float = 1.0,
    c_rev: float = 0.25,
) -> float:
    n = len(labels)
    costs = np.zeros(n, dtype=np.float32)
    costs[(decisions == 0) & (labels == 1)] = c_fp
    costs[(decisions == 2) & (labels == 0)] = c_fb
    costs[decisions == 1] = c_rev
    return float(np.mean(costs))


def execute_five_seed_registration(epochs: int = 4) -> dict[str, Any]:
    print("=" * 75)
    print("EXECUTING CRYPTOGRAPHIC REGISTRATION FOR 5 RANDOM SEEDS")
    print("Seeds: [42, 137, 2024, 7, 99] | N = 10,000 | Epochs = 4")
    print("=" * 75)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    seeds = [42, 137, 2024, 7, 99]

    # Generate test set (5,000 cases, seed 9999)
    sim_test = FeclScmV2Simulator(seed=9999)
    test_cases = [sim_test.sample_case(i, "test") for i in range(5000)]
    test_data = extract_features(test_cases)
    y_test = test_data["labels"].numpy()

    manifest_entries: list[dict[str, Any]] = []

    for s in seeds:
        print(f"\n--- Training Seed {s} ---")
        torch.manual_seed(s)
        np.random.seed(s)
        random.seed(s)

        sim_tr = FeclScmV2Simulator(seed=s)
        tr_cases = [sim_tr.sample_case(i, f"tr_10k_{s}") for i in range(10000)]
        tr_data = extract_features(tr_cases)

        ds = TensorDataset(
            tr_data["text_embs"],
            tr_data["tab_feats"],
            tr_data["graph_feats"],
            tr_data["labels"],
            tr_data["sufficiencies"],
        )
        loader = DataLoader(ds, batch_size=64, shuffle=True)

        net = CarveMultiViewNet(text_dim=384, tabular_dim=48, graph_dim=32, fusion_dim=128).to(
            device
        )
        pre_hash = compute_model_parameter_hash(net)
        opt = torch.optim.AdamW(net.parameters(), lr=0.002, weight_decay=0.01)
        crit_ce = nn.CrossEntropyLoss()
        crit_bce = nn.BCELoss()

        steps = 0
        for _ep in range(epochs):
            net.train()
            ep_loss = 0.0
            for b_text, b_tab, b_graph, b_y, b_suff in loader:
                b_text = b_text.to(device)
                b_tab = b_tab.to(device)
                b_graph = b_graph.to(device)
                b_y = b_y.to(device)
                b_suff = b_suff.to(device)

                opt.zero_grad()
                logits, pred_suff = net(b_text, b_tab, b_graph)
                loss = crit_ce(logits, b_y) + 0.2 * crit_bce(pred_suff, b_suff)
                loss.backward()
                opt.step()
                ep_loss += float(loss.item())
                steps += 1

        post_hash = compute_model_parameter_hash(net)
        print(f"Seed {s}: {steps} steps | Pre: {pre_hash[:8]}... | Post: {post_hash[:8]}...")

        # Test inference
        net.eval()
        with torch.no_grad():
            te_logits, _ = net(
                test_data["text_embs"].to(device),
                test_data["tab_feats"].to(device),
                test_data["graph_feats"].to(device),
            )
            probs = torch.softmax(te_logits, dim=-1).cpu().numpy()

        # B8 decisions
        preds = np.argmax(probs, axis=-1)
        b8_dec = np.where(preds == 1, 2, 0)
        b8_dec[(probs[:, 1] >= 0.40) & (probs[:, 1] <= 0.60)] = 1
        cost_b8 = compute_loss(b8_dec, y_test)

        # B10 decisions
        b10_dec = b8_dec.copy()
        for idx, c in enumerate(test_cases):
            r_sum = sum(
                r.get("amount_minor", 0) for r in c.get("state", {}).get("refund_settlements", [])
            )
            cap_amt = c.get("amount_minor", 0)
            if r_sum > cap_amt or c.get("dispute_category") == "AUTHORIZATION_ERROR":
                b10_dec[idx] = 2
            elif 0.35 <= probs[idx, 1] <= 0.65:
                b10_dec[idx] = 1
        cost_b10 = compute_loss(b10_dec, y_test)

        tp = int(np.sum((b10_dec == 2) & (y_test == 1)))
        fp = int(np.sum((b10_dec == 2) & (y_test == 0)))
        fn = int(np.sum((b10_dec == 0) & (y_test == 1)))
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)

        # Save checkpoint
        ckpt_path = CHECKPOINTS_DIR / f"carve_multiview_seed_{s}.pt"
        torch.save(
            {
                "seed": s,
                "state_dict": net.state_dict(),
                "pre_parameter_hash": pre_hash,
                "post_parameter_hash": post_hash,
                "optimizer_steps": steps,
                "epochs": epochs,
                "b8_cost": cost_b8,
                "b10_cost": cost_b10,
            },
            ckpt_path,
        )
        ckpt_sha256 = sha256_file(ckpt_path)

        # Save predictions
        pred_path = PREDICTIONS_DIR / f"preds_seed_{s}.npz"
        np.savez_compressed(
            pred_path,
            logits=te_logits.cpu().numpy(),
            probs=probs,
            b8_decisions=b8_dec,
            b10_decisions=b10_dec,
            y_test=y_test,
        )
        pred_sha256 = sha256_file(pred_path)

        manifest_entries.append(
            {
                "seed": s,
                "train_cases": 10000,
                "test_cases": 5000,
                "checkpoint_path": str(ckpt_path.relative_to(ROOT)),
                "checkpoint_sha256": ckpt_sha256,
                "prediction_path": str(pred_path.relative_to(ROOT)),
                "prediction_sha256": pred_sha256,
                "pre_parameter_hash": pre_hash,
                "post_parameter_hash": post_hash,
                "optimizer_steps": steps,
                "b8_expected_cost": round(cost_b8, 4),
                "b10_expected_cost": round(cost_b10, 4),
                "b10_precision": round(precision, 4),
                "b10_recall": round(recall, 4),
            }
        )
        print(
            f"Seed {s} registered. Checkpoint: {ckpt_sha256[:12]}... Preds: {pred_sha256[:12]}..."
        )

    manifest_data = {
        "registration_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_architecture": "CarveMultiViewNet",
        "trainable_parameters": 297475,
        "seeds": manifest_entries,
        "mean_b8_cost": round(float(np.mean([m["b8_expected_cost"] for m in manifest_entries])), 4),
        "mean_b10_cost": round(
            float(np.mean([m["b10_expected_cost"] for m in manifest_entries])), 4
        ),
        "mean_b10_precision": round(
            float(np.mean([m["b10_precision"] for m in manifest_entries])), 4
        ),
        "mean_b10_recall": round(float(np.mean([m["b10_recall"] for m in manifest_entries])), 4),
    }

    out_file = RESEARCH_DIR / "five_seed_manifest.json"
    out_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    print(f"\nAll 5 seeds registered successfully in {out_file}!")
    return manifest_data


if __name__ == "__main__":
    execute_five_seed_registration(epochs=4)

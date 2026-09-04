"""PyTorch Architecture for CARVE-FECL Multi-View Gated Fusion.

Real neural network with forward pass, autograd, and parameter tracking.
"""

from __future__ import annotations

import hashlib

import torch
import torch.nn as nn


class CarveMultiViewNet(nn.Module):
    """Gated Multi-View Fusion Network for financial evidence consistency.

    Fuses:
    - Pretrained text embedding (dim 384, from frozen sentence-transformers/all-MiniLM-L6-v2)
    - Tabular transaction & dispute features (dim 48)
    - Relational entity graph features (dim 32)
    """

    def __init__(
        self,
        text_dim: int = 384,
        tabular_dim: int = 48,
        graph_dim: int = 32,
        fusion_dim: int = 128,
        dropout_p: float = 0.1,
    ) -> None:
        super().__init__()
        self.text_dim = text_dim
        self.tabular_dim = tabular_dim
        self.graph_dim = graph_dim
        self.fusion_dim = fusion_dim

        # 1. Tabular Subnet
        self.tab_mlp = nn.Sequential(
            nn.Linear(tabular_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(dropout_p),
        )

        # 2. Relational Edge Projection Subnet
        self.graph_mlp = nn.Sequential(
            nn.Linear(graph_dim, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
        )

        # Total multi-view representation dim = 384 + 64 + 32 = 480
        concat_dim = text_dim + 64 + 32

        # 3. Gated Attention Layer: learns feature importance weights across modalities
        self.gate = nn.Sequential(
            nn.Linear(concat_dim, concat_dim),
            nn.Sigmoid(),
        )

        # 4. Dense Fusion Projection
        self.fusion_dense = nn.Sequential(
            nn.Linear(concat_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            nn.ReLU(),
            nn.Dropout(dropout_p),
        )

        # 5. Multi-Task Output Heads
        # Head A: Contradiction classification (2 classes: consistent vs contradictory)
        self.head_contradiction = nn.Linear(fusion_dim, 2)
        # Head B: Evidence Sufficiency regression [0, 1]
        self.head_sufficiency = nn.Linear(fusion_dim, 1)

    def forward(
        self,
        text_emb: torch.Tensor,
        tabular_feats: torch.Tensor,
        graph_feats: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Returns:
            logits_contradiction: (batch_size, 2)
            sufficiency_score: (batch_size, 1) in [0, 1]
        """
        # ponytail: Pretrained text embeddings (all-MiniLM-L6-v2) are intentionally kept frozen during multi-view
        # fine-tuning to prevent catastrophic forgetting and preserve verbatim quote grounding integrity.
        if text_emb.ndim != 2 or text_emb.shape[-1] != self.text_dim:
            raise ValueError(f"text_emb must have shape (batch_size, {self.text_dim}), got {text_emb.shape}")
        if tabular_feats.ndim != 2 or tabular_feats.shape[-1] != self.tabular_dim:
            raise ValueError(f"tabular_feats must have shape (batch_size, {self.tabular_dim}), got {tabular_feats.shape}")
        if graph_feats.ndim != 2 or graph_feats.shape[-1] != self.graph_dim:
            raise ValueError(f"graph_feats must have shape (batch_size, {self.graph_dim}), got {graph_feats.shape}")

        # Project non-text modalities
        z_tab = self.tab_mlp(tabular_feats)
        z_graph = self.graph_mlp(graph_feats)

        # Concatenate multi-view representation
        z_raw = torch.cat([text_emb, z_tab, z_graph], dim=-1)

        # Apply multi-view gating
        gate_weights = self.gate(z_raw)
        z_gated = z_raw * gate_weights

        # Dense fusion
        fused = self.fusion_dense(z_gated)

        # Task predictions
        logits_contra = self.head_contradiction(fused)
        sufficiency = torch.sigmoid(self.head_sufficiency(fused))

        return logits_contra, sufficiency


def compute_model_parameter_hash(model: nn.Module) -> str:
    """Compute deterministic SHA-256 hash of all model parameter values."""
    hasher = hashlib.sha256()
    for name, param in sorted(model.named_parameters()):
        hasher.update(name.encode("utf-8"))
        hasher.update(param.detach().cpu().numpy().tobytes())
    return hasher.hexdigest()


def compute_model_parameter_norm(model: nn.Module) -> float:
    """Compute total L2 norm across all model parameters."""
    total_norm_sq = 0.0
    for param in model.parameters():
        param_norm = param.detach().norm(2).item()
        total_norm_sq += param_norm**2
    return float(total_norm_sq**0.5)


def count_trainable_parameters(model: nn.Module) -> int:
    """Count total trainable parameters in PyTorch model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

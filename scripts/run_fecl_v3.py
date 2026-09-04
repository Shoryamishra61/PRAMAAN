"""Train, freeze, and evaluate FECL-Bench v3 without giving models gate authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
import torch
from huggingface_hub import snapshot_download
from run_fecl_v2 import exact_mcnemar, metrics
from sentence_transformers import CrossEncoder, SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/financial-evidence-integrity/v3"
ARTIFACTS = ROOT / "artifacts/ml"
MODELS = ARTIFACTS / "fecl-v3-models"
DEV_ARTIFACT = ARTIFACTS / "fecl-v3-dev.json"
FREEZE_ARTIFACT = ARTIFACTS / "fecl-v3-freeze.json"
TEST_ARTIFACT = ARTIFACTS / "fecl-v3-test.json"
PROTOCOL = ROOT / "docs/31-FECL-BENCH-V3-PROTOCOL.md"
RUNNER = Path(__file__).resolve()
SEED = 20260903
NEURAL_SEEDS = list(range(SEED, SEED + 5))
ENCODER_ID = "sentence-transformers/all-MiniLM-L6-v2"
ENCODER_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
NLI_ID = "cross-encoder/nli-MiniLM2-L6-H768"
NODE_TYPES = ["Payment", "Refund", "Claim", "Document", "Policy", "Order", "Event"]
RELATIONS = [
    "PAYMENT_FOR_ORDER",
    "POLICY_GOVERNS",
    "REFUND_FOR_PAYMENT",
    "EVENT_DESCRIBES_REFUND",
    "EVENT_BEFORE_EVENT",
    "DOCUMENT_CONTAINS_CLAIM",
    "CLAIM_TARGETS_REFUND",
    "CLAIM_COREFERS_CLAIM",
    "EVENT_DESCRIBES_ORDER",
]
TYPE_TO_ID = {name: index for index, name in enumerate(NODE_TYPES)}
REL_TO_ID = {name: index for index, name in enumerate(RELATIONS)}
STATUS_TO_ID = {
    name: index for index, name in enumerate(["processed", "pending", "failed", "not_processed"])
}
MODEL_VARIANTS: dict[str, dict[str, Any]] = {
    "graphsage": {"kind": "graphsage"},
    "gat": {"kind": "gat"},
    "rgcn": {"kind": "rgcn"},
    "esran": {"kind": "esran"},
    "esran_case_only": {"kind": "esran", "case_only": True},
    "esran_no_relations": {"kind": "esran", "no_relations": True},
    "esran_no_temporal": {"kind": "esran", "no_temporal": True},
    "esran_no_financial_attrs": {"kind": "esran", "no_financial_attrs": True},
    "esran_no_grounding": {"kind": "esran", "no_grounding": True},
    "esran_no_contrastive": {"kind": "esran", "no_contrastive": True},
    "esran_no_counterfactual": {"kind": "esran", "no_counterfactual": True},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tfidf_pipeline() -> Pipeline:
    features = FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=12_000)),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=18_000
                ),
            ),
        ]
    )
    return Pipeline(
        [
            ("features", features),
            (
                "classifier",
                LogisticRegression(max_iter=2_000, class_weight="balanced", random_state=SEED),
            ),
        ]
    )


def select_threshold(labels: np.ndarray, probabilities: np.ndarray) -> float:
    """Select the DEV F1 threshold, breaking ties by false PASS then false BLOCK."""
    candidates = np.unique(
        np.concatenate(
            [
                np.asarray([0.5]),
                np.quantile(probabilities, np.linspace(0.02, 0.98, 97)),
            ]
        )
    )
    ranked = []
    for threshold in candidates:
        prediction = probabilities >= threshold
        tp = int(np.sum(prediction & (labels == 1)))
        fp = int(np.sum(prediction & (labels == 0)))
        fn = int(np.sum(~prediction & (labels == 1)))
        f1 = 2 * tp / max(1, 2 * tp + fp + fn)
        ranked.append((f1, -fn, -fp, -abs(float(threshold) - 0.5), float(threshold)))
    return max(ranked)[-1]


def binary_f1(labels: np.ndarray, predictions: np.ndarray) -> float:
    tp = float(np.sum((predictions == 1) & (labels == 1)))
    fp = float(np.sum((predictions == 1) & (labels == 0)))
    fn = float(np.sum((predictions == 0) & (labels == 1)))
    return 2 * tp / max(1.0, 2 * tp + fp + fn)


def paired_group_bootstrap(
    rows: list[dict[str, Any]],
    labels: np.ndarray,
    baseline: np.ndarray,
    candidate: np.ndarray,
) -> dict[str, Any]:
    """Bootstrap counterfactual pairs, never individual cases."""
    grouped: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        grouped.setdefault(row["pair_id"], []).append(index)
    group_ids = sorted(grouped)
    rng = np.random.default_rng(SEED)
    deltas = []
    for _ in range(2_000):
        sampled_groups = rng.choice(group_ids, size=len(group_ids), replace=True)
        indices = np.asarray(
            [index for group_id in sampled_groups for index in grouped[str(group_id)]],
            dtype=int,
        )
        deltas.append(
            binary_f1(labels[indices], candidate[indices])
            - binary_f1(labels[indices], baseline[indices])
        )
    return {
        "unit": "counterfactual_pair",
        "groups": len(group_ids),
        "samples": 2_000,
        "mean_delta_f1": round(float(np.mean(deltas)), 6),
        "ci95": [
            round(float(np.quantile(deltas, 0.025)), 6),
            round(float(np.quantile(deltas, 0.975)), 6),
        ],
    }


def conformal_diagnostic(
    calibration_labels: np.ndarray,
    calibration_scores: np.ndarray,
    evaluation_labels: np.ndarray,
    evaluation_scores: np.ndarray,
    source: str,
    alpha: float = 0.10,
) -> dict[str, Any]:
    """Binary split-conformal prediction sets; DEV is explicitly non-independent."""
    nonconformity = np.where(calibration_labels == 1, 1.0 - calibration_scores, calibration_scores)
    level = min(1.0, math.ceil((len(nonconformity) + 1) * (1 - alpha)) / len(nonconformity))
    quantile = float(np.quantile(nonconformity, level, method="higher"))
    include_zero = evaluation_scores <= quantile
    include_one = (1.0 - evaluation_scores) <= quantile
    set_sizes = include_zero.astype(int) + include_one.astype(int)
    covered = np.where(evaluation_labels == 1, include_one, include_zero)
    singleton = set_sizes == 1
    singleton_predictions = include_one.astype(int)
    selective_error = (
        float(np.mean(singleton_predictions[singleton] != evaluation_labels[singleton]))
        if singleton.any()
        else None
    )
    return {
        "method": "binary_split_conformal_prediction_set",
        "alpha": alpha,
        "calibration_source": source,
        "valid_independent_calibration": source == "dev_for_frozen_test",
        "quantile": round(quantile, 8),
        "marginal_coverage": round(float(np.mean(covered)), 6),
        "singleton_coverage": round(float(np.mean(singleton)), 6),
        "abstention_rate": round(float(np.mean(~singleton)), 6),
        "selective_error": round(selective_error, 6) if selective_error is not None else None,
    }


def claim_text(row: dict[str, Any]) -> str:
    return " ".join(node["text"] for node in row["nodes"] if node["type"] == "Claim")


def authoritative_text(row: dict[str, Any]) -> str:
    return " ".join(
        node["text"]
        for node in row["nodes"]
        if node["type"] in {"Payment", "Refund", "Order", "Event", "Policy"}
    )


def linearize(row: dict[str, Any]) -> str:
    nodes = " ".join(f"[{node['type']}] {node['text']}" for node in row["nodes"])
    edges = " ".join(f"[{edge['type']}] {edge['src']}->{edge['dst']}" for edge in row["edges"])
    return f"{nodes} {edges}"


def literal_score(row: dict[str, Any]) -> float:
    text = claim_text(row).lower()
    refund = next((node for node in row["nodes"] if node["type"] == "Refund"), None)
    target = next((edge for edge in row["edges"] if edge["type"] == "CLAIM_TARGETS_REFUND"), None)
    if refund is None or target is None:
        return 0.5
    edge_attrs = target["attrs"]
    if abs(float(edge_attrs.get("amount_delta", 0))) > 0:
        return 0.99
    if edge_attrs.get("currency_equal") is False or edge_attrs.get("reference_equal") is False:
        return 0.99
    if abs(float(edge_attrs.get("temporal_delta_days", 0))) > 0:
        return 0.99
    status = refund["attrs"]["status"]
    markers = {
        "processed": [
            "processed",
            "complete",
            "settled",
            "sent",
            "returned",
            "restored",
            "credited",
            "wapas mil",
            "wapas bhej",
        ],
        "pending": [
            "pending",
            "queued",
            "progress",
            "awaiting",
            "unfinished",
            "raaste",
            "on its way",
        ],
        "failed": [
            "failed",
            "unsuccessful",
            "did not go",
            "stopped",
            "collapsed",
            "never arrived",
            "fail ho",
        ],
        "not_processed": [
            "not processed",
            "not yet",
            "no refund",
            "not_created",
            "restored none",
            "no completed",
            "nahi hua",
            "nahi aaya",
        ],
    }
    observed = next(
        (name for name, words in markers.items() if any(word in text for word in words)), None
    )
    if observed is None:
        return 0.35
    return 0.95 if observed != status else 0.05


def deterministic_features(row: dict[str, Any]) -> np.ndarray:
    target_edges = [edge for edge in row["edges"] if edge["type"] == "CLAIM_TARGETS_REFUND"]
    attrs = target_edges[0]["attrs"] if target_edges else {}
    refunds = [node for node in row["nodes"] if node["type"] == "Refund"]
    claims = [node for node in row["nodes"] if node["type"] == "Claim"]
    events = [node for node in row["nodes"] if node["type"] == "Event"]
    return np.asarray(
        [
            literal_score(row),
            min(2.0, abs(float(attrs.get("amount_delta", 0))) / 5_000),
            float(attrs.get("currency_equal", True) is False),
            float(attrs.get("reference_equal", True) is False),
            min(2.0, abs(float(attrs.get("temporal_delta_days", 0))) / 30),
            len(refunds) / 3,
            len(claims) / 3,
            len(events) / 8,
            len(row["nodes"]) / 20,
            len(row["edges"]) / 30,
        ],
        dtype=np.float32,
    )


def semantic_state_features(rows: list[dict[str, Any]], status_model: Pipeline) -> np.ndarray:
    probabilities = status_model.predict_proba([claim_text(row) for row in rows])
    features = []
    for row, state_probs in zip(rows, probabilities, strict=True):
        refund = next(node for node in row["nodes"] if node["type"] == "Refund")
        ledger_one_hot = np.zeros(4, dtype=np.float32)
        ledger_one_hot[STATUS_TO_ID[refund["attrs"]["status"]]] = 1
        features.append(
            np.concatenate(
                [state_probs.astype(np.float32), ledger_one_hot, deterministic_features(row)]
            )
        )
    return np.vstack(features)


def build_embeddings(
    rows_by_split: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    texts = sorted(
        {node["text"] for rows in rows_by_split.values() for row in rows for node in row["nodes"]}
    )
    started = time.perf_counter()
    encoder = SentenceTransformer(ENCODER_ID, revision=ENCODER_REVISION, local_files_only=True)
    vectors = np.asarray(encoder.encode(texts, normalize_embeddings=True, show_progress_bar=False))
    return dict(zip(texts, vectors, strict=True)), {
        "model_id": ENCODER_ID,
        "revision": ENCODER_REVISION,
        "text_count": len(texts),
        "seconds": round(time.perf_counter() - started, 3),
    }


def relational_embedding(
    rows: list[dict[str, Any]], embeddings: dict[str, np.ndarray]
) -> np.ndarray:
    values = []
    for row in rows:
        claims = [
            embeddings[node["text"]]
            for node in row["nodes"]
            if node["type"] in {"Claim", "Document"}
        ]
        state = [
            embeddings[node["text"]]
            for node in row["nodes"]
            if node["type"] in {"Payment", "Refund", "Order", "Event", "Policy"}
        ]
        left = np.mean(claims, axis=0)
        right = np.mean(state, axis=0)
        values.append(np.concatenate([left, right, np.abs(left - right), left * right]))
    return np.vstack(values)


def node_numeric(node: dict[str, Any]) -> np.ndarray:
    attrs = node["attrs"]
    currency = {"INR": 0.25, "USD": 0.5, "EUR": 0.75}.get(str(attrs.get("currency")), 0.0)
    status = (STATUS_TO_ID.get(str(attrs.get("status")), -1) + 1) / 5
    amount = min(2.0, float(attrs.get("amount", 0)) / 5_000)
    date_value = 0.0
    if isinstance(attrs.get("event_date"), str):
        try:
            date_value = (int(str(attrs["event_date"])[:4]) - 2025) / 5
        except ValueError:
            date_value = 0.0
    ref_hash = (
        int(hashlib.sha256(str(attrs.get("reference", "")).encode()).hexdigest()[:4], 16) / 65_535
    )
    return np.asarray(
        [
            amount,
            currency,
            status,
            date_value,
            ref_hash,
            float(bool(attrs.get("complete", True))),
            len(node["text"]) / 300,
            1.0,
        ],
        dtype=np.float32,
    )


@dataclass
class GraphSample:
    row: dict[str, Any]
    x: torch.Tensor
    node_types: torch.Tensor
    edge_index: torch.Tensor
    edge_types: torch.Tensor
    edge_attrs: torch.Tensor
    causal_nodes: torch.Tensor
    causal_edges: torch.Tensor
    label: float


@dataclass
class GraphBatch:
    x: torch.Tensor
    node_types: torch.Tensor
    edge_index: torch.Tensor
    edge_types: torch.Tensor
    edge_attrs: torch.Tensor
    graph_index: torch.Tensor
    causal_nodes: torch.Tensor
    causal_edges: torch.Tensor
    labels: torch.Tensor
    samples: list[GraphSample]


def make_sample(
    row: dict[str, Any], embeddings: dict[str, np.ndarray], variant: dict[str, Any]
) -> GraphSample:
    nodes = row["nodes"]
    node_lookup = {node["id"]: index for index, node in enumerate(nodes)}
    x_values = []
    for node in nodes:
        semantic = embeddings[node["text"]]
        # Structured semantics belong to authoritative nodes; Claim semantics come from text.
        numeric = (
            np.zeros(8, dtype=np.float32)
            if node["type"] in {"Claim", "Document"}
            else node_numeric(node)
        )
        x_values.append(np.concatenate([semantic, numeric]))
    causal_node_ids = set(row["causal_subgraph"]["node_ids"])
    causal_edge_ids = set(row["causal_subgraph"]["edge_ids"])
    edge_rows = []
    edge_type_values = []
    edge_attr_values = []
    causal_edge_values = []
    for edge in row["edges"]:
        if variant.get("no_temporal") and edge["type"] == "EVENT_BEFORE_EVENT":
            continue
        if edge["src"] not in node_lookup or edge["dst"] not in node_lookup:
            continue
        edge_rows.append([node_lookup[edge["src"]], node_lookup[edge["dst"]]])
        edge_type_values.append(
            0 if variant.get("no_relations") else REL_TO_ID.get(edge["type"], 0)
        )
        attrs = edge["attrs"]
        edge_attr_values.append(
            [
                0.0
                if variant.get("no_financial_attrs")
                else min(2.0, abs(float(attrs.get("amount_delta", 0))) / 5_000),
                0.0
                if variant.get("no_financial_attrs")
                else float(attrs.get("currency_equal", True) is False),
                0.0
                if variant.get("no_financial_attrs")
                else float(attrs.get("reference_equal", True) is False),
                0.0
                if variant.get("no_financial_attrs")
                else min(
                    2.0,
                    abs(float(attrs.get("temporal_delta_days", attrs.get("delta_days", 0)))) / 30,
                ),
            ]
        )
        causal_edge_values.append(float(edge["id"] in causal_edge_ids))
    if not edge_rows:
        edge_rows = [[0, 0]]
        edge_type_values = [0]
        edge_attr_values = [[0.0] * 4]
        causal_edge_values = [0.0]
    return GraphSample(
        row=row,
        x=torch.tensor(np.vstack(x_values), dtype=torch.float32),
        node_types=torch.tensor([TYPE_TO_ID[node["type"]] for node in nodes], dtype=torch.long),
        edge_index=torch.tensor(edge_rows, dtype=torch.long).T,
        edge_types=torch.tensor(edge_type_values, dtype=torch.long),
        edge_attrs=torch.tensor(edge_attr_values, dtype=torch.float32),
        causal_nodes=torch.tensor([float(node["id"] in causal_node_ids) for node in nodes]),
        causal_edges=torch.tensor(causal_edge_values),
        label=float(row["material_contradiction"] or 0),
    )


def batch_graphs(samples: list[GraphSample]) -> GraphBatch:
    xs, types, edges, rels, attrs, graph_ids, node_labels, edge_labels = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    offset = 0
    for graph_index, sample in enumerate(samples):
        xs.append(sample.x)
        types.append(sample.node_types)
        edges.append(sample.edge_index + offset)
        rels.append(sample.edge_types)
        attrs.append(sample.edge_attrs)
        graph_ids.append(torch.full((len(sample.x),), graph_index, dtype=torch.long))
        node_labels.append(sample.causal_nodes)
        edge_labels.append(sample.causal_edges)
        offset += len(sample.x)
    return GraphBatch(
        x=torch.cat(xs),
        node_types=torch.cat(types),
        edge_index=torch.cat(edges, dim=1),
        edge_types=torch.cat(rels),
        edge_attrs=torch.cat(attrs),
        graph_index=torch.cat(graph_ids),
        causal_nodes=torch.cat(node_labels),
        causal_edges=torch.cat(edge_labels),
        labels=torch.tensor([sample.label for sample in samples], dtype=torch.float32),
        samples=samples,
    )


def segment_softmax(scores: torch.Tensor, index: torch.Tensor, groups: int) -> torch.Tensor:
    maximum = torch.full((groups, scores.shape[1]), -1e9, device=scores.device)
    maximum.scatter_reduce_(
        0, index[:, None].expand_as(scores), scores, reduce="amax", include_self=True
    )
    exp_scores = torch.exp(scores - maximum[index])
    denominator = torch.zeros_like(maximum)
    denominator.index_add_(0, index, exp_scores)
    return exp_scores / (denominator[index] + 1e-9)


class MessageLayer(torch.nn.Module):
    def __init__(self, kind: str, hidden: int, relations: int, heads: int = 4) -> None:
        super().__init__()
        self.kind = kind
        self.hidden = hidden
        self.heads = heads
        self.self_linear = torch.nn.Linear(hidden, hidden)
        self.shared = torch.nn.Linear(hidden, hidden)
        self.q = torch.nn.Linear(hidden, hidden)
        self.k = torch.nn.Linear(hidden, hidden)
        self.v = torch.nn.Linear(hidden, hidden)
        self.rel_scale_k = torch.nn.Parameter(torch.ones(relations, hidden))
        self.rel_scale_v = torch.nn.Parameter(torch.ones(relations, hidden))
        self.rel_bias = torch.nn.Parameter(torch.zeros(relations, heads))
        self.edge_bias = torch.nn.Linear(4, heads, bias=False)
        self.rgcn = torch.nn.Parameter(torch.empty(relations, hidden, hidden))
        torch.nn.init.xavier_uniform_(self.rgcn)
        self.norm = torch.nn.LayerNorm(hidden)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_types: torch.Tensor,
        edge_attrs: torch.Tensor,
    ) -> torch.Tensor:
        src, dst = edge_index
        aggregate = torch.zeros_like(x)
        if self.kind == "graphsage":
            message = self.shared(x[src])
            aggregate.index_add_(0, dst, message)
            degree = torch.zeros(len(x), device=x.device).index_add_(
                0, dst, torch.ones(len(dst), device=x.device)
            )
            aggregate = aggregate / degree.clamp_min(1)[:, None]
        elif self.kind == "rgcn":
            for relation in range(self.rgcn.shape[0]):
                mask = edge_types == relation
                if bool(mask.any()):
                    aggregate.index_add_(0, dst[mask], x[src[mask]] @ self.rgcn[relation])
        else:
            head_dim = self.hidden // self.heads
            q = self.q(x[dst]).view(-1, self.heads, head_dim)
            k_base = self.k(x[src])
            v_base = self.v(x[src])
            if self.kind == "esran":
                k_base = k_base * self.rel_scale_k[edge_types]
                v_base = v_base * self.rel_scale_v[edge_types]
            k = k_base.view(-1, self.heads, head_dim)
            v = v_base.view(-1, self.heads, head_dim)
            scores = (q * k).sum(-1) / math.sqrt(head_dim)
            if self.kind == "esran":
                scores = scores + self.rel_bias[edge_types] + self.edge_bias(edge_attrs)
            weights = segment_softmax(scores, dst, len(x))
            message = (weights[..., None] * v).reshape(-1, self.hidden)
            aggregate.index_add_(0, dst, message)
        return self.norm(x + torch.relu(self.self_linear(x) + aggregate))


class EvidenceGraphModel(torch.nn.Module):
    def __init__(self, input_dim: int, kind: str) -> None:
        super().__init__()
        hidden = 64
        self.type_projection = torch.nn.ModuleList(
            [torch.nn.Linear(input_dim, hidden) for _ in NODE_TYPES]
        )
        self.layers = torch.nn.ModuleList(
            [MessageLayer(kind, hidden, len(RELATIONS)) for _ in range(2)]
        )
        self.pool = torch.nn.Linear(hidden, 1)
        self.case_head = torch.nn.Linear(hidden, 1)
        self.ground_head = torch.nn.Linear(hidden, 1)
        self.relation_head = torch.nn.Linear(hidden * 2, len(RELATIONS))
        self.dropout = torch.nn.Dropout(0.15)

    def forward(
        self, batch: GraphBatch
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        x = torch.zeros((len(batch.x), 64), dtype=batch.x.dtype, device=batch.x.device)
        for node_type, projection in enumerate(self.type_projection):
            mask = batch.node_types == node_type
            if bool(mask.any()):
                x[mask] = projection(batch.x[mask])
        x = torch.relu(x)
        for layer in self.layers:
            x = self.dropout(layer(x, batch.edge_index, batch.edge_types, batch.edge_attrs))
        pool_scores = self.pool(x)
        pool_weights = segment_softmax(pool_scores, batch.graph_index, len(batch.samples))
        graph_z = torch.zeros((len(batch.samples), x.shape[1]), dtype=x.dtype, device=x.device)
        graph_z.index_add_(0, batch.graph_index, pool_weights * x)
        src, dst = batch.edge_index
        relation_logits = self.relation_head(torch.cat([x[src], x[dst]], dim=1))
        return (
            self.case_head(graph_z).squeeze(1),
            self.ground_head(x).squeeze(1),
            relation_logits,
            graph_z,
        )


def pair_losses(
    logits: torch.Tensor, embeddings: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    consistent = torch.arange(0, len(logits), 2)
    contradictory = consistent + 1
    representation_distance = torch.linalg.vector_norm(
        embeddings[contradictory] - embeddings[consistent], dim=1
    )
    contrastive = torch.relu(1.0 - representation_distance).mean()
    counterfactual = torch.relu(1.0 - (logits[contradictory] - logits[consistent])).mean()
    return contrastive, counterfactual


def train_graph_model(
    train_batch: GraphBatch,
    dev_batch: GraphBatch,
    variant: dict[str, Any],
    seed: int,
) -> tuple[EvidenceGraphModel, dict[str, Any]]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    model = EvidenceGraphModel(train_batch.x.shape[1], variant["kind"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.002, weight_decay=0.0001)
    case_loss_fn = torch.nn.BCEWithLogitsLoss()
    ground_loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(4.0))
    relation_loss_fn = torch.nn.CrossEntropyLoss()
    best_state: dict[str, torch.Tensor] | None = None
    best_dev = -1.0
    patience = 0
    history = []
    started = time.perf_counter()
    for epoch in range(80):
        model.train()
        optimizer.zero_grad()
        case_logits, node_logits, relation_logits, graph_z = model(train_batch)
        case_loss = case_loss_fn(case_logits, train_batch.labels)
        relation_loss = relation_loss_fn(relation_logits, train_batch.edge_types)
        grounding_loss = ground_loss_fn(node_logits, train_batch.causal_nodes)
        contrastive_loss, counterfactual_loss = pair_losses(case_logits, graph_z)
        if variant.get("case_only"):
            loss = case_loss
        else:
            loss = case_loss + 0.20 * relation_loss
            if not variant.get("no_grounding"):
                loss = loss + 0.35 * grounding_loss
            if not variant.get("no_contrastive"):
                loss = loss + 0.15 * contrastive_loss
            if not variant.get("no_counterfactual"):
                loss = loss + 0.30 * counterfactual_loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0)
        optimizer.step()
        model.eval()
        with torch.no_grad():
            dev_logits = model(dev_batch)[0]
            labels = dev_batch.labels.numpy()
            predictions = (torch.sigmoid(dev_logits).numpy() >= 0.5).astype(int)
            tp = float(np.sum((predictions == 1) & (labels == 1)))
            fp = float(np.sum((predictions == 1) & (labels == 0)))
            fn = float(np.sum((predictions == 0) & (labels == 1)))
            dev_f1 = 2 * tp / max(1.0, 2 * tp + fp + fn)
        history.append(
            {"epoch": epoch + 1, "loss": round(float(loss.item()), 6), "dev_f1": round(dev_f1, 6)}
        )
        if dev_f1 > best_dev + 1e-6:
            best_dev = dev_f1
            best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
        if patience >= 10:
            break
    if best_state is None:
        raise RuntimeError("Neural training produced no checkpoint.")
    model.load_state_dict(best_state)
    return model, {
        "seed": seed,
        "epochs": len(history),
        "best_dev_f1": round(best_dev, 6),
        "seconds": round(time.perf_counter() - started, 3),
        "history": history,
    }


def graph_probabilities(
    model: EvidenceGraphModel, batch: GraphBatch
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    model.eval()
    with torch.no_grad():
        case_logits, node_logits, _, graph_z = model(batch)
    return (
        torch.sigmoid(case_logits).numpy(),
        torch.sigmoid(node_logits).numpy(),
        graph_z.numpy(),
    )


def save_torch_model(
    name: str, seed: int, model: EvidenceGraphModel, variant: dict[str, Any]
) -> dict[str, Any]:
    path = MODELS / f"{name}-seed-{seed}.pt"
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "variant": variant, "input_dim": 392}, path)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def load_torch_model(record: dict[str, Any]) -> EvidenceGraphModel:
    payload = torch.load(ROOT / record["path"], map_location="cpu", weights_only=True)
    model = EvidenceGraphModel(int(payload["input_dim"]), payload["variant"]["kind"])
    model.load_state_dict(payload["state_dict"])
    return model


def pair_metrics(
    rows: list[dict[str, Any]], probabilities: np.ndarray, threshold: float = 0.5
) -> dict[str, Any]:
    by_case = {row["case_id"]: index for index, row in enumerate(rows)}
    seen: set[str] = set()
    both_correct = 0
    changed = 0
    causal_direction = 0
    detected_contradictions = 0
    repaired_to_consistent = 0
    pairs = 0
    predictions = (probabilities >= threshold).astype(int)
    for row in rows:
        if row["pair_id"] in seen:
            continue
        seen.add(row["pair_id"])
        other_index = by_case[row["counterfactual_case_id"]]
        index = by_case[row["case_id"]]
        indices = [index, other_index]
        labels = [int(rows[item]["material_contradiction"]) for item in indices]
        if predictions[indices[0]] == labels[0] and predictions[indices[1]] == labels[1]:
            both_correct += 1
        if predictions[indices[0]] != predictions[indices[1]]:
            changed += 1
        pos = indices[labels.index(1)]
        neg = indices[labels.index(0)]
        if predictions[pos] == 1:
            detected_contradictions += 1
            repaired_to_consistent += int(predictions[neg] == 0)
        if probabilities[pos] > probabilities[neg]:
            causal_direction += 1
        pairs += 1
    return {
        "pairs": pairs,
        "both_correct_rate": round(both_correct / pairs, 6),
        "decision_changed_rate": round(changed / pairs, 6),
        "causal_direction_rate": round(causal_direction / pairs, 6),
        "repair_flip_rate": round(repaired_to_consistent / max(1, detected_contradictions), 6),
    }


def grounding_metrics(batch: GraphBatch, node_probabilities: np.ndarray) -> dict[str, Any]:
    truth = batch.causal_nodes.numpy().astype(int)
    predicted = (node_probabilities >= 0.5).astype(int)
    tp = int(np.sum((truth == 1) & (predicted == 1)))
    fp = int(np.sum((truth == 0) & (predicted == 1)))
    fn = int(np.sum((truth == 1) & (predicted == 0)))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def explanation_faithfulness(
    model: EvidenceGraphModel,
    samples: list[GraphSample],
    case_probabilities: np.ndarray,
    node_probabilities: np.ndarray,
    decision_threshold: float,
    limit: int = 48,
) -> dict[str, Any]:
    offsets = np.cumsum([0] + [len(sample.x) for sample in samples])
    selected_indices = [
        index
        for index, sample in enumerate(samples)
        if sample.label == 1 and case_probabilities[index] >= decision_threshold
    ][:limit]
    deletion_drops, random_drops, insertion_scores, sizes, exact = [], [], [], [], 0
    rng = np.random.default_rng(SEED)
    examples = []
    for index in selected_indices:
        sample = samples[index]
        local_scores = node_probabilities[offsets[index] : offsets[index + 1]]
        keep = list(np.flatnonzero(local_scores >= 0.5))
        if not keep:
            keep = list(np.argsort(local_scores)[-2:])
        # Greedy minimal sufficient set under the model's own 0.5 decision threshold.
        for candidate in sorted(keep, key=lambda item: local_scores[item]):
            trial = [item for item in keep if item != candidate]
            if not trial:
                continue
            modified = make_masked_sample(sample, trial, insertion=True)
            if graph_probabilities(model, batch_graphs([modified]))[0][0] >= decision_threshold:
                keep = trial
        deleted = make_masked_sample(sample, keep, insertion=False)
        inserted = make_masked_sample(sample, keep, insertion=True)
        deleted_score = graph_probabilities(model, batch_graphs([deleted]))[0][0]
        inserted_score = graph_probabilities(model, batch_graphs([inserted]))[0][0]
        random_keep = rng.choice(
            len(sample.x), size=min(len(keep), len(sample.x)), replace=False
        ).tolist()
        random_deleted = make_masked_sample(sample, random_keep, insertion=False)
        random_score = graph_probabilities(model, batch_graphs([random_deleted]))[0][0]
        deletion_drops.append(float(case_probabilities[index] - deleted_score))
        random_drops.append(float(case_probabilities[index] - random_score))
        insertion_scores.append(float(inserted_score))
        sizes.append(len(keep))
        truth = set(torch.nonzero(sample.causal_nodes, as_tuple=False).flatten().tolist())
        exact += int(set(keep) == truth)
        examples.append(
            {
                "case_id": sample.row["case_id"],
                "node_ids": [sample.row["nodes"][item]["id"] for item in keep],
                "deletion_drop": round(deletion_drops[-1], 6),
                "insertion_score": round(insertion_scores[-1], 6),
            }
        )
    count = len(selected_indices)
    return {
        "evaluated": count,
        "mean_nodes": round(float(np.mean(sizes)), 6) if sizes else 0.0,
        "exact_subgraph_rate": round(exact / count, 6) if count else 0.0,
        "mean_deletion_drop": round(float(np.mean(deletion_drops)), 6) if deletion_drops else 0.0,
        "random_deletion_drop": round(float(np.mean(random_drops)), 6) if random_drops else 0.0,
        "mean_insertion_score": round(float(np.mean(insertion_scores)), 6)
        if insertion_scores
        else 0.0,
        "examples": examples[:8],
    }


def make_masked_sample(sample: GraphSample, selected: list[int], insertion: bool) -> GraphSample:
    x = sample.x.clone()
    mask = (
        torch.ones(len(x), dtype=torch.bool) if insertion else torch.zeros(len(x), dtype=torch.bool)
    )
    mask[selected] = not insertion
    x[mask] = 0
    return GraphSample(
        row=sample.row,
        x=x,
        node_types=sample.node_types,
        edge_index=sample.edge_index,
        edge_types=sample.edge_types,
        edge_attrs=sample.edge_attrs,
        causal_nodes=sample.causal_nodes,
        causal_edges=sample.causal_edges,
        label=sample.label,
    )


def schema_reject(row: dict[str, Any]) -> bool:
    node_ids = {node.get("id") for node in row.get("nodes", [])}
    node_types = {node.get("type") for node in row.get("nodes", [])}
    text = " ".join(str(node.get("text", "")) for node in row.get("nodes", []))
    if not {"Claim", "Document", "Refund"}.issubset(node_types):
        return True
    if len(row.get("nodes", [])) > 30 or "output pass" in text.lower() or "払い戻し" in text:
        return True
    for node in row.get("nodes", []):
        if node.get("attrs", {}).get("currency") == "ZZZ":
            return True
    for edge in row.get("edges", []):
        if edge.get("src") not in node_ids or edge.get("dst") not in node_ids:
            return True
        if (
            edge.get("type") == "EVENT_BEFORE_EVENT"
            and edge.get("attrs", {}).get("delta_days", 0) < 0
        ):
            return True
    return False


def nli_probabilities(rows: list[dict[str, Any]]) -> tuple[np.ndarray | None, dict[str, Any]]:
    try:
        try:
            local_path = snapshot_download(repo_id=NLI_ID, local_files_only=True)
        except Exception:
            cache = (
                Path.home()
                / ".cache/huggingface/hub/models--cross-encoder--nli-MiniLM2-L6-H768/snapshots"
            )
            local_path = str(
                next(
                    path
                    for path in sorted(cache.glob("*"))
                    if (path / "model.safetensors").exists() and (path / "config.json").exists()
                )
            )
        model = CrossEncoder(local_path)
        pairs = [[claim_text(row), authoritative_text(row)] for row in rows]
        raw = np.asarray(model.predict(pairs, show_progress_bar=False))
        labels = model.model.config.id2label
        contradiction_index = next(
            (int(index) for index, label in labels.items() if "contrad" in str(label).lower()),
            0,
        )
        probabilities = torch.softmax(torch.tensor(raw), dim=1).numpy()[:, contradiction_index]
        return probabilities, {
            "status": "EXECUTED",
            "model_id": NLI_ID,
            "snapshot": Path(local_path).name,
            "labels": labels,
        }
    except Exception as error:
        return None, {"status": "UNAVAILABLE", "reason": str(error)}


def evaluate_stage(
    stage: Literal["dev", "test"], *, resume_dev_models: bool = False
) -> dict[str, Any]:
    manifest = read_json(DATA / "manifest.json")
    train_rows = read_jsonl(DATA / "train.jsonl")
    evaluation_rows = read_jsonl(DATA / f"{stage}.jsonl")
    ood_rows = read_jsonl(DATA / "ood.jsonl")
    if stage == "test":
        freeze = read_json(FREEZE_ARTIFACT)
        checks = {
            "protocol_sha256": sha256(PROTOCOL),
            "runner_sha256": sha256(RUNNER),
            "manifest_sha256": sha256(DATA / "manifest.json"),
            "dev_sha256": sha256(DEV_ARTIFACT),
            "test_dataset_sha256": sha256(DATA / "test.jsonl"),
        }
        if any(freeze.get(key) != value for key, value in checks.items()):
            raise RuntimeError("FECL v3 freeze mismatch; TEST execution refused.")
    embeddings, encoder_record = build_embeddings(
        {"train": train_rows, stage: evaluation_rows, "ood": ood_rows}
    )
    y_train = np.asarray([row["material_contradiction"] for row in train_rows], dtype=int)
    y_eval = np.asarray([row["material_contradiction"] for row in evaluation_rows], dtype=int)
    models: dict[str, Any] = {}
    scores: dict[str, np.ndarray] = {}

    scores["literal_rules"] = np.asarray([literal_score(row) for row in evaluation_rows])
    models["literal_rules"] = {
        "architecture": "literal semantic markers + deterministic parsed value relations",
        "metrics": metrics(y_eval, scores["literal_rules"]),
    }

    baseline_specs = {
        "communication_tfidf": (
            [claim_text(row) for row in train_rows],
            [claim_text(row) for row in evaluation_rows],
        ),
        "linearized_tfidf": (
            [linearize(row) for row in train_rows],
            [linearize(row) for row in evaluation_rows],
        ),
    }
    for name, (train_texts, eval_texts) in baseline_specs.items():
        if stage == "dev":
            model = tfidf_pipeline()
            model.fit(train_texts, y_train)
            path = MODELS / f"{name}.joblib"
            path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, path, compress=3)
        else:
            path = MODELS / f"{name}.joblib"
            model = joblib.load(path)
        scores[name] = model.predict_proba(eval_texts)[:, 1]
        models[name] = {
            "architecture": name.replace("_", " "),
            "metrics": metrics(y_eval, scores[name]),
            "model_sha256": sha256(path),
        }

    train_rel = relational_embedding(train_rows, embeddings)
    eval_rel = relational_embedding(evaluation_rows, embeddings)
    if stage == "dev":
        bi_model = LogisticRegression(
            max_iter=2_000, class_weight="balanced", random_state=SEED
        ).fit(train_rel, y_train)
        joblib.dump(bi_model, MODELS / "bi_encoder.joblib", compress=3)
    else:
        bi_model = joblib.load(MODELS / "bi_encoder.joblib")
    scores["bi_encoder"] = bi_model.predict_proba(eval_rel)[:, 1]
    models["bi_encoder"] = {
        "architecture": "frozen MiniLM evidence/state relation vector",
        "metrics": metrics(y_eval, scores["bi_encoder"]),
        "model_sha256": sha256(MODELS / "bi_encoder.joblib"),
    }

    if stage == "dev":
        pca = PCA(n_components=32, random_state=SEED).fit(train_rel)
        xgb = XGBClassifier(
            n_estimators=140,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.8,
            n_jobs=1,
            random_state=SEED,
            eval_metric="logloss",
        )
        xgb.fit(
            np.hstack(
                [
                    pca.transform(train_rel),
                    np.vstack([deterministic_features(row) for row in train_rows]),
                ]
            ),
            y_train,
        )
        joblib.dump((pca, xgb), MODELS / "relational_xgboost.joblib", compress=3)
    else:
        pca, xgb = joblib.load(MODELS / "relational_xgboost.joblib")
    xgb_eval = np.hstack(
        [
            pca.transform(eval_rel),
            np.vstack([deterministic_features(row) for row in evaluation_rows]),
        ]
    )
    scores["relational_xgboost"] = xgb.predict_proba(xgb_eval)[:, 1]
    models["relational_xgboost"] = {
        "architecture": "PCA MiniLM relation + deterministic features + XGBoost",
        "metrics": metrics(y_eval, scores["relational_xgboost"]),
        "model_sha256": sha256(MODELS / "relational_xgboost.joblib"),
    }

    train_claims = [
        node["text"] for row in train_rows for node in row["nodes"] if node["type"] == "Claim"
    ]
    train_status = [
        node["attrs"]["status"]
        for row in train_rows
        for node in row["nodes"]
        if node["type"] == "Claim"
    ]
    if stage == "dev":
        status_model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), analyzer="char_wb", min_df=2)),
                ("head", LogisticRegression(max_iter=2_000, random_state=SEED)),
            ]
        ).fit(train_claims, train_status)
        neuro_model = LogisticRegression(
            max_iter=2_000, class_weight="balanced", random_state=SEED
        ).fit(semantic_state_features(train_rows, status_model), y_train)
        joblib.dump(
            (status_model, neuro_model), MODELS / "fecl_v2_neuro_symbolic.joblib", compress=3
        )
    else:
        status_model, neuro_model = joblib.load(MODELS / "fecl_v2_neuro_symbolic.joblib")
    scores["fecl_v2_neuro_symbolic"] = neuro_model.predict_proba(
        semantic_state_features(evaluation_rows, status_model)
    )[:, 1]
    models["fecl_v2_neuro_symbolic"] = {
        "architecture": "FECL-v2 semantic-state + deterministic relation baseline",
        "metrics": metrics(y_eval, scores["fecl_v2_neuro_symbolic"]),
        "model_sha256": sha256(MODELS / "fecl_v2_neuro_symbolic.joblib"),
    }

    nli_scores, nli_record = nli_probabilities(evaluation_rows)
    if nli_scores is not None:
        scores["nli_cross_encoder"] = nli_scores
        models["nli_cross_encoder"] = {
            "architecture": "pinned zero-shot NLI cross-encoder",
            "metrics": metrics(y_eval, nli_scores),
            **nli_record,
        }
    else:
        models["nli_cross_encoder"] = nli_record

    neural_records: dict[str, Any] = {}
    ensemble_embeddings: dict[str, np.ndarray] = {}
    node_outputs: dict[str, np.ndarray] = {}
    for name, variant in MODEL_VARIANTS.items():
        train_samples = [make_sample(row, embeddings, variant) for row in train_rows]
        eval_samples = [make_sample(row, embeddings, variant) for row in evaluation_rows]
        train_batch = batch_graphs(train_samples)
        eval_batch = batch_graphs(eval_samples)
        seed_scores, seed_node_scores, seed_embeddings, seed_metrics, model_records = (
            [],
            [],
            [],
            [],
            [],
        )
        trained_models = []
        for seed in NEURAL_SEEDS:
            if stage == "dev" and resume_dev_models:
                path = MODELS / f"{name}-seed-{seed}.pt"
                record = {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
                model = load_torch_model(record)
                training = {
                    "seed": seed,
                    "recovered_after_post_training_evaluation_failure": True,
                }
            elif stage == "dev":
                model, training = train_graph_model(train_batch, eval_batch, variant, seed)
                record = save_torch_model(name, seed, model, variant)
            else:
                dev = read_json(DEV_ARTIFACT)
                record = next(
                    item for item in dev["models"][name]["model_records"] if item["seed"] == seed
                )["artifact"]
                model = load_torch_model(record)
                training = {"seed": seed, "loaded_from_dev": True}
            probabilities, node_probabilities, graph_z = graph_probabilities(model, eval_batch)
            seed_scores.append(probabilities)
            seed_node_scores.append(node_probabilities)
            seed_embeddings.append(graph_z)
            seed_metrics.append(metrics(y_eval, probabilities))
            model_records.append({"seed": seed, "training": training, "artifact": record})
            trained_models.append(model)
        scores[name] = np.mean(seed_scores, axis=0)
        node_outputs[name] = np.mean(seed_node_scores, axis=0)
        ensemble_embeddings[name] = np.mean(seed_embeddings, axis=0)
        neural_records[name] = {
            "architecture": f"{variant['kind']} heterogeneous graph model",
            "metrics": metrics(y_eval, scores[name]),
            "pair_metrics": pair_metrics(evaluation_rows, scores[name]),
            "grounding": grounding_metrics(eval_batch, node_outputs[name]),
            "seed_f1": [record["f1"] for record in seed_metrics],
            "seed_f1_mean": round(float(np.mean([record["f1"] for record in seed_metrics])), 6),
            "seed_f1_std": round(
                float(np.std([record["f1"] for record in seed_metrics], ddof=1)), 6
            ),
            "model_records": model_records,
        }
    models.update(neural_records)

    if stage == "dev":
        thresholds = {
            name: select_threshold(y_eval, probability) for name, probability in scores.items()
        }
    else:
        dev_thresholds = read_json(DEV_ARTIFACT)["thresholds"]
        thresholds = {name: float(dev_thresholds[name]) for name in scores}
    for name, probability in scores.items():
        if name in models:
            models[name]["threshold"] = round(thresholds[name], 8)
            models[name]["metrics"] = metrics(y_eval, probability, thresholds[name])
            models[name]["pair_metrics"] = pair_metrics(
                evaluation_rows, probability, thresholds[name]
            )
            if stage == "dev":
                calibration_labels = y_eval
                calibration_scores = probability
                calibration_source = "same_dev_diagnostic_only"
            else:
                dev_predictions = read_json(DEV_ARTIFACT)["predictions"]
                calibration_labels = np.asarray(
                    [item["label"] for item in dev_predictions], dtype=int
                )
                calibration_scores = np.asarray(
                    [item["scores"][name] for item in dev_predictions], dtype=float
                )
                calibration_source = "dev_for_frozen_test"
            models[name]["conformal"] = conformal_diagnostic(
                calibration_labels,
                calibration_scores,
                y_eval,
                probability,
                calibration_source,
            )

    esran_samples = [
        make_sample(row, embeddings, MODEL_VARIANTS["esran"]) for row in evaluation_rows
    ]
    esran_explainer = load_torch_model(models["esran"]["model_records"][0]["artifact"])
    models["esran"]["explanation"] = explanation_faithfulness(
        esran_explainer,
        esran_samples,
        scores["esran"],
        node_outputs["esran"],
        thresholds["esran"],
    )

    comparisons = {}
    esran_prediction = (scores["esran"] >= thresholds["esran"]).astype(int)
    statistical_comparators = [
        "literal_rules",
        "linearized_tfidf",
        "relational_xgboost",
        "rgcn",
        "fecl_v2_neuro_symbolic",
    ]
    if "nli_cross_encoder" in scores:
        statistical_comparators.append("nli_cross_encoder")
    for comparator in statistical_comparators:
        comparator_prediction = (scores[comparator] >= thresholds[comparator]).astype(int)
        comparisons[comparator] = {
            "mcnemar": exact_mcnemar(y_eval, comparator_prediction, esran_prediction),
            "bootstrap": paired_group_bootstrap(
                evaluation_rows,
                y_eval,
                comparator_prediction,
                esran_prediction,
            ),
        }

    ood_schema = np.asarray([schema_reject(row) for row in ood_rows])
    if stage == "dev":
        centroid = ensemble_embeddings["esran"].mean(axis=0)
        dev_distances = np.linalg.norm(ensemble_embeddings["esran"] - centroid, axis=1)
        distance_threshold = float(np.quantile(dev_distances, 0.95))
    else:
        ood_reference = read_json(DEV_ARTIFACT)["ood_reference"]
        centroid = np.asarray(ood_reference["centroid"], dtype=float)
        distance_threshold = float(ood_reference["distance_threshold"])
    ood_samples = [make_sample(row, embeddings, MODEL_VARIANTS["esran"]) for row in ood_rows]
    ood_batch = batch_graphs(ood_samples)
    if stage == "dev":
        esran_models = [
            load_torch_model(item["artifact"]) for item in models["esran"]["model_records"]
        ]
    else:
        esran_models = [
            load_torch_model(item["artifact"])
            for item in read_json(DEV_ARTIFACT)["models"]["esran"]["model_records"]
        ]
    ood_graph_z = np.mean(
        [graph_probabilities(model, ood_batch)[2] for model in esran_models], axis=0
    )
    learned_reject = np.linalg.norm(ood_graph_z - centroid, axis=1) > distance_threshold
    combined_reject = ood_schema | learned_reject

    predictions = []
    for index, row in enumerate(evaluation_rows):
        predictions.append(
            {
                "case_id": row["case_id"],
                "pair_id": row["pair_id"],
                "counterfactual_case_id": row["counterfactual_case_id"],
                "family": row["family"],
                "phenomenon": row["phenomenon"],
                "label": int(row["material_contradiction"]),
                "scores": {name: round(float(value[index]), 8) for name, value in scores.items()},
                "decisions": {
                    name: int(value[index] >= thresholds[name]) for name, value in scores.items()
                },
                "esran_grounding": [
                    {"node_id": node["id"], "probability": round(float(probability), 8)}
                    for node, probability in zip(
                        row["nodes"],
                        node_outputs["esran"][
                            sum(len(item["nodes"]) for item in evaluation_rows[:index]) : sum(
                                len(item["nodes"]) for item in evaluation_rows[: index + 1]
                            )
                        ],
                        strict=True,
                    )
                ],
                "causal_subgraph": row["causal_subgraph"],
                "repair": row["repair"],
            }
        )

    eligible_comparators = [
        "literal_rules",
        "linearized_tfidf",
        "relational_xgboost",
        "rgcn",
        "fecl_v2_neuro_symbolic",
    ]
    if "nli_cross_encoder" in scores:
        eligible_comparators.append("nli_cross_encoder")
    strongest = max(
        eligible_comparators,
        key=lambda name: models[name]["metrics"]["f1"],
    )
    esran = models["esran"]
    gates = {
        "f1_margin": esran["metrics"]["f1"] >= models[strongest]["metrics"]["f1"] + 0.03,
        "bootstrap_ci_excludes_zero": comparisons[strongest]["bootstrap"]["ci95"][0] > 0,
        "mcnemar_p_lt_005": comparisons[strongest]["mcnemar"]["exact_two_sided_p"] < 0.05,
        "false_pass_lower": esran["metrics"]["false_pass"]
        < models[strongest]["metrics"]["false_pass"],
        "pair_both_correct_lift": esran["pair_metrics"]["both_correct_rate"]
        >= models["fecl_v2_neuro_symbolic"]["pair_metrics"]["both_correct_rate"] + 0.05,
        "selective_risk_improves": esran["metrics"]["risk_coverage"][2]["risk"]
        < esran["metrics"]["risk_coverage"][-1]["risk"],
        "combined_ood_ge_095": float(np.mean(combined_reject)) >= 0.95,
        "causal_subgraph_f1": esran["grounding"]["f1"] >= 0.75,
        "deletion_beats_random": esran["explanation"]["mean_deletion_drop"]
        > esran["explanation"]["random_deletion_drop"],
        "repair_flip_rate": esran["pair_metrics"]["repair_flip_rate"] >= 0.80,
        "artifacts_saved": True,
    }
    status = (
        "DEV_ONLY"
        if stage == "dev"
        else ("RESEARCH_CANDIDATE_NOT_DEPLOYED" if all(gates.values()) else "NO_GO_METHOD_REJECTED")
    )
    return {
        "artifact_version": "fecl-v3",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "boundary": {
            "split": stage.upper(),
            "synthetic": True,
            "runtime_changed": False,
            "gate_authority": False,
            "v1_v2_holdouts_accessed": False,
        },
        "dataset": {
            "manifest": manifest,
            "train_cases": len(train_rows),
            "evaluation_cases": len(evaluation_rows),
        },
        "encoder": encoder_record,
        "models": models,
        "thresholds": {name: round(value, 8) for name, value in thresholds.items()},
        "predictions": predictions,
        "statistical_tests": comparisons,
        "ood_reference": {
            "source": "DEV",
            "centroid": [round(float(value), 8) for value in centroid],
            "distance_threshold": round(distance_threshold, 8),
        },
        "ood": {
            "count": len(ood_rows),
            "schema_rejection_rate": round(float(np.mean(ood_schema)), 6),
            "learned_rejection_rate": round(float(np.mean(learned_reject)), 6),
            "combined_rejection_rate": round(float(np.mean(combined_reject)), 6),
            "distance_threshold": round(distance_threshold, 6),
        },
        "promotion": {
            "status": status,
            "strongest_comparator": strongest,
            "gates": gates,
            "selected_runtime": "regex-baseline-v1",
            "runtime_changed": False,
        },
    }


def freeze() -> int:
    if not DEV_ARTIFACT.exists():
        raise RuntimeError("Run DEV before freezing FECL v3.")
    payload = {
        "artifact_version": "fecl-v3-freeze",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(RUNNER),
        "manifest_sha256": sha256(DATA / "manifest.json"),
        "dev_sha256": sha256(DEV_ARTIFACT),
        "test_dataset_sha256": sha256(DATA / "test.jsonl"),
        "test_open_count": 0,
        "runtime_changed": False,
    }
    dump(FREEZE_ARTIFACT, payload)
    print(json.dumps(payload, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["dev", "test"])
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--confirm-final-test", action="store_true")
    parser.add_argument("--resume-dev-models", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        return freeze()
    if args.stage is None:
        parser.error("Choose --stage dev, --freeze, or --stage test --confirm-final-test.")
    if args.stage == "test" and not args.confirm_final_test:
        raise RuntimeError("TEST requires --confirm-final-test and may be executed once.")
    if args.stage == "test" and TEST_ARTIFACT.exists():
        raise RuntimeError("FECL v3 TEST artifact already exists; a second run is refused.")
    artifact = evaluate_stage(args.stage, resume_dev_models=args.resume_dev_models)
    target = DEV_ARTIFACT if args.stage == "dev" else TEST_ARTIFACT
    dump(target, artifact)
    print(json.dumps({"artifact": str(target), "promotion": artifact["promotion"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

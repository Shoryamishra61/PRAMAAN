"""Typed research orchestration; model nodes never own financial decisions."""

from __future__ import annotations

from itertools import pairwise
from time import perf_counter
from typing import Any, Literal, TypedDict, cast

from langgraph.graph import END, START, StateGraph

Decision = Literal["PASS", "REVIEW", "BLOCK"]


class TraceSpan(TypedDict):
    node: str
    latency_ms: float
    model_revision: str | None
    abstention_reason: str | None


class ResearchState(TypedDict, total=False):
    evidence: str
    context: list[dict[str, str]]
    claims: list[dict[str, Any]]
    grounded_claims: list[dict[str, Any]]
    structured_features: dict[str, float]
    semantic_findings: list[dict[str, Any]]
    deterministic_decision: Decision
    final_decision: Decision
    model_revision: str
    ood: bool
    abstention_reason: str | None
    human_review_required: bool
    trace: list[TraceSpan]


def _span(state: ResearchState, node: str, started: float) -> list[TraceSpan]:
    return [
        *state.get("trace", []),
        {
            "node": node,
            "latency_ms": round((perf_counter() - started) * 1_000, 6),
            "model_revision": state.get("model_revision"),
            "abstention_reason": state.get("abstention_reason"),
        },
    ]


def _observed_node(node: str):  # type: ignore[no-untyped-def]
    def run(state: ResearchState) -> dict[str, Any]:
        started = perf_counter()
        return {"trace": _span(state, node, started)}

    return run


def _ground(state: ResearchState) -> dict[str, Any]:
    started = perf_counter()
    evidence = state.get("evidence", "")
    grounded = []
    for claim in state.get("claims", []):
        quote = str(claim.get("source_quote", ""))
        matches = evidence.count(quote) if quote else 0
        grounded.append({**claim, "grounding_status": "GROUNDED" if matches == 1 else "REJECTED"})
    abstention = state.get("abstention_reason")
    if any(claim["grounding_status"] != "GROUNDED" for claim in grounded):
        abstention = "GROUNDING_FAILURE"
    updated = cast(ResearchState, {**state, "abstention_reason": abstention})
    return {
        "grounded_claims": grounded,
        "abstention_reason": abstention,
        "trace": _span(updated, "grounding_verification", started),
    }


def _uncertainty_gate(state: ResearchState) -> dict[str, Any]:
    started = perf_counter()
    abstention = state.get("abstention_reason")
    if state.get("ood") and abstention is None:
        abstention = "OOD_INPUT"
    deterministic = state.get("deterministic_decision", "REVIEW")
    final: Decision = "REVIEW" if abstention else deterministic
    updated = cast(ResearchState, {**state, "abstention_reason": abstention})
    return {
        "abstention_reason": abstention,
        "final_decision": final,
        "trace": _span(updated, "uncertainty_ood_gate", started),
    }


def _human_review(state: ResearchState) -> dict[str, Any]:
    started = perf_counter()
    return {
        "human_review_required": state.get("final_decision", "REVIEW") != "PASS",
        "trace": _span(state, "human_review", started),
    }


def build_research_graph() -> Any:
    """Compile the fixed evidence-to-trace graph with a deterministic decision input."""
    graph = StateGraph(ResearchState)
    graph.add_node("evidence_ingestion", _observed_node("evidence_ingestion"))
    graph.add_node("retrieval_context", _observed_node("retrieval_context"))
    graph.add_node("claim_extraction", _observed_node("claim_extraction"))
    graph.add_node("grounding_verification", _ground)
    graph.add_node("structured_features", _observed_node("structured_features"))
    graph.add_node("semantic_nli", _observed_node("semantic_nli"))
    graph.add_node("deterministic_reconciliation", _observed_node("deterministic_reconciliation"))
    graph.add_node("uncertainty_ood_gate", _uncertainty_gate)
    graph.add_node("human_review", _human_review)
    graph.add_node("evaluation_trace", _observed_node("evaluation_trace"))
    ordered = [
        "evidence_ingestion",
        "retrieval_context",
        "claim_extraction",
        "grounding_verification",
        "structured_features",
        "semantic_nli",
        "deterministic_reconciliation",
        "uncertainty_ood_gate",
        "human_review",
        "evaluation_trace",
    ]
    graph.add_edge(START, ordered[0])
    for source, target in pairwise(ordered):
        graph.add_edge(source, target)
    graph.add_edge(ordered[-1], END)
    return graph.compile()

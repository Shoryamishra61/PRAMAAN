from app.research_graph import build_research_graph


def test_graph_preserves_deterministic_block_and_exact_grounding() -> None:
    result = build_research_graph().invoke(
        {
            "evidence": "Your refund was processed.",
            "claims": [{"source_quote": "Your refund was processed."}],
            "deterministic_decision": "BLOCK",
            "model_revision": "test-model@abc123",
            "trace": [],
        }
    )
    assert result["final_decision"] == "BLOCK"
    assert result["grounded_claims"][0]["grounding_status"] == "GROUNDED"
    assert [span["node"] for span in result["trace"]] == [
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


def test_graph_can_only_make_an_uncertain_model_safer() -> None:
    result = build_research_graph().invoke(
        {
            "evidence": "Ambiguous evidence",
            "claims": [{"source_quote": "invented quote"}],
            "deterministic_decision": "PASS",
            "ood": True,
            "trace": [],
        }
    )
    assert result["abstention_reason"] == "GROUNDING_FAILURE"
    assert result["final_decision"] == "REVIEW"
    assert result["human_review_required"] is True

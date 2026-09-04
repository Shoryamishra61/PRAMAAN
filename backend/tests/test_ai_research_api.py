import json
from pathlib import Path

import pytest
from app.ai_research_api import AiResearchArtifactError, load_ai_research, load_fecl_v2


def test_ai_research_reads_generated_dev_artifact() -> None:
    response = load_ai_research()
    assert response.generated is True
    assert response.artifact["boundary"]["holdout_accessed"] is False
    assert response.artifact["promotion"]["runtime_selection_changed"] is False
    assert len(response.artifact_sha256) == 64


def test_ai_research_rejects_holdout_projection(tmp_path: Path) -> None:
    path = tmp_path / "research.json"
    path.write_text(
        json.dumps(
            {
                "artifact_version": "ai-research-study-v1",
                "boundary": {"holdout_accessed": True},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(AiResearchArtifactError):
        load_ai_research(path)


def test_fecl_v2_reads_frozen_generated_artifacts() -> None:
    response = load_fecl_v2()
    assert response.generated is True
    assert response.test["boundary"]["split"] == "TEST"
    assert response.test["promotion"]["status"] == "RESEARCH_WINNER_NOT_DEPLOYED"
    assert response.analysis["tuning_performed"] is False


def test_fecl_v2_rejects_unbound_analysis(tmp_path: Path) -> None:
    test_path = tmp_path / "test.json"
    analysis_path = tmp_path / "analysis.json"
    test_path.write_text(
        json.dumps(
            {
                "artifact_version": "fecl-v2",
                "boundary": {"split": "TEST"},
            }
        ),
        encoding="utf-8",
    )
    analysis_path.write_text(
        json.dumps({"source_test_sha256": "wrong", "tuning_performed": False}),
        encoding="utf-8",
    )
    with pytest.raises(AiResearchArtifactError):
        load_fecl_v2(test_path, analysis_path)

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.decision import GateStatus
from app.evaluation_artifact import (
    CasePrediction,
    DatasetProvenance,
    EvaluationResultArtifact,
    SystemProvenance,
    write_evaluation_artifact,
)
from app.main import create_app
from fastapi.testclient import TestClient


def saved_run(run_id: str, hour: int) -> EvaluationResultArtifact:
    return EvaluationResultArtifact(
        run_id=run_id,
        created_at=datetime(2026, 8, 23, hour, tzinfo=timezone.utc),
        system=SystemProvenance(
            system_version="deterministic-v1",
            extractor_id="regex-baseline-v1",
            model_id=None,
            prompt_version="not-applicable-regex-v1",
            claim_schema_version="1.0",
            config_sha256="a" * 64,
            code_commit="UNAVAILABLE_NOT_A_GIT_REPOSITORY",
        ),
        dataset=DatasetProvenance(
            dataset_id="DIG-RNP-SYN-v1",
            generator_version="1.0.0",
            split="dev",
            synthetic=True,
            manifest_sha256="b" * 64,
        ),
        predictions=(
            CasePrediction(
                case_id=f"case-{run_id}",
                predicted_status=GateStatus.BLOCK,
                expected_status=GateStatus.BLOCK,
                slice="test-fixture",
            ),
        ),
        metrics={
            "fixture_only": True,
            "material_conflict": {
                "precision": {"numerator": 1, "denominator": 1, "value": 1.0},
                "recall": {"numerator": 1, "denominator": 1, "value": 1.0},
                "f1": 1.0,
            },
        },
    )


def test_evaluation_endpoint_says_not_measured_when_no_artifact(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "db.sqlite3", results_directory=tmp_path / "missing"
    )

    response = TestClient(create_app(settings)).get("/api/v1/evaluation/latest")

    assert response.status_code == 200
    assert response.json() == {"status": "NOT_YET_MEASURED"}


def test_evaluation_endpoint_projects_newest_saved_artifact_only(tmp_path: Path) -> None:
    results = tmp_path / "results"
    write_evaluation_artifact(results, saved_run("older", 10))
    newest = write_evaluation_artifact(results, saved_run("newest", 12))
    settings = Settings(database_path=tmp_path / "db.sqlite3", results_directory=results)

    response = TestClient(create_app(settings)).get("/api/v1/evaluation/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "MEASURED"
    assert payload["run_id"] == "newest"
    assert payload["dataset"]["dataset_id"] == "DIG-RNP-SYN-v1"
    assert payload["dataset"]["synthetic"] is True
    assert "not production prevalence" in payload["synthetic_warning"]
    assert payload["metrics"]["fixture_only"] is True
    assert payload["artifact_sha256"] == newest.sha256
    assert "predictions" not in payload


def test_evaluation_endpoint_rejects_tampered_saved_artifact(tmp_path: Path) -> None:
    results = tmp_path / "results"
    written = write_evaluation_artifact(results, saved_run("tampered", 10))
    written.path.write_text("{}\n", encoding="utf-8")
    settings = Settings(database_path=tmp_path / "db.sqlite3", results_directory=results)

    response = TestClient(create_app(settings)).get("/api/v1/evaluation/latest")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "EVALUATION_ARTIFACT_INVALID"

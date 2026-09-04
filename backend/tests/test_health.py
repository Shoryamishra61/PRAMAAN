from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.database import connect_database
from app.main import create_app
from fastapi.testclient import TestClient


def test_health_reports_real_database_and_worker_state_without_secrets(tmp_path: Path) -> None:
    database_path = tmp_path / "health.sqlite3"
    settings = Settings(
        database_path=database_path,
        webhook_secret="must-never-appear",
        model_api_key="also-must-never-appear",
    )
    client = TestClient(create_app(settings))

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "app": "ok",
        "database": "ready",
        "worker": "idle",
        "inference_mode": "offline",
        "last_successful_job_at": None,
    }
    assert "secret" not in response.text.lower()
    assert "key" not in response.text.lower()
    assert "must-never-appear" not in response.text


def test_health_worker_status_is_derived_from_durable_queue(tmp_path: Path) -> None:
    database_path = tmp_path / "health.sqlite3"
    client = TestClient(create_app(Settings(database_path=database_path)))
    assert client.get("/api/v1/health").json()["database"] == "ready"
    with connect_database(database_path) as connection:
        connection.execute(
            "INSERT INTO dispute_cases "
            "(id, payment_id, amount_minor, currency, reason_profile, processing_status, "
            "workflow_status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "case_health",
                "pay_health",
                100,
                "INR",
                "refund_not_processed_v1",
                "QUEUED",
                "REVIEW_PENDING",
                "2026-08-23T10:00:00Z",
                "2026-08-23T10:00:00Z",
            ),
        )
        connection.execute(
            "INSERT INTO jobs "
            "(id, case_id, job_type, status, available_at, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "job_health",
                "case_health",
                "PROCESS_CASE",
                "PENDING",
                "2026-08-23T10:00:00Z",
                "2026-08-23T10:00:00Z",
                "2026-08-23T10:00:00Z",
            ),
        )

    assert client.get("/api/v1/health").json()["worker"] == "work_pending"


def test_health_degrades_when_database_path_is_unusable(tmp_path: Path) -> None:
    parent_file = tmp_path / "not_a_directory"
    parent_file.write_text("fixture", encoding="utf-8")
    client = TestClient(create_app(Settings(database_path=parent_file / "health.sqlite3")))

    assert client.get("/api/v1/health").json() == {
        "app": "degraded",
        "database": "unavailable",
        "worker": "unavailable",
        "inference_mode": "offline",
        "last_successful_job_at": None,
    }

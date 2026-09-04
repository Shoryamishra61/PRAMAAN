"""Truthful local health snapshot derived from SQLite state."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.config import InferenceMode
from app.database import SCHEMA_VERSION, connect_database, initialize_database


class HealthResponse(BaseModel):
    """Public health data with no credential or secret-presence fields."""

    model_config = ConfigDict(extra="forbid")

    app: Literal["ok", "degraded"]
    database: Literal["ready", "unavailable"]
    worker: Literal["idle", "work_pending", "processing", "failed", "unavailable"]
    inference_mode: InferenceMode
    last_successful_job_at: str | None = None


def read_health(database_path: Path, inference_mode: InferenceMode) -> HealthResponse:
    """Read schema and durable job state; do not claim an external dependency is healthy."""
    try:
        initialize_database(database_path)
        with connect_database(database_path) as connection:
            migration = connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
            ).fetchone()
            if migration is None or int(migration["version"]) != SCHEMA_VERSION:
                raise sqlite3.DatabaseError("schema version is unavailable")
            counts = {
                str(row["status"]): int(row["count"])
                for row in connection.execute(
                    "SELECT status, count(*) AS count FROM jobs GROUP BY status"
                ).fetchall()
            }
            completed = connection.execute(
                "SELECT max(updated_at) AS completed_at FROM jobs WHERE status = 'COMPLETED'"
            ).fetchone()
    except (OSError, sqlite3.Error):
        return HealthResponse(
            app="degraded",
            database="unavailable",
            worker="unavailable",
            inference_mode=inference_mode,
        )

    if counts.get("PROCESSING", 0):
        worker = "processing"
    elif counts.get("PENDING", 0) or counts.get("RETRYABLE_ERROR", 0):
        worker = "work_pending"
    elif counts.get("FAILED", 0):
        worker = "failed"
    else:
        worker = "idle"
    return HealthResponse(
        app="degraded" if worker == "failed" else "ok",
        database="ready",
        worker=worker,
        inference_mode=inference_mode,
        last_successful_job_at=(
            str(completed["completed_at"])
            if completed is not None and completed["completed_at"] is not None
            else None
        ),
    )

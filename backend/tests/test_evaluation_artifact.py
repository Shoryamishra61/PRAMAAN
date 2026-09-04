from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from app.decision import GateStatus
from app.evaluation_artifact import (
    CasePrediction,
    EvaluationResultArtifact,
    SystemProvenance,
    compute_config_sha256,
    read_dataset_provenance,
    write_evaluation_artifact,
)
from pydantic import ValidationError

REPO_ROOT = Path(__file__).parents[2]


def artifact() -> EvaluationResultArtifact:
    return EvaluationResultArtifact(
        run_id="dev-regex-001",
        created_at=datetime(2026, 8, 23, 12, tzinfo=timezone.utc),
        system=SystemProvenance(
            system_version="deterministic-v1",
            extractor_id="regex-baseline-v1",
            model_id=None,
            prompt_version="not-applicable-regex-v1",
            claim_schema_version="1.0",
            config_sha256=compute_config_sha256(
                REPO_ROOT,
                (REPO_ROOT / "contracts" / "grounded-claim.schema.json",),
            ),
            code_commit="UNAVAILABLE_NOT_A_GIT_REPOSITORY",
        ),
        dataset=read_dataset_provenance(REPO_ROOT / "data" / "benchmark" / "v1", "dev"),
        predictions=(
            CasePrediction(
                case_id="case_dev_001",
                predicted_status=GateStatus.PASS,
                expected_status=GateStatus.PASS,
                slice="claimed_processed_match",
            ),
        ),
        metrics={},
    )


def test_writer_records_provenance_and_matches_json_schema(tmp_path: Path) -> None:
    result = write_evaluation_artifact(tmp_path, artifact())
    stored: dict[str, Any] = json.loads(result.path.read_text(encoding="utf-8"))
    schema = json.loads(
        (REPO_ROOT / "contracts" / "evaluation-result.schema.json").read_text(encoding="utf-8")
    )

    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(
        stored
    )
    assert stored["dataset"]["dataset_id"] == "DIG-RNP-SYN-v1"
    assert stored["dataset"]["split"] == "dev"
    assert stored["dataset"]["synthetic"] is True
    assert stored["system"]["code_commit"] == "UNAVAILABLE_NOT_A_GIT_REPOSITORY"
    assert stored["predictions"][0]["case_id"] == "case_dev_001"


def test_writer_digest_matches_exact_saved_bytes_and_refuses_overwrite(tmp_path: Path) -> None:
    run = artifact()
    result = write_evaluation_artifact(tmp_path, run)

    assert hashlib.sha256(result.path.read_bytes()).hexdigest() == result.sha256
    assert result.digest_path.read_text(encoding="ascii") == (
        f"{result.sha256}  dev-regex-001.json\n"
    )
    with pytest.raises(FileExistsError, match="already exists"):
        write_evaluation_artifact(tmp_path, run)


def test_config_hash_changes_with_bytes_and_is_order_independent(tmp_path: Path) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.yaml"
    first.write_text("{}\n", encoding="utf-8")
    second.write_text("version: 1\n", encoding="utf-8")
    before = compute_config_sha256(tmp_path, (first, second))

    assert before == compute_config_sha256(tmp_path, (second, first))
    second.write_text("version: 2\n", encoding="utf-8")
    assert compute_config_sha256(tmp_path, (first, second)) != before


def test_contract_rejects_duplicate_case_ids_and_naive_timestamp() -> None:
    run = artifact()
    with pytest.raises(ValidationError, match="unique"):
        run.model_copy(update={"predictions": run.predictions * 2}).model_validate(
            run.model_copy(update={"predictions": run.predictions * 2}).model_dump()
        )
    with pytest.raises(ValidationError, match="timezone"):
        EvaluationResultArtifact.model_validate(
            {**run.model_dump(), "created_at": datetime(2026, 8, 23, 12)}
        )


def test_run_id_cannot_escape_output_directory() -> None:
    with pytest.raises(ValidationError, match="run_id"):
        artifact().model_copy(update={"run_id": "../escape"}).model_validate(
            artifact().model_copy(update={"run_id": "../escape"}).model_dump()
        )

"""Versioned evaluation result contract and immutable-by-convention writer."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

from app.decision import GateStatus
from app.domain import require_utc

ARTIFACT_SCHEMA_VERSION: Literal["1.0"] = "1.0"


class ClaimEvaluationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_type: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    normalized_value: JsonValue = None

    @model_validator(mode="after")
    def validate_span(self) -> ClaimEvaluationRecord:
        if self.end <= self.start:
            raise ValueError("claim end must be greater than start")
        return self


class CasePrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    predicted_status: GateStatus
    expected_status: GateStatus
    finding_codes: tuple[str, ...] = ()
    review_reasons: tuple[str, ...] = ()
    predicted_claims: tuple[ClaimEvaluationRecord, ...] = ()
    expected_claims: tuple[ClaimEvaluationRecord, ...] = ()
    slice: str = Field(min_length=1)


class SystemProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_id: Literal["dispute-integrity-gate"] = "dispute-integrity-gate"
    system_version: str = Field(min_length=1)
    extractor_id: str = Field(min_length=1)
    model_id: str | None
    prompt_version: str = Field(min_length=1)
    claim_schema_version: str = Field(min_length=1)
    config_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_commit: str = Field(min_length=1)


class DatasetProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(min_length=1)
    generator_version: str = Field(min_length=1)
    split: Literal["dev", "holdout"]
    synthetic: bool
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class EvaluationResultArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_schema_version: Literal["1.0"] = ARTIFACT_SCHEMA_VERSION
    run_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    created_at: datetime
    system: SystemProvenance
    dataset: DatasetProvenance
    predictions: tuple[CasePrediction, ...] = Field(min_length=1)
    metrics: dict[str, JsonValue]

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        return require_utc(value)

    @model_validator(mode="after")
    def validate_predictions(self) -> EvaluationResultArtifact:
        case_ids = [prediction.case_id for prediction in self.predictions]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("prediction case IDs must be unique")
        return self


class WrittenArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: Path
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    digest_path: Path


def compute_config_sha256(repo_root: Path, config_paths: tuple[Path, ...]) -> str:
    """Hash ordered path names and bytes so configuration provenance is reproducible."""
    root = repo_root.resolve()
    records: list[tuple[str, bytes]] = []
    for path in config_paths:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError(f"Config path is outside repository root: {path}") from exc
        records.append((relative, resolved.read_bytes()))
    if not records:
        raise ValueError("At least one config path is required.")
    digest = hashlib.sha256()
    for relative, content in sorted(records):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(content)
        digest.update(b"\x00")
    return digest.hexdigest()


def read_dataset_provenance(
    dataset_root: Path, split: Literal["dev", "holdout"]
) -> DatasetProvenance:
    dataset_value = json.loads((dataset_root / "dataset.json").read_text(encoding="utf-8"))
    if not isinstance(dataset_value, dict):
        raise ValueError("dataset.json must contain an object")
    dataset = cast(dict[str, object], dataset_value)
    return DatasetProvenance(
        dataset_id=str(dataset["dataset_id"]),
        generator_version=str(dataset["generator_version"]),
        split=split,
        synthetic=bool(dataset["synthetic"]),
        manifest_sha256=str(dataset["holdout_manifest_sha256"]),
    )


def write_evaluation_artifact(
    output_directory: Path, artifact: EvaluationResultArtifact
) -> WrittenArtifact:
    """Write a new canonical JSON artifact and digest sidecar; never overwrite either."""
    output_directory.mkdir(parents=True, exist_ok=True)
    artifact_path = output_directory / f"{artifact.run_id}.json"
    digest_path = output_directory / f"{artifact.run_id}.json.sha256"
    if artifact_path.exists() or digest_path.exists():
        raise FileExistsError(f"Evaluation run already exists: {artifact.run_id}")

    content = (
        json.dumps(
            artifact.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    with artifact_path.open("xb") as artifact_file:
        artifact_file.write(content)
    try:
        with digest_path.open("x", encoding="ascii", newline="\n") as digest_file:
            digest_file.write(f"{digest}  {artifact_path.name}\n")
    except BaseException:
        artifact_path.unlink(missing_ok=True)
        raise
    return WrittenArtifact(path=artifact_path, sha256=digest, digest_path=digest_path)

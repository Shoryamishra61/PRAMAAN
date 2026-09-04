"""Exact runtime/config freeze manifest for a repository without Git metadata."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.benchmark_integrity import verify_holdout_manifest
from app.domain import require_utc
from app.evaluation_artifact import compute_config_sha256

FREEZE_SCHEMA_VERSION: Literal["1.0"] = "1.0"
CODE_COMMIT_UNAVAILABLE: Literal["UNAVAILABLE_NOT_A_GIT_REPOSITORY"] = (
    "UNAVAILABLE_NOT_A_GIT_REPOSITORY"
)
CONFIG_PATHS = (
    Path("contracts/grounded-claim.schema.json"),
    Path("contracts/refund_not_processed_v1.yaml"),
)


class FrozenFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReleaseFreeze(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = FREEZE_SCHEMA_VERSION
    created_at: datetime
    code_commit: Literal["UNAVAILABLE_NOT_A_GIT_REPOSITORY"] = CODE_COMMIT_UNAVAILABLE
    code_bundle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    config_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    files: tuple[FrozenFile, ...] = Field(min_length=1)

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        return require_utc(value)


class ReleaseFreezeError(ValueError):
    """Raised when runtime bytes differ from the recorded pre-holdout freeze."""


def release_files(repo_root: Path) -> tuple[Path, ...]:
    """Return the complete implemented detector/evaluator surface in stable order."""
    paths = list((repo_root / "backend" / "app").glob("*.py"))
    paths.extend(
        repo_root / relative
        for relative in (
            "scripts/evaluate_benchmark.py",
            "scripts/freeze_release.py",
            "contracts/evaluation-result.schema.json",
            "contracts/gate-decision.schema.json",
            "contracts/grounded-claim.schema.json",
            "contracts/refund_not_processed_v1.yaml",
            "pyproject.toml",
        )
    )
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing[0])
    return tuple(sorted((path.resolve() for path in paths), key=lambda path: path.as_posix()))


def _file_records(repo_root: Path) -> tuple[FrozenFile, ...]:
    root = repo_root.resolve()
    return tuple(
        FrozenFile(
            path=path.relative_to(root).as_posix(),
            bytes=len(content := path.read_bytes()),
            sha256=hashlib.sha256(content).hexdigest(),
        )
        for path in release_files(root)
    )


def _bundle_digest(files: tuple[FrozenFile, ...]) -> str:
    digest = hashlib.sha256()
    for record in files:
        digest.update(record.path.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(record.bytes.to_bytes(8, byteorder="big"))
        digest.update(record.sha256.encode("ascii"))
        digest.update(b"\x00")
    return digest.hexdigest()


def create_release_freeze(
    repo_root: Path,
    dataset_root: Path,
    output_path: Path,
    created_at: datetime,
) -> ReleaseFreeze:
    """Write a new pre-holdout freeze manifest and refuse replacement."""
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite release freeze: {output_path}")
    root = repo_root.resolve()
    files = _file_records(root)
    freeze = ReleaseFreeze(
        created_at=created_at,
        code_bundle_sha256=_bundle_digest(files),
        config_sha256=compute_config_sha256(
            root, tuple(root / relative for relative in CONFIG_PATHS)
        ),
        holdout_manifest_sha256=verify_holdout_manifest(dataset_root),
        files=files,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(freeze.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return freeze


def verify_release_freeze(repo_root: Path, freeze_path: Path) -> ReleaseFreeze:
    """Fail if any relevant path, byte count, content hash, or bundle digest changed."""
    freeze = ReleaseFreeze.model_validate_json(freeze_path.read_bytes())
    current_files = _file_records(repo_root.resolve())
    if current_files != freeze.files or _bundle_digest(current_files) != freeze.code_bundle_sha256:
        raise ReleaseFreezeError("Runtime code/config bytes differ from release freeze.")
    current_config = compute_config_sha256(
        repo_root.resolve(),
        tuple(repo_root.resolve() / relative for relative in CONFIG_PATHS),
    )
    if current_config != freeze.config_sha256:
        raise ReleaseFreezeError("Extractor configuration differs from release freeze.")
    return freeze

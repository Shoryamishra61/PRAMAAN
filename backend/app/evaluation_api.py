"""Read-only evaluation dashboard projection from saved result artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue

from app.evaluation_artifact import DatasetProvenance, EvaluationResultArtifact, SystemProvenance

SYNTHETIC_WARNING = (
    "Synthetic, class-balanced diagnostic benchmark; not production prevalence or outcome evidence."
)


class EvaluationNotMeasured(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["NOT_YET_MEASURED"] = "NOT_YET_MEASURED"


class EvaluationDashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["MEASURED"] = "MEASURED"
    run_id: str
    created_at: str
    synthetic_warning: str
    dataset: DatasetProvenance
    system: SystemProvenance
    metrics: dict[str, JsonValue]
    artifact_sha256: str


class EvaluationArtifactError(ValueError):
    pass


def _validated_artifact(path: Path) -> tuple[EvaluationResultArtifact, str]:
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    digest_path = path.with_name(f"{path.name}.sha256")
    expected_sidecar = f"{digest}  {path.name}\n"
    if not digest_path.is_file() or digest_path.read_text(encoding="ascii") != expected_sidecar:
        raise EvaluationArtifactError(f"Artifact digest mismatch: {path.name}")
    try:
        artifact = EvaluationResultArtifact.model_validate_json(content)
    except ValueError as error:
        raise EvaluationArtifactError(f"Artifact schema invalid: {path.name}") from error
    return artifact, digest


def load_latest_evaluation(
    results_directory: Path,
) -> EvaluationDashboardResponse | EvaluationNotMeasured:
    """Load the newest saved JSON result without computing any metric."""
    if not results_directory.is_dir():
        return EvaluationNotMeasured()
    candidates = [_validated_artifact(path) for path in sorted(results_directory.glob("*.json"))]
    if not candidates:
        return EvaluationNotMeasured()
    artifact, digest = max(candidates, key=lambda item: item[0].created_at)
    if not artifact.dataset.synthetic:
        raise EvaluationArtifactError("MVP evaluation artifact must identify its dataset boundary.")
    return EvaluationDashboardResponse(
        run_id=artifact.run_id,
        created_at=artifact.created_at.isoformat().replace("+00:00", "Z"),
        synthetic_warning=SYNTHETIC_WARNING,
        dataset=artifact.dataset,
        system=artifact.system,
        metrics=json.loads(json.dumps(artifact.metrics)),
        artifact_sha256=digest,
    )

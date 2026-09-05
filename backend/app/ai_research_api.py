"""Read-only projection of the generated AI research artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ARTIFACT = REPO_ROOT / "artifacts/ml/ai-research-study-v1-dev.json"
FECL_V2_TEST_ARTIFACT = REPO_ROOT / "artifacts/ml/fecl-v2-test.json"
FECL_V2_ANALYSIS_ARTIFACT = REPO_ROOT / "artifacts/ml/fecl-v2-analysis.json"


class AiResearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_sha256: str
    generated: bool
    artifact: dict[str, Any]


class AiResearchArtifactError(ValueError):
    pass


class FeclV2Response(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated: bool
    test_sha256: str
    analysis_sha256: str
    test: dict[str, Any]
    analysis: dict[str, Any]


def load_ai_research(path: Path = RESEARCH_ARTIFACT) -> AiResearchResponse:
    try:
        raw = path.read_bytes()
        artifact = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise AiResearchArtifactError(str(error)) from error
    if not isinstance(artifact, dict):
        raise AiResearchArtifactError("AI research artifact must be an object.")
    boundary = artifact.get("boundary")
    if not isinstance(boundary, dict) or boundary.get("holdout_accessed") is not False:
        raise AiResearchArtifactError("Only the generated DEV research artifact may back /ai.")
    if artifact.get("artifact_version") != "ai-research-study-v1":
        raise AiResearchArtifactError("Unsupported AI research artifact version.")
    return AiResearchResponse(
        artifact_sha256=hashlib.sha256(raw).hexdigest(),
        generated=True,
        artifact=artifact,
    )


def _matches_sha(raw: bytes, expected: str | None) -> bool:
    if not expected:
        return False
    if hashlib.sha256(raw).hexdigest() == expected:
        return True
    lf_hash = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if lf_hash == expected:
        return True
    crlf_hash = hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
    return crlf_hash == expected


def load_fecl_v2(
    test_path: Path = FECL_V2_TEST_ARTIFACT,
    analysis_path: Path = FECL_V2_ANALYSIS_ARTIFACT,
) -> FeclV2Response:
    try:
        test_raw = test_path.read_bytes()
        analysis_raw = analysis_path.read_bytes()
        test = json.loads(test_raw)
        analysis = json.loads(analysis_raw)
    except (OSError, json.JSONDecodeError) as error:
        raise AiResearchArtifactError(str(error)) from error
    if not isinstance(test, dict) or not isinstance(analysis, dict):
        raise AiResearchArtifactError("FECL v2 artifacts must be objects.")
    if test.get("artifact_version") != "fecl-v2":
        raise AiResearchArtifactError("Unsupported FECL v2 test artifact version.")
    boundary = test.get("boundary")
    if not isinstance(boundary, dict) or boundary.get("split") != "TEST":
        raise AiResearchArtifactError("FECL v2 endpoint accepts only the frozen TEST artifact.")
    if not _matches_sha(test_raw, analysis.get("source_test_sha256")):
        raise AiResearchArtifactError("FECL v2 analysis is not bound to the test artifact.")
    if analysis.get("tuning_performed") is not False:
        raise AiResearchArtifactError("Post-hoc FECL analysis must not tune the holdout.")
    return FeclV2Response(
        generated=True,
        test_sha256=hashlib.sha256(test_raw).hexdigest(),
        analysis_sha256=hashlib.sha256(analysis_raw).hexdigest(),
        test=test,
        analysis=analysis,
    )

"""Small structured-log boundary that cannot accept evidence or secrets."""

from __future__ import annotations

import json
import logging

from pydantic import BaseModel, ConfigDict, Field

LOGGER = logging.getLogger("dispute_integrity_gate")


class StructuredLogEvent(BaseModel):
    """Allowlisted operational metadata only; untrusted content has no field."""

    model_config = ConfigDict(extra="forbid")

    module: str = Field(min_length=1, max_length=64)
    action: str = Field(min_length=1, max_length=96)
    correlation_id: str | None = Field(default=None, max_length=128)
    event_id: str | None = Field(default=None, max_length=128)
    case_id: str | None = Field(default=None, max_length=128)
    job_id: str | None = Field(default=None, max_length=128)
    extractor_id: str | None = Field(default=None, max_length=128)
    model_id: str | None = Field(default=None, max_length=128)
    request_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    schema_version: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=64)
    latency_ms: int | None = Field(default=None, ge=0)
    failure_class: str | None = Field(default=None, max_length=128)


def emit_log(event: StructuredLogEvent) -> None:
    """Emit deterministic JSON; JSON escaping prevents log-line injection."""
    LOGGER.info(
        json.dumps(
            event.model_dump(mode="json", exclude_none=True),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )

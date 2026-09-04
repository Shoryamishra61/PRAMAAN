"""Versioned, read-only structured-output replay adapter."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.extraction import CLAIM_SCHEMA_VERSION, ExtractionRequest, ExtractionResult

OFFLINE_CACHE_VERSION: Literal["1.0"] = "1.0"


class OfflineReplayMiss(LookupError):
    """Raised when the exact document/config/schema tuple was not precomputed."""


class OfflineReplayCache(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cache_version: Literal["1.0"] = OFFLINE_CACHE_VERSION
    source_mode: Literal["precomputed_regex_fixture"]
    extractor_config_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prompt_version: str
    schema_version: str
    entries: dict[str, ExtractionResult]


def offline_cache_key(
    canonical_text: str,
    extractor_config_sha256: str,
    schema_version: str = CLAIM_SCHEMA_VERSION,
) -> str:
    """Bind replay to exact UTF-8 text bytes, extractor config, and claim schema."""
    if len(extractor_config_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in extractor_config_sha256
    ):
        raise ValueError("extractor_config_sha256 must be lowercase SHA-256 hex")
    document_hash = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
    return hashlib.sha256(
        f"{document_hash}{extractor_config_sha256}{schema_version}".encode()
    ).hexdigest()


class OfflineReplayExtractor:
    """Exact cache lookup only; no tools, DB access, secrets, or fallback inference."""

    def __init__(self, cache_path: Path) -> None:
        self._cache = OfflineReplayCache.model_validate_json(cache_path.read_bytes())

    @property
    def source_mode(self) -> str:
        return self._cache.source_mode

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        key = offline_cache_key(
            request.canonical_text,
            self._cache.extractor_config_sha256,
            self._cache.schema_version,
        )
        result = self._cache.entries.get(key)
        if result is None:
            raise OfflineReplayMiss("No exact offline replay entry for document/config/schema.")
        return result.model_copy(deep=True)

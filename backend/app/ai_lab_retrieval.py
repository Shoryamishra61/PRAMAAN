"""Bounded local retrieval over an allowlisted, exact-quote documentation corpus."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict, Field
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import-untyped]

ALLOWED_SOURCE_PREFIX = "docs/"


class RetrievalChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    section: str = Field(min_length=1)
    text: str = Field(min_length=1)


class RetrievalCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    source_path: str
    section: str
    exact_excerpt: str


class BoundedRetriever:
    """TF-IDF ranking whose output is exact source text, not generated evidence."""

    def __init__(self, repo_root: Path, corpus_path: Path) -> None:
        self._repo_root = repo_root.resolve()
        raw = json.loads(corpus_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("AI lab retrieval corpus must be a JSON array.")
        chunks = tuple(RetrievalChunk.model_validate(item) for item in raw)
        if not chunks:
            raise ValueError("AI lab retrieval corpus must not be empty.")
        for chunk in chunks:
            if not chunk.source_path.startswith(ALLOWED_SOURCE_PREFIX):
                raise ValueError(
                    f"Retrieval source is outside the docs allowlist: {chunk.source_path}"
                )
            source = (self._repo_root / chunk.source_path).resolve()
            if self._repo_root not in source.parents or not source.is_file():
                raise ValueError(f"Retrieval source does not resolve inside repository: {source}")
            if chunk.text not in source.read_text(encoding="utf-8"):
                raise ValueError(
                    f"Retrieval excerpt is not exact in {chunk.source_path}: {chunk.chunk_id}"
                )
        self._chunks = chunks
        self._corpus_sha256 = hashlib.sha256(corpus_path.read_bytes()).hexdigest()
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)
        self._matrix = self._vectorizer.fit_transform([chunk.text for chunk in chunks])

    @property
    def corpus_sha256(self) -> str:
        return self._corpus_sha256

    def retrieve(self, query: str, *, limit: int = 3) -> tuple[RetrievalCitation, ...]:
        if not query.strip():
            return ()
        query_vector = self._vectorizer.transform([query])
        scores = cast(list[float], (self._matrix @ query_vector.T).toarray().ravel().tolist())
        ranked = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        selected = [index for index in ranked if scores[index] > 0.0][:limit]
        return tuple(
            RetrievalCitation(
                rank=rank,
                source_path=self._chunks[index].source_path,
                section=self._chunks[index].section,
                exact_excerpt=self._chunks[index].text,
            )
            for rank, index in enumerate(selected, start=1)
        )

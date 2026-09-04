"""Executable reason-profile metadata loaded from the canonical contract."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_PROFILE_ID = "refund_not_processed_v1"
DEFAULT_CONTRACT_PATH = Path(__file__).parents[2] / "contracts" / f"{DEFAULT_PROFILE_ID}.yaml"


class MaterialRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    condition: str = Field(min_length=1)
    action: Literal["REVIEW", "BLOCK"]


class ReasonProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: Literal["refund_not_processed_v1"]
    purpose: str
    external_alignment: dict[str, str]
    suggested_evidence: tuple[str, ...]
    review_if_missing: Literal[True]
    material_rules: tuple[MaterialRule, ...]
    notes: tuple[str, ...]


class ProfileResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    supported: bool
    profile: ReasonProfile | None = None
    review_reason: Literal["OUT_OF_SCOPE"] | None = None


@lru_cache
def load_default_profile() -> ReasonProfile:
    """Load and strictly validate the repository's canonical v1 profile contract."""
    raw = cast(object, yaml.safe_load(DEFAULT_CONTRACT_PATH.read_text(encoding="utf-8")))
    return ReasonProfile.model_validate(raw)


def resolve_profile(profile_id: str) -> ProfileResolution:
    """Resolve local scope without interpreting the raw Razorpay reason code."""
    if profile_id != DEFAULT_PROFILE_ID:
        return ProfileResolution(supported=False, review_reason="OUT_OF_SCOPE")
    return ProfileResolution(supported=True, profile=load_default_profile())


def missing_suggested_evidence(
    profile: ReasonProfile, available_categories: set[str]
) -> tuple[str, ...]:
    """List absent suggested categories; callers route any absence to REVIEW."""
    return tuple(
        category for category in profile.suggested_evidence if category not in available_categories
    )

"""Environment-backed application configuration."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class InferenceMode(str, Enum):
    """Supported semantic extraction modes."""

    LIVE = "live"
    OFFLINE = "offline"
    DISABLED = "disabled"


class Settings(BaseSettings):
    """Runtime configuration loaded only from environment variables."""

    model_config = SettingsConfigDict(env_prefix="DIG_", extra="ignore")

    environment: str = "development"
    database_path: Path = Path("var/dispute-integrity-gate.sqlite3")
    results_directory: Path = Path("results")
    inference_mode: InferenceMode = InferenceMode.OFFLINE
    demo_operator_id: str = "demo_operator"
    webhook_secret: SecretStr | None = None
    model_api_key: SecretStr | None = Field(default=None, repr=False)

    @model_validator(mode="after")
    def require_live_model_key(self) -> Settings:
        """Fail fast when live inference is selected without a credential."""
        if self.inference_mode is InferenceMode.LIVE and self.model_api_key is None:
            raise ValueError("DIG_MODEL_API_KEY is required when DIG_INFERENCE_MODE=live")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings snapshot per process."""
    return Settings()

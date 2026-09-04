from __future__ import annotations

import pytest
from app.config import InferenceMode, Settings
from pydantic import ValidationError


def test_defaults_use_offline_replay_without_external_inference() -> None:
    settings = Settings()

    assert settings.inference_mode is InferenceMode.OFFLINE
    assert settings.model_api_key is None


def test_live_mode_requires_model_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DIG_INFERENCE_MODE", "live")
    monkeypatch.delenv("DIG_MODEL_API_KEY", raising=False)

    with pytest.raises(ValidationError, match="DIG_MODEL_API_KEY"):
        Settings()

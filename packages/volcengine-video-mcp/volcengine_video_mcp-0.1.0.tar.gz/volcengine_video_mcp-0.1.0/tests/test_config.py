"""Tests for configuration module."""

import os

import pytest

from app.config import Config


def test_config_constants():
    """Test that configuration constants are properly defined."""
    assert Config.SERVER_NAME == "volcengine-video-mcp"
    assert Config.SERVER_VERSION == "0.1.0"
    assert Config.API_VERSION == "v3"
    assert "/api/v3/contents/generations/tasks" in Config.TASKS_ENDPOINT


def test_supported_models():
    """Test that supported models are defined."""
    assert len(Config.SUPPORTED_MODELS) > 0
    assert "doubao-seedance-1-0-pro" in Config.SUPPORTED_MODELS


def test_default_parameters():
    """Test default parameter values."""
    assert Config.DEFAULT_RESOLUTION == "720p"
    assert Config.DEFAULT_RATIO == "16:9"
    assert Config.DEFAULT_DURATION == 5
    assert Config.DEFAULT_FPS == 24
    assert Config.DEFAULT_SEED == -1


def test_get_full_url():
    """Test URL construction."""
    endpoint = "/api/v3/test"
    full_url = Config.get_full_url(endpoint)
    assert endpoint in full_url
    assert full_url.startswith("https://")


def test_validate_missing_api_key():
    """Test validation fails when API key is missing."""
    original_key = os.getenv("ARK_API_KEY")

    # Temporarily remove API key
    if original_key:
        del os.environ["ARK_API_KEY"]
        # Force config reload
        import importlib

        import app.config

        importlib.reload(app.config)
        from app.config import Config as ReloadedConfig

        with pytest.raises(ValueError, match="ARK_API_KEY"):
            ReloadedConfig.validate()

        # Restore original key
        os.environ["ARK_API_KEY"] = original_key
    else:
        with pytest.raises(ValueError, match="ARK_API_KEY"):
            Config.validate()

"""
Tests for configuration management.
"""

import pytest
from elanka_chat_ai.config import Settings


def test_settings_loads():
    """Test that settings can be instantiated."""
    settings = Settings()
    assert settings is not None


def test_default_values():
    """Test default configuration values."""
    settings = Settings()
    assert settings.mongodb_database == "elanka_chat_ai"
    assert settings.debug == True
    assert settings. crawl_delay == 1.0
    assert settings.max_crawl_depth == 2


def test_is_configured_false_when_empty():
    """Test is_configured returns False when keys are empty."""
    settings = Settings(mongodb_uri="", google_api_key="")
    assert settings.is_configured == False
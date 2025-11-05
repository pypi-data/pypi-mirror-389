"""Tests for configuration management."""

import pytest
from pathlib import Path

from inquire.config import ResearchConfig
from inquire.exceptions import ConfigurationError


def test_default_config():
    """Test default configuration values."""
    config = ResearchConfig()
    assert config.research_model == "gpt-4o"
    assert config.max_iterations == 5
    assert config.baml_dir == Path.cwd() / "baml_schemas"


def test_from_dict():
    """Test creating config from dict."""
    config = ResearchConfig.from_dict(
        {
            "research_model": "gpt-4-turbo",
            "max_iterations": 10,
        }
    )
    assert config.research_model == "gpt-4-turbo"
    assert config.max_iterations == 10


def test_from_dict_with_env_vars(monkeypatch):
    """Test environment variable fallback."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    config = ResearchConfig.from_dict({})
    assert config.openai_api_key == "test-key"


def test_validation_no_api_keys():
    """Test validation fails without API keys."""
    config = ResearchConfig()
    errors = config.validate()
    assert len(errors) > 0
    assert "No LLM API key" in errors[0]


def test_validation_tavily_requires_key():
    """Test Tavily search requires API key."""
    config = ResearchConfig(openai_api_key="test", search_api="tavily")
    errors = config.validate()
    assert any("Tavily" in e for e in errors)


def test_validate_or_raise():
    """Test validate_or_raise raises ConfigurationError."""
    config = ResearchConfig()
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_or_raise()
    assert "Configuration validation failed" in str(exc_info.value)


def test_valid_config_no_errors():
    """Test valid configuration passes validation."""
    config = ResearchConfig(
        openai_api_key="test-key", tavily_api_key="test-tavily"
    )
    errors = config.validate()
    assert len(errors) == 0
    config.validate_or_raise()  # Should not raise

"""Tests for core researcher."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from inquire.core import Researcher, research
from inquire.exceptions import ConfigurationError, ExtractionError


@pytest.fixture
def valid_config():
    """Valid test configuration."""
    return {
        "openai_api_key": "test-key",
        "tavily_api_key": "test-tavily",
    }


@pytest.mark.asyncio
async def test_researcher_init(valid_config, tmp_path):
    """Test Researcher initialization."""
    researcher = Researcher(
        baml_dir=tmp_path / "baml_schemas", config=valid_config
    )

    assert researcher.config.openai_api_key == "test-key"
    assert researcher.config.baml_dir == tmp_path / "baml_schemas"


def test_researcher_init_invalid_config():
    """Test Researcher raises on invalid config."""
    with pytest.raises(ConfigurationError):
        Researcher(config={})  # No API keys


@pytest.mark.asyncio
async def test_research_basic_flow(valid_config, tmp_path):
    """Test basic research flow."""
    researcher = Researcher(
        baml_dir=tmp_path / "baml_schemas", config=valid_config
    )

    # Mock dependencies
    with patch.object(
        researcher.baml_manager, "init", new_callable=AsyncMock
    ):
        with patch.object(researcher.baml_manager, "verify_function"):
            with patch.object(
                researcher, "_run_research", new_callable=AsyncMock, return_value="[Mock research output]"
            ):
                # Mock BAML function
                class MockResult:
                    pass

                async def mock_baml_func(research_output: str):
                    return MockResult()

                result = await researcher.research(
                    research_instructions="Test research",
                    schema=MockResult,
                    baml_function=mock_baml_func,
                )

                assert isinstance(result, MockResult)


@pytest.mark.asyncio
async def test_research_extraction_error(valid_config, tmp_path):
    """Test research handles extraction errors."""
    researcher = Researcher(
        baml_dir=tmp_path / "baml_schemas", config=valid_config
    )

    with patch.object(
        researcher.baml_manager, "init", new_callable=AsyncMock
    ):
        with patch.object(researcher.baml_manager, "verify_function"):
            with patch.object(
                researcher, "_run_research", new_callable=AsyncMock, return_value="[Mock research output]"
            ):
                # Mock BAML function that raises
                async def mock_baml_func(research_output: str):
                    raise ValueError("Extraction failed")

                with pytest.raises(ExtractionError) as exc_info:
                    await researcher.research(
                        research_instructions="Test",
                        schema=object,
                        baml_function=mock_baml_func,
                    )

                assert "BAML extraction failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_research_type_mismatch(valid_config, tmp_path):
    """Test research validates result type."""
    researcher = Researcher(
        baml_dir=tmp_path / "baml_schemas", config=valid_config
    )

    with patch.object(
        researcher.baml_manager, "init", new_callable=AsyncMock
    ):
        with patch.object(researcher.baml_manager, "verify_function"):
            with patch.object(
                researcher, "_run_research", new_callable=AsyncMock, return_value="[Mock research output]"
            ):
                class ExpectedType:
                    pass

                class WrongType:
                    pass

                async def mock_baml_func(research_output: str):
                    return WrongType()

                with pytest.raises(ExtractionError) as exc_info:
                    await researcher.research(
                        research_instructions="Test",
                        schema=ExpectedType,
                        baml_function=mock_baml_func,
                    )

                assert "expected" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_convenience_function(valid_config, tmp_path):
    """Test convenience research() function."""
    with patch("inquire.core.Researcher") as mock_researcher_class:
        mock_instance = MagicMock()
        mock_instance.research = AsyncMock(return_value="result")
        mock_researcher_class.return_value = mock_instance

        result = await research(
            research_instructions="Test",
            schema=object,
            baml_function=lambda x: x,
            config=valid_config,
        )

        mock_researcher_class.assert_called_once()
        mock_instance.research.assert_called_once()
        assert result == "result"

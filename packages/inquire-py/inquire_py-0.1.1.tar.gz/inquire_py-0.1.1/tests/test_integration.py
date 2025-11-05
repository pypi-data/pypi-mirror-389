"""End-to-end integration tests."""

import pytest
from unittest.mock import AsyncMock, patch

from inquire import research, Researcher


@pytest.mark.asyncio
@pytest.mark.integration
async def test_end_to_end_research_flow(tmp_path):
    """Test complete research flow from API to result."""
    # Setup
    baml_dir = tmp_path / "baml_schemas"
    (baml_dir / "baml_src").mkdir(parents=True)
    (baml_dir / "baml_client").mkdir(parents=True)

    config = {
        "openai_api_key": "test-key",
        "tavily_api_key": "test-tavily",
    }

    # Mock BAML components
    class MockCompanyInfo:
        def __init__(self):
            self.name = "Test Company"
            self.description = "A test company"
            self.founders = ["Founder 1", "Founder 2"]
            self.funding = "$10M"

    async def mock_baml_function(research_output: str):
        return MockCompanyInfo()

    # Mock BamlManager
    with patch("inquire.core.BamlManager") as mock_manager_class:
        mock_manager = mock_manager_class.return_value
        mock_manager.init = AsyncMock()
        mock_manager.verify_function = lambda x: None

        # Mock the _run_research method on Researcher class
        with patch("inquire.core.Researcher._run_research", new_callable=AsyncMock, return_value="[Mock research output]"):
            # Execute research
            result = await research(
                research_instructions="Research Test Company",
                schema=MockCompanyInfo,
                baml_function=mock_baml_function,
                config=config,
            )

            # Verify
            assert result.name == "Test Company"
            assert len(result.founders) == 2
            assert result.funding == "$10M"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_researcher_multiple_calls(tmp_path):
    """Test Researcher can handle multiple sequential calls."""
    baml_dir = tmp_path / "baml_schemas"
    (baml_dir / "baml_src").mkdir(parents=True)

    config = {
        "openai_api_key": "test-key",
        "tavily_api_key": "test-tavily",
    }

    researcher = Researcher(baml_dir=baml_dir, config=config)

    class MockResult:
        pass

    async def mock_func(output: str):
        return MockResult()

    with patch.object(researcher.baml_manager, "init", new_callable=AsyncMock):
        with patch.object(researcher.baml_manager, "verify_function"):
            with patch.object(researcher, "_run_research", new_callable=AsyncMock, return_value="[Mock research output]"):
                # First call
                result1 = await researcher.research(
                    research_instructions="Test 1",
                    schema=MockResult,
                    baml_function=mock_func,
                )

                # Second call
                result2 = await researcher.research(
                    research_instructions="Test 2",
                    schema=MockResult,
                    baml_function=mock_func,
                )

                assert isinstance(result1, MockResult)
                assert isinstance(result2, MockResult)

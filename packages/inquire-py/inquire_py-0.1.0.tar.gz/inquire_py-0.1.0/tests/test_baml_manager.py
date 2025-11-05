"""Tests for BAML manager."""

import pytest
from unittest.mock import AsyncMock, patch

from inquire.baml_manager import BamlManager
from inquire.exceptions import BamlError


@pytest.fixture
def baml_dir(tmp_path):
    """Create temporary BAML directory."""
    return tmp_path / "baml_schemas"


@pytest.mark.asyncio
async def test_init_creates_project(baml_dir):
    """Test initialization creates BAML project if missing."""
    manager = BamlManager(baml_dir)

    with patch.object(
        manager, "_run_baml_init", new_callable=AsyncMock
    ) as mock_init:
        with patch.object(
            manager, "_run_baml_generate", new_callable=AsyncMock
        ) as mock_gen:
            await manager.init()

            mock_init.assert_called_once()
            mock_gen.assert_called_once()
            assert manager._initialized


@pytest.mark.asyncio
async def test_init_skips_if_exists(baml_dir):
    """Test initialization skips if project exists."""
    (baml_dir / "baml_src").mkdir(parents=True)
    manager = BamlManager(baml_dir)

    with patch.object(
        manager, "_run_baml_init", new_callable=AsyncMock
    ) as mock_init:
        with patch.object(
            manager, "_run_baml_generate", new_callable=AsyncMock
        ) as mock_gen:
            await manager.init()

            mock_init.assert_not_called()
            mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_init_idempotent(baml_dir):
    """Test init can be called multiple times safely."""
    manager = BamlManager(baml_dir)

    with patch.object(manager, "_run_baml_init", new_callable=AsyncMock):
        with patch.object(
            manager, "_run_baml_generate", new_callable=AsyncMock
        ) as mock_gen:
            await manager.init()
            await manager.init()  # Second call

            # Generate should only be called once
            assert mock_gen.call_count == 1


def test_verify_function_valid():
    """Test verify_function accepts valid callable."""
    manager = BamlManager()

    # Mock BAML function
    async def mock_baml_func(research_output: str):
        return {}

    # Should not raise
    manager.verify_function(mock_baml_func)


def test_verify_function_invalid():
    """Test verify_function rejects non-callable."""
    manager = BamlManager()

    with pytest.raises(BamlError) as exc_info:
        manager.verify_function("not_a_function")

    assert "Invalid BAML function" in str(exc_info.value)


def test_get_function_name():
    """Test extracting function name."""
    manager = BamlManager()

    def test_function():
        pass

    name = manager.get_function_name(test_function)
    assert name == "test_function"

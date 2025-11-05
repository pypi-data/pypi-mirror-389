# Implementation Plan: inquire

**Target:** Build the `inquire` library from scratch following the technical design.

**Approach:** Sequential, test-driven implementation with validation at each step.

---

## Phase 1: Project Bootstrap

### Task 1.1: Initialize Python Project with uv

**Objective:** Create project structure and configure `pyproject.toml`

**Steps:**
1. Create directory: `inquire/`
2. Run: `uv init --lib`
3. Create `pyproject.toml` with:
   ```toml
   [project]
   name = "inquire"
   version = "0.1.0"
   description = "Intelligent inquiry with structured results - BAML + Deep Research"
   requires-python = ">=3.11"

   dependencies = [
       "baml-py>=0.60.0",
       "pydantic>=2.0",
   ]

   [project.optional-dependencies]
   dev = [
       "pytest>=8.0",
       "pytest-asyncio>=0.23",
       "pytest-cov>=4.0",
       "ruff>=0.3",
       "mypy>=1.8",
   ]

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```

4. Create directory structure:
   ```
   inquire/
   ├── pyproject.toml
   ├── README.md
   ├── .gitignore
   ├── src/inquire/
   │   ├── __init__.py
   │   ├── core.py
   │   ├── baml_manager.py
   │   ├── config.py
   │   ├── exceptions.py
   │   └── types.py
   ├── baml_schemas/
   │   └── .gitkeep
   ├── examples/
   │   └── .gitkeep
   └── tests/
       └── .gitkeep
   ```

5. Create `.gitignore`:
   ```gitignore
   baml_schemas/baml_client/
   __pycache__/
   *.pyc
   .pytest_cache/
   .mypy_cache/
   .ruff_cache/
   dist/
   *.egg-info/
   .venv/
   .env
   ```

6. Run: `uv sync`

**Validation:**
- `uv run python -c "import inquire"` succeeds
- All directories created
- Dependencies installed

---

### Task 1.2: Create Exception Classes

**Objective:** Define custom exceptions for the library

**File:** `src/inquire/exceptions.py`

**Implementation:**
```python
"""Custom exceptions for inquire library."""


class InquireError(Exception):
    """Base exception for all inquire errors."""
    pass


class BamlError(InquireError):
    """BAML-related errors (init, generation, function not found)."""
    pass


class ResearchError(InquireError):
    """Research execution errors."""
    pass


class ExtractionError(InquireError):
    """BAML extraction/parsing errors."""
    pass


class ConfigurationError(InquireError):
    """Configuration validation errors."""
    pass
```

**Validation:**
- `uv run python -c "from inquire.exceptions import InquireError"` succeeds
- All exception classes importable

---

### Task 1.3: Create Type Definitions

**Objective:** Define type hints and protocols

**File:** `src/inquire/types.py`

**Implementation:**
```python
"""Type definitions and protocols for inquire."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BamlFunction(Protocol):
    """Protocol for BAML-generated functions."""

    async def __call__(self, research_output: str, **kwargs: Any) -> Any:
        """Execute BAML function with research output."""
        ...


# Type alias for config dict
ConfigDict = dict[str, Any]
```

**Validation:**
- `uv run python -c "from inquire.types import BamlFunction, ConfigDict"` succeeds

---

## Phase 2: Configuration System

### Task 2.1: Implement Configuration Class

**Objective:** Create `ResearchConfig` for managing API keys and settings

**File:** `src/inquire/config.py`

**Implementation:**
```python
"""Configuration management for inquire."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from inquire.exceptions import ConfigurationError


@dataclass
class ResearchConfig:
    """Configuration for research execution."""

    # API Keys
    openai_api_key: str | None = None
    tavily_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Model selection
    research_model: str = "gpt-4o"
    extraction_model: str = "gpt-4o-mini"

    # Research parameters
    max_iterations: int = 5
    max_search_queries: int = 10
    search_api: str = "tavily"

    # BAML configuration
    baml_dir: Path = field(default_factory=lambda: Path.cwd() / "baml_schemas")

    # Base URLs (for custom deployments)
    openai_base_url: str | None = None
    anthropic_base_url: str | None = None

    @classmethod
    def from_dict(cls, config: dict) -> "ResearchConfig":
        """Create config from dict, with environment variable fallback."""
        return cls(
            openai_api_key=config.get("openai_api_key") or os.getenv("OPENAI_API_KEY"),
            tavily_api_key=config.get("tavily_api_key") or os.getenv("TAVILY_API_KEY"),
            anthropic_api_key=config.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY"),
            research_model=config.get("research_model", "gpt-4o"),
            extraction_model=config.get("extraction_model", "gpt-4o-mini"),
            max_iterations=config.get("max_iterations", 5),
            max_search_queries=config.get("max_search_queries", 10),
            search_api=config.get("search_api", "tavily"),
            baml_dir=Path(config.get("baml_dir", Path.cwd() / "baml_schemas")),
            openai_base_url=config.get("openai_base_url"),
            anthropic_base_url=config.get("anthropic_base_url"),
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # At least one LLM API key required
        if not self.openai_api_key and not self.anthropic_api_key:
            errors.append(
                "No LLM API key provided. Set OPENAI_API_KEY or ANTHROPIC_API_KEY"
            )

        # Search API validation
        if self.search_api == "tavily" and not self.tavily_api_key:
            errors.append("Tavily API key required. Set TAVILY_API_KEY")

        # BAML directory validation
        if not self.baml_dir:
            errors.append("baml_dir must be specified")

        return errors

    def validate_or_raise(self) -> None:
        """Validate config and raise ConfigurationError if invalid."""
        errors = self.validate()
        if errors:
            raise ConfigurationError(
                f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )
```

**Tests:** `tests/test_config.py`

```python
"""Tests for configuration management."""

import os
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
    config = ResearchConfig.from_dict({
        "research_model": "gpt-4-turbo",
        "max_iterations": 10,
    })
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
    config = ResearchConfig(
        openai_api_key="test",
        search_api="tavily"
    )
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
        openai_api_key="test-key",
        tavily_api_key="test-tavily"
    )
    errors = config.validate()
    assert len(errors) == 0
    config.validate_or_raise()  # Should not raise
```

**Validation:**
- Run: `uv run pytest tests/test_config.py -v`
- All tests pass

---

## Phase 3: BAML Manager

### Task 3.1: Implement BamlManager

**Objective:** Create BAML CLI wrapper for initialization and verification

**File:** `src/inquire/baml_manager.py`

**Implementation:**
```python
"""BAML project management and CLI wrapper."""

import asyncio
from pathlib import Path
from typing import Any

from inquire.exceptions import BamlError
from inquire.types import BamlFunction


class BamlManager:
    """Manages BAML CLI and project initialization."""

    def __init__(self, baml_dir: Path | None = None):
        """Initialize BAML manager.

        Args:
            baml_dir: Path to BAML project directory (default: cwd/baml_schemas)
        """
        self.baml_dir = baml_dir or Path.cwd() / "baml_schemas"
        self._initialized = False

    async def init(self) -> None:
        """Initialize BAML project if needed."""
        if self._initialized:
            return

        # Check if BAML project exists
        baml_src = self.baml_dir / "baml_src"
        if not baml_src.exists():
            await self._run_baml_init()

        # Run baml-cli generate to ensure types are up-to-date
        await self._run_baml_generate()

        self._initialized = True

    async def _run_baml_init(self) -> None:
        """Run 'baml init' to create project structure."""
        self.baml_dir.mkdir(parents=True, exist_ok=True)

        process = await asyncio.create_subprocess_exec(
            "baml", "init",
            cwd=self.baml_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise BamlError(
                f"BAML init failed: {stderr.decode()}"
            )

    async def _run_baml_generate(self) -> None:
        """Run 'baml-cli generate' to generate Python types."""
        process = await asyncio.create_subprocess_exec(
            "baml-cli", "generate",
            cwd=self.baml_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise BamlError(
                f"BAML generate failed: {stderr.decode()}"
            )

    def verify_function(self, baml_function: Any) -> None:
        """Verify that a BAML function is valid.

        Args:
            baml_function: BAML function callable from baml_client.b

        Raises:
            BamlError: If function is not valid
        """
        if not isinstance(baml_function, BamlFunction):
            raise BamlError(
                f"Invalid BAML function: {baml_function}. "
                "Must be a callable from baml_client.b"
            )

    def get_function_name(self, baml_function: Any) -> str:
        """Get the name of a BAML function.

        Args:
            baml_function: BAML function callable

        Returns:
            Function name as string
        """
        if hasattr(baml_function, '__name__'):
            return baml_function.__name__
        return str(baml_function)
```

**Tests:** `tests/test_baml_manager.py`

```python
"""Tests for BAML manager."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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

    with patch.object(manager, '_run_baml_init', new_callable=AsyncMock) as mock_init:
        with patch.object(manager, '_run_baml_generate', new_callable=AsyncMock) as mock_gen:
            await manager.init()

            mock_init.assert_called_once()
            mock_gen.assert_called_once()
            assert manager._initialized


@pytest.mark.asyncio
async def test_init_skips_if_exists(baml_dir):
    """Test initialization skips if project exists."""
    (baml_dir / "baml_src").mkdir(parents=True)
    manager = BamlManager(baml_dir)

    with patch.object(manager, '_run_baml_init', new_callable=AsyncMock) as mock_init:
        with patch.object(manager, '_run_baml_generate', new_callable=AsyncMock) as mock_gen:
            await manager.init()

            mock_init.assert_not_called()
            mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_init_idempotent(baml_dir):
    """Test init can be called multiple times safely."""
    manager = BamlManager(baml_dir)

    with patch.object(manager, '_run_baml_init', new_callable=AsyncMock):
        with patch.object(manager, '_run_baml_generate', new_callable=AsyncMock) as mock_gen:
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
```

**Validation:**
- Run: `uv run pytest tests/test_baml_manager.py -v`
- All tests pass

---

## Phase 4: Core Researcher

### Task 4.1: Implement Researcher Class (Stub)

**Objective:** Create main orchestration class with stub implementation

**File:** `src/inquire/core.py`

**Implementation:**
```python
"""Core research orchestration."""

from pathlib import Path
from typing import Any

from inquire.baml_manager import BamlManager
from inquire.config import ResearchConfig
from inquire.exceptions import ResearchError, ExtractionError
from inquire.types import BamlFunction, ConfigDict


class Researcher:
    """Main research orchestrator using BAML-generated types."""

    def __init__(
        self,
        baml_dir: Path | None = None,
        config: ConfigDict | None = None
    ):
        """Initialize researcher.

        Args:
            baml_dir: Path to BAML project directory (default: cwd/baml_schemas)
            config: Optional configuration overrides
        """
        self.config = ResearchConfig.from_dict(config or {})

        # Override baml_dir if provided
        if baml_dir:
            self.config.baml_dir = baml_dir

        self.baml_manager = BamlManager(self.config.baml_dir)

        # Validate configuration
        self.config.validate_or_raise()

    async def research(
        self,
        research_instructions: str,
        schema: type,
        baml_function: Any,
    ) -> Any:
        """Execute research with BAML extraction.

        Args:
            research_instructions: What to research (can include context/focus)
            schema: BAML-generated type (from baml_client.types)
            baml_function: BAML function callable (from baml_client.b)

        Returns:
            Instance of schema with researched data

        Raises:
            ResearchError: If research execution fails
            ExtractionError: If BAML extraction fails
        """
        # Initialize BAML if needed
        await self.baml_manager.init()

        # Verify function is valid
        self.baml_manager.verify_function(baml_function)

        # Execute research (stub for now)
        research_output = await self._run_research(research_instructions)

        # Call BAML function for extraction
        try:
            result = await baml_function(research_output)
        except Exception as e:
            raise ExtractionError(
                f"BAML extraction failed: {e}"
            ) from e

        # Validate result matches schema
        if not isinstance(result, schema):
            raise ExtractionError(
                f"BAML function returned {type(result)}, expected {schema}"
            )

        return result

    async def _run_research(self, instructions: str) -> str:
        """Execute deep research and return text output.

        This is a stub implementation. Real implementation will integrate
        with open-deep-research library.

        Args:
            instructions: Research instructions

        Returns:
            Research output as text
        """
        # TODO: Integrate with open-deep-research
        # For now, return placeholder
        return f"[Research output for: {instructions}]"


async def research(
    research_instructions: str,
    schema: type,
    baml_function: Any,
    config: ConfigDict | None = None
) -> Any:
    """Convenience function for one-off research calls.

    Args:
        research_instructions: What to research (can include context/focus)
        schema: BAML-generated type (from baml_client.types)
        baml_function: BAML function callable (from baml_client.b)
        config: Optional configuration overrides

    Returns:
        Instance of schema with researched data
    """
    researcher = Researcher(config=config)
    return await researcher.research(
        research_instructions=research_instructions,
        schema=schema,
        baml_function=baml_function
    )
```

**Tests:** `tests/test_core.py`

```python
"""Tests for core researcher."""

import pytest
from pathlib import Path
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
        baml_dir=tmp_path / "baml_schemas",
        config=valid_config
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
        baml_dir=tmp_path / "baml_schemas",
        config=valid_config
    )

    # Mock dependencies
    with patch.object(researcher.baml_manager, 'init', new_callable=AsyncMock):
        with patch.object(researcher.baml_manager, 'verify_function'):
            # Mock BAML function
            class MockResult:
                pass

            async def mock_baml_func(research_output: str):
                return MockResult()

            result = await researcher.research(
                research_instructions="Test research",
                schema=MockResult,
                baml_function=mock_baml_func
            )

            assert isinstance(result, MockResult)


@pytest.mark.asyncio
async def test_research_extraction_error(valid_config, tmp_path):
    """Test research handles extraction errors."""
    researcher = Researcher(
        baml_dir=tmp_path / "baml_schemas",
        config=valid_config
    )

    with patch.object(researcher.baml_manager, 'init', new_callable=AsyncMock):
        with patch.object(researcher.baml_manager, 'verify_function'):
            # Mock BAML function that raises
            async def mock_baml_func(research_output: str):
                raise ValueError("Extraction failed")

            with pytest.raises(ExtractionError) as exc_info:
                await researcher.research(
                    research_instructions="Test",
                    schema=object,
                    baml_function=mock_baml_func
                )

            assert "BAML extraction failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_research_type_mismatch(valid_config, tmp_path):
    """Test research validates result type."""
    researcher = Researcher(
        baml_dir=tmp_path / "baml_schemas",
        config=valid_config
    )

    with patch.object(researcher.baml_manager, 'init', new_callable=AsyncMock):
        with patch.object(researcher.baml_manager, 'verify_function'):
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
                    baml_function=mock_baml_func
                )

            assert "expected ExpectedType" in str(exc_info.value)


@pytest.mark.asyncio
async def test_convenience_function(valid_config, tmp_path):
    """Test convenience research() function."""
    with patch('inquire.core.Researcher') as mock_researcher_class:
        mock_instance = MagicMock()
        mock_instance.research = AsyncMock(return_value="result")
        mock_researcher_class.return_value = mock_instance

        result = await research(
            research_instructions="Test",
            schema=object,
            baml_function=lambda x: x,
            config=valid_config
        )

        mock_researcher_class.assert_called_once()
        mock_instance.research.assert_called_once()
```

**Validation:**
- Run: `uv run pytest tests/test_core.py -v`
- All tests pass

---

### Task 4.2: Update Package Exports

**Objective:** Export main API from `__init__.py`

**File:** `src/inquire/__init__.py`

**Implementation:**
```python
"""inquire - Intelligent inquiry with structured results."""

from inquire.core import Researcher, research
from inquire.exceptions import (
    InquireError,
    BamlError,
    ResearchError,
    ExtractionError,
    ConfigurationError,
)

__version__ = "0.1.0"

__all__ = [
    "research",
    "Researcher",
    "InquireError",
    "BamlError",
    "ResearchError",
    "ExtractionError",
    "ConfigurationError",
]
```

**Validation:**
- Run: `uv run python -c "from inquire import research, Researcher"`
- No import errors

---

## Phase 5: Example Implementation

### Task 5.1: Create Example BAML Schema

**Objective:** Create working example for testing end-to-end flow

**Directory:** Create `baml_schemas/baml_src/` in project root

**File:** `baml_schemas/baml_src/company.baml`

```baml
class CompanyInfo {
  name string @description("Company's legal name")
  description string @description("What the company does")
  founders string[] @description("List of founder names")
  funding string? @description("Total funding raised (optional)")
}

function ExtractCompanyInfo(research_output: string) -> CompanyInfo {
  client GPT4
  prompt #"
    Extract company information from the research:

    {{ research_output }}

    {{ ctx.output_format }}
  "#
}

function ExtractCompanyFinancials(research_output: string) -> CompanyInfo {
  client GPT4
  prompt #"
    You are a financial analyst. Focus on financial metrics and revenue models.

    {{ research_output }}

    {{ ctx.output_format }}
  "#
}
```

**File:** `baml_schemas/baml_src/baml_client.baml`

```baml
client GPT4 {
  provider openai
  options {
    model gpt-4o
    temperature 0
  }
}
```

**Commands:**
1. Run: `baml-cli generate` from `baml_schemas/`
2. Verify `baml_schemas/baml_client/` is created

---

### Task 5.2: Create Basic Example

**Objective:** Working example demonstrating the API

**File:** `examples/01_basic_usage.py`

```python
"""Basic usage example for inquire library."""

import asyncio
import os

from inquire import research
from baml_client.types import CompanyInfo
from baml_client import b


async def main():
    """Run basic research example."""
    # Ensure API keys are set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Set OPENAI_API_KEY environment variable")
        return

    print("🔍 Researching Stripe...")

    result = await research(
        research_instructions="Research Stripe's founders and their backgrounds",
        schema=CompanyInfo,
        baml_function=b.ExtractCompanyInfo
    )

    print(f"\n✅ Results:")
    print(f"  Company: {result.name}")
    print(f"  Description: {result.description}")
    print(f"  Founders: {', '.join(result.founders)}")
    if result.funding:
        print(f"  Funding: {result.funding}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Validation:**
- Run: `uv run python examples/01_basic_usage.py`
- Should execute without errors (with OPENAI_API_KEY set)

---

## Phase 6: Integration Testing

### Task 6.1: End-to-End Integration Test

**Objective:** Test full flow with mocked external dependencies

**File:** `tests/test_integration.py`

```python
"""End-to-end integration tests."""

import pytest
from pathlib import Path
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
    with patch('inquire.core.BamlManager') as mock_manager_class:
        mock_manager = mock_manager_class.return_value
        mock_manager.init = AsyncMock()
        mock_manager.verify_function = lambda x: None

        # Execute research
        result = await research(
            research_instructions="Research Test Company",
            schema=MockCompanyInfo,
            baml_function=mock_baml_function,
            config=config
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

    with patch.object(researcher.baml_manager, 'init', new_callable=AsyncMock):
        with patch.object(researcher.baml_manager, 'verify_function'):
            # First call
            result1 = await researcher.research(
                research_instructions="Test 1",
                schema=MockResult,
                baml_function=mock_func
            )

            # Second call
            result2 = await researcher.research(
                research_instructions="Test 2",
                schema=MockResult,
                baml_function=mock_func
            )

            assert isinstance(result1, MockResult)
            assert isinstance(result2, MockResult)
```

**Validation:**
- Run: `uv run pytest tests/test_integration.py -v -m integration`
- All integration tests pass

---

## Phase 7: Documentation

### Task 7.1: Create README

**Objective:** User-facing documentation

**File:** `README.md`

```markdown
# inquire

**Intelligent inquiry with structured results**

Combine BAML's structured extraction with deep research capabilities.

## Installation

```bash
pip install inquire
```

## Quick Start

### 1. Define Schema in BAML

Create `baml_schemas/baml_src/company.baml`:

```baml
class CompanyInfo {
  name string @description("Company's legal name")
  description string @description("What the company does")
  founders string[] @description("List of founder names")
}

function ExtractCompanyInfo(research_output: string) -> CompanyInfo {
  client GPT4
  prompt #"
    Extract company information from the research:

    {{ research_output }}
    {{ ctx.output_format }}
  "#
}
```

### 2. Use in Python

```python
import asyncio
from inquire import research
from baml_client.types import CompanyInfo
from baml_client import b

async def main():
    result = await research(
        research_instructions="Research Stripe's founders",
        schema=CompanyInfo,
        baml_function=b.ExtractCompanyInfo
    )

    print(f"Company: {result.name}")
    print(f"Founders: {', '.join(result.founders)}")

asyncio.run(main())
```

## Features

- ✅ **BAML-first** - Single source of truth, no sync issues
- ✅ **Type-safe** - Full IDE autocomplete and validation
- ✅ **Extensible** - Multiple BAML functions per schema
- ✅ **Simple API** - One function call does everything

## Configuration

Set environment variables:

```bash
export OPENAI_API_KEY="your-key"
export TAVILY_API_KEY="your-key"  # For web search
```

Or pass config explicitly:

```python
from inquire import Researcher

researcher = Researcher(config={
    "openai_api_key": "your-key",
    "research_model": "gpt-4o",
})
```

## License

MIT
```

**Validation:**
- README renders correctly on GitHub
- All code examples are valid

---

## Phase 8: Final Validation

### Task 8.1: Run Full Test Suite

**Commands:**
```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=inquire --cov-report=term-missing

# Type checking
uv run mypy src/inquire

# Linting
uv run ruff check src/inquire tests
```

**Success Criteria:**
- All tests pass
- Test coverage >80%
- No type errors
- No linting errors

---

### Task 8.2: Build and Install Package

**Commands:**
```bash
# Build package
uv build

# Install locally
uv pip install -e .

# Test import
python -c "from inquire import research, Researcher; print('✅ Import successful')"
```

**Success Criteria:**
- Package builds successfully
- Local installation works
- Import successful

---

## Phase 9: Next Steps (Post-MVP)

### Open Deep Research Integration

**TODO:** Replace `_run_research` stub with actual integration:

```python
async def _run_research(self, instructions: str) -> str:
    """Execute deep research using open-deep-research library."""
    from open_deep_research import DeepResearch

    researcher = DeepResearch(
        api_key=self.config.openai_api_key,
        model=self.config.research_model,
        max_iterations=self.config.max_iterations,
    )

    result = await researcher.research(instructions)
    return result.output
```

### Additional Examples

1. `examples/02_multiple_functions.py` - Using different BAML functions
2. `examples/03_researcher_class.py` - Using Researcher for multiple calls
3. `examples/04_founder_research.py` - Real-world founder research example

### Error Handling Improvements

1. Retry logic for transient failures
2. Better error messages with suggestions
3. Partial result handling

---

## Success Criteria

**MVP is complete when:**

1. ✅ All core components implemented (Config, BamlManager, Researcher)
2. ✅ Main API works (`research()` function)
3. ✅ BAML integration functional (init, generate, function calls)
4. ✅ Test suite passes (unit + integration)
5. ✅ Example demonstrates end-to-end flow
6. ✅ Package can be installed and imported
7. ✅ README documentation complete

**Ready for real-world use when:**

1. ✅ Open Deep Research integration complete
2. ✅ Error handling production-ready
3. ✅ Multiple examples covering common patterns
4. ✅ Test coverage >85%
5. ✅ CI/CD pipeline configured

---

**END OF PLAN**

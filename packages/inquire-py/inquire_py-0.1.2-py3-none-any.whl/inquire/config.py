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
            anthropic_api_key=config.get("anthropic_api_key")
            or os.getenv("ANTHROPIC_API_KEY"),
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
                "Configuration validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

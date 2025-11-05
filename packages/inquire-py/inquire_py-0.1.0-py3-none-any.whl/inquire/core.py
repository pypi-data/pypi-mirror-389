"""Core research orchestration."""

from pathlib import Path
from typing import Any

from inquire.baml_manager import BamlManager
from inquire.config import ResearchConfig
from inquire.exceptions import ExtractionError, ResearchError
from inquire.types import ConfigDict


class Researcher:
    """Main research orchestrator using BAML-generated types."""

    def __init__(self, baml_dir: Path | None = None, config: ConfigDict | None = None):
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
            raise ExtractionError(f"BAML extraction failed: {e}") from e

        # Validate result matches schema
        if not isinstance(result, schema):
            raise ExtractionError(
                f"BAML function returned {type(result)}, expected {schema}"
            )

        return result

    async def _run_research(self, instructions: str) -> str:
        """Execute deep research and return text output.

        Uses Tavily for web search and OpenAI/Anthropic for synthesis.

        Args:
            instructions: Research instructions

        Returns:
            Research output as text synthesized from web research
        """
        from tavily import AsyncTavilyClient  # type: ignore
        from openai import AsyncOpenAI

        # Initialize Tavily client
        tavily_client = AsyncTavilyClient(api_key=self.config.tavily_api_key)

        # Perform web search
        try:
            search_results = await tavily_client.search(
                query=instructions,
                max_results=self.config.max_search_queries,
                include_raw_content=True,
            )
        except Exception as e:
            raise ResearchError(f"Web search failed: {e}") from e

        # Extract and format search results
        research_content = self._format_search_results(search_results)

        # Synthesize findings using LLM
        openai_client = AsyncOpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url,
        )

        synthesis_prompt = f"""Based on the following web search results, provide a comprehensive research report.

Research Query: {instructions}

Search Results:
{research_content}

Please synthesize these findings into a cohesive research report that addresses the query."""

        try:
            response = await openai_client.chat.completions.create(
                model=self.config.research_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a research assistant providing comprehensive, well-researched reports.",
                    },
                    {"role": "user", "content": synthesis_prompt},
                ],
                temperature=0.1,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ResearchError(f"Research synthesis failed: {e}") from e

    def _format_search_results(self, search_results: dict) -> str:
        """Format Tavily search results into readable text.

        Args:
            search_results: Raw search results from Tavily

        Returns:
            Formatted string of search results
        """
        formatted = []
        for idx, result in enumerate(search_results.get("results", []), 1):
            formatted.append(f"Source {idx}: {result.get('title', 'Untitled')}")
            formatted.append(f"URL: {result.get('url', 'No URL')}")
            formatted.append(f"Content: {result.get('content', 'No content')}")
            formatted.append("")

        return "\n".join(formatted)


async def research(
    research_instructions: str,
    schema: type,
    baml_function: Any,
    config: ConfigDict | None = None,
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
        baml_function=baml_function,
    )

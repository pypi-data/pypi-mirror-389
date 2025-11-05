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

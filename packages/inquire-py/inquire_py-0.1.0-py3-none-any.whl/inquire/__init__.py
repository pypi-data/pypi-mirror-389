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

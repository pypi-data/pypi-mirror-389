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

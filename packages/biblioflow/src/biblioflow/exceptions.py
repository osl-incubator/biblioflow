"""Exceptions raised by biblioflow."""


class BiblioFlowError(Exception):
    """Base class for biblioflow exceptions."""


class UnsupportedFormatError(BiblioFlowError):
    """Raised when an input or output format is not supported."""


class AmbiguousSourceError(BiblioFlowError):
    """Raised when a source cannot be interpreted without more information."""


class OptionalDependencyError(BiblioFlowError):
    """Raised when an optional dependency is required for an operation."""

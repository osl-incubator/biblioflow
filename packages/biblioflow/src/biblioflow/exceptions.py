"""
title: Exceptions raised by biblioflow.
"""


class BiblioFlowError(Exception):
    """
    title: Base class for biblioflow exceptions.
    """


class UnsupportedFormatError(BiblioFlowError):
    """
    title: Raised when an input or output format is not supported.
    """


class UnsupportedSourceError(BiblioFlowError):
    """
    title: Raised when a bibliographic source/provider is not supported.
    """


class AmbiguousSourceError(BiblioFlowError):
    """
    title: Raised when a source cannot be interpreted without more information.
    """


class SourceDetectionError(AmbiguousSourceError):
    """
    title: Raised when source and format auto-detection fails.
    """


class ParseError(BiblioFlowError):
    """
    title: Raised when input content cannot be parsed.
    """


class APIConfigurationError(BiblioFlowError):
    """
    title: Raised when an API connector is missing required configuration.
    """


class OptionalDependencyError(BiblioFlowError):
    """
    title: Raised when an optional dependency is required for an operation.
    """

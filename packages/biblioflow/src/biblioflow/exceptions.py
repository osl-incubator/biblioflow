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


class AmbiguousSourceError(BiblioFlowError):
    """
    title: Raised when a source cannot be interpreted without more information.
    """


class OptionalDependencyError(BiblioFlowError):
    """
    title: Raised when an optional dependency is required for an operation.
    """

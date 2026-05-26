"""Notebook app exceptions."""

from __future__ import annotations


class BiblioFlowNotebookError(Exception):
    """Base exception for biblioflow-nb."""


class NoDatasetError(BiblioFlowNotebookError):
    """Raised when an operation requires an active dataset."""

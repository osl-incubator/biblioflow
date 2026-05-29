"""
title: Report-generation exceptions.
"""

from __future__ import annotations

from biblioflow.exceptions import BiblioFlowError


class ReportError(BiblioFlowError):
    """
    title: Base class for report-generation errors.
    """


class ReportRenderError(ReportError):
    """
    title: Raised when Quarto cannot render a report.
    """

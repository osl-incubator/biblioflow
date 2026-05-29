"""
title: Professional Quarto and Typst reporting for biblioflow projects.
"""

from biblioflow.reporting.context import build_report_context, write_context
from biblioflow.reporting.errors import ReportError, ReportRenderError
from biblioflow.reporting.models import (
    PrismaFlow,
    ReportAsset,
    ReportProject,
    ReportResult,
    ReportSource,
    ReportWarning,
)
from biblioflow.reporting.prisma import (
    default_prisma,
    prisma_rows,
    render_prisma_svg,
    validate_prisma,
    write_prisma_svg,
)
from biblioflow.reporting.renderer import (
    ReportRenderer,
    generate_report,
    render_qmd,
    report,
)

__all__ = [
    "PrismaFlow",
    "ReportAsset",
    "ReportError",
    "ReportProject",
    "ReportRenderError",
    "ReportRenderer",
    "ReportResult",
    "ReportSource",
    "ReportWarning",
    "build_report_context",
    "default_prisma",
    "generate_report",
    "prisma_rows",
    "render_prisma_svg",
    "render_qmd",
    "report",
    "validate_prisma",
    "write_context",
    "write_prisma_svg",
]

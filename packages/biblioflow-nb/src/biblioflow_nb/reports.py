"""Convenience helpers for generating notebook reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from biblioflow_nb.services.dataset_service import DatasetService
from biblioflow_nb.services.report_service import ReportService
from biblioflow_nb.state import NotebookSession


def generate_report(
    records: Any,
    output: str | Path,
    **kwargs: Any,
) -> Any:
    """Generate a report from records using the notebook service wrapper."""
    session = NotebookSession()
    datasets = DatasetService(session)
    datasets.load(records, name=kwargs.pop("name", None))
    return ReportService(session, datasets).generate_report(output, **kwargs)

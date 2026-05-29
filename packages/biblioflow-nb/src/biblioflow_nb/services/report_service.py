"""Notebook report service backed by core biblioflow.reporting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from biblioflow_nb.services.dataset_service import DatasetService
from biblioflow_nb.state import NotebookExport, NotebookSession


class ReportService:
    """Generate notebook reports by delegating to biblioflow.reporting."""

    def __init__(self, session: NotebookSession, datasets: DatasetService) -> None:
        self.session = session
        self.datasets = datasets

    def generate_report(
        self,
        path: str | Path,
        *,
        title: str | None = None,
        subtitle: str | None = None,
        authors: list[str] | None = None,
        organization: str | None = None,
        template: str = "modern",
        completeness: str = "standard",
        render: bool = True,
        keep_qmd: bool = False,
        prisma: dict[str, Any] | None = None,
    ) -> Any:
        """Generate a PDF report for the active notebook dataset."""
        import biblioflow.reporting as reporting

        dataset = self.datasets.require_dataset()
        target = Path(path)
        report_project = reporting.ReportProject.from_records(
            dataset,
            title=title or self.session.active_dataset_name or "biblioflow report",
            subtitle=subtitle,
            authors=authors or [],
            organization=organization,
            project_id=self.session.session_id,
            prisma=prisma,
            metadata={"notebook_session": self.session.to_manifest()},
        )
        result = reporting.generate_report(
            report_project,
            output=target,
            template=template,
            completeness=_completeness(completeness),
            render=render,
            keep_qmd=keep_qmd or not render,
            keep_context=True,
        )
        self.session.add_export(
            NotebookExport(
                name=target.name,
                path=target,
                kind="report",
                format="pdf",
            )
        )
        return result


def _completeness(value: str) -> Any:
    if value not in {"summary", "standard", "complete"}:
        raise ValueError(f"Unsupported report completeness: {value}.")
    return value

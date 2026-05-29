"""Report orchestration service backed by core biblioflow reporting."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.services.dataset_service import DatasetService
from biblioflow_web_backend.services.project_store import ProjectStore, utc_now


class ReportService:
    """Generate downloadable reports using biblioflow.reporting."""

    def __init__(self, projects: ProjectStore, datasets: DatasetService) -> None:
        self.projects = projects
        self.datasets = datasets

    def list_reports(self, project_id: str) -> list[dict[str, Any]]:
        """List report artifacts for a project."""
        self.projects.get_project(project_id)
        reports_dir = self.projects.reports_dir(project_id)
        artifacts = []
        for path in sorted(reports_dir.iterdir(), key=lambda item: item.name):
            if path.is_file() and path.suffix.casefold() == ".pdf":
                artifacts.append(self._metadata(path.stem, path))
        return artifacts

    def generate_report(
        self,
        project_id: str,
        *,
        dataset_id: str | None = None,
        title: str | None = None,
        subtitle: str | None = None,
        authors: list[str] | None = None,
        organization: str | None = None,
        template: str = "modern",
        completeness: str = "standard",
        render: bool = True,
        keep_qmd: bool = False,
        prisma: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate a report through the core biblioflow reporting API."""
        import biblioflow.reporting as reporting

        project = self.projects.get_project(project_id)
        selected_dataset_id = dataset_id or project.get("active_dataset_id")
        if not selected_dataset_id:
            raise ApiError(
                "dataset_required",
                "Load a dataset before generating a report.",
                400,
            )
        dataset = self.datasets.get_biblioflow_dataset(
            project_id, str(selected_dataset_id)
        )
        report_id = uuid4().hex
        output = self.projects.reports_dir(project_id) / f"{report_id}.pdf"
        report_project = reporting.ReportProject.from_records(
            dataset,
            title=title or str(project.get("name") or "biblioflow project report"),
            subtitle=subtitle,
            authors=authors or [],
            organization=organization,
            project_id=project_id,
            prisma=prisma,
            metadata={
                "web_project_id": project_id,
                "dataset_id": selected_dataset_id,
                "project_created_at": project.get("created_at"),
            },
        )
        result = reporting.generate_report(
            report_project,
            output=output,
            template=template,
            completeness=_completeness(completeness),
            render=render,
            keep_qmd=keep_qmd or not render,
            keep_context=True,
        )
        metadata = self._metadata(report_id, output)
        metadata.update(
            {
                "dataset_id": selected_dataset_id,
                "rendered": result.rendered,
                "qmd_path": str(result.qmd_path),
                "context_path": str(result.context_path),
                "assets_dir": str(result.assets_dir),
                "warnings": [warning.to_dict() for warning in result.warnings],
                "sections_rendered": result.sections_rendered,
                "sections_skipped": result.sections_skipped,
            }
        )
        return metadata

    def report_path(self, project_id: str, filename: str) -> Path:
        """Return a safe report artifact path."""
        self.projects.get_project(project_id)
        reports_dir = self.projects.reports_dir(project_id).resolve()
        path = (reports_dir / filename).resolve()
        if not path.is_file() or not path.is_relative_to(reports_dir):
            raise ApiError("report_not_found", "Report was not found.", 404)
        return Path(path)

    def _metadata(self, report_id: str, path: Path) -> dict[str, Any]:
        return {
            "report_id": report_id,
            "kind": "report",
            "format": "pdf",
            "filename": path.name,
            "path": str(path),
            "size": path.stat().st_size if path.exists() else 0,
            "created_at": utc_now(),
        }


def _completeness(value: str) -> Any:
    if value not in {"summary", "standard", "complete"}:
        raise ApiError(
            "unsupported_report_completeness",
            f"Unsupported report completeness: {value}.",
            400,
        )
    return value

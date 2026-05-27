"""Export orchestration service."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from biblioflow_web_backend.services.dataset_service import DatasetService
from biblioflow_web_backend.services.project_store import ProjectStore, utc_now


class ExportService:
    """Generate downloadable exports using biblioflow."""

    def __init__(self, projects: ProjectStore, datasets: DatasetService) -> None:
        self.projects = projects
        self.datasets = datasets

    def list_exports(self, project_id: str) -> list[dict[str, Any]]:
        """List export artifacts for a project."""
        self.projects.get_project(project_id)
        exports_dir = self.projects.exports_dir(project_id)
        artifacts = []
        for path in sorted(exports_dir.iterdir(), key=lambda item: item.name):
            if path.is_file():
                artifacts.append(
                    self._metadata(
                        path.stem,
                        path,
                        format=path.suffix.removeprefix(".") or "unknown",
                        kind="dataset",
                    )
                )
        return artifacts

    def export_dataset(
        self,
        project_id: str,
        dataset_id: str,
        *,
        format: str = "json",
    ) -> dict[str, Any]:
        """Export a dataset and return export metadata."""
        import biblioflow as bf

        dataset = self.datasets.get_biblioflow_dataset(project_id, dataset_id)
        export_id = uuid4().hex
        extension = "csv" if format == "csv" else "json"
        output = self.projects.exports_dir(project_id) / f"{export_id}.{extension}"
        bf.export(dataset, output, format=format)
        return self._metadata(export_id, output, format=format, kind="dataset")

    def _metadata(
        self, export_id: str, path: Path, *, format: str, kind: str
    ) -> dict[str, Any]:
        return {
            "export_id": export_id,
            "kind": kind,
            "format": format,
            "filename": path.name,
            "path": str(path),
            "size": path.stat().st_size,
            "created_at": utc_now(),
        }

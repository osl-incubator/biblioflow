"""Export service for notebook workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from biblioflow_nb.errors import BiblioFlowNotebookError
from biblioflow_nb.services.dataset_service import DatasetService
from biblioflow_nb.state import NotebookExport, NotebookSession


class ExportService:
    """Export datasets and cached results through biblioflow."""

    def __init__(self, session: NotebookSession, datasets: DatasetService) -> None:
        self.session = session
        self.datasets = datasets

    def export_dataset(self, path: str | Path, *, format: str | None = None) -> Path:
        """Export the current dataset."""
        import biblioflow as bf

        target = Path(path)
        bf.export(self.datasets.require_dataset(), target, format=format)
        self.session.add_export(
            NotebookExport(
                name=target.name,
                path=target,
                kind="dataset",
                format=format or target.suffix.lstrip(".") or "json",
            )
        )
        return target

    def export_object(
        self,
        obj: Any,
        path: str | Path,
        *,
        kind: str,
        format: str | None = None,
    ) -> Path:
        """Export a result object."""
        import biblioflow as bf

        if obj is None:
            raise BiblioFlowNotebookError("Nothing is available to export.")
        target = Path(path)
        bf.export(obj, target, format=format)
        self.session.add_export(
            NotebookExport(
                name=target.name,
                path=target,
                kind=kind,
                format=format or target.suffix.lstrip(".") or "json",
            )
        )
        return target

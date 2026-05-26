"""Analysis service for notebook panels."""

from __future__ import annotations

from typing import Any

from biblioflow_nb.services.dataset_service import DatasetService
from biblioflow_nb.state import NotebookSession


class AnalysisService:
    """Run analyses with biblioflow and cache results in the session."""

    def __init__(self, session: NotebookSession, datasets: DatasetService) -> None:
        self.session = session
        self.datasets = datasets

    def overview(self, *, top_n: int = 20) -> dict[str, Any]:
        """Run descriptive overview analysis."""
        import biblioflow as bf

        result = bf.analyze(self.datasets.require_dataset(), top_n=top_n)
        payload = result.to_dict()
        self.session.analysis_cache[f"overview:{top_n}"] = payload
        self.session.touch()
        return payload

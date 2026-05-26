"""Analysis orchestration service."""

from __future__ import annotations

from typing import Any

from biblioflow_web_backend.services.dataset_service import DatasetService


class AnalysisService:
    """Run biblioflow analyses for persisted datasets."""

    def __init__(self, datasets: DatasetService) -> None:
        self.datasets = datasets

    def overview(
        self,
        project_id: str,
        dataset_id: str,
        *,
        top_n: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return descriptive overview analysis."""
        import biblioflow as bf

        dataset = self.datasets.get_biblioflow_dataset(project_id, dataset_id)
        if filters:
            dataset = bf.filter_dataset(dataset, filters).dataset
        return bf.analyze(dataset, top_n=top_n).to_dict()

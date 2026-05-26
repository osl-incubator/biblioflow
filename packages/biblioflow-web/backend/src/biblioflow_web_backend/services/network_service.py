"""Network orchestration service."""

from __future__ import annotations

from typing import Any

from biblioflow_web_backend.services.dataset_service import DatasetService


class NetworkService:
    """Build network responses from biblioflow results."""

    def __init__(self, datasets: DatasetService) -> None:
        self.datasets = datasets

    def build(
        self,
        project_id: str,
        dataset_id: str,
        *,
        kind: str = "co_occurrence",
        unit: str = "keywords_all",
        normalize: str | None = None,
        min_occurrences: int = 1,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a bibliometric network."""
        import biblioflow as bf

        dataset = self.datasets.get_biblioflow_dataset(project_id, dataset_id)
        if filters:
            dataset = bf.filter_dataset(dataset, filters).dataset
        result = bf.network(
            dataset,
            kind=kind,
            unit=unit,
            normalize=normalize,
            min_occurrences=min_occurrences,
        )
        return result.to_dict()

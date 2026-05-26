"""Network service for notebook panels."""

from __future__ import annotations

from typing import Any

from biblioflow_nb.services.dataset_service import DatasetService
from biblioflow_nb.state import NotebookSession


class NetworkService:
    """Build networks with biblioflow."""

    def __init__(self, session: NotebookSession, datasets: DatasetService) -> None:
        self.session = session
        self.datasets = datasets

    def build(
        self,
        *,
        kind: str = "co_occurrence",
        unit: str = "keywords_all",
        normalize: str | None = None,
        min_occurrences: int = 1,
    ) -> Any:
        """Build and cache a bibliometric network."""
        import biblioflow as bf

        result = bf.network(
            self.datasets.require_dataset(),
            kind=kind,
            unit=unit,
            normalize=normalize,
            min_occurrences=min_occurrences,
        )
        key = f"{kind}:{unit}:{normalize}:{min_occurrences}"
        self.session.network_cache[key] = result
        self.session.touch()
        return result

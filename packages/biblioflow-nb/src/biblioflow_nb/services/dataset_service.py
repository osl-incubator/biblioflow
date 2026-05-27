"""Dataset service that delegates calculations to biblioflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from biblioflow_nb.errors import NoDatasetError
from biblioflow_nb.state import NotebookSession, NotebookUpload


class DatasetService:
    """Load, summarize, validate, and filter datasets."""

    def __init__(self, session: NotebookSession) -> None:
        self.session = session

    def load(
        self,
        source: str | Path | list[dict[str, Any]] | Any,
        *,
        name: str | None = None,
        provider: str = "auto",
        format: str = "auto",
    ) -> Any:
        """Load a source with biblioflow and store it in the session."""
        import biblioflow as bf

        if _is_dataset(source):
            dataset = source
        else:
            dataset = bf.load(source, provider=provider, format=format)
        self.session.set_dataset(dataset, name=name or _source_name(source))
        if isinstance(source, str | Path):
            path = Path(source)
            self.session.add_upload(
                NotebookUpload(
                    name=path.name,
                    path=path,
                    size=path.stat().st_size if path.exists() else None,
                )
            )
        return dataset

    def from_pubmed(
        self,
        *,
        query: str,
        limit: int = 100,
        email: str | None = None,
        api_key: str | None = None,
        tool: str = "biblioflow-nb",
        name: str | None = None,
    ) -> Any:
        """Search PubMed and store the result in the session."""
        import biblioflow as bf

        search_query = _required_query(query)
        dataset = bf.from_pubmed(
            query=search_query,
            limit=limit,
            tool=tool,
            email=_optional_string(email),
            api_key=_optional_string(api_key),
        )
        self.session.set_dataset(
            dataset,
            name=_remote_dataset_name("PubMed", search_query, name),
        )
        return dataset

    def from_pmc(
        self,
        *,
        query: str,
        limit: int = 100,
        email: str | None = None,
        api_key: str | None = None,
        tool: str = "biblioflow-nb",
        name: str | None = None,
    ) -> Any:
        """Search PubMed Central and store the result in the session."""
        import biblioflow as bf

        search_query = _required_query(query)
        dataset = bf.from_pmc(
            query=search_query,
            limit=limit,
            tool=tool,
            email=_optional_string(email),
            api_key=_optional_string(api_key),
        )
        self.session.set_dataset(
            dataset,
            name=_remote_dataset_name("PMC", search_query, name),
        )
        return dataset

    def require_dataset(self) -> Any:
        """Return the current dataset or raise a friendly error."""
        dataset = self.session.dataset
        if dataset is None:
            raise NoDatasetError("Load a dataset before running this action.")
        return dataset

    def summary(self) -> dict[str, Any]:
        """Return a summary for the current dataset."""
        import biblioflow as bf

        return bf.summarize_dataset(self.require_dataset()).to_dict()

    def validation(self) -> dict[str, Any]:
        """Return validation details for the active dataset."""
        dataset = self.require_dataset()
        return {
            "records": len(dataset),
            "warnings": (
                dataset.warning_dicts() if hasattr(dataset, "warning_dicts") else []
            ),
            "metadata": dict(getattr(dataset, "metadata", {})),
        }

    def records(self, *, limit: int = 10) -> list[dict[str, Any]]:
        """Return a limited record preview."""
        return list(self.require_dataset().to_records()[:limit])

    def filter_options(self) -> dict[str, Any]:
        """Return available filter values for the active dataset."""
        import biblioflow as bf

        base = self.session.active_dataset
        if base is None:
            raise NoDatasetError("Load a dataset before configuring filters.")
        return bf.available_filter_values(base).to_dict()

    def apply_filters(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Apply filters and store the filtered dataset in the session."""
        import biblioflow as bf

        base = self.session.active_dataset
        if base is None:
            raise NoDatasetError("Load a dataset before applying filters.")
        result = bf.filter_dataset(base, spec)
        self.session.active_filters = result.spec
        self.session.filtered_dataset = result.dataset
        self.session.touch()
        return result.to_dict()

    def reset_filters(self) -> None:
        """Clear active filters."""
        self.session.active_filters = None
        self.session.filtered_dataset = None
        self.session.touch()


def _is_dataset(value: Any) -> bool:
    return hasattr(value, "to_records") and hasattr(value, "metadata")


def _source_name(source: Any) -> str | None:
    if isinstance(source, str | Path):
        return Path(source).name
    if _is_dataset(source):
        return "dataset"
    return None


def _required_query(query: str) -> str:
    stripped = query.strip()
    if not stripped:
        raise ValueError("Provide a PubMed or PubMed Central query.")
    return stripped


def _optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _remote_dataset_name(label: str, query: str, name: str | None) -> str:
    if name and name.strip():
        return name.strip()
    return f"{label}: {query}"

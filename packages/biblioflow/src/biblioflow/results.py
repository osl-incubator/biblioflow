"""Reusable JSON-serializable result helpers for biblioflow."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from biblioflow.core.dataset import BibliographicDataset


@dataclass(frozen=True)
class DatasetSummary:
    """High-level summary of a bibliographic dataset."""

    documents: int
    sources: int
    authors: int
    keywords: int
    timespan_start: int | None
    timespan_end: int | None
    documents_with_doi: int
    warnings: list[dict[str, object]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "documents": self.documents,
            "sources": self.sources,
            "authors": self.authors,
            "keywords": self.keywords,
            "timespan_start": self.timespan_start,
            "timespan_end": self.timespan_end,
            "documents_with_doi": self.documents_with_doi,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ImportSummary:
    """Summary of an import/load operation."""

    records: int
    format: str | None
    provider: str | None
    warnings: list[dict[str, object]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "records": self.records,
            "format": self.format,
            "provider": self.provider,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


def _list_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text and text.lower() != "nan" else []


def summarize_dataset(dataset: BibliographicDataset) -> DatasetSummary:
    """Build a reusable high-level dataset summary."""
    rows = dataset.to_records()
    years = [
        int(row["publication_year"]) for row in rows if row.get("publication_year")
    ]
    sources = Counter(
        str(row["source_title"]) for row in rows if row.get("source_title")
    )
    authors = Counter(
        author for row in rows for author in _list_values(row.get("authors"))
    )
    keywords = Counter(
        keyword for row in rows for keyword in _list_values(row.get("keywords_all"))
    )
    return DatasetSummary(
        documents=len(rows),
        sources=len(sources),
        authors=len(authors),
        keywords=len(keywords),
        timespan_start=min(years) if years else None,
        timespan_end=max(years) if years else None,
        documents_with_doi=sum(1 for row in rows if row.get("doi")),
        warnings=dataset.warning_dicts(),
        metadata=dict(dataset.metadata),
    )


def summarize_import(dataset: BibliographicDataset) -> ImportSummary:
    """Build a reusable summary for a loaded dataset."""
    return ImportSummary(
        records=len(dataset),
        format=dataset.metadata.get("format"),
        provider=dataset.metadata.get("provider"),
        warnings=dataset.warning_dicts(),
        metadata=dict(dataset.metadata),
    )

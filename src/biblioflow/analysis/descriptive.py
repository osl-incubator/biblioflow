"""Descriptive bibliometric analysis."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.core.frames import make_record_frame
from biblioflow.load.dispatcher import load


@dataclass
class DescriptiveSummary:
    """Descriptive bibliometric analysis result."""

    main_information: dict[str, Any]
    annual_production: Any
    top_authors: Any
    top_sources: Any
    top_keywords: Any
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return the summary as dictionaries and record lists."""
        return {
            "main_information": self.main_information,
            "annual_production": self.annual_production.to_dict(orient="records"),
            "top_authors": self.top_authors.to_dict(orient="records"),
            "top_sources": self.top_sources.to_dict(orient="records"),
            "top_keywords": self.top_keywords.to_dict(orient="records"),
            "metadata": self.metadata,
        }


def _counter_frame(counter: Counter[str], *, key: str, value: str, limit: int) -> Any:
    rows = [{key: name, value: count} for name, count in counter.most_common(limit)]
    return make_record_frame(rows, [key, value])


def analyze(
    records: BibliographicDataset | Any, *, top_n: int = 20
) -> DescriptiveSummary:
    """Compute a descriptive bibliometric summary."""
    dataset = (
        load(records) if not isinstance(records, BibliographicDataset) else records
    )
    rows = dataset.to_records()

    years = [
        int(row["publication_year"]) for row in rows if row.get("publication_year")
    ]
    authors_counter: Counter[str] = Counter()
    keyword_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter(
        str(row["source_title"]) for row in rows if row.get("source_title")
    )

    for row in rows:
        authors = row.get("authors")
        if isinstance(authors, list):
            authors_counter.update(author for author in authors if author)
        keywords = row.get("keywords_all")
        if isinstance(keywords, list):
            keyword_counter.update(keyword for keyword in keywords if keyword)

    annual_counter = Counter(years)
    annual_rows = [
        {"publication_year": year, "documents": annual_counter[year]}
        for year in sorted(annual_counter)
    ]
    annual_production = make_record_frame(
        annual_rows, ["publication_year", "documents"]
    )

    author_counts_per_doc = [
        len(row["authors"]) if isinstance(row.get("authors"), list) else 0
        for row in rows
    ]
    documents = len(rows)
    main_information = {
        "documents": documents,
        "sources": len(source_counter),
        "authors": len(authors_counter),
        "keywords": len(keyword_counter),
        "timespan_start": min(years) if years else None,
        "timespan_end": max(years) if years else None,
        "documents_with_doi": sum(1 for row in rows if row.get("doi")),
        "average_authors_per_document": (
            sum(author_counts_per_doc) / documents if documents else 0.0
        ),
    }
    return DescriptiveSummary(
        main_information=main_information,
        annual_production=annual_production,
        top_authors=_counter_frame(
            authors_counter, key="author", value="documents", limit=top_n
        ),
        top_sources=_counter_frame(
            source_counter, key="source_title", value="documents", limit=top_n
        ),
        top_keywords=_counter_frame(
            keyword_counter, key="keyword", value="documents", limit=top_n
        ),
        metadata={"top_n": top_n},
    )

"""
title: Reusable dataset filtering helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.results import summarize_dataset


@dataclass(frozen=True)
class DatasetFilterSpec:
    """
    title: Serializable filter specification for bibliographic datasets.
    attributes:
      year_min:
        type: int | None
        description: Year min attribute.
      year_max:
        type: int | None
        description: Year max attribute.
      document_types:
        type: list[str] | None
        description: Document types attribute.
      sources:
        type: list[str] | None
        description: Sources attribute.
      authors:
        type: list[str] | None
        description: Authors attribute.
      affiliations:
        type: list[str] | None
        description: Affiliations attribute.
      countries:
        type: list[str] | None
        description: Countries attribute.
      keywords:
        type: list[str] | None
        description: Keywords attribute.
      include_missing_year:
        type: bool
        description: Include missing year attribute.
      min_global_citations:
        type: int | None
        description: Min global citations attribute.
      custom_field_filters:
        type: dict[str, list[Any]]
        description: Custom field filters attribute.
    """

    year_min: int | None = None
    year_max: int | None = None
    document_types: list[str] | None = None
    sources: list[str] | None = None
    authors: list[str] | None = None
    affiliations: list[str] | None = None
    countries: list[str] | None = None
    keywords: list[str] | None = None
    include_missing_year: bool = True
    min_global_citations: int | None = None
    custom_field_filters: dict[str, list[Any]] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | None) -> DatasetFilterSpec:
        """
        title: Create a filter spec from a plain dictionary.
        parameters:
          payload:
            type: dict[str, Any] | None
            description: Payload value.
        returns:
          type: DatasetFilterSpec
        """
        if not payload:
            return cls()
        return cls(
            year_min=payload.get("year_min"),
            year_max=payload.get("year_max"),
            document_types=_optional_str_list(payload.get("document_types")),
            sources=_optional_str_list(payload.get("sources")),
            authors=_optional_str_list(payload.get("authors")),
            affiliations=_optional_str_list(payload.get("affiliations")),
            countries=_optional_str_list(payload.get("countries")),
            keywords=_optional_str_list(payload.get("keywords")),
            include_missing_year=bool(payload.get("include_missing_year", True)),
            min_global_citations=payload.get("min_global_citations"),
            custom_field_filters=dict(payload.get("custom_field_filters") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        title: Return a JSON-serializable representation.
        returns:
          type: dict[str, Any]
        """
        return {
            "year_min": self.year_min,
            "year_max": self.year_max,
            "document_types": self.document_types,
            "sources": self.sources,
            "authors": self.authors,
            "affiliations": self.affiliations,
            "countries": self.countries,
            "keywords": self.keywords,
            "include_missing_year": self.include_missing_year,
            "min_global_citations": self.min_global_citations,
            "custom_field_filters": self.custom_field_filters,
        }


@dataclass(frozen=True)
class FilteredDatasetResult:
    """
    title: Result returned by :func:`filter_dataset`.
    attributes:
      dataset:
        type: BibliographicDataset
        description: Dataset attribute.
      input_records:
        type: int
        description: Input records attribute.
      output_records:
        type: int
        description: Output records attribute.
      spec:
        type: DatasetFilterSpec
        description: Spec attribute.
    """

    dataset: BibliographicDataset
    input_records: int
    output_records: int
    spec: DatasetFilterSpec

    def to_dict(self) -> dict[str, Any]:
        """
        title: Return a JSON-serializable summary of the filtering operation.
        returns:
          type: dict[str, Any]
        """
        return {
            "input_records": self.input_records,
            "output_records": self.output_records,
            "spec": self.spec.to_dict(),
            "summary": summarize_dataset(self.dataset).to_dict(),
        }


@dataclass(frozen=True)
class FilterOptions:
    """
    title: Available values that can be used to build dataset filters.
    attributes:
      years:
        type: list[int]
        description: Years attribute.
      document_types:
        type: list[str]
        description: Document types attribute.
      sources:
        type: list[str]
        description: Sources attribute.
      authors:
        type: list[str]
        description: Authors attribute.
      affiliations:
        type: list[str]
        description: Affiliations attribute.
      countries:
        type: list[str]
        description: Countries attribute.
      keywords:
        type: list[str]
        description: Keywords attribute.
    """

    years: list[int]
    document_types: list[str]
    sources: list[str]
    authors: list[str]
    affiliations: list[str]
    countries: list[str]
    keywords: list[str]

    def to_dict(self) -> dict[str, Any]:
        """
        title: Return a JSON-serializable representation.
        returns:
          type: dict[str, Any]
        """
        return {
            "years": self.years,
            "document_types": self.document_types,
            "sources": self.sources,
            "authors": self.authors,
            "affiliations": self.affiliations,
            "countries": self.countries,
            "keywords": self.keywords,
        }


def _optional_str_list(value: Any) -> list[str] | None:
    """
    title: Implement the optional str list helper.
    parameters:
      value:
        type: Any
        description: Value value.
    returns:
      type: list[str] | None
    """
    if value is None:
        return None
    if isinstance(value, list):
        values = [str(item) for item in value if str(item).strip()]
    else:
        values = [str(value)] if str(value).strip() else []
    return values or None


def _values(value: Any) -> list[str]:
    """
    title: Implement the values helper.
    parameters:
      value:
        type: Any
        description: Value value.
    returns:
      type: list[str]
    """
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text and text.lower() != "nan" else []


def _matches_any(row_value: Any, expected: list[str] | None) -> bool:
    """
    title: Implement the matches any helper.
    parameters:
      row_value:
        type: Any
        description: Row value value.
      expected:
        type: list[str] | None
        description: Expected value.
    returns:
      type: bool
    """
    if not expected:
        return True
    actual = {value.casefold() for value in _values(row_value)}
    wanted = {value.casefold() for value in expected}
    return bool(actual.intersection(wanted))


def _matches_scalar(row_value: Any, expected: list[str] | None) -> bool:
    """
    title: Implement the matches scalar helper.
    parameters:
      row_value:
        type: Any
        description: Row value value.
      expected:
        type: list[str] | None
        description: Expected value.
    returns:
      type: bool
    """
    if not expected:
        return True
    if row_value is None:
        return False
    return str(row_value).casefold() in {value.casefold() for value in expected}


def _matches_year(row: dict[str, Any], spec: DatasetFilterSpec) -> bool:
    """
    title: Implement the matches year helper.
    parameters:
      row:
        type: dict[str, Any]
        description: Row value.
      spec:
        type: DatasetFilterSpec
        description: Spec value.
    returns:
      type: bool
    """
    if spec.year_min is None and spec.year_max is None:
        return True
    raw_year = row.get("publication_year")
    if raw_year in {None, ""}:
        return spec.include_missing_year
    year = int(str(raw_year))
    if spec.year_min is not None and year < spec.year_min:
        return False
    return not (spec.year_max is not None and year > spec.year_max)


def _matches_custom_fields(row: dict[str, Any], spec: DatasetFilterSpec) -> bool:
    """
    title: Implement the matches custom fields helper.
    parameters:
      row:
        type: dict[str, Any]
        description: Row value.
      spec:
        type: DatasetFilterSpec
        description: Spec value.
    returns:
      type: bool
    """
    for field_name, allowed_values in spec.custom_field_filters.items():
        if not allowed_values:
            continue
        if not _matches_any(
            row.get(field_name), [str(value) for value in allowed_values]
        ):
            return False
    return True


def _matches(row: dict[str, Any], spec: DatasetFilterSpec) -> bool:
    """
    title: Implement the matches helper.
    parameters:
      row:
        type: dict[str, Any]
        description: Row value.
      spec:
        type: DatasetFilterSpec
        description: Spec value.
    returns:
      type: bool
    """
    if not _matches_year(row, spec):
        return False
    if not _matches_scalar(row.get("document_type"), spec.document_types):
        return False
    if not _matches_scalar(row.get("source_title"), spec.sources):
        return False
    if not _matches_any(row.get("authors"), spec.authors):
        return False
    if not _matches_any(row.get("affiliations"), spec.affiliations):
        return False
    if not _matches_any(row.get("countries"), spec.countries):
        return False
    if not _matches_any(row.get("keywords_all"), spec.keywords):
        return False
    if spec.min_global_citations is not None:
        citations = row.get("cited_by_count") or 0
        if int(citations) < spec.min_global_citations:
            return False
    return _matches_custom_fields(row, spec)


def filter_dataset(
    dataset: BibliographicDataset, spec: DatasetFilterSpec | dict[str, Any] | None
) -> FilteredDatasetResult:
    """
    title: Filter a dataset using a reusable serializable filter specification.
    parameters:
      dataset:
        type: BibliographicDataset
        description: Dataset value.
      spec:
        type: DatasetFilterSpec | dict[str, Any] | None
        description: Spec value.
    returns:
      type: FilteredDatasetResult
    """
    if isinstance(spec, DatasetFilterSpec):
        filter_spec = spec
    else:
        filter_spec = DatasetFilterSpec.from_mapping(spec)
    rows = dataset.to_records()
    filtered = [row for row in rows if _matches(row, filter_spec)]
    metadata = {
        **dict(dataset.metadata),
        "filtered_from_records": len(rows),
        "records": len(filtered),
        "filter_spec": filter_spec.to_dict(),
    }
    return FilteredDatasetResult(
        dataset=BibliographicDataset.from_records(
            filtered,
            raw=[],
            metadata=metadata,
            warnings=dataset.warnings,
            errors=dataset.errors,
        ),
        input_records=len(rows),
        output_records=len(filtered),
        spec=filter_spec,
    )


def available_filter_values(dataset: BibliographicDataset) -> FilterOptions:
    """
    title: Return available values for common dataset filters.
    parameters:
      dataset:
        type: BibliographicDataset
        description: Dataset value.
    returns:
      type: FilterOptions
    """
    rows = dataset.to_records()
    years = sorted(
        {int(row["publication_year"]) for row in rows if row.get("publication_year")}
    )
    return FilterOptions(
        years=years,
        document_types=sorted(
            {str(row["document_type"]) for row in rows if row.get("document_type")}
        ),
        sources=sorted(
            {str(row["source_title"]) for row in rows if row.get("source_title")}
        ),
        authors=sorted(
            {value for row in rows for value in _values(row.get("authors"))}
        ),
        affiliations=sorted(
            {value for row in rows for value in _values(row.get("affiliations"))}
        ),
        countries=sorted(
            {value for row in rows for value in _values(row.get("countries"))}
        ),
        keywords=sorted(
            {value for row in rows for value in _values(row.get("keywords_all"))}
        ),
    )


def summarize_filters(
    dataset: BibliographicDataset, spec: DatasetFilterSpec | dict[str, Any] | None
) -> dict[str, Any]:
    """
    title: Return a summary for applying a filter spec to a dataset.
    parameters:
      dataset:
        type: BibliographicDataset
        description: Dataset value.
      spec:
        type: DatasetFilterSpec | dict[str, Any] | None
        description: Spec value.
    returns:
      type: dict[str, Any]
    """
    return filter_dataset(dataset, spec).to_dict()

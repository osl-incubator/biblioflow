"""
title: Deduplication and metadata enrichment helpers.
"""

from __future__ import annotations

from typing import Any

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.core.warnings import LoadWarning
from biblioflow.load.dispatcher import load
from biblioflow.normalize.records import normalize_doi


def _key(row: dict[str, Any], by: str) -> str:
    """
    title: Implement the key helper.
    parameters:
      row:
        type: dict[str, Any]
        description: Row value.
      by:
        type: str
        description: By value.
    returns:
      type: str
    """
    if by == "doi":
        return normalize_doi(row.get("doi")) or ""
    if by == "title":
        return str(row.get("title") or "").strip().casefold()
    if by == "source_id":
        return str(row.get("source_id") or "").strip().casefold()
    if by == "doi_or_title":
        return _key(row, "doi") or _key(row, "title")
    return str(row.get(by) or "").strip().casefold()


def deduplicate(
    records: BibliographicDataset | Any,
    *,
    by: str = "doi_or_title",
    keep: str = "first",
) -> BibliographicDataset:
    """
    title: Remove duplicate records from a dataset.
    summary: |-
      Parameters
      ----------
      by:
      Field to use as the duplicate key. `doi_or_title` first tries DOI and
      falls back to normalized title.
      keep:
      Currently only `first` is supported.
    parameters:
      records:
        type: BibliographicDataset | Any
        description: Records value.
      by:
        type: str
        description: By value.
      keep:
        type: str
        description: Keep value.
    returns:
      type: BibliographicDataset
    """
    if keep != "first":
        msg = "Only keep='first' is currently supported."
        raise ValueError(msg)
    dataset = (
        load(records) if not isinstance(records, BibliographicDataset) else records
    )
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    duplicates = 0
    for row in dataset.to_records():
        marker = _key(row, by)
        if marker and marker in seen:
            duplicates += 1
            continue
        if marker:
            seen.add(marker)
        unique.append(row)
    warnings = list(dataset.warnings)
    if duplicates:
        warnings.append(
            LoadWarning(
                code="duplicates_removed",
                count=duplicates,
                severity="info",
                message="Duplicate records were removed.",
                field=by,
            )
        )
    metadata = {
        **dataset.metadata,
        "deduplicated_by": by,
        "duplicates_removed": duplicates,
    }
    return BibliographicDataset.from_records(
        unique,
        raw=dataset.raw,
        metadata=metadata,
        warnings=warnings,
        errors=dataset.errors,
    )


def enrich(
    records: BibliographicDataset | Any,
    metadata: dict[str, dict[str, Any]] | list[dict[str, Any]],
    *,
    by: str = "doi",
) -> BibliographicDataset:
    """
    title: >-
      Merge local metadata into records by DOI, title, source_id, or another
      field.
    summary: |-
      This is an offline enrichment helper. Network-backed
      Crossref/OpenAlex
      enrichment can be layered on top later without changing the merge
      semantics.
    parameters:
      records:
        type: BibliographicDataset | Any
        description: Records value.
      metadata:
        type: dict[str, dict[str, Any]] | list[dict[str, Any]]
        description: Metadata value.
      by:
        type: str
        description: By value.
    returns:
      type: BibliographicDataset
    """
    dataset = (
        load(records) if not isinstance(records, BibliographicDataset) else records
    )
    if isinstance(metadata, list):
        lookup = {_key(item, by): item for item in metadata if _key(item, by)}
    else:
        lookup = {str(key).casefold(): value for key, value in metadata.items()}
    enriched: list[dict[str, Any]] = []
    hits = 0
    for row in dataset.to_records():
        marker = _key(row, by)
        extra = lookup.get(marker) if marker else None
        if extra:
            hits += 1
            row = {
                **row,
                **{key: value for key, value in extra.items() if value is not None},
            }
        enriched.append(row)
    return BibliographicDataset.from_records(
        enriched,
        raw=dataset.raw,
        metadata={**dataset.metadata, "enriched_by": by, "enrichment_hits": hits},
        warnings=dataset.warnings,
        errors=dataset.errors,
    )

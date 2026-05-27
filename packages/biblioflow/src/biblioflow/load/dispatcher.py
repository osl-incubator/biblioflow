"""
title: Main loading dispatcher.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.exceptions import AmbiguousSourceError, UnsupportedFormatError
from biblioflow.io import (
    read_bibtex_records,
    read_csv_records,
    read_json_records,
    read_jsonl_records,
    read_nbib_records,
    read_ris_records,
    read_wos_records,
    read_xml_records,
    read_yaml_records,
)
from biblioflow.load.infer import (
    infer_format,
    infer_provider,
    normalize_format_name,
    normalize_provider_name,
)
from biblioflow.normalize.records import normalize_record
from biblioflow.providers import adapt_record
from biblioflow.validation import validate_records


def _read_records(
    path: Path, fmt: str, provider: str = "generic"
) -> list[dict[str, Any]]:
    """
    title: Implement the read records helper.
    parameters:
      path:
        type: Path
        description: Path value.
      fmt:
        type: str
        description: Fmt value.
      provider:
        type: str
        description: Provider/source name.
    returns:
      type: list[dict[str, Any]]
    """
    if fmt == "json":
        return read_json_records(path)
    if fmt == "jsonl":
        return read_jsonl_records(path)
    if fmt == "csv":
        return read_csv_records(path, delimiter=",")
    if fmt == "tsv":
        return read_csv_records(path, delimiter="\t")
    if fmt == "ris":
        return read_ris_records(path)
    if fmt == "bibtex":
        return read_bibtex_records(path)
    if fmt == "plain_text" and provider == "web_of_science":
        return read_wos_records(path)
    if fmt == "nbib":
        return read_nbib_records(path)
    if fmt == "xml":
        return read_xml_records(path)
    if fmt == "yaml":
        return read_yaml_records(path)
    msg = f"Unsupported input format: {fmt!r}"
    raise UnsupportedFormatError(msg)


def _normalize_raw_records(
    records: list[dict[str, Any]],
    *,
    provider: str,
    source_format: str,
    keep_raw: bool,
) -> list[dict[str, Any]]:
    """
    title: Normalize raw records for one provider/source format.
    parameters:
      records:
        type: list[dict[str, Any]]
        description: Raw records.
      provider:
        type: str
        description: Provider/source name.
      source_format:
        type: str
        description: Source format.
      keep_raw:
        type: bool
        description: Whether raw payloads should be preserved.
    returns:
      type: list[dict[str, Any]]
    """
    normalized: list[dict[str, Any]] = []
    for record in records:
        row = normalize_record(
            adapt_record(provider, record),
            provider=provider,
            source_format=source_format,
        )
        if not keep_raw:
            row["raw"] = None
        normalized.append(row)
    return normalized


def load(
    path_or_buffer: str | Path | list[dict[str, Any]] | BibliographicDataset,
    *,
    source: str | None = None,
    provider: str = "auto",
    format: str = "auto",
    keep_raw: bool = True,
    strict: bool = False,
    as_dataframe: bool = False,
    schema: str = "canonical",
    **_: Any,
) -> BibliographicDataset | Any:
    """
    title: Load bibliographic records into a :class:`BibliographicDataset`.
    summary: |-
      Supports local bibliographic files and in-memory record lists. Use
      from_openalex, from_crossref, or from_scopus for API-backed imports.
    parameters:
      path_or_buffer:
        type: str | Path | list[dict[str, Any]] | BibliographicDataset
        description: File path, records, or dataset value.
      source:
        type: str | None
        description: Provider/source alias, such as scopus or wos.
      provider:
        type: str
        description: Provider value.
      format:
        type: str
        description: Format value.
      keep_raw:
        type: bool
        description: Keep raw value.
      strict:
        type: bool
        description: Strict value.
      as_dataframe:
        type: bool
        description: As dataframe value.
      schema:
        type: str
        description: Schema value.
      _:
        type: Any
        description: Additional keyword arguments.
        variadic: keyword
    returns:
      type: BibliographicDataset | Any
    """
    if source is not None:
        provider = source
    provider = normalize_provider_name(provider)
    format = normalize_format_name(format)

    if isinstance(path_or_buffer, BibliographicDataset):
        return (
            path_or_buffer.to_dataframe(schema=schema)
            if as_dataframe
            else path_or_buffer
        )

    if isinstance(path_or_buffer, list):
        raw = [dict(record) for record in path_or_buffer]
        fmt = "records"
        prov = "generic" if provider == "auto" else provider
        normalized = _normalize_raw_records(
            raw,
            provider=prov,
            source_format=fmt,
            keep_raw=keep_raw,
        )
        warnings = validate_records(normalized)
        if strict and any(w.severity == "warning" for w in warnings):
            msg = "; ".join(w.message or w.code for w in warnings)
            raise ValueError(msg)
        dataset = BibliographicDataset.from_records(
            normalized,
            raw=raw if keep_raw else [],
            metadata={"source": "memory", "format": fmt, "provider": prov},
            warnings=warnings,
        )
        return dataset.to_dataframe(schema=schema) if as_dataframe else dataset

    path = Path(path_or_buffer)
    if not path.exists():
        msg = (
            f"Could not detect the source or format of {str(path_or_buffer)!r}.\n\n"
            "For files, pass a local path and optionally source=... and format=...\n"
            "Examples:\n"
            '  bf.load("records.txt", source="wos")\n'
            '  bf.load("records.csv", source="scopus")\n\n'
            "For APIs, use bf.from_openalex(...), bf.from_crossref(...), "
            "bf.from_scopus(...), bf.from_pubmed(...), or "
            "bf.from_pubmed_central(...)."
        )
        raise AmbiguousSourceError(msg)

    fmt = infer_format(path) if format == "auto" else format
    if fmt == "unknown":
        msg = f"Could not infer input format for {path}. Pass format= explicitly."
        raise UnsupportedFormatError(msg)
    prov = infer_provider(path, format=fmt) if provider == "auto" else provider
    prov = normalize_provider_name(prov)
    raw = _read_records(path, fmt, prov)
    normalized = _normalize_raw_records(
        raw,
        provider=prov,
        source_format=fmt,
        keep_raw=keep_raw,
    )
    warnings = validate_records(normalized)
    if strict and any(w.severity == "warning" for w in warnings):
        msg = "; ".join(w.message or w.code for w in warnings)
        raise ValueError(msg)
    dataset = BibliographicDataset.from_records(
        normalized,
        raw=raw if keep_raw else [],
        metadata={
            "source": str(path),
            "format": fmt,
            "provider": prov,
            "raw_records": len(raw),
        },
        warnings=warnings,
    )
    return dataset.to_dataframe(schema=schema) if as_dataframe else dataset

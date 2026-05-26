"""Main loading dispatcher."""

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
    read_yaml_records,
)
from biblioflow.load.infer import infer_format, infer_provider
from biblioflow.normalize import normalize_record
from biblioflow.validation import validate_records


def _read_records(path: Path, fmt: str) -> list[dict[str, Any]]:
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
    if fmt == "nbib":
        return read_nbib_records(path)
    if fmt == "yaml":
        return read_yaml_records(path)
    msg = f"Unsupported input format: {fmt!r}"
    raise UnsupportedFormatError(msg)


def load(
    source: str | Path | list[dict[str, Any]] | BibliographicDataset,
    *,
    provider: str = "auto",
    format: str = "auto",
    keep_raw: bool = True,
    strict: bool = False,
    as_dataframe: bool = False,
    schema: str = "canonical",
    **_: Any,
) -> BibliographicDataset | Any:
    """Load bibliographic records into a :class:`BibliographicDataset`.

    The current implementation supports local files and in-memory record lists.
    API query connectors are intentionally not implemented yet; pass a file path
    or a list of dictionaries for now.
    """
    if isinstance(source, BibliographicDataset):
        return source.to_dataframe(schema=schema) if as_dataframe else source

    if isinstance(source, list):
        raw = [dict(record) for record in source]
        fmt = "records"
        prov = "generic" if provider == "auto" else provider
        normalized = [
            normalize_record(record, provider=prov, source_format=fmt) for record in raw
        ]
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

    path = Path(source)
    if not path.exists():
        msg = (
            f"Source {str(source)!r} is not a local file. API query connectors "
            "are planned but not implemented in this scaffold."
        )
        raise AmbiguousSourceError(msg)

    fmt = infer_format(path) if format == "auto" else format
    if fmt == "unknown":
        msg = f"Could not infer input format for {path}. Pass format= explicitly."
        raise UnsupportedFormatError(msg)
    prov = infer_provider(path, format=fmt) if provider == "auto" else provider
    raw = _read_records(path, fmt)
    normalized = [
        normalize_record(record, provider=prov, source_format=fmt) for record in raw
    ]
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

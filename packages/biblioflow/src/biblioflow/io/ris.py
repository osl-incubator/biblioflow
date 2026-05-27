"""
title: Minimal RIS reader.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

_TAG_MAP = {
    "TY": "document_type",
    "AU": "authors",
    "A1": "authors",
    "TI": "title",
    "T1": "title",
    "AB": "abstract",
    "N2": "abstract",
    "PY": "publication_year",
    "Y1": "publication_year",
    "JO": "source_title",
    "JF": "source_title",
    "T2": "source_title",
    "DO": "doi",
    "DI": "doi",
    "UR": "url",
    "KW": "keywords_author",
    "SN": "issn",
    "VL": "volume",
    "IS": "issue",
    "SP": "start_page",
    "EP": "end_page",
    "PB": "publisher",
}

_MULTI_FIELDS = {"authors", "keywords_author", "references"}


def _append(record: dict[str, Any], key: str, value: str) -> None:
    """
    title: Implement the append helper.
    parameters:
      record:
        type: dict[str, Any]
        description: Record value.
      key:
        type: str
        description: Key value.
      value:
        type: str
        description: Value value.
    """
    if key in _MULTI_FIELDS:
        record.setdefault(key, []).append(value)
    elif record.get(key):
        record[key] = f"{record[key]} {value}".strip()
    else:
        record[key] = value


def read_ris_records(path: str | Path) -> list[dict[str, Any]]:
    """
    title: Read RIS records using a small pure-Python parser.
    parameters:
      path:
        type: str | Path
        description: Path value.
    returns:
      type: list[dict[str, Any]]
    """
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = defaultdict(list)
    last_key: str | None = None

    for raw_line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        if not raw_line.strip():
            continue
        if len(raw_line) >= 5 and raw_line[2:5] == "  -":
            tag = raw_line[:2]
            value = raw_line[5:].strip()
            if tag == "ER":
                if current:
                    record = dict(current)
                    record["raw"] = dict(current)
                    records.append(record)
                current = defaultdict(list)
                last_key = None
                continue
            key = _TAG_MAP.get(tag, tag.lower())
            _append(current, key, value)
            last_key = key
        elif last_key:
            continuation = raw_line.strip()
            if continuation:
                _append(current, last_key, continuation)
    if current:
        record = dict(current)
        record["raw"] = dict(current)
        records.append(record)
    return records

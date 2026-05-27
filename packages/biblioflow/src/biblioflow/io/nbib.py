"""
title: PubMed NBIB reader.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

_TAG_MAP = {
    "PMCID": "pmcid",
    "PMC": "pmcid",
    "PMID": "source_id",
    "TI": "title",
    "AB": "abstract",
    "AU": "authors",
    "FAU": "authors",
    "JT": "source_title",
    "TA": "journal_abbrev",
    "DP": "publication_year",
    "LID": "doi",
    "AID": "doi",
    "MH": "keywords_index",
    "OT": "keywords_author",
    "PT": "document_type",
    "LA": "language",
    "PG": "pages",
    "VI": "volume",
    "IP": "issue",
    "JID": "nlm_journal_id",
    "IS": "issn",
    "AD": "affiliations",
    "GR": "grants",
    "SI": "secondary_source_ids",
}

_MULTI_FIELDS = {
    "authors",
    "keywords_author",
    "keywords_index",
    "document_type",
    "affiliations",
    "grants",
    "secondary_source_ids",
}


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
    if key == "doi":
        lower = value.lower()
        if "[pmcid]" in lower:
            record["pmcid"] = re.sub(r"\s*\[pmcid\]\s*$", "", value, flags=re.I)
            return
        if " [doi]" in lower:
            value = re.sub(r"\s*\[doi\]\s*$", "", value, flags=re.I).strip()
        elif "[doi]" not in lower and record.get("doi"):
            return
    if key == "issn" and "electronic" in value.casefold():
        key = "eissn"
    if key in {"issn", "eissn"}:
        value = re.sub(r"\s*\([^)]*\)\s*$", "", value).strip()
    if key in _MULTI_FIELDS:
        record.setdefault(key, []).append(value)
    elif record.get(key):
        record[key] = f"{record[key]} {value}".strip()
    else:
        record[key] = value


def read_nbib_records(path: str | Path) -> list[dict[str, Any]]:
    """
    title: Read PubMed NBIB records.
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
            if current:
                records.append(dict(current))
                current = defaultdict(list)
                last_key = None
            continue
        if len(raw_line) >= 6 and raw_line[4:6] == "- ":
            tag = raw_line[:4].strip()
            value = raw_line[6:].strip()
            key = _TAG_MAP.get(tag, tag.lower())
            _append(current, key, value)
            last_key = key
        elif last_key:
            _append(current, last_key, raw_line.strip())
    if current:
        records.append(dict(current))
    return records

"""
title: Web of Science plain-text reader.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_REPEATED_TAGS = {"AU", "AF", "C1", "CR", "EM"}


def _append_tag(record: dict[str, Any], tag: str, value: str) -> None:
    """
    title: Append a Web of Science tag value.
    parameters:
      record:
        type: dict[str, Any]
        description: Raw record.
      tag:
        type: str
        description: WoS tag.
      value:
        type: str
        description: Tag value.
    """
    if tag in _REPEATED_TAGS:
        record.setdefault(tag, []).append(value)
    elif tag in record:
        record[tag] = f"{record[tag]} {value}".strip()
    else:
        record[tag] = value


def _append_continuation(record: dict[str, Any], tag: str, value: str) -> None:
    """
    title: Append continuation text to the previous WoS tag.
    parameters:
      record:
        type: dict[str, Any]
        description: Raw record.
      tag:
        type: str
        description: Previous WoS tag.
      value:
        type: str
        description: Continuation value.
    """
    if tag in _REPEATED_TAGS and isinstance(record.get(tag), list) and record[tag]:
        record[tag][-1] = f"{record[tag][-1]} {value}".strip()
    elif tag in record:
        record[tag] = f"{record[tag]} {value}".strip()


def parse_wos_records(text: str) -> list[dict[str, Any]]:
    """
    title: Parse raw Web of Science plain-text records.
    parameters:
      text:
        type: str
        description: WoS plain-text content.
    returns:
      type: list[dict[str, Any]]
    """
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    last_tag: str | None = None
    tag_pattern = re.compile(r"^([A-Z0-9]{2})\s+(.*)$")
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line == "ER":
            if current:
                records.append(current)
            current = {}
            last_tag = None
            continue
        if line == "EF":
            break
        match = tag_pattern.match(line)
        if match:
            tag, value = match.groups()
            _append_tag(current, tag, value.strip())
            last_tag = tag
            continue
        if last_tag and line.startswith(" "):
            _append_continuation(current, last_tag, line.strip())
    if current:
        records.append(current)
    return records


def normalize_wos_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    title: Normalize a raw Web of Science record into biblioflow-friendly keys.
    parameters:
      record:
        type: dict[str, Any]
        description: Raw WoS tag dictionary.
    returns:
      type: dict[str, Any]
    """
    authors = record.get("AF") or record.get("AU") or []
    author_raw = record.get("AU") or authors
    return {
        "source": "web_of_science",
        "source_id": record.get("UT"),
        "authors_raw": author_raw,
        "authors": authors,
        "title": record.get("TI"),
        "source_title": record.get("SO"),
        "language": record.get("LA"),
        "document_type": record.get("DT") or record.get("PT"),
        "keywords_author": record.get("DE"),
        "keywords_index": record.get("ID"),
        "abstract": record.get("AB"),
        "affiliations": record.get("C1"),
        "corresponding_author_address": record.get("RP"),
        "emails": record.get("EM"),
        "references_raw": record.get("CR"),
        "references": record.get("CR"),
        "reference_count": record.get("NR"),
        "cited_by_count": record.get("TC"),
        "publication_year": record.get("PY"),
        "publication_date": record.get("PD") or record.get("PY"),
        "volume": record.get("VL"),
        "issue": record.get("IS"),
        "start_page": record.get("BP"),
        "end_page": record.get("EP"),
        "article_number": record.get("AR"),
        "doi": record.get("DI"),
        "issn": record.get("SN"),
        "eissn": record.get("EI"),
        "publisher": record.get("PU"),
        "wos_categories": record.get("WC"),
        "research_areas": record.get("SC"),
        "raw": dict(record),
    }


def read_wos_records(path: str | Path) -> list[dict[str, Any]]:
    """
    title: Read Web of Science plain-text export records.
    parameters:
      path:
        type: str | Path
        description: Input path.
    returns:
      type: list[dict[str, Any]]
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    return [normalize_wos_record(record) for record in parse_wos_records(text)]

"""
title: Small BibTeX reader for common bibliographic exports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_FIELD_MAP = {
    "title": "title",
    "author": "authors",
    "journal": "source_title",
    "journaltitle": "source_title",
    "booktitle": "source_title",
    "year": "publication_year",
    "date": "publication_year",
    "doi": "doi",
    "url": "url",
    "abstract": "abstract",
    "keywords": "keywords_author",
    "volume": "volume",
    "number": "issue",
    "pages": "pages",
    "issn": "issn",
    "isbn": "isbn",
    "publisher": "publisher",
}


def _balanced_entries(text: str) -> list[tuple[str, str, str]]:
    """
    title: Implement the balanced entries helper.
    parameters:
      text:
        type: str
        description: Text value.
    returns:
      type: list[tuple[str, str, str]]
    """
    entries: list[tuple[str, str, str]] = []
    i = 0
    while True:
        start = text.find("@", i)
        if start == -1:
            break
        brace = text.find("{", start)
        if brace == -1:
            break
        entry_type = text[start + 1 : brace].strip().lower()
        depth = 0
        end = brace
        while end < len(text):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    break
            end += 1
        body = text[brace + 1 : end]
        key, _, fields = body.partition(",")
        entries.append((entry_type, key.strip(), fields))
        i = end + 1
    return entries


def _parse_fields(body: str) -> dict[str, str]:
    """
    title: Implement the parse fields helper.
    parameters:
      body:
        type: str
        description: Body value.
    returns:
      type: dict[str, str]
    """
    fields: dict[str, str] = {}
    i = 0
    while i < len(body):
        while i < len(body) and body[i] in "\n\r\t ,":
            i += 1
        name_start = i
        while i < len(body) and (body[i].isalnum() or body[i] in "_-"):
            i += 1
        name = body[name_start:i].strip().lower()
        if not name:
            break
        while i < len(body) and body[i].isspace():
            i += 1
        if i >= len(body) or body[i] != "=":
            break
        i += 1
        while i < len(body) and body[i].isspace():
            i += 1
        if i < len(body) and body[i] in '{"':
            opener = body[i]
            closer = "}" if opener == "{" else '"'
            i += 1
            value_start = i
            depth = 1 if opener == "{" else 0
            while i < len(body):
                char = body[i]
                if opener == "{" and char == "{":
                    depth += 1
                elif char == closer:
                    if opener == "{":
                        depth -= 1
                        if depth == 0:
                            break
                    else:
                        break
                i += 1
            value = body[value_start:i].strip()
            i += 1
        else:
            value_start = i
            while i < len(body) and body[i] != ",":
                i += 1
            value = body[value_start:i].strip()
        fields[name] = " ".join(value.split())
        while i < len(body) and body[i] != ",":
            i += 1
        if i < len(body) and body[i] == ",":
            i += 1
    return fields


def read_bibtex_records(path: str | Path) -> list[dict[str, Any]]:
    """
    title: Read common BibTeX records.
    parameters:
      path:
        type: str | Path
        description: Path value.
    returns:
      type: list[dict[str, Any]]
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    records: list[dict[str, Any]] = []
    for entry_type, key, body in _balanced_entries(text):
        fields = _parse_fields(body)
        record: dict[str, Any] = {
            "source_id": key,
            "document_type": entry_type,
        }
        for source, target in _FIELD_MAP.items():
            if source in fields:
                record[target] = fields[source]
        records.append(record)
    return records

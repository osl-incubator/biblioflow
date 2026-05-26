"""
title: Record normalization helpers.
"""

from __future__ import annotations

import re
from typing import Any

from biblioflow.schema import CANONICAL_FIELDS

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "source_id": ("id", "source_id", "eid", "pmid", "ut", "accession_number"),
    "title": ("title", "ti", "article_title", "article title", "t1"),
    "abstract": ("abstract", "ab", "summary", "notes", "n2"),
    "authors": ("authors", "author", "au", "a1", "author_names"),
    "source_title": (
        "source_title",
        "source",
        "journal",
        "journal_name",
        "publication name",
        "so",
        "jf",
        "jo",
        "t2",
    ),
    "publication_year": ("publication_year", "year", "py", "y1", "da", "date"),
    "doi": ("doi", "di", "do"),
    "url": ("url", "ur", "link"),
    "keywords_author": ("keywords_author", "keywords", "author keywords", "de", "kw"),
    "keywords_index": ("keywords_index", "index keywords", "mesh_terms", "mesh", "id"),
    "references": ("references", "cited_references", "cr", "ref", "refs"),
    "document_type": ("document_type", "type", "dt", "ty"),
    "language": ("language", "la"),
    "volume": ("volume", "vl"),
    "issue": ("issue", "number", "is"),
    "start_page": ("start_page", "sp"),
    "end_page": ("end_page", "ep"),
    "pages": ("pages", "page", "pg"),
    "issn": ("issn", "sn"),
    "isbn": ("isbn", "bn"),
    "publisher": ("publisher", "pb"),
    "affiliations": ("affiliations", "institutions", "addresses", "c1"),
    "countries": ("countries", "country", "country_codes"),
    "cited_by_count": ("cited_by_count", "citations", "times_cited", "tc"),
}

_LIST_FIELDS = {
    "authors",
    "keywords_author",
    "keywords_index",
    "keywords_all",
    "references",
    "affiliations",
    "countries",
}


def _canonical_key(key: str) -> str:
    """
    title: Implement the canonical key helper.
    parameters:
      key:
        type: str
        description: Key value.
    returns:
      type: str
    """
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def _first_value(value: Any) -> Any:
    """
    title: Implement the first value helper.
    parameters:
      value:
        type: Any
        description: Value value.
    returns:
      type: Any
    """
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _string_or_none(value: Any) -> str | None:
    """
    title: Implement the string or none helper.
    parameters:
      value:
        type: Any
        description: Value value.
    returns:
      type: str | None
    """
    value = _first_value(value)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_list(value: Any) -> list[str]:
    """
    title: Implement the as list helper.
    parameters:
      value:
        type: Any
        description: Value value.
    returns:
      type: list[str]
    """
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        output: list[str] = []
        for item in value:
            output.extend(_as_list(item))
        return _dedupe(output)
    text = str(value).strip()
    if not text:
        return []
    # Bibliographic exports commonly use semicolons for people/keywords. RIS
    # parsers also pass repeated tags as lists, so this split remains conservative.
    parts = re.split(r"\s*;\s*|\s*\|\s*", text)
    if len(parts) == 1 and "," in text and not re.search(r"\w,\s+\w", text):
        parts = re.split(r"\s*,\s*", text)
    return _dedupe(part.strip() for part in parts if part.strip())


def _dedupe(values: Any) -> list[str]:
    """
    title: Implement the dedupe helper.
    parameters:
      values:
        type: Any
        description: Values value.
    returns:
      type: list[str]
    """
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        marker = text.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        output.append(text)
    return output


def normalize_doi(value: Any) -> str | None:
    """
    title: Normalize a DOI string.
    parameters:
      value:
        type: Any
        description: Value value.
    returns:
      type: str | None
    """
    text = _string_or_none(value)
    if text is None:
        return None
    text = re.sub(r"^https?://(dx\.)?doi\.org/", "", text.strip(), flags=re.I)
    text = text.replace("doi:", "").strip().strip(".")
    return text.lower() or None


def parse_year(value: Any) -> int | None:
    """
    title: Extract a plausible publication year from a value.
    parameters:
      value:
        type: Any
        description: Value value.
    returns:
      type: int | None
    """
    text = _string_or_none(value)
    if not text:
        return None
    match = re.search(r"(1[5-9]\d{2}|20\d{2}|21\d{2})", text)
    if not match:
        return None
    year = int(match.group(1))
    return year if 1500 <= year <= 2199 else None


def normalize_record(
    record: dict[str, Any],
    *,
    provider: str = "generic",
    source_format: str = "unknown",
) -> dict[str, Any]:
    """
    title: Normalize one provider/export record into the canonical schema.
    parameters:
      record:
        type: dict[str, Any]
        description: Record value.
      provider:
        type: str
        description: Provider value.
      source_format:
        type: str
        description: Source format value.
    returns:
      type: dict[str, Any]
    """
    by_key = {_canonical_key(k): v for k, v in record.items()}
    normalized: dict[str, Any] = {field: None for field in CANONICAL_FIELDS}

    for field_name, aliases in _FIELD_ALIASES.items():
        for alias in aliases:
            key = _canonical_key(alias)
            if key in by_key:
                normalized[field_name] = by_key[key]
                break

    for field_name in _LIST_FIELDS:
        if field_name == "keywords_all":
            continue
        normalized[field_name] = _as_list(normalized.get(field_name))

    # BibTeX authors use "and" as a delimiter.
    if isinstance(normalized.get("authors"), list) and len(normalized["authors"]) == 1:
        author_text = normalized["authors"][0]
        if " and " in author_text:
            normalized["authors"] = _dedupe(
                part.strip() for part in author_text.split(" and ")
            )

    for field_name in CANONICAL_FIELDS:
        if field_name in _LIST_FIELDS:
            continue
        if field_name == "publication_year":
            normalized[field_name] = parse_year(normalized.get(field_name))
        elif field_name == "cited_by_count":
            value = _string_or_none(normalized.get(field_name))
            try:
                normalized[field_name] = int(value) if value is not None else None
            except ValueError:
                normalized[field_name] = None
        elif field_name == "doi":
            normalized[field_name] = normalize_doi(normalized.get(field_name))
        elif field_name not in {"provider", "source_format"}:
            normalized[field_name] = _string_or_none(normalized.get(field_name))

    keywords: list[str] = []
    keywords.extend(normalized.get("keywords_author") or [])
    keywords.extend(normalized.get("keywords_index") or [])
    normalized["keywords_all"] = _dedupe(keywords)
    normalized["provider"] = provider
    normalized["source_format"] = source_format
    return normalized

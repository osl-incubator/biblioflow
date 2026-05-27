"""
title: Record normalization helpers.
"""

from __future__ import annotations

import re
from typing import Any

from biblioflow.normalize.authors import author_names
from biblioflow.normalize.dates import (
    parse_publication_date as _parse_publication_date,
)
from biblioflow.normalize.dates import (
    parse_year as _parse_year,
)
from biblioflow.normalize.ids import normalize_doi as _normalize_doi
from biblioflow.normalize.references import reference_texts
from biblioflow.normalize.text import normalize_language, split_keywords
from biblioflow.schema import CANONICAL_FIELDS

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "id": ("id",),
    "source": ("source", "provider", "database", "source_database"),
    "source_id": (
        "source_id",
        "eid",
        "pmid",
        "ut",
        "accession_number",
        "unique_id",
        "unique-id",
        "openalex_id",
    ),
    "title": ("title", "ti", "article_title", "article title", "t1"),
    "abstract": ("abstract", "ab", "summary", "notes", "n2"),
    "authors_raw": ("authors_raw", "author_raw", "authors", "author", "au"),
    "authors": ("authors", "author", "au", "a1", "author_names"),
    "journal": ("journal", "journal_name", "source_title", "source title", "so"),
    "source_title": (
        "source_title",
        "source title",
        "source",
        "journal",
        "journal_name",
        "publication name",
        "publicationname",
        "prism_publicationname",
        "so",
        "jf",
        "jo",
        "t2",
    ),
    "year": ("year", "publication_year", "py", "y1", "da", "date"),
    "publication_year": ("publication_year", "year", "py", "y1", "da", "date"),
    "publication_date": (
        "publication_date",
        "publication date",
        "cover_date",
        "coverdate",
        "prism_coverdate",
        "pd",
        "date",
        "da",
    ),
    "journal_abbrev": ("journal_abbrev", "journal_abbreviation", "short_title"),
    "doi": ("doi", "di", "do"),
    "url": ("url", "ur", "link", "landing_page_url"),
    "author_keywords": ("author_keywords", "keywords_author", "keywords", "de", "kw"),
    "keywords_author": ("keywords_author", "author_keywords", "keywords", "de", "kw"),
    "keywords_index": ("keywords_index", "index keywords", "mesh_terms", "mesh"),
    "references_raw": ("references_raw", "references", "cited_references", "cr"),
    "references": ("references", "cited_references", "cr", "ref", "refs"),
    "document_type": ("document_type", "type", "dt", "ty"),
    "language": ("language", "la"),
    "volume": ("volume", "vl"),
    "issue": ("issue", "number", "is"),
    "start_page": ("start_page", "sp"),
    "end_page": ("end_page", "ep"),
    "pages": ("pages", "page", "pg"),
    "article_number": ("article_number", "art_no", "art no", "ar"),
    "page_count": ("page_count", "page count"),
    "issn": ("issn", "sn"),
    "eissn": ("eissn", "ei"),
    "isbn": ("isbn", "bn"),
    "publisher": ("publisher", "pb"),
    "affiliations": ("affiliations", "institutions", "addresses", "c1"),
    "institutions": ("institutions", "affiliations"),
    "countries": ("countries", "country", "country_codes"),
    "author_ids": ("author_ids", "author s id", "author(s) id"),
    "authors_with_affiliations": (
        "authors_with_affiliations",
        "authors with affiliations",
    ),
    "publication_stage": ("publication_stage", "publication stage"),
    "source_database": ("source_database", "source", "database"),
    "open_access_status": ("open_access_status", "open_access", "open access"),
    "open_access_url": ("open_access_url",),
    "license": ("license",),
    "funders": ("funders", "funder"),
    "grants": ("grants", "grant"),
    "concepts": ("concepts",),
    "wos_categories": ("wos_categories", "web of science categories", "wc"),
    "research_areas": ("research_areas", "research areas", "sc"),
    "emails": ("emails", "email_addresses", "em"),
    "corresponding_author_address": ("corresponding_author_address", "rp"),
    "cited_by_count": ("cited_by_count", "citations", "times_cited", "tc"),
    "reference_count": ("reference_count", "nr"),
    "raw": ("raw",),
}

_LIST_FIELDS = {
    "authors",
    "author_keywords",
    "keywords_author",
    "keywords_index",
    "keywords_all",
    "references",
    "references_raw",
    "affiliations",
    "institutions",
    "countries",
    "author_ids",
    "funders",
    "grants",
    "concepts",
    "wos_categories",
    "research_areas",
    "emails",
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
    return _normalize_doi(value)


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
    return _parse_year(value)


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

    normalized["raw"] = record.get("raw", dict(record))
    normalized["provider"] = provider
    normalized["source"] = normalized.get("source") or provider
    normalized["source_format"] = source_format

    if normalized.get("source_title") is None and normalized.get("journal") is not None:
        normalized["source_title"] = normalized["journal"]
    if normalized.get("journal") is None and normalized.get("source_title") is not None:
        normalized["journal"] = normalized["source_title"]
    if (
        normalized.get("publication_year") is None
        and normalized.get("year") is not None
    ):
        normalized["publication_year"] = normalized["year"]
    if (
        normalized.get("year") is None
        and normalized.get("publication_year") is not None
    ):
        normalized["year"] = normalized["publication_year"]
    if (
        normalized.get("keywords_author") is None
        and normalized.get("author_keywords") is not None
    ):
        normalized["keywords_author"] = normalized["author_keywords"]
    if (
        normalized.get("author_keywords") is None
        and normalized.get("keywords_author") is not None
    ):
        normalized["author_keywords"] = normalized["keywords_author"]
    if (
        normalized.get("references") is None
        and normalized.get("references_raw") is not None
    ):
        normalized["references"] = normalized["references_raw"]
    if (
        normalized.get("references_raw") is None
        and normalized.get("references") is not None
    ):
        normalized["references_raw"] = normalized["references"]
    if normalized.get("authors_raw") is None and normalized.get("authors") is not None:
        if isinstance(normalized["authors"], list):
            normalized["authors_raw"] = "; ".join(
                str(author) for author in normalized["authors"]
            )
        else:
            normalized["authors_raw"] = normalized["authors"]

    for field_name in _LIST_FIELDS:
        if field_name == "keywords_all":
            continue
        if field_name in {"author_keywords", "keywords_author", "keywords_index"}:
            normalized[field_name] = split_keywords(normalized.get(field_name))
        elif field_name == "references":
            normalized[field_name] = reference_texts(normalized.get(field_name))
        elif field_name == "references_raw":
            normalized[field_name] = _as_list(normalized.get(field_name))
        elif field_name == "authors":
            normalized[field_name] = author_names(
                normalized.get(field_name),
                source=provider,
            )
        else:
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
        if field_name == "raw":
            continue
        if field_name in {"publication_year", "year"}:
            normalized[field_name] = parse_year(normalized.get(field_name))
        elif field_name == "publication_date":
            normalized[field_name] = _parse_publication_date(normalized.get(field_name))
        elif field_name == "cited_by_count":
            value = _string_or_none(normalized.get(field_name))
            try:
                normalized[field_name] = int(value) if value is not None else None
            except ValueError:
                normalized[field_name] = None
        elif field_name == "reference_count":
            value = _string_or_none(normalized.get(field_name))
            try:
                normalized[field_name] = int(value) if value is not None else None
            except ValueError:
                normalized[field_name] = None
        elif field_name == "doi":
            normalized[field_name] = normalize_doi(normalized.get(field_name))
        elif field_name == "language":
            normalized[field_name] = normalize_language(normalized.get(field_name))
        elif field_name not in {"provider", "source_format"}:
            normalized[field_name] = _string_or_none(normalized.get(field_name))

    if normalized.get("source_id") is None:
        normalized["source_id"] = (
            normalized.get("id")
            or normalized.get("doi")
            or normalized.get("url")
            or normalized.get("title")
        )
    if normalized.get("id") is None:
        normalized["id"] = normalized.get("source_id")
    if normalized.get("source_title") is None and normalized.get("journal") is not None:
        normalized["source_title"] = normalized["journal"]
    if normalized.get("journal") is None and normalized.get("source_title") is not None:
        normalized["journal"] = normalized["source_title"]
    if (
        normalized.get("year") is None
        and normalized.get("publication_year") is not None
    ):
        normalized["year"] = normalized["publication_year"]
    if (
        normalized.get("publication_year") is None
        and normalized.get("year") is not None
    ):
        normalized["publication_year"] = normalized["year"]

    keywords: list[str] = []
    keywords.extend(normalized.get("keywords_author") or [])
    keywords.extend(normalized.get("keywords_index") or [])
    normalized["author_keywords"] = list(normalized.get("keywords_author") or [])
    normalized["keywords_all"] = _dedupe(keywords)
    return normalized

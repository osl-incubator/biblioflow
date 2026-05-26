"""
title: Provider-specific raw-record adapters.
"""

from __future__ import annotations

from typing import Any


def _first(value: Any) -> Any:
    """
    title: Implement the first helper.
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


def _date_parts(value: Any) -> int | None:
    """
    title: Implement the date parts helper.
    parameters:
      value:
        type: Any
        description: Value value.
    returns:
      type: int | None
    """
    if isinstance(value, dict):
        parts = value.get("date-parts")
        if (
            isinstance(parts, list)
            and parts
            and isinstance(parts[0], list)
            and parts[0]
        ):
            try:
                return int(parts[0][0])
            except (TypeError, ValueError):
                return None
    return None


def adapt_openalex(record: dict[str, Any]) -> dict[str, Any]:
    """
    title: Adapt an OpenAlex work object to biblioflow-friendly keys.
    parameters:
      record:
        type: dict[str, Any]
        description: Record value.
    returns:
      type: dict[str, Any]
    """
    primary_location = record.get("primary_location") or {}
    source = primary_location.get("source") or {}
    authors = []
    affiliations = []
    countries = []
    for authorship in record.get("authorships") or []:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            authors.append(name)
        for institution in authorship.get("institutions") or []:
            if not isinstance(institution, dict):
                continue
            if institution.get("display_name"):
                affiliations.append(institution["display_name"])
            if institution.get("country_code"):
                countries.append(institution["country_code"])

    concepts = [
        concept.get("display_name")
        for concept in record.get("concepts") or []
        if isinstance(concept, dict) and concept.get("display_name")
    ]
    keywords = [
        keyword.get("display_name") or keyword.get("keyword")
        for keyword in record.get("keywords") or []
        if isinstance(keyword, dict)
    ]
    return {
        **record,
        "source_id": record.get("id") or record.get("openalex_id"),
        "title": record.get("title") or record.get("display_name"),
        "publication_year": record.get("publication_year"),
        "doi": record.get("doi"),
        "url": record.get("landing_page_url")
        or primary_location.get("landing_page_url"),
        "source_title": source.get("display_name"),
        "authors": authors,
        "keywords_author": [item for item in keywords if item],
        "keywords_index": concepts,
        "cited_by_count": record.get("cited_by_count"),
        "document_type": record.get("type"),
        "affiliations": affiliations,
        "countries": countries,
    }


def adapt_crossref(record: dict[str, Any]) -> dict[str, Any]:
    """
    title: Adapt a Crossref work object to biblioflow-friendly keys.
    parameters:
      record:
        type: dict[str, Any]
        description: Record value.
    returns:
      type: dict[str, Any]
    """
    authors = []
    for author in record.get("author") or []:
        if not isinstance(author, dict):
            continue
        family = author.get("family") or ""
        given = author.get("given") or ""
        name = ", ".join(part for part in (family, given) if part).strip()
        if name:
            authors.append(name)

    year = None
    for key in ("published-print", "published-online", "published", "created"):
        year = _date_parts(record.get(key))
        if year:
            break

    references = []
    for reference in record.get("reference") or []:
        if not isinstance(reference, dict):
            continue
        references.append(
            reference.get("DOI")
            or reference.get("doi")
            or reference.get("article-title")
            or reference.get("unstructured")
        )

    return {
        **record,
        "source_id": record.get("URL") or record.get("DOI"),
        "title": _first(record.get("title")),
        "abstract": record.get("abstract"),
        "authors": authors,
        "source_title": _first(record.get("container-title"))
        or _first(record.get("short-container-title")),
        "publication_year": year,
        "doi": record.get("DOI") or record.get("doi"),
        "url": record.get("URL")
        or record.get("resource", {}).get("primary", {}).get("URL"),
        "keywords_author": record.get("subject") or [],
        "references": [ref for ref in references if ref],
        "document_type": record.get("type"),
        "volume": record.get("volume"),
        "issue": record.get("issue"),
        "pages": record.get("page"),
        "issn": record.get("ISSN") or record.get("issn"),
        "isbn": record.get("ISBN") or record.get("isbn"),
        "publisher": record.get("publisher"),
        "cited_by_count": record.get("is-referenced-by-count"),
    }


def adapt_pubmed(record: dict[str, Any]) -> dict[str, Any]:
    """
    title: Adapt PubMed/PubMed XML-like records.
    parameters:
      record:
        type: dict[str, Any]
        description: Record value.
    returns:
      type: dict[str, Any]
    """
    return {
        **record,
        "source_id": record.get("pmid")
        or record.get("PMID")
        or record.get("source_id"),
        "keywords_index": record.get("mesh_terms") or record.get("keywords_index"),
    }


def adapt_record(provider: str, record: dict[str, Any]) -> dict[str, Any]:
    """
    title: Apply a provider-specific adapter when one is available.
    parameters:
      provider:
        type: str
        description: Provider value.
      record:
        type: dict[str, Any]
        description: Record value.
    returns:
      type: dict[str, Any]
    """
    provider_key = provider.casefold().replace("-", "_")
    if provider_key == "openalex":
        return adapt_openalex(record)
    if provider_key == "crossref":
        return adapt_crossref(record)
    if provider_key in {"pubmed", "pmc"}:
        return adapt_pubmed(record)
    return record

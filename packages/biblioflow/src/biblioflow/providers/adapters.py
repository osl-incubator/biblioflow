"""
title: Provider-specific raw-record adapters.
"""

from __future__ import annotations

from typing import Any

from biblioflow.normalize.authors import author_names, normalize_author_name
from biblioflow.normalize.dates import parse_publication_date
from biblioflow.normalize.ids import normalize_doi
from biblioflow.normalize.references import reference_texts
from biblioflow.normalize.text import split_keywords


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
    institutions = []
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
                institutions.append(institution["display_name"])
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
    open_access = record.get("open_access") or {}
    return {
        **record,
        "source": "openalex",
        "source_id": record.get("id") or record.get("openalex_id"),
        "title": record.get("title") or record.get("display_name"),
        "publication_year": record.get("publication_year"),
        "publication_date": record.get("publication_date"),
        "doi": record.get("doi"),
        "url": record.get("landing_page_url")
        or primary_location.get("landing_page_url")
        or open_access.get("oa_url"),
        "source_title": source.get("display_name"),
        "issn": source.get("issn_l") or source.get("issn"),
        "abstract": reconstruct_openalex_abstract(record.get("abstract_inverted_index"))
        or record.get("abstract"),
        "authors": authors,
        "keywords_author": [item for item in keywords if item],
        "keywords_index": concepts,
        "concepts": concepts,
        "cited_by_count": record.get("cited_by_count"),
        "document_type": record.get("type"),
        "language": record.get("language"),
        "affiliations": affiliations,
        "institutions": institutions,
        "countries": countries,
        "references": record.get("referenced_works"),
        "open_access_status": open_access.get("oa_status"),
        "open_access_url": open_access.get("oa_url"),
        "grants": record.get("grants") or [],
        "raw": dict(record),
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
        name = normalize_author_name(
            " ".join(
                part for part in (author.get("given"), author.get("family")) if part
            )
        )["name"]
        if name:
            authors.append(name)

    publication_date = parse_crossref_date(record)
    year = None
    for key in (
        "published-print",
        "published-online",
        "published",
        "issued",
        "created",
        "deposited",
    ):
        year = _date_parts(record.get(key))
        if year:
            break

    return {
        **record,
        "source": "crossref",
        "source_id": record.get("URL") or record.get("DOI"),
        "title": _first(record.get("title")),
        "abstract": record.get("abstract"),
        "authors": authors,
        "source_title": _first(record.get("container-title"))
        or _first(record.get("short-container-title")),
        "journal_abbrev": _first(record.get("short-container-title")),
        "publication_year": year,
        "publication_date": publication_date,
        "doi": record.get("DOI") or record.get("doi"),
        "url": record.get("URL")
        or record.get("resource", {}).get("primary", {}).get("URL"),
        "keywords_author": record.get("subject") or [],
        "references": reference_texts(record.get("reference")),
        "references_raw": record.get("reference"),
        "document_type": record.get("type"),
        "volume": record.get("volume"),
        "issue": record.get("issue"),
        "pages": record.get("page"),
        "article_number": record.get("article-number"),
        "issn": record.get("ISSN") or record.get("issn"),
        "isbn": record.get("ISBN") or record.get("isbn"),
        "publisher": record.get("publisher"),
        "cited_by_count": record.get("is-referenced-by-count"),
        "funders": record.get("funder") or [],
        "license": record.get("license"),
        "raw": dict(record),
    }


def reconstruct_openalex_abstract(inverted_index: Any) -> str | None:
    """
    title: Reconstruct an OpenAlex abstract from an inverted index.
    parameters:
      inverted_index:
        type: Any
        description: OpenAlex abstract inverted index.
    returns:
      type: str | None
    """
    if not isinstance(inverted_index, dict):
        return None
    positions: dict[int, str] = {}
    for token, indexes in inverted_index.items():
        if not isinstance(indexes, list):
            continue
        for index in indexes:
            try:
                positions[int(index)] = str(token)
            except (TypeError, ValueError):
                continue
    if not positions:
        return None
    return " ".join(positions[index] for index in sorted(positions))


def parse_crossref_date(record: dict[str, Any]) -> str | None:
    """
    title: Parse the best Crossref publication date.
    parameters:
      record:
        type: dict[str, Any]
        description: Crossref work.
    returns:
      type: str | None
    """
    for key in (
        "published-print",
        "published-online",
        "published",
        "issued",
        "created",
        "deposited",
    ):
        parsed = parse_publication_date(record.get(key))
        if parsed:
            return parsed
    return None


def adapt_scopus(record: dict[str, Any]) -> dict[str, Any]:
    """
    title: Adapt a Scopus CSV or BibTeX record to biblioflow-friendly keys.
    parameters:
      record:
        type: dict[str, Any]
        description: Raw Scopus record.
    returns:
      type: dict[str, Any]
    """
    get = record.get
    authors = get("Author full names") or get("Authors") or get("authors")
    return {
        **record,
        "source": "scopus",
        "source_id": get("EID") or get("eid") or get("source_id"),
        "authors_raw": get("Authors") or get("authors_raw"),
        "authors": author_names(authors, source="scopus"),
        "author_ids": get("Author(s) ID") or get("author_ids"),
        "title": get("Title") or get("title"),
        "publication_year": get("Year") or get("year"),
        "source_title": get("Source title") or get("source_title") or get("journal"),
        "volume": get("Volume") or get("volume"),
        "issue": get("Issue") or get("issue"),
        "article_number": get("Art. No.") or get("article_number"),
        "start_page": get("Page start") or get("start_page"),
        "end_page": get("Page end") or get("end_page"),
        "page_count": get("Page count") or get("page_count"),
        "cited_by_count": get("Cited by") or get("cited_by_count") or get("citedby"),
        "doi": normalize_doi(get("DOI") or get("doi")),
        "url": get("Link") or get("url"),
        "affiliations": get("Affiliations") or get("affiliations"),
        "authors_with_affiliations": get("Authors with affiliations"),
        "abstract": get("Abstract") or get("abstract"),
        "keywords_author": split_keywords(get("Author Keywords")),
        "keywords_index": split_keywords(get("Index Keywords")),
        "references_raw": get("References") or get("references_raw"),
        "references": get("References") or get("references"),
        "document_type": get("Document Type") or get("document_type"),
        "publication_stage": get("Publication Stage") or get("publication_stage"),
        "open_access_status": get("Open Access") or get("open_access_status"),
        "source_database": get("Source") or get("source_database"),
        "issn": get("ISSN") or get("issn"),
        "isbn": get("ISBN") or get("isbn"),
        "publisher": get("Publisher") or get("publisher"),
        "language": get("Language of Original Document") or get("language"),
        "raw": dict(record),
    }


def adapt_scopus_api(record: dict[str, Any]) -> dict[str, Any]:
    """
    title: Adapt a Scopus API result to biblioflow-friendly keys.
    parameters:
      record:
        type: dict[str, Any]
        description: Raw Scopus API result.
    returns:
      type: dict[str, Any]
    """
    links = record.get("link") or []
    url = None
    if isinstance(links, list):
        for link in links:
            if isinstance(link, dict) and link.get("@href"):
                url = link["@href"]
                break
    return adapt_scopus(
        {
            **record,
            "EID": record.get("eid"),
            "Title": record.get("dc:title"),
            "DOI": record.get("prism:doi"),
            "Year": record.get("prism:coverDate"),
            "Source title": record.get("prism:publicationName"),
            "Volume": record.get("prism:volume"),
            "Issue": record.get("prism:issueIdentifier"),
            "pages": record.get("prism:pageRange"),
            "Cited by": record.get("citedby-count"),
            "Document Type": record.get("subtypeDescription"),
            "Open Access": record.get("openaccess"),
            "Link": url,
        }
    )


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
    if provider_key == "scopus":
        return adapt_scopus(record)
    if provider_key == "scopus_api":
        return adapt_scopus_api(record)
    if provider_key in {"pubmed", "pmc"}:
        return adapt_pubmed(record)
    return record

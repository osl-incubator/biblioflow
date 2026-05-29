"""
title: Provider-specific raw-record adapters.
"""

from __future__ import annotations

import re
from typing import Any

from biblioflow.normalize.authors import author_names, normalize_author_name
from biblioflow.normalize.dates import parse_publication_date, parse_year
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


def _key(value: str) -> str:
    """
    title: Normalize provider payload keys for lookup.
    parameters:
      value:
        type: str
        description: Raw key value.
    returns:
      type: str
    """
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _lookup(record: dict[str, Any], *keys: str) -> Any:
    """
    title: Look up the first matching value using exact and normalized keys.
    parameters:
      record:
        type: dict[str, Any]
        description: Record dictionary.
      keys:
        type: str
        description: Candidate keys.
        variadic: positional
    returns:
      type: Any
    """
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    normalized = {_key(str(key)): value for key, value in record.items()}
    for key in keys:
        value = normalized.get(_key(key))
        if value not in (None, ""):
            return value
    return None


def _first_text(value: Any) -> str | None:
    """
    title: Convert the first scalar value to text.
    parameters:
      value:
        type: Any
        description: Raw value.
    returns:
      type: str | None
    """
    value = _first(value)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _list_texts(value: Any) -> list[str]:
    """
    title: Convert nested values into a deduplicated text list.
    parameters:
      value:
        type: Any
        description: Raw list-like value.
    returns:
      type: list[str]
    """
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        output: list[str] = []
        for item in value:
            output.extend(_list_texts(item))
        return _dedupe_texts(output)
    if isinstance(value, dict):
        for key in (
            "name",
            "display_name",
            "term",
            "keyword",
            "value",
            "text",
            "DescriptorName",
            "descriptor_name",
        ):
            text = _first_text(value.get(key))
            if text:
                return [text]
        return []
    text = _first_text(value)
    if text is None:
        return []
    return _dedupe_texts(split_keywords(text) or [text])


def _dedupe_texts(values: list[str]) -> list[str]:
    """
    title: Deduplicate text values case-insensitively.
    parameters:
      values:
        type: list[str]
        description: Text values.
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


def _identifier(record: dict[str, Any], identifier: str) -> str | None:
    """
    title: Extract a typed identifier from common article id containers.
    parameters:
      record:
        type: dict[str, Any]
        description: Record dictionary.
      identifier:
        type: str
        description: Identifier type, such as doi or pmid.
    returns:
      type: str | None
    """
    direct = _lookup(record, identifier, identifier.upper())
    if direct:
        return _first_text(direct)
    containers = _lookup(
        record,
        "ids",
        "article_ids",
        "articleids",
        "identifiers",
        "article_id",
    )
    if isinstance(containers, dict):
        direct = _lookup(containers, identifier, identifier.upper())
        if direct:
            return _first_text(direct)
    if isinstance(containers, list | tuple):
        for item in containers:
            if not isinstance(item, dict):
                continue
            id_type = _lookup(item, "type", "id_type", "idtype", "IdType")
            id_type_text = _first_text(id_type)
            if id_type_text and id_type_text.casefold() == identifier.casefold():
                value = _lookup(item, "value", "id", "identifier", "text")
                if value:
                    return _first_text(value)
    return None


def _pubmed_authors(value: Any) -> list[str]:
    """
    title: Normalize PubMed author payloads to display names.
    parameters:
      value:
        type: Any
        description: Author payload.
    returns:
      type: list[str]
    """
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        output: list[str] = []
        for item in value:
            output.extend(_pubmed_authors(item))
        return _dedupe_texts(output)
    if isinstance(value, dict):
        name = _lookup(value, "name", "full_name", "fullname", "display_name")
        if name:
            return [_first_text(name) or ""]
        collective = _lookup(value, "collective_name", "CollectiveName")
        if collective:
            return [_first_text(collective) or ""]
        family = _first_text(_lookup(value, "last_name", "lastname", "LastName"))
        given = _first_text(
            _lookup(
                value,
                "fore_name",
                "forename",
                "first_name",
                "firstname",
                "initials",
            )
        )
        name = " ".join(part for part in (given, family) if part)
        return [name] if name else []
    return author_names(value, source="pubmed")


def _pubmed_publication_date(record: dict[str, Any]) -> str | None:
    """
    title: Parse PubMed publication date fields.
    parameters:
      record:
        type: dict[str, Any]
        description: Record dictionary.
    returns:
      type: str | None
    """
    value = _lookup(
        record,
        "publication_date",
        "pub_date",
        "pubdate",
        "date",
        "pubmed_date",
        "article_date",
    )
    if isinstance(value, dict):
        year = _first_text(_lookup(value, "year", "Year"))
        month = _first_text(_lookup(value, "month", "Month"))
        day = _first_text(_lookup(value, "day", "Day"))
        if year and month and day and month.isdigit() and day.isdigit():
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        if year and month and month.isdigit():
            return f"{int(year):04d}-{int(month):02d}"
        if year:
            return f"{int(year):04d}"
    return parse_publication_date(value)


def _pubmed_year(record: dict[str, Any]) -> int | None:
    """
    title: Extract a PubMed publication year.
    parameters:
      record:
        type: dict[str, Any]
        description: Record dictionary.
    returns:
      type: int | None
    """
    date = _pubmed_publication_date(record)
    return parse_year(
        _lookup(record, "publication_year", "year", "pub_year", "pubdate", "date")
        or date
    )


def _pmcid(value: Any) -> str | None:
    """
    title: Normalize a PubMed Central identifier.
    parameters:
      value:
        type: Any
        description: Raw PMCID value.
    returns:
      type: str | None
    """
    text = _first_text(value)
    if not text:
        return None
    text = text.strip()
    if text.upper().startswith("PMC"):
        return f"PMC{text[3:].strip()}"
    if text.isdigit():
        return f"PMC{text}"
    return text


def _pubmed_url(pmid: str | None) -> str | None:
    """
    title: Build a PubMed URL for a PMID.
    parameters:
      pmid:
        type: str | None
        description: PubMed identifier.
    returns:
      type: str | None
    """
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None


def _pmc_url(pmcid: str | None) -> str | None:
    """
    title: Build a PubMed Central article URL for a PMCID.
    parameters:
      pmcid:
        type: str | None
        description: PubMed Central identifier.
    returns:
      type: str | None
    """
    return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else None


def _adapt_pubmed_common(record: dict[str, Any], *, source: str) -> dict[str, Any]:
    """
    title: Adapt PubMed-family records to biblioflow-friendly keys.
    parameters:
      record:
        type: dict[str, Any]
        description: Raw PubMed-family record.
      source:
        type: str
        description: Normalized source name.
    returns:
      type: dict[str, Any]
    """
    pmid = _identifier(record, "pmid") or _lookup(record, "source_id", "pubmed_id")
    pmid_text = _first_text(pmid)
    pmcid_text = _pmcid(
        _identifier(record, "pmcid") or _lookup(record, "pmc_id", "pmc")
    )
    doi = normalize_doi(_identifier(record, "doi") or _lookup(record, "doi", "DOI"))
    journal = _lookup(record, "source_title", "journal", "journal_title", "journal")
    journal_abbrev = _lookup(
        record,
        "journal_abbrev",
        "journal_abbreviation",
        "iso_abbreviation",
        "medline_ta",
    )
    keywords_author = _list_texts(_lookup(record, "keywords_author", "keywords"))
    mesh_terms = _list_texts(_lookup(record, "keywords_index", "mesh_terms", "mesh"))
    pub_date = _pubmed_publication_date(record)
    pmc_url = _pmc_url(pmcid_text)
    pubmed_url = _pubmed_url(pmid_text)
    full_text = _lookup(record, "full_text", "article_text", "body", "text")
    full_text_url = _lookup(record, "full_text_url", "pmc_url") or pmc_url

    return {
        **record,
        "source": source,
        "source_id": pmcid_text if source == "pmc" and pmcid_text else pmid_text,
        "pmid": pmid_text,
        "pmcid": pmcid_text,
        "doi": doi,
        "title": _lookup(record, "title", "article_title"),
        "abstract": _lookup(record, "abstract", "summary"),
        "full_text": full_text,
        "authors": _pubmed_authors(_lookup(record, "authors", "author", "author_list")),
        "authors_raw": _lookup(record, "authors_raw", "authors", "author"),
        "source_title": journal,
        "journal": journal,
        "journal_abbrev": journal_abbrev,
        "publication_year": _pubmed_year(record),
        "publication_date": pub_date,
        "keywords_author": keywords_author,
        "keywords_index": mesh_terms,
        "document_type": "; ".join(
            _list_texts(_lookup(record, "document_type", "publication_type", "type"))
        )
        or None,
        "language": _lookup(record, "language", "languages"),
        "volume": _lookup(record, "volume"),
        "issue": _lookup(record, "issue"),
        "pages": _lookup(record, "pages", "page", "pagination"),
        "start_page": _lookup(record, "start_page"),
        "end_page": _lookup(record, "end_page"),
        "issn": _lookup(record, "issn"),
        "eissn": _lookup(record, "eissn"),
        "publisher": _lookup(record, "publisher"),
        "affiliations": _list_texts(_lookup(record, "affiliations", "affiliation")),
        "grants": _list_texts(_lookup(record, "grants", "grant")),
        "references": _lookup(record, "references"),
        "references_raw": _lookup(record, "references_raw", "references"),
        "url": _lookup(record, "url", "link")
        or (pmc_url if source == "pmc" else pubmed_url),
        "full_text_url": full_text_url,
        "open_access_url": _lookup(record, "open_access_url") or full_text_url,
        "raw": dict(record),
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
    return _adapt_pubmed_common(record, source="pubmed")


def adapt_pmc(record: dict[str, Any]) -> dict[str, Any]:
    """
    title: Adapt PubMed Central records.
    parameters:
      record:
        type: dict[str, Any]
        description: Record value.
    returns:
      type: dict[str, Any]
    """
    return _adapt_pubmed_common(record, source="pmc")


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
    if provider_key == "pubmed":
        return adapt_pubmed(record)
    if provider_key == "pmc":
        return adapt_pmc(record)
    return record

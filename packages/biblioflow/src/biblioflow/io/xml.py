"""
title: XML readers for common bibliographic records.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def _text(element: ET.Element | None) -> str | None:
    """
    title: Implement the text helper.
    parameters:
      element:
        type: ET.Element | None
        description: Element value.
    returns:
      type: str | None
    """
    if element is None:
        return None
    value = "".join(element.itertext()).strip()
    return value or None


def _find_text(element: ET.Element, *paths: str) -> str | None:
    """
    title: Implement the find text helper.
    parameters:
      element:
        type: ET.Element
        description: Element value.
      paths:
        type: str
        description: Additional positional arguments.
        variadic: positional
    returns:
      type: str | None
    """
    for path in paths:
        value = _text(element.find(path))
        if value:
            return value
    return None


def _find_all_text(element: ET.Element, *paths: str) -> list[str]:
    """
    title: Find all non-empty text values for XML paths.
    parameters:
      element:
        type: ET.Element
        description: Element value.
      paths:
        type: str
        description: Additional positional arguments.
        variadic: positional
    returns:
      type: list[str]
    """
    values: list[str] = []
    for path in paths:
        for child in element.findall(path):
            value = _text(child)
            if value:
                values.append(value)
    return values


def _pub_date(article: ET.Element) -> str | None:
    """
    title: Extract a PubMed publication date.
    parameters:
      article:
        type: ET.Element
        description: PubMed article element.
    returns:
      type: str | None
    """
    for date in article.findall(".//ArticleDate") + article.findall(".//PubDate"):
        year = _find_text(date, "Year")
        if not year:
            continue
        month = _find_text(date, "Month")
        day = _find_text(date, "Day")
        if month and month.isdigit() and day and day.isdigit():
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        if month and month.isdigit():
            return f"{int(year):04d}-{int(month):02d}"
        return f"{int(year):04d}"
    return None


def _article_ids(article: ET.Element) -> dict[str, str]:
    """
    title: Extract PubMed article identifiers.
    parameters:
      article:
        type: ET.Element
        description: PubMed article element.
    returns:
      type: dict[str, str]
    """
    ids: dict[str, str] = {}
    pmid = _find_text(article, ".//PMID")
    if pmid:
        ids["pmid"] = pmid
    for article_id in article.findall(".//ArticleId"):
        id_type = article_id.attrib.get("IdType", "").lower()
        value = _text(article_id)
        if id_type and value:
            ids[id_type] = value
    for elocation in article.findall(".//ELocationID"):
        id_type = elocation.attrib.get("EIdType", "").lower()
        value = _text(elocation)
        if id_type and value:
            ids[id_type] = value
    return ids


def _pubmed_article(article: ET.Element) -> dict[str, Any]:
    """
    title: Implement the pubmed article helper.
    parameters:
      article:
        type: ET.Element
        description: Article value.
    returns:
      type: dict[str, Any]
    """
    authors = []
    for author in article.findall(".//Author"):
        collective = _find_text(author, "CollectiveName")
        if collective:
            authors.append(collective)
            continue
        last = _find_text(author, "LastName") or ""
        fore = _find_text(author, "ForeName", "Initials") or ""
        name = ", ".join(part for part in (last, fore) if part).strip()
        if name:
            authors.append(name)

    ids = _article_ids(article)

    mesh_terms = [
        text
        for descriptor in article.findall(".//MeshHeading/DescriptorName")
        if (text := _text(descriptor))
    ]
    mesh_terms.extend(
        text
        for qualifier in article.findall(".//MeshHeading/QualifierName")
        if (text := _text(qualifier))
    )
    keywords = [
        text for keyword in article.findall(".//Keyword") if (text := _text(keyword))
    ]
    abstract = "\n".join(_find_all_text(article, ".//Abstract/AbstractText")) or None
    publication_types = _find_all_text(article, ".//PublicationType")
    languages = _find_all_text(article, ".//Language")
    affiliations = _find_all_text(article, ".//Affiliation")
    issn = None
    eissn = None
    for issn_element in article.findall(".//Journal/ISSN"):
        value = _text(issn_element)
        if not value:
            continue
        if issn_element.attrib.get("IssnType", "").casefold() == "electronic":
            eissn = value
        else:
            issn = value
    pmcid = ids.get("pmc") or ids.get("pmcid")
    pmid = ids.get("pmid")
    pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else None
    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None

    return {
        "source_id": pmid,
        "pmid": pmid,
        "pmcid": pmcid,
        "title": _find_text(article, ".//ArticleTitle"),
        "abstract": abstract,
        "authors": authors,
        "source_title": _find_text(article, ".//Journal/Title", ".//MedlineTA"),
        "journal_abbrev": _find_text(article, ".//ISOAbbreviation", ".//MedlineTA"),
        "publication_year": _find_text(
            article, ".//PubDate/Year", ".//ArticleDate/Year"
        ),
        "publication_date": _pub_date(article),
        "doi": ids.get("doi"),
        "keywords_author": keywords,
        "keywords_index": mesh_terms,
        "document_type": "; ".join(publication_types) if publication_types else None,
        "language": languages[0] if languages else None,
        "volume": _find_text(article, ".//JournalIssue/Volume"),
        "issue": _find_text(article, ".//JournalIssue/Issue"),
        "start_page": _find_text(article, ".//Pagination/StartPage", ".//MedlinePgn"),
        "pages": _find_text(article, ".//MedlinePgn"),
        "issn": issn,
        "eissn": eissn,
        "affiliations": affiliations,
        "url": pubmed_url,
        "full_text_url": pmc_url,
        "open_access_url": pmc_url,
    }


def _generic_record(record: ET.Element) -> dict[str, Any]:
    """
    title: Implement the generic record helper.
    parameters:
      record:
        type: ET.Element
        description: Record value.
    returns:
      type: dict[str, Any]
    """
    output: dict[str, Any] = {}
    for child in list(record):
        tag = child.tag.split("}")[-1]
        value = _text(child)
        if value:
            if tag in output:
                existing = output[tag]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    output[tag] = [existing, value]
            else:
                output[tag] = value
    return output


def read_xml_records(path: str | Path) -> list[dict[str, Any]]:
    """
    title: Read records from PubMed-style or simple generic XML.
    parameters:
      path:
        type: str | Path
        description: Path value.
    returns:
      type: list[dict[str, Any]]
    """
    root = ET.parse(path).getroot()
    articles = root.findall(".//PubmedArticle")
    if articles:
        return [_pubmed_article(article) for article in articles]

    records = root.findall(".//record") or root.findall(".//Record")
    if records:
        return [_generic_record(record) for record in records]

    return [_generic_record(root)]

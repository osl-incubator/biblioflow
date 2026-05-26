"""XML readers for common bibliographic records."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def _text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    value = "".join(element.itertext()).strip()
    return value or None


def _find_text(element: ET.Element, *paths: str) -> str | None:
    for path in paths:
        value = _text(element.find(path))
        if value:
            return value
    return None


def _pubmed_article(article: ET.Element) -> dict[str, Any]:
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

    doi = None
    for article_id in article.findall(".//ArticleId"):
        if article_id.attrib.get("IdType", "").lower() == "doi":
            doi = _text(article_id)
            break
    if doi is None:
        for elocation in article.findall(".//ELocationID"):
            if elocation.attrib.get("EIdType", "").lower() == "doi":
                doi = _text(elocation)
                break

    mesh_terms = [
        text
        for descriptor in article.findall(".//MeshHeading/DescriptorName")
        if (text := _text(descriptor))
    ]
    keywords = [
        text for keyword in article.findall(".//Keyword") if (text := _text(keyword))
    ]

    return {
        "source_id": _find_text(article, ".//PMID"),
        "title": _find_text(article, ".//ArticleTitle"),
        "abstract": _find_text(article, ".//Abstract/AbstractText"),
        "authors": authors,
        "source_title": _find_text(article, ".//Journal/Title", ".//MedlineTA"),
        "publication_year": _find_text(
            article, ".//PubDate/Year", ".//ArticleDate/Year"
        ),
        "doi": doi,
        "keywords_author": keywords,
        "keywords_index": mesh_terms,
        "document_type": _find_text(article, ".//PublicationType"),
        "language": _find_text(article, ".//Language"),
        "volume": _find_text(article, ".//JournalIssue/Volume"),
        "issue": _find_text(article, ".//JournalIssue/Issue"),
        "start_page": _find_text(article, ".//Pagination/StartPage", ".//MedlinePgn"),
    }


def _generic_record(record: ET.Element) -> dict[str, Any]:
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
    """Read records from PubMed-style or simple generic XML."""
    root = ET.parse(path).getroot()
    articles = root.findall(".//PubmedArticle")
    if articles:
        return [_pubmed_article(article) for article in articles]

    records = root.findall(".//record") or root.findall(".//Record")
    if records:
        return [_generic_record(record) for record in records]

    return [_generic_record(root)]

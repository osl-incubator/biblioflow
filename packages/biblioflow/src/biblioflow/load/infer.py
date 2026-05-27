"""
title: Input format and provider inference.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from biblioflow.schema import FORMAT_EXTENSIONS

SOURCE_ALIASES = {
    "auto": "auto",
    "generic": "generic",
    "bib": "bibtex",
    "bibtex": "bibtex",
    "ris": "ris",
    "wos": "web_of_science",
    "webofscience": "web_of_science",
    "web_of_science": "web_of_science",
    "web-of-science": "web_of_science",
    "scopus": "scopus",
    "openalex": "openalex",
    "crossref": "crossref",
    "pubmed": "pubmed",
    "pmc": "pmc",
    "pmcid": "pmc",
    "pubmed_central": "pmc",
    "pubmedcentral": "pmc",
}

FORMAT_ALIASES = {
    "auto": "auto",
    "bib": "bibtex",
    "bibtex": "bibtex",
    "ris": "ris",
    "csv": "csv",
    "tsv": "tsv",
    "json": "json",
    "jsonl": "jsonl",
    "nbib": "nbib",
    "xml": "xml",
    "txt": "plain_text",
    "text": "plain_text",
    "plain_text": "plain_text",
    "plain-text": "plain_text",
    "yaml": "yaml",
    "yml": "yaml",
    "records": "records",
}

_KNOWN_PROVIDERS = (
    "scopus",
    "wos",
    "webofscience",
    "pubmed",
    "pmc",
    "openalex",
    "crossref",
    "lens",
    "dimensions",
    "cochrane",
)


def normalize_provider_name(value: str) -> str:
    """
    title: Normalize provider/source aliases.
    parameters:
      value:
        type: str
        description: Provider alias.
    returns:
      type: str
    """
    key = value.casefold().replace("-", "_").replace(" ", "_")
    return SOURCE_ALIASES.get(key, key)


def normalize_format_name(value: str) -> str:
    """
    title: Normalize format aliases.
    parameters:
      value:
        type: str
        description: Format alias.
    returns:
      type: str
    """
    key = value.casefold().replace("-", "_").replace(" ", "_")
    return FORMAT_ALIASES.get(key, key)


def _read_sample(source: str | Path, *, limit: int = 8192) -> str:
    """
    title: Read a small text sample for content detection.
    parameters:
      source:
        type: str | Path
        description: Input path.
      limit:
        type: int
        description: Maximum characters.
    returns:
      type: str
    """
    try:
        with Path(source).open("r", encoding="utf-8-sig", errors="replace") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def _detect_text_format(sample: str) -> str | None:
    """
    title: Detect a text-based bibliographic format from a sample.
    parameters:
      sample:
        type: str
        description: Text sample.
    returns:
      type: str | None
    """
    if "@article" in sample.lower() or "@book" in sample.lower():
        return "bibtex"
    if "TY  -" in sample and "ER  -" in sample:
        return "ris"
    if "FN Clarivate" in sample or "\nPT " in f"\n{sample}":
        return "plain_text"
    return None


def infer_format(source: str | Path) -> str:
    """
    title: Infer an input format from a path extension.
    parameters:
      source:
        type: str | Path
        description: Source value.
    returns:
      type: str
    """
    suffix = Path(source).suffix.lower()
    extension_format = FORMAT_EXTENSIONS.get(suffix)
    if extension_format and extension_format != "plain_text":
        return normalize_format_name(extension_format)
    sample = _read_sample(source)
    detected = _detect_text_format(sample)
    if detected:
        return detected
    return normalize_format_name(extension_format) if extension_format else "unknown"


def _csv_headers(source: str | Path) -> set[str]:
    """
    title: Read CSV headers for provider detection.
    parameters:
      source:
        type: str | Path
        description: Input path.
    returns:
      type: set[str]
    """
    sample = _read_sample(source)
    if not sample:
        return set()
    try:
        reader = csv.reader(sample.splitlines())
        headers = next(reader)
    except (csv.Error, StopIteration):
        return set()
    return {header.strip().casefold() for header in headers}


def _json_kind(source: str | Path) -> str | None:
    """
    title: Detect whether a JSON file looks like OpenAlex or Crossref.
    parameters:
      source:
        type: str | Path
        description: Input path.
    returns:
      type: str | None
    """
    sample = _read_sample(source, limit=200_000)
    if not sample:
        return None
    try:
        obj = json.loads(sample)
    except json.JSONDecodeError:
        return None
    probe = obj
    if isinstance(obj, dict) and isinstance(obj.get("message"), dict):
        message = obj["message"]
        if isinstance(message.get("items"), list) and message["items"]:
            probe = message["items"][0]
        else:
            probe = message
    elif isinstance(obj, dict) and isinstance(obj.get("results"), list):
        if obj["results"]:
            probe = obj["results"][0]
    elif isinstance(obj, list) and obj:
        probe = obj[0]
    if not isinstance(probe, dict):
        return None
    if str(probe.get("id", "")).startswith("https://openalex.org/") or (
        "authorships" in probe and "publication_year" in probe
    ):
        return "openalex"
    if "DOI" in probe or "container-title" in probe or "message-type" in obj:
        return "crossref"
    return None


def infer_provider(source: str | Path, *, format: str = "auto") -> str:
    """
    title: Infer a bibliographic provider from format and file name.
    parameters:
      source:
        type: str | Path
        description: Source value.
      format:
        type: str
        description: Format value.
    returns:
      type: str
    """
    fmt = infer_format(source) if format == "auto" else normalize_format_name(format)
    if fmt == "nbib":
        return "pubmed"
    if fmt == "bibtex":
        name = Path(source).name.lower().replace("-", "_")
        if "wos" in name or "web_of_science" in name or "webofscience" in name:
            return "web_of_science"
        if "scopus" in name:
            return "scopus"
        return "bibtex"
    if fmt == "ris":
        return "ris"
    if fmt == "plain_text":
        sample = _read_sample(source)
        if "FN Clarivate" in sample or "\nPT " in f"\n{sample}":
            return "web_of_science"
    if fmt == "csv":
        headers = _csv_headers(source)
        scopus_headers = {
            "authors",
            "author full names",
            "title",
            "year",
            "source title",
            "cited by",
            "doi",
            "eid",
        }
        if len(headers & scopus_headers) >= 4 or "eid" in headers:
            return "scopus"
        if {"id", "doi", "publication_year"} <= headers:
            return "openalex"
    if fmt == "json":
        detected = _json_kind(source)
        if detected:
            return detected
    name = Path(source).name.lower().replace("-", "_")
    for provider in _KNOWN_PROVIDERS:
        if provider in name:
            if provider in {"wos", "webofscience"}:
                return "web_of_science"
            return normalize_provider_name(provider)
    return "generic"

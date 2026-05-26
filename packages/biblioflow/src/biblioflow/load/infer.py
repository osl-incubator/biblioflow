"""
title: Input format and provider inference.
"""

from __future__ import annotations

from pathlib import Path

from biblioflow.schema import FORMAT_EXTENSIONS

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
    return FORMAT_EXTENSIONS.get(suffix, "unknown")


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
    fmt = infer_format(source) if format == "auto" else format
    if fmt == "nbib":
        return "pubmed"
    name = Path(source).name.lower().replace("-", "_")
    for provider in _KNOWN_PROVIDERS:
        if provider in name:
            return "wos" if provider == "webofscience" else provider
    return "generic"

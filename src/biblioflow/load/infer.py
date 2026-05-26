"""Input format and provider inference."""

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
    """Infer an input format from a path extension."""
    suffix = Path(source).suffix.lower()
    return FORMAT_EXTENSIONS.get(suffix, "unknown")


def infer_provider(source: str | Path, *, format: str = "auto") -> str:
    """Infer a bibliographic provider from format and file name."""
    fmt = infer_format(source) if format == "auto" else format
    if fmt == "nbib":
        return "pubmed"
    name = Path(source).name.lower().replace("-", "_")
    for provider in _KNOWN_PROVIDERS:
        if provider in name:
            return "wos" if provider == "webofscience" else provider
    return "generic"

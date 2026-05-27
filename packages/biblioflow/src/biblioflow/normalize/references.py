"""
title: Reference normalization helpers.
"""

from __future__ import annotations

from typing import Any

from biblioflow.normalize.ids import normalize_doi
from biblioflow.normalize.text import clean_text


def normalize_reference(value: Any) -> dict[str, Any]:
    """
    title: Normalize one reference into a lightweight dictionary.
    parameters:
      value:
        type: Any
        description: Reference-like value.
    returns:
      type: dict[str, Any]
    """
    if isinstance(value, dict):
        raw = (
            value.get("unstructured")
            or value.get("article-title")
            or value.get("raw")
            or value.get("DOI")
            or value.get("doi")
        )
        doi = normalize_doi(value.get("DOI") or value.get("doi"))
    else:
        raw = value
        doi = normalize_doi(value)
    return {"raw": clean_text(raw), "doi": doi}


def reference_texts(value: Any) -> list[str]:
    """
    title: Return lightweight reference text values.
    parameters:
      value:
        type: Any
        description: Reference value or values.
    returns:
      type: list[str]
    """
    if value is None:
        return []
    values = value if isinstance(value, list | tuple | set) else [value]
    output: list[str] = []
    for item in values:
        normalized = normalize_reference(item)
        text = normalized["doi"] or normalized["raw"]
        if text:
            output.append(str(text))
    return output

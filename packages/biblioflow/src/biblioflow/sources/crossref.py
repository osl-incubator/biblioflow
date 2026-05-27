"""
title: Crossref source helpers.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, cast

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.load.dispatcher import load
from biblioflow.providers.adapters import adapt_crossref, parse_crossref_date


def normalize_crossref_work(work: dict[str, Any]) -> dict[str, Any]:
    """
    title: Normalize one Crossref work.
    parameters:
      work:
        type: dict[str, Any]
        description: Raw Crossref work object.
    returns:
      type: dict[str, Any]
    """
    return adapt_crossref(work)


def _request_json(url: str) -> dict[str, Any]:
    """
    title: Fetch JSON from a URL.
    parameters:
      url:
        type: str
        description: Request URL.
    returns:
      type: dict[str, Any]
    """
    with urllib.request.urlopen(url, timeout=30) as response:
        return cast(dict[str, Any], json.loads(response.read().decode("utf-8")))


def from_crossref(
    *,
    query: str | None = None,
    filter: dict[str, Any] | None = None,
    limit: int = 100,
    rows: int = 100,
    mailto: str | None = None,
) -> BibliographicDataset:
    """
    title: Query Crossref works and return a normalized dataset.
    parameters:
      query:
        type: str | None
        description: Bibliographic search query.
      filter:
        type: dict[str, Any] | None
        description: Crossref filter mapping.
      limit:
        type: int
        description: Maximum records to retrieve.
      rows:
        type: int
        description: Page size.
      mailto:
        type: str | None
        description: Polite pool email address.
    returns:
      type: BibliographicDataset
    """
    output: list[dict[str, Any]] = []
    offset = 0
    rows = max(1, min(rows, 1000))
    while len(output) < limit:
        page_size = min(rows, limit - len(output))
        params: dict[str, str] = {"rows": str(page_size), "offset": str(offset)}
        if query:
            params["query"] = query
        if filter:
            params["filter"] = ",".join(
                f"{key}:{value}" for key, value in filter.items()
            )
        if mailto:
            params["mailto"] = mailto
        url = f"https://api.crossref.org/works?{urllib.parse.urlencode(params)}"
        payload = _request_json(url)
        items = (payload.get("message") or {}).get("items") or []
        if not isinstance(items, list) or not items:
            break
        output.extend(item for item in items if isinstance(item, dict))
        offset += len(items)
    return load(output, source="crossref")


__all__ = ["from_crossref", "normalize_crossref_work", "parse_crossref_date"]

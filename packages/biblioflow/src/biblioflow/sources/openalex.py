"""
title: OpenAlex source helpers.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, cast

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.load.dispatcher import load
from biblioflow.providers.adapters import (
    adapt_openalex,
    reconstruct_openalex_abstract,
)

__all__ = [
    "from_openalex",
    "normalize_openalex_work",
    "reconstruct_openalex_abstract",
]


def normalize_openalex_work(work: dict[str, Any]) -> dict[str, Any]:
    """
    title: Normalize one OpenAlex work.
    parameters:
      work:
        type: dict[str, Any]
        description: Raw OpenAlex work object.
    returns:
      type: dict[str, Any]
    """
    return adapt_openalex(work)


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


def from_openalex(
    *,
    search: str | None = None,
    filter: dict[str, Any] | None = None,
    sort: str | None = None,
    limit: int = 100,
    per_page: int = 200,
    mailto: str | None = None,
) -> BibliographicDataset:
    """
    title: Query OpenAlex works and return a normalized dataset.
    parameters:
      search:
        type: str | None
        description: Search query.
      filter:
        type: dict[str, Any] | None
        description: OpenAlex filter mapping.
      sort:
        type: str | None
        description: Sort expression.
      limit:
        type: int
        description: Maximum records to retrieve.
      per_page:
        type: int
        description: Page size.
      mailto:
        type: str | None
        description: Polite pool email address.
    returns:
      type: BibliographicDataset
    """
    rows: list[dict[str, Any]] = []
    cursor = "*"
    per_page = max(1, min(per_page, 200))
    while len(rows) < limit:
        page_size = min(per_page, limit - len(rows))
        query: dict[str, str] = {
            "per-page": str(page_size),
            "cursor": cursor,
        }
        if search:
            query["search"] = search
        if filter:
            query["filter"] = ",".join(
                f"{key}:{value}" for key, value in filter.items()
            )
        if sort:
            query["sort"] = sort
        if mailto:
            query["mailto"] = mailto
        url = f"https://api.openalex.org/works?{urllib.parse.urlencode(query)}"
        payload = _request_json(url)
        results = payload.get("results") or []
        if not isinstance(results, list) or not results:
            break
        rows.extend(result for result in results if isinstance(result, dict))
        next_cursor = (payload.get("meta") or {}).get("next_cursor")
        if not next_cursor:
            break
        cursor = str(next_cursor)
    return load(rows, source="openalex")

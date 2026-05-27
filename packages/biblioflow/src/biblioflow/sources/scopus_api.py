"""
title: Scopus API source helpers.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.exceptions import APIConfigurationError, OptionalDependencyError
from biblioflow.load.dispatcher import load
from biblioflow.providers.adapters import adapt_scopus_api


def normalize_scopus_api_result(result: dict[str, Any]) -> dict[str, Any]:
    """
    title: Normalize one Scopus API search result.
    parameters:
      result:
        type: dict[str, Any]
        description: Raw Scopus API search result.
    returns:
      type: dict[str, Any]
    """
    return adapt_scopus_api(result)


def from_scopus(
    *,
    query: str,
    limit: int = 100,
    refresh: bool = False,
    subscriber: bool = True,
) -> BibliographicDataset:
    """
    title: Query the Scopus API with pybliometrics.
    parameters:
      query:
        type: str
        description: Scopus query string.
      limit:
        type: int
        description: Maximum records to retrieve.
      refresh:
        type: bool
        description: Whether pybliometrics should refresh cached results.
      subscriber:
        type: bool
        description: Whether subscriber access should be requested.
    returns:
      type: BibliographicDataset
    """
    try:
        scopus_module = import_module("pybliometrics.scopus")
    except ImportError as exc:
        msg = "Install biblioflow[scopus] to use from_scopus()."
        raise OptionalDependencyError(msg) from exc

    try:
        search = scopus_module.ScopusSearch(
            query,
            refresh=refresh,
            subscriber=subscriber,
        )
    except Exception as exc:  # pragma: no cover - depends on local config
        msg = "Scopus API access requires pybliometrics configuration and an API key."
        raise APIConfigurationError(msg) from exc

    results = []
    for result in search.results or []:
        if hasattr(result, "_asdict"):
            results.append(result._asdict())
        elif isinstance(result, dict):
            results.append(result)
        else:
            results.append(dict(vars(result)))
        if len(results) >= limit:
            break
    return load(results, source="scopus_api")

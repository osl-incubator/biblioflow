"""
title: PubMed and PubMed Central source helpers.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import asdict, is_dataclass
from importlib import import_module
from typing import Any

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.exceptions import APIConfigurationError, OptionalDependencyError
from biblioflow.load.dispatcher import load
from biblioflow.providers.adapters import adapt_pmc, adapt_pubmed

_EMAIL_ENV_VARS = ("BIBLIOFLOW_NCBI_EMAIL", "NCBI_EMAIL", "ENTREZ_EMAIL")
_API_KEY_ENV_VARS = (
    "BIBLIOFLOW_NCBI_API_KEY",
    "NCBI_API_KEY",
    "ENTREZ_API_KEY",
)


def _env_value(names: tuple[str, ...]) -> str | None:
    """
    title: Return the first non-empty environment value.
    parameters:
      names:
        type: tuple[str, Ellipsis]
        description: Environment variable names.
    returns:
      type: str | None
    """
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _contact(email: str | None, api_key: str | None) -> tuple[str, str | None]:
    """
    title: Resolve NCBI contact details for API requests.
    parameters:
      email:
        type: str | None
        description: Contact email passed by the caller.
      api_key:
        type: str | None
        description: NCBI API key passed by the caller.
    returns:
      type: tuple[str, str | None]
    """
    resolved_email = (email or "").strip() or _env_value(_EMAIL_ENV_VARS)
    resolved_api_key = (api_key or "").strip() or _env_value(_API_KEY_ENV_VARS)
    if not resolved_email:
        msg = (
            "PubMed and PubMed Central API calls require a contact email. "
            "Pass email='you@example.org' or set BIBLIOFLOW_NCBI_EMAIL."
        )
        raise APIConfigurationError(msg)
    return resolved_email, resolved_api_key


def _pymedx_client(
    client_name: str,
    *,
    tool: str,
    email: str,
    api_key: str | None,
) -> Any:
    """
    title: Create a PyMedX client dynamically.
    parameters:
      client_name:
        type: str
        description: PyMedX client class name.
      tool:
        type: str
        description: NCBI tool name.
      email:
        type: str
        description: Contact email.
      api_key:
        type: str | None
        description: Optional NCBI API key.
    returns:
      type: Any
    """
    try:
        pymedx = import_module("pymedx")
    except ImportError as exc:
        msg = "Install pymedx to use PubMed and PubMed Central search."
        raise OptionalDependencyError(msg) from exc
    client_class = getattr(pymedx, client_name, None)
    if client_class is None:
        msg = f"pymedx does not expose a {client_name} client."
        raise APIConfigurationError(msg)
    return client_class(tool=tool, email=email, api_key=api_key or "")


def _coerce_value(value: Any) -> Any:
    """
    title: Coerce nested PyMedX values into plain Python containers.
    parameters:
      value:
        type: Any
        description: Raw value.
    returns:
      type: Any
    """
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(key): _coerce_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_coerce_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return _coerce_value(asdict(value))
    if hasattr(value, "_asdict"):
        return _coerce_value(value._asdict())
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _coerce_value(value.to_dict())
    if hasattr(value, "__dict__"):
        return {
            key: _coerce_value(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


def coerce_pymedx_article(article: Any) -> dict[str, Any]:
    """
    title: Convert a PyMedX article object to a dictionary.
    parameters:
      article:
        type: Any
        description: PyMedX article object or dictionary.
    returns:
      type: dict[str, Any]
    """
    value = _coerce_value(article)
    if isinstance(value, dict):
        return dict(value)
    return {"value": value}


def normalize_pubmed_article(article: Any) -> dict[str, Any]:
    """
    title: Normalize one PyMedX PubMed article.
    parameters:
      article:
        type: Any
        description: PyMedX article object or dictionary.
    returns:
      type: dict[str, Any]
    """
    record = coerce_pymedx_article(article)
    return adapt_pubmed(record)


def normalize_pmc_article(article: Any) -> dict[str, Any]:
    """
    title: Normalize one PyMedX PubMed Central article.
    parameters:
      article:
        type: Any
        description: PyMedX article object or dictionary.
    returns:
      type: dict[str, Any]
    """
    record = coerce_pymedx_article(article)
    return adapt_pmc(record)


def _limited(values: Iterable[Any], limit: int) -> list[Any]:
    """
    title: Materialize at most limit values.
    parameters:
      values:
        type: Iterable[Any]
        description: Values returned by PyMedX.
      limit:
        type: int
        description: Maximum values to keep.
    returns:
      type: list[Any]
    """
    if limit <= 0:
        return []
    output = []
    for value in values:
        output.append(value)
        if len(output) >= limit:
            break
    return output


def _search(
    *,
    client_name: str,
    source: str,
    query: str,
    limit: int,
    tool: str,
    email: str | None,
    api_key: str | None,
    keep_raw: bool,
    strict: bool,
    as_dataframe: bool,
    schema: str,
) -> BibliographicDataset | Any:
    """
    title: Execute a PyMedX search and load normalized records.
    parameters:
      client_name:
        type: str
        description: PyMedX client class name.
      source:
        type: str
        description: biblioflow source name.
      query:
        type: str
        description: Search query.
      limit:
        type: int
        description: Maximum number of records.
      tool:
        type: str
        description: NCBI tool name.
      email:
        type: str | None
        description: Contact email.
      api_key:
        type: str | None
        description: Optional NCBI API key.
      keep_raw:
        type: bool
        description: Whether raw payloads should be preserved.
      strict:
        type: bool
        description: Whether warnings should raise errors.
      as_dataframe:
        type: bool
        description: Whether to return a DataFrame-like object.
      schema:
        type: str
        description: Output schema.
    returns:
      type: BibliographicDataset | Any
    """
    resolved_email, resolved_api_key = _contact(email, api_key)
    client = _pymedx_client(
        client_name,
        tool=tool,
        email=resolved_email,
        api_key=resolved_api_key,
    )
    try:
        articles = client.query(query, max_results=limit)
    except Exception as exc:  # pragma: no cover - depends on network/client state
        msg = f"{client_name} search failed for query {query!r}."
        raise APIConfigurationError(msg) from exc
    normalizer = normalize_pmc_article if source == "pmc" else normalize_pubmed_article
    records = [normalizer(article) for article in _limited(articles or [], limit)]
    return load(
        records,
        source=source,
        keep_raw=keep_raw,
        strict=strict,
        as_dataframe=as_dataframe,
        schema=schema,
    )


def from_pubmed(
    *,
    query: str,
    limit: int = 100,
    tool: str = "biblioflow",
    email: str | None = None,
    api_key: str | None = None,
    keep_raw: bool = True,
    strict: bool = False,
    as_dataframe: bool = False,
    schema: str = "canonical",
) -> BibliographicDataset | Any:
    """
    title: Search PubMed and return a biblioflow dataset.
    parameters:
      query:
        type: str
        description: PubMed query string.
      limit:
        type: int
        description: Maximum number of records.
      tool:
        type: str
        description: NCBI tool name.
      email:
        type: str | None
        description: Contact email.
      api_key:
        type: str | None
        description: Optional NCBI API key.
      keep_raw:
        type: bool
        description: Whether raw payloads should be preserved.
      strict:
        type: bool
        description: Whether warnings should raise errors.
      as_dataframe:
        type: bool
        description: Whether to return a DataFrame-like object.
      schema:
        type: str
        description: Output schema.
    returns:
      type: BibliographicDataset | Any
    """
    return _search(
        client_name="PubMed",
        source="pubmed",
        query=query,
        limit=limit,
        tool=tool,
        email=email,
        api_key=api_key,
        keep_raw=keep_raw,
        strict=strict,
        as_dataframe=as_dataframe,
        schema=schema,
    )


def from_pubmed_central(
    *,
    query: str,
    limit: int = 100,
    tool: str = "biblioflow",
    email: str | None = None,
    api_key: str | None = None,
    keep_raw: bool = True,
    strict: bool = False,
    as_dataframe: bool = False,
    schema: str = "canonical",
) -> BibliographicDataset | Any:
    """
    title: Search PubMed Central and return a biblioflow dataset.
    parameters:
      query:
        type: str
        description: PubMed Central query string.
      limit:
        type: int
        description: Maximum number of records.
      tool:
        type: str
        description: NCBI tool name.
      email:
        type: str | None
        description: Contact email.
      api_key:
        type: str | None
        description: Optional NCBI API key.
      keep_raw:
        type: bool
        description: Whether raw payloads should be preserved.
      strict:
        type: bool
        description: Whether warnings should raise errors.
      as_dataframe:
        type: bool
        description: Whether to return a DataFrame-like object.
      schema:
        type: str
        description: Output schema.
    returns:
      type: BibliographicDataset | Any
    """
    return _search(
        client_name="PubMedCentral",
        source="pmc",
        query=query,
        limit=limit,
        tool=tool,
        email=email,
        api_key=api_key,
        keep_raw=keep_raw,
        strict=strict,
        as_dataframe=as_dataframe,
        schema=schema,
    )


def from_pmc(
    *,
    query: str,
    limit: int = 100,
    tool: str = "biblioflow",
    email: str | None = None,
    api_key: str | None = None,
    keep_raw: bool = True,
    strict: bool = False,
    as_dataframe: bool = False,
    schema: str = "canonical",
) -> BibliographicDataset | Any:
    """
    title: Search PubMed Central using the short PMC alias.
    parameters:
      query:
        type: str
        description: PubMed Central query string.
      limit:
        type: int
        description: Maximum number of records.
      tool:
        type: str
        description: NCBI tool name.
      email:
        type: str | None
        description: Contact email.
      api_key:
        type: str | None
        description: Optional NCBI API key.
      keep_raw:
        type: bool
        description: Whether raw payloads should be preserved.
      strict:
        type: bool
        description: Whether warnings should raise errors.
      as_dataframe:
        type: bool
        description: Whether to return a DataFrame-like object.
      schema:
        type: str
        description: Output schema.
    returns:
      type: BibliographicDataset | Any
    """
    return from_pubmed_central(
        query=query,
        limit=limit,
        tool=tool,
        email=email,
        api_key=api_key,
        keep_raw=keep_raw,
        strict=strict,
        as_dataframe=as_dataframe,
        schema=schema,
    )

"""
title: PubMed and PubMed Central source helpers.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from dataclasses import asdict, is_dataclass
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
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
    if hasattr(value, "toDict") and callable(value.toDict):
        return _coerce_value(value.toDict())
    slots = getattr(value, "__slots__", None)
    if isinstance(slots, tuple | list):
        return {
            str(key): _coerce_value(getattr(value, key))
            for key in slots
            if isinstance(key, str) and hasattr(value, key)
        }
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


def _int_or_none(value: Any) -> int | None:
    """
    title: Convert a value to an integer when possible.
    parameters:
      value:
        type: Any
        description: Raw value.
    returns:
      type: int | None
    """
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _pymedx_version() -> str | None:
    """
    title: Return the installed PyMedX version when available.
    returns:
      type: str | None
    """
    try:
        return version("pymedx")
    except PackageNotFoundError:  # pragma: no cover - guarded by import
        return None


def _search_response_summary(response: dict[str, Any]) -> dict[str, Any]:
    """
    title: Extract safe NCBI eSearch metadata from a PyMedX response.
    parameters:
      response:
        type: dict[str, Any]
        description: Raw eSearch response.
    returns:
      type: dict[str, Any]
    """
    esearch = response.get("esearchresult")
    if not isinstance(esearch, dict):
        return {}
    ids = [str(item) for item in esearch.get("idlist") or [] if item]
    summary: dict[str, Any] = {
        "total_results": _int_or_none(esearch.get("count")),
        "page_size": _int_or_none(esearch.get("retmax")),
        "page_start": _int_or_none(esearch.get("retstart")),
        "retrieved_id_count": len(ids),
    }
    if ids:
        summary["retrieved_ids"] = ids[:1000]
        summary["retrieved_ids_truncated"] = len(ids) > 1000
    query_translation = esearch.get("querytranslation")
    if query_translation:
        summary["query_translation"] = str(query_translation)
    return {key: value for key, value in summary.items() if value is not None}


def _replace_instance_method(
    instance: Any,
    name: str,
    replacement: Callable[..., Any],
) -> Callable[[], None]:
    """
    title: Replace an instance method and return a restore callback.
    parameters:
      instance:
        type: Any
        description: Object whose method should be replaced.
      name:
        type: str
        description: Method name.
      replacement:
        type: Callable[Ellipsis, Any]
        description: Replacement callable.
    returns:
      type: Callable[[], None]
    """
    original_dict = getattr(instance, "__dict__", {})
    had_instance_value = isinstance(original_dict, dict) and name in original_dict
    original_value = original_dict.get(name) if had_instance_value else None
    setattr(instance, name, replacement)

    def restore() -> None:
        """
        title: Restore the original instance method.
        """
        if had_instance_value:
            setattr(instance, name, original_value)
        else:
            try:
                delattr(instance, name)
            except AttributeError:
                pass

    return restore


def _capture_search_metadata(client: Any) -> tuple[dict[str, Any], Callable[[], None]]:
    """
    title: Capture safe PyMedX search metadata while a query executes.
    summary: |-
      PyMedX exposes useful NCBI search metadata through its public
      ``getTotalResultsCount`` helper and, internally, through eSearch
      responses. This function records that metadata without storing contact
      email addresses or API keys.
    parameters:
      client:
        type: Any
        description: PyMedX client instance.
    returns:
      type: tuple[dict[str, Any], Callable[[], None]]
    """
    state: dict[str, Any] = {
        "search_responses": [],
        "total_results": None,
        "metadata_errors": [],
    }
    restore_callbacks: list[Callable[[], None]] = []

    get_total = getattr(client, "getTotalResultsCount", None)
    if callable(get_total):

        def recording_total_count(*args: Any, **kwargs: Any) -> Any:
            """
            title: Record total result count returned by PyMedX.
            parameters:
              args:
                type: Any
                description: Positional arguments passed to PyMedX.
                variadic: positional
              kwargs:
                type: Any
                description: Keyword arguments passed to PyMedX.
                variadic: keyword
            returns:
              type: Any
            """
            total = get_total(*args, **kwargs)
            state["total_results"] = _int_or_none(total)
            return total

        try:
            restore_callbacks.append(
                _replace_instance_method(
                    client,
                    "getTotalResultsCount",
                    recording_total_count,
                )
            )
        except (AttributeError, TypeError):  # pragma: no cover - client-specific
            pass

    get_request = getattr(client, "_get", None)
    if callable(get_request):

        def recording_get(*args: Any, **kwargs: Any) -> Any:
            """
            title: Record NCBI eSearch response metadata returned by PyMedX.
            parameters:
              args:
                type: Any
                description: Positional arguments passed to PyMedX.
                variadic: positional
              kwargs:
                type: Any
                description: Keyword arguments passed to PyMedX.
                variadic: keyword
            returns:
              type: Any
            """
            response = get_request(*args, **kwargs)
            url = kwargs.get("url")
            if url is None and args:
                url = args[0]
            if (
                isinstance(url, str)
                and "esearch.fcgi" in url
                and isinstance(response, dict)
            ):
                summary = _search_response_summary(response)
                if summary:
                    cast_responses = state["search_responses"]
                    if isinstance(cast_responses, list):
                        cast_responses.append(summary)
            return response

        try:
            restore_callbacks.append(
                _replace_instance_method(client, "_get", recording_get)
            )
        except (AttributeError, TypeError):  # pragma: no cover - client-specific
            pass

    def restore() -> None:
        """
        title: Restore all patched PyMedX metadata methods.
        """
        for callback in reversed(restore_callbacks):
            callback()

    return state, restore


def _ensure_total_results(
    client: Any,
    query: str,
    state: dict[str, Any],
) -> None:
    """
    title: >-
      Populate total result count when PyMedX did not expose it during query.
    parameters:
      client:
        type: Any
        description: PyMedX client.
      query:
        type: str
        description: Search query.
      state:
        type: dict[str, Any]
        description: Captured metadata state.
    """
    if state.get("total_results") is not None:
        return
    get_total = getattr(client, "getTotalResultsCount", None)
    if not callable(get_total):
        return
    try:
        total = get_total(query)
    except Exception:  # pragma: no cover - depends on network/client state
        errors = state.get("metadata_errors")
        if isinstance(errors, list):
            errors.append("Unable to retrieve total result count.")
        return
    state["total_results"] = _int_or_none(total)


def _merged_search_response_metadata(state: dict[str, Any]) -> dict[str, Any]:
    """
    title: Merge captured eSearch response summaries.
    parameters:
      state:
        type: dict[str, Any]
        description: Captured metadata state.
    returns:
      type: dict[str, Any]
    """
    responses = state.get("search_responses")
    if not isinstance(responses, list):
        responses = []

    total_results = state.get("total_results")
    if total_results is None:
        for response in responses:
            if isinstance(response, dict) and response.get("total_results") is not None:
                total_results = response.get("total_results")
                break

    retrieved_ids: list[str] = []
    query_translation: str | None = None
    for response in responses:
        if not isinstance(response, dict):
            continue
        if query_translation is None and response.get("query_translation"):
            query_translation = str(response["query_translation"])
        for identifier in response.get("retrieved_ids") or []:
            identifier_text = str(identifier)
            if identifier_text and identifier_text not in retrieved_ids:
                retrieved_ids.append(identifier_text)

    metadata: dict[str, Any] = {
        "total_results": _int_or_none(total_results),
        "search_response_count": len(responses),
    }
    if query_translation:
        metadata["query_translation"] = query_translation
    if retrieved_ids:
        metadata["retrieved_id_count"] = len(retrieved_ids)
        metadata["retrieved_ids"] = retrieved_ids[:1000]
        metadata["retrieved_ids_truncated"] = len(retrieved_ids) > 1000
    errors = state.get("metadata_errors")
    if isinstance(errors, list) and errors:
        metadata["metadata_errors"] = [str(error) for error in errors]
    return {key: value for key, value in metadata.items() if value is not None}


def _dataset_search_metadata(
    *,
    client: Any,
    client_name: str,
    source: str,
    query: str,
    limit: int,
    returned_count: int,
    tool: str,
    resolved_email: str,
    resolved_api_key: str | None,
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    title: Build safe PubMed-family dataset metadata.
    parameters:
      client:
        type: Any
        description: PyMedX client instance.
      client_name:
        type: str
        description: PyMedX client class name.
      source:
        type: str
        description: Normalized provider name.
      query:
        type: str
        description: Search query.
      limit:
        type: int
        description: Requested record limit.
      returned_count:
        type: int
        description: Number of normalized records returned.
      tool:
        type: str
        description: NCBI tool name.
      resolved_email:
        type: str
        description: Resolved contact email.
      resolved_api_key:
        type: str | None
        description: Resolved NCBI API key.
      state:
        type: dict[str, Any]
        description: Captured metadata state.
    returns:
      type: dict[str, Any]
    """
    parameters = getattr(client, "parameters", {})
    database = parameters.get("db") if isinstance(parameters, dict) else None
    rate_limit = _int_or_none(getattr(client, "_rateLimit", None))
    metadata = {
        "source": "pymedx",
        "provider": source,
        "format": "api",
        "remote_source": source,
        "query": query,
        "requested_limit": limit,
        "returned_count": returned_count,
        "client": client_name,
        "client_package": "pymedx",
        "client_version": _pymedx_version(),
        "ncbi_database": database,
        "tool": tool,
        "email_provided": bool(resolved_email),
        "api_key_present": bool(resolved_api_key),
        "rate_limit_per_second": rate_limit,
        **_merged_search_response_metadata(state),
    }
    return {key: value for key, value in metadata.items() if value is not None}


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
    metadata_state, restore_metadata_capture = _capture_search_metadata(client)
    try:
        articles = client.query(query, max_results=limit)
        materialized_articles = _limited(articles or [], limit)
        _ensure_total_results(client, query, metadata_state)
    except Exception as exc:  # pragma: no cover - depends on network/client state
        msg = f"{client_name} search failed for query {query!r}."
        raise APIConfigurationError(msg) from exc
    finally:
        restore_metadata_capture()
    normalizer = normalize_pmc_article if source == "pmc" else normalize_pubmed_article
    records = [normalizer(article) for article in materialized_articles]
    dataset = load(
        records,
        source=source,
        keep_raw=keep_raw,
        strict=strict,
        as_dataframe=False,
        schema=schema,
    )
    if isinstance(dataset, BibliographicDataset):
        dataset.metadata.update(
            _dataset_search_metadata(
                client=client,
                client_name=client_name,
                source=source,
                query=query,
                limit=limit,
                returned_count=len(records),
                tool=tool,
                resolved_email=resolved_email,
                resolved_api_key=resolved_api_key,
                state=metadata_state,
            )
        )
        return dataset.to_dataframe(schema=schema) if as_dataframe else dataset
    return dataset


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

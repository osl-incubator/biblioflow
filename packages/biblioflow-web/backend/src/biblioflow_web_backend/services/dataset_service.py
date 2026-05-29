"""Dataset orchestration service backed by the biblioflow library."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.core.json import to_jsonable
from biblioflow_web_backend.services.file_store import FileStore
from biblioflow_web_backend.services.project_store import ProjectStore, utc_now


class DatasetService:
    """Load, persist, and retrieve normalized biblioflow datasets."""

    def __init__(self, projects: ProjectStore, files: FileStore) -> None:
        self.projects = projects
        self.files = files

    def load_dataset(
        self,
        project_id: str,
        upload_ids: list[str] | None = None,
        *,
        provider: str = "auto",
        format: str = "auto",
    ) -> dict[str, Any]:
        """Load one or more uploads through biblioflow and persist a dataset."""
        import biblioflow as bf

        uploads = self.files.list_uploads(project_id)
        selected_ids = upload_ids or [str(upload["upload_id"]) for upload in uploads]
        if not selected_ids:
            raise ApiError("no_uploads", "No uploads are available for loading.", 400)

        records: list[dict[str, Any]] = []
        load_metadata: list[dict[str, Any]] = []
        warnings: list[dict[str, object]] = []
        for upload_id in selected_ids:
            path = self.files.upload_path(project_id, upload_id)
            dataset = bf.load(path, provider=provider, format=format)
            records.extend(dataset.to_records())
            load_metadata.append({"upload_id": upload_id, **dict(dataset.metadata)})
            warnings.extend(dataset.warning_dicts())

        combined = bf.load(records, provider="generic", format="records")
        return self._persist_dataset(
            project_id,
            combined,
            upload_ids=selected_ids,
            metadata={"sources": load_metadata},
            warnings=warnings or combined.warning_dicts(),
        )

    def import_remote_source(
        self,
        project_id: str,
        *,
        source: str,
        query: str,
        limit: int,
        email: str | None,
        api_key: str | None,
        tool: str,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Import PubMed or PMC records and persist them as a dataset."""
        dataset, normalized_source, label, search_query, safe_tool = (
            self._fetch_remote_source_dataset(
                source=source,
                query=query,
                limit=limit,
                email=email,
                api_key=api_key,
                tool=tool,
            )
        )
        dataset_name = (
            name.strip() if name and name.strip() else f"{label}: {search_query}"
        )
        return self._persist_dataset(
            project_id,
            dataset,
            upload_ids=[],
            metadata={
                "imported_from": "remote_source",
                "remote_source": normalized_source,
                "source_label": label,
                "query": search_query,
                "limit": limit,
                "tool": safe_tool,
                "name": dataset_name,
            },
        )

    def search_remote_source(
        self,
        project_id: str,
        *,
        source: str,
        query: str,
        limit: int,
        email: str | None,
        api_key: str | None,
        tool: str,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Search PubMed or PMC and persist records as screening candidates."""
        dataset, normalized_source, label, search_query, safe_tool = (
            self._fetch_remote_source_dataset(
                source=source,
                query=query,
                limit=limit,
                email=email,
                api_key=api_key,
                tool=tool,
            )
        )
        created_at = utc_now()
        search_id = uuid4().hex
        candidates = [
            _candidate_from_record(record, created_at=created_at)
            for record in _dataset_records(dataset)
        ]
        search_name = (
            name.strip() if name and name.strip() else f"{label}: {search_query}"
        )
        metadata = {
            **_metadata_without_secrets(dict(getattr(dataset, "metadata", {}))),
            "imported_from": "remote_source_screening",
            "remote_source": normalized_source,
            "source_label": label,
            "query": search_query,
            "limit": limit,
            "tool": safe_tool,
            "name": search_name,
            "records": len(candidates),
            "status_counts": _candidate_status_counts(candidates),
        }
        payload = {
            "search_id": search_id,
            "created_at": created_at,
            "updated_at": created_at,
            "source": normalized_source,
            "source_label": label,
            "query": search_query,
            "limit": limit,
            "name": search_name,
            "records": len(candidates),
            "status_counts": _candidate_status_counts(candidates),
            "candidates": candidates,
            "warnings": _dataset_warnings(dataset),
            "metadata": metadata,
        }
        self._write_remote_search(project_id, search_id, payload)
        self._upsert_remote_search_index(project_id, payload)
        return payload

    def list_remote_searches(self, project_id: str) -> list[dict[str, Any]]:
        """List persisted remote source screening searches for a project."""
        project = self.projects.get_project(project_id)
        return [dict(item) for item in project.get("remote_searches", [])]

    def get_remote_search(self, project_id: str, search_id: str) -> dict[str, Any]:
        """Return a persisted remote source screening search."""
        path = self._remote_search_path(project_id, search_id)
        if not path.exists():
            raise ApiError(
                "remote_search_not_found", "Remote search was not found.", 404
            )
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))

    def update_remote_candidates(
        self,
        project_id: str,
        search_id: str,
        *,
        candidate_ids: list[str],
        status: str,
    ) -> dict[str, Any]:
        """Apply a screening status to one or more remote-search candidates."""
        candidate_ids_set = {
            candidate_id for candidate_id in candidate_ids if candidate_id
        }
        if not candidate_ids_set:
            raise ApiError(
                "no_candidates_selected",
                "Select at least one candidate before applying a decision.",
                400,
            )
        if status not in {"candidate", "selected", "excluded", "duplicate"}:
            raise ApiError(
                "unsupported_candidate_status",
                f"Unsupported candidate status: {status}.",
                400,
            )
        payload = self.get_remote_search(project_id, search_id)
        candidates = _search_candidates(payload)
        existing_ids = {str(candidate["candidate_id"]) for candidate in candidates}
        missing = sorted(candidate_ids_set - existing_ids)
        if missing:
            raise ApiError(
                "candidate_not_found",
                "One or more candidates were not found.",
                404,
                details={"candidate_ids": missing},
            )
        updated_at = utc_now()
        for candidate in candidates:
            if str(candidate["candidate_id"]) in candidate_ids_set:
                candidate["status"] = status
                candidate["updated_at"] = updated_at
        return self._save_remote_search(project_id, payload, updated_at=updated_at)

    def promote_remote_candidates(
        self,
        project_id: str,
        search_id: str,
        *,
        candidate_ids: list[str] | None = None,
        include_statuses: list[str] | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Promote screened candidates into the active project dataset."""
        import biblioflow as bf

        payload = self.get_remote_search(project_id, search_id)
        candidates = _search_candidates(payload)
        candidate_ids_set = (
            {candidate_id for candidate_id in candidate_ids if candidate_id}
            if candidate_ids is not None
            else None
        )
        if candidate_ids is not None and not candidate_ids_set:
            raise ApiError(
                "no_candidates_selected",
                "Select at least one candidate before creating a dataset.",
                400,
            )
        if candidate_ids_set is not None:
            existing_ids = {str(candidate["candidate_id"]) for candidate in candidates}
            missing = sorted(candidate_ids_set - existing_ids)
            if missing:
                raise ApiError(
                    "candidate_not_found",
                    "One or more candidates were not found.",
                    404,
                    details={"candidate_ids": missing},
                )
        status_set = set(include_statuses or ["selected"])
        if candidate_ids_set is not None:
            selected_candidates = [
                candidate
                for candidate in candidates
                if str(candidate["candidate_id"]) in candidate_ids_set
            ]
        else:
            selected_candidates = [
                candidate
                for candidate in candidates
                if str(candidate.get("status")) in status_set
            ]
        if not selected_candidates:
            raise ApiError(
                "no_candidates_selected",
                "No remote-source candidates match the selected screening decision.",
                400,
            )
        records = [dict(candidate["record"]) for candidate in selected_candidates]
        dataset = bf.load(records, source=str(payload["source"]))
        dataset_name = (
            name.strip()
            if name and name.strip()
            else f"{payload['name']} — screened records"
        )
        dataset_payload = self._persist_dataset(
            project_id,
            dataset,
            upload_ids=[],
            metadata={
                "imported_from": "remote_source_screening",
                "remote_search_id": search_id,
                "remote_source": payload["source"],
                "source_label": payload["source_label"],
                "query": payload["query"],
                "limit": payload["limit"],
                "name": dataset_name,
                "candidate_count": len(candidates),
                "selected_count": len(selected_candidates),
            },
        )
        updated_at = utc_now()
        promoted_ids = {
            str(candidate["candidate_id"]) for candidate in selected_candidates
        }
        for candidate in candidates:
            if str(candidate["candidate_id"]) in promoted_ids:
                candidate["status"] = "imported"
                candidate["updated_at"] = updated_at
                candidate["imported_dataset_id"] = dataset_payload["dataset_id"]
        self._save_remote_search(project_id, payload, updated_at=updated_at)
        return dataset_payload

    def _fetch_remote_source_dataset(
        self,
        *,
        source: str,
        query: str,
        limit: int,
        email: str | None,
        api_key: str | None,
        tool: str,
    ) -> tuple[Any, str, str, str, str]:
        """Search a remote source and return a normalized biblioflow dataset."""
        import biblioflow as bf
        from biblioflow.exceptions import (
            APIConfigurationError,
            BiblioFlowError,
            OptionalDependencyError,
        )

        normalized_source = _normalize_remote_source(source)
        search_query = query.strip()
        if not search_query:
            raise ApiError(
                "empty_query",
                "Provide a PubMed or PubMed Central query before importing.",
                400,
            )
        safe_tool = tool.strip() or "biblioflow-web"
        email_value = _optional_string(email)
        api_key_value = _optional_string(api_key)

        try:
            if normalized_source == "pubmed":
                dataset = bf.from_pubmed(
                    query=search_query,
                    limit=limit,
                    tool=safe_tool,
                    email=email_value,
                    api_key=api_key_value,
                )
            else:
                dataset = bf.from_pmc(
                    query=search_query,
                    limit=limit,
                    tool=safe_tool,
                    email=email_value,
                    api_key=api_key_value,
                )
        except APIConfigurationError as exc:
            message = _sanitize_error(str(exc), api_key)
            status_code = 502 if "search failed" in message.lower() else 400
            raise ApiError(
                "remote_source_configuration",
                message,
                status_code,
                details={"source": normalized_source},
            ) from exc
        except OptionalDependencyError as exc:
            raise ApiError(
                "remote_source_dependency_missing",
                _sanitize_error(str(exc), api_key),
                503,
                details={"source": normalized_source},
            ) from exc
        except BiblioFlowError as exc:
            raise ApiError(
                "remote_source_failed",
                _sanitize_error(str(exc), api_key),
                502,
                details={"source": normalized_source},
            ) from exc

        label = "PubMed" if normalized_source == "pubmed" else "PubMed Central"
        return dataset, normalized_source, label, search_query, safe_tool

    def list_datasets(self, project_id: str) -> list[dict[str, Any]]:
        """List dataset metadata for a project."""
        project = self.projects.get_project(project_id)
        return [dict(dataset) for dataset in project.get("datasets", [])]

    def get_dataset_payload(self, project_id: str, dataset_id: str) -> dict[str, Any]:
        """Return a persisted dataset payload."""
        path = self._dataset_path(project_id, dataset_id)
        if not path.exists():
            raise ApiError("dataset_not_found", "Dataset was not found.", 404)
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))

    def get_biblioflow_dataset(self, project_id: str, dataset_id: str) -> Any:
        """Return a persisted dataset as a biblioflow dataset."""
        import biblioflow as bf

        payload = self.get_dataset_payload(project_id, dataset_id)
        dataset = bf.load(payload["records"], provider="generic", format="records")
        dataset.metadata.update(payload.get("metadata") or {})
        return dataset

    def summarize(self, project_id: str, dataset_id: str) -> dict[str, Any]:
        """Return a high-level dataset summary."""
        import biblioflow as bf

        return bf.summarize_dataset(
            self.get_biblioflow_dataset(project_id, dataset_id)
        ).to_dict()

    def validation(self, project_id: str, dataset_id: str) -> dict[str, Any]:
        """Return validation warnings and metadata for a dataset."""
        payload = self.get_dataset_payload(project_id, dataset_id)
        return {
            "dataset_id": dataset_id,
            "records": len(payload.get("records", [])),
            "warnings": payload.get("warnings", []),
            "metadata": payload.get("metadata", {}),
        }

    def filter_options(self, project_id: str, dataset_id: str) -> dict[str, Any]:
        """Return available filter values for a dataset."""
        import biblioflow as bf

        return bf.available_filter_values(
            self.get_biblioflow_dataset(project_id, dataset_id)
        ).to_dict()

    def filter_preview(
        self, project_id: str, dataset_id: str, spec: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Return a filter preview without persisting a new dataset."""
        import biblioflow as bf

        return bf.filter_dataset(
            self.get_biblioflow_dataset(project_id, dataset_id), spec
        ).to_dict()

    def _persist_dataset(
        self,
        project_id: str,
        dataset: Any,
        *,
        upload_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        warnings: list[dict[str, object]] | None = None,
    ) -> dict[str, Any]:
        """Persist a normalized biblioflow dataset and make it active."""
        records = _dataset_records(dataset)
        dataset_id = uuid4().hex
        created_at = utc_now()
        dataset_metadata = {
            **_metadata_without_secrets(dict(getattr(dataset, "metadata", {}))),
            **_metadata_without_secrets(metadata or {}),
            "records": len(records),
        }
        payload = {
            "dataset_id": dataset_id,
            "created_at": created_at,
            "upload_ids": upload_ids or [],
            "records": records,
            "warnings": warnings
            if warnings is not None
            else _dataset_warnings(dataset),
            "metadata": dataset_metadata,
        }
        self._write_dataset(project_id, dataset_id, payload)
        project = self.projects.get_project(project_id)
        project.setdefault("datasets", []).append(
            {
                "dataset_id": dataset_id,
                "created_at": created_at,
                "records": len(records),
                "upload_ids": upload_ids or [],
                "metadata": dataset_metadata,
            }
        )
        project["active_dataset_id"] = dataset_id
        self.projects.save_project(project)
        return payload

    def _dataset_path(self, project_id: str, dataset_id: str) -> Path:
        return self.projects.datasets_dir(project_id) / f"{dataset_id}.json"

    def _remote_search_path(self, project_id: str, search_id: str) -> Path:
        return self.projects.remote_searches_dir(project_id) / f"{search_id}.json"

    def _write_dataset(
        self, project_id: str, dataset_id: str, payload: dict[str, Any]
    ) -> None:
        self._dataset_path(project_id, dataset_id).write_text(
            json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _write_remote_search(
        self, project_id: str, search_id: str, payload: dict[str, Any]
    ) -> None:
        self._remote_search_path(project_id, search_id).write_text(
            json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _save_remote_search(
        self, project_id: str, payload: dict[str, Any], *, updated_at: str
    ) -> dict[str, Any]:
        """Persist an updated remote search payload and refresh its index row."""
        payload["updated_at"] = updated_at
        status_counts = _candidate_status_counts(_search_candidates(payload))
        payload["records"] = len(_search_candidates(payload))
        payload["status_counts"] = status_counts
        payload["metadata"]["status_counts"] = status_counts
        self._write_remote_search(project_id, str(payload["search_id"]), payload)
        self._upsert_remote_search_index(project_id, payload)
        return payload

    def _upsert_remote_search_index(
        self, project_id: str, payload: dict[str, Any]
    ) -> None:
        """Create or replace a compact remote search row on project metadata."""
        project = self.projects.get_project(project_id)
        search_id = str(payload["search_id"])
        existing = [
            dict(item)
            for item in project.get("remote_searches", [])
            if str(item.get("search_id")) != search_id
        ]
        existing.append(_remote_search_list_item(payload))
        project["remote_searches"] = existing
        self.projects.save_project(project)


def _normalize_remote_source(source: str) -> str:
    """Normalize remote-source aliases accepted by the API."""
    normalized = source.strip().casefold().replace("-", "_")
    if normalized == "pubmed":
        return "pubmed"
    if normalized in {"pmc", "pubmed_central", "pubmedcentral"}:
        return "pmc"
    raise ApiError(
        "unsupported_remote_source",
        f"Unsupported remote source: {source}.",
        400,
    )


def _optional_string(value: str | None) -> str | None:
    """Return a stripped string, or None when it is empty."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _sanitize_error(message: str, secret: str | None) -> str:
    """Remove a submitted API key from an error message defensively."""
    cleaned = message
    if secret and secret.strip():
        cleaned = cleaned.replace(secret.strip(), "<redacted>")
    return cleaned


def _metadata_without_secrets(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return metadata without known secret-bearing keys."""
    secret_keys = {"api_key", "apikey", "ncbi_api_key", "ncbiapikey"}

    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: clean(item)
                for key, item in value.items()
                if str(key).replace("-", "_").casefold() not in secret_keys
            }
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value

    cleaned = clean(metadata)
    return cast(dict[str, Any], cleaned) if isinstance(cleaned, dict) else {}


def _dataset_records(dataset: Any) -> list[dict[str, Any]]:
    """Return JSON-ready records from a biblioflow dataset-like object."""
    return [dict(record) for record in dataset.to_records()]


def _dataset_warnings(dataset: Any) -> list[dict[str, object]]:
    """Return JSON-ready warnings from a biblioflow dataset-like object."""
    if hasattr(dataset, "warning_dicts"):
        return [dict(warning) for warning in dataset.warning_dicts()]
    return []


def _candidate_from_record(
    record: dict[str, Any], *, created_at: str
) -> dict[str, Any]:
    """Return a persisted screening candidate for one normalized record."""
    return {
        "candidate_id": uuid4().hex,
        "status": "candidate",
        "created_at": created_at,
        "updated_at": created_at,
        "record": record,
        "identifiers": _record_identifiers(record),
        "title": _record_title(record),
        "year": _record_year(record),
        "authors": _record_authors(record),
        "source_title": _record_source_title(record),
    }


def _search_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return candidate dictionaries from a remote-search payload."""
    raw_candidates = payload.get("candidates", [])
    if not isinstance(raw_candidates, list):
        return []
    return [candidate for candidate in raw_candidates if isinstance(candidate, dict)]


def _candidate_status_counts(candidates: list[dict[str, Any]]) -> dict[str, int]:
    """Return counts grouped by screening candidate status."""
    counts: dict[str, int] = {}
    for candidate in candidates:
        status = str(candidate.get("status") or "candidate")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _remote_search_list_item(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a compact remote-search row for project metadata."""
    candidates = _search_candidates(payload)
    return {
        "search_id": payload["search_id"],
        "created_at": payload["created_at"],
        "updated_at": payload["updated_at"],
        "source": payload["source"],
        "source_label": payload["source_label"],
        "query": payload["query"],
        "limit": payload["limit"],
        "name": payload["name"],
        "records": len(candidates),
        "status_counts": _candidate_status_counts(candidates),
        "metadata": {
            key: value
            for key, value in dict(payload.get("metadata", {})).items()
            if key not in {"api_key", "apikey", "apiKey"}
        },
    }


def _record_identifiers(record: dict[str, Any]) -> dict[str, str]:
    """Return stable bibliographic identifiers from a normalized record."""
    identifiers = {}
    for key in ["pmid", "pmcid", "doi", "source_id"]:
        value = _record_string(record.get(key))
        if value:
            identifiers[key] = value
    return identifiers


def _record_title(record: dict[str, Any]) -> str:
    """Return a display title for a candidate record."""
    return _record_string(record.get("title")) or "Untitled record"


def _record_source_title(record: dict[str, Any]) -> str | None:
    """Return a candidate journal or source title."""
    return _record_string(record.get("source_title") or record.get("journal"))


def _record_year(record: dict[str, Any]) -> int | None:
    """Return a display publication year for a candidate record."""
    raw_year = record.get("publication_year", record.get("year"))
    if isinstance(raw_year, int):
        return raw_year
    if isinstance(raw_year, str) and raw_year.strip().isdigit():
        return int(raw_year.strip())
    return None


def _record_authors(record: dict[str, Any]) -> list[str]:
    """Return display authors for a candidate record."""
    raw_authors = record.get("authors") or record.get("authors_raw") or []
    if isinstance(raw_authors, str):
        return [raw_authors]
    if isinstance(raw_authors, list | tuple):
        return [str(author) for author in raw_authors if str(author).strip()][:8]
    return []


def _record_string(value: Any) -> str | None:
    """Return a stripped string value when available."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, int | float):
        return str(value)
    return None

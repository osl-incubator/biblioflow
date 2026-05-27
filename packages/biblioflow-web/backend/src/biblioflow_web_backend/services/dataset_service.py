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

    def _write_dataset(
        self, project_id: str, dataset_id: str, payload: dict[str, Any]
    ) -> None:
        self._dataset_path(project_id, dataset_id).write_text(
            json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


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
    secret_keys = {"api_key", "apikey", "apiKey", "ncbi_api_key", "ncbiApiKey"}
    return {key: value for key, value in metadata.items() if key not in secret_keys}


def _dataset_records(dataset: Any) -> list[dict[str, Any]]:
    """Return JSON-ready records from a biblioflow dataset-like object."""
    return [dict(record) for record in dataset.to_records()]


def _dataset_warnings(dataset: Any) -> list[dict[str, object]]:
    """Return JSON-ready warnings from a biblioflow dataset-like object."""
    if hasattr(dataset, "warning_dicts"):
        return [dict(warning) for warning in dataset.warning_dicts()]
    return []

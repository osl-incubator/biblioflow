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
        dataset_id = uuid4().hex
        payload = {
            "dataset_id": dataset_id,
            "created_at": utc_now(),
            "upload_ids": selected_ids,
            "records": combined.to_records(),
            "warnings": warnings or combined.warning_dicts(),
            "metadata": {
                **dict(combined.metadata),
                "sources": load_metadata,
                "records": len(combined),
            },
        }
        self._write_dataset(project_id, dataset_id, payload)
        project = self.projects.get_project(project_id)
        project.setdefault("datasets", []).append(
            {
                "dataset_id": dataset_id,
                "created_at": payload["created_at"],
                "records": len(combined),
                "upload_ids": selected_ids,
            }
        )
        project["active_dataset_id"] = dataset_id
        self.projects.save_project(project)
        return payload

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

    def _dataset_path(self, project_id: str, dataset_id: str) -> Path:
        return self.projects.datasets_dir(project_id) / f"{dataset_id}.json"

    def _write_dataset(
        self, project_id: str, dataset_id: str, payload: dict[str, Any]
    ) -> None:
        self._dataset_path(project_id, dataset_id).write_text(
            json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

"""In-kernel state model for biblioflow-nb."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class NotebookUpload:
    """Uploaded or selected source file metadata."""

    name: str
    path: Path | None = None
    size: int | None = None
    content_type: str | None = None
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable upload record."""
        return {
            "name": self.name,
            "path": str(self.path) if self.path else None,
            "size": self.size,
            "content_type": self.content_type,
            "created_at": self.created_at,
        }


@dataclass
class NotebookExport:
    """Exported notebook artifact metadata."""

    name: str
    path: Path
    kind: str
    format: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable export record."""
        return {
            "name": self.name,
            "path": str(self.path),
            "kind": self.kind,
            "format": self.format,
            "created_at": self.created_at,
        }


@dataclass
class NotebookSession:
    """Mutable in-kernel notebook app state."""

    session_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    uploads: list[NotebookUpload] = field(default_factory=list)
    active_dataset: Any | None = None
    active_dataset_name: str | None = None
    active_filters: Any | None = None
    filtered_dataset: Any | None = None
    analysis_cache: dict[str, Any] = field(default_factory=dict)
    matrix_cache: dict[str, Any] = field(default_factory=dict)
    network_cache: dict[str, Any] = field(default_factory=dict)
    exports: list[NotebookExport] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    screening_runs: list[dict[str, Any]] = field(default_factory=list)
    active_screening_run_id: str | None = None

    @property
    def dataset(self) -> Any | None:
        """Return filtered dataset when available, else the active dataset."""
        return self.filtered_dataset or self.active_dataset

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = utc_now()

    def set_dataset(self, dataset: Any, *, name: str | None = None) -> None:
        """Set the active dataset and reset derived state."""
        self.active_dataset = dataset
        self.active_dataset_name = name
        self.filtered_dataset = None
        self.analysis_cache.clear()
        self.matrix_cache.clear()
        self.network_cache.clear()
        self.warnings = _warning_dicts(dataset)
        self.touch()

    def add_upload(self, upload: NotebookUpload) -> None:
        """Register an upload in the session."""
        self.uploads.append(upload)
        self.touch()

    def add_export(self, export: NotebookExport) -> None:
        """Register an export in the session."""
        self.exports.append(export)
        self.touch()

    def add_screening_run(self, run: dict[str, Any]) -> None:
        """Register or replace a screening run in the session."""
        screening_run_id = str(run["screening_run_id"])
        self.screening_runs = [
            item
            for item in self.screening_runs
            if str(item.get("screening_run_id")) != screening_run_id
        ]
        self.screening_runs.append(run)
        self.active_screening_run_id = screening_run_id
        self.touch()

    def get_screening_run(self, screening_run_id: str) -> dict[str, Any]:
        """Return one screening run by ID."""
        for run in self.screening_runs:
            if str(run.get("screening_run_id")) == screening_run_id:
                return run
        raise KeyError(screening_run_id)

    def active_screening_run(self) -> dict[str, Any] | None:
        """Return the active screening run when one is selected."""
        if self.active_screening_run_id is None:
            return None
        try:
            return self.get_screening_run(self.active_screening_run_id)
        except KeyError:
            return None

    def clear(self) -> None:
        """Clear datasets, caches, warnings, and exports."""
        self.active_dataset = None
        self.active_dataset_name = None
        self.active_filters = None
        self.filtered_dataset = None
        self.analysis_cache.clear()
        self.matrix_cache.clear()
        self.network_cache.clear()
        self.exports.clear()
        self.warnings.clear()
        self.touch()

    def reset(self) -> None:
        """Reset the entire session."""
        self.uploads.clear()
        self.screening_runs.clear()
        self.active_screening_run_id = None
        self.clear()

    def to_manifest(self) -> dict[str, Any]:
        """Return a reproducibility manifest."""
        active_records = (
            len(self.active_dataset) if self.active_dataset is not None else 0
        )
        filtered_records = (
            len(self.filtered_dataset) if self.filtered_dataset is not None else None
        )
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "active_dataset_name": self.active_dataset_name,
            "active_records": active_records,
            "filtered_records": filtered_records,
            "uploads": [upload.to_dict() for upload in self.uploads],
            "exports": [export.to_dict() for export in self.exports],
            "screening_runs": [
                _screening_run_manifest(run) for run in self.screening_runs
            ],
            "warnings": self.warnings,
        }


def _warning_dicts(dataset: Any) -> list[dict[str, Any]]:
    if hasattr(dataset, "warning_dicts"):
        return [dict(warning) for warning in dataset.warning_dicts()]
    return []


def _screening_run_manifest(run: dict[str, Any]) -> dict[str, Any]:
    """Return a compact manifest row for a screening run."""
    return {
        "screening_run_id": run.get("screening_run_id"),
        "name": run.get("name"),
        "origin_type": run.get("origin_type"),
        "source": run.get("source"),
        "format": run.get("format"),
        "records": run.get("records"),
        "status_counts": dict(run.get("status_counts", {})),
        "promoted_dataset_ids": list(run.get("promoted_dataset_ids", [])),
    }

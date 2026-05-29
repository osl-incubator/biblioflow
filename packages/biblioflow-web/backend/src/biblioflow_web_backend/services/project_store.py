"""Filesystem-backed project/session store."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.core.json import to_jsonable


def utc_now() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class ProjectStore:
    """Store projects, uploads, datasets, analyses, and exports on disk."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.projects_dir = data_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, name: str | None = None) -> dict[str, Any]:
        """Create and persist a project."""
        project_id = uuid4().hex
        project: dict[str, Any] = {
            "project_id": project_id,
            "name": name or "Untitled project",
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "source_files": [],
            "datasets": [],
            "remote_searches": [],
            "screening_runs": [],
            "active_dataset_id": None,
            "filters": {},
            "analysis_cache_keys": [],
            "metadata": {},
        }
        project_dir = self.project_dir(project_id)
        (project_dir / "uploads").mkdir(parents=True, exist_ok=True)
        (project_dir / "datasets").mkdir(parents=True, exist_ok=True)
        (project_dir / "remote_searches").mkdir(parents=True, exist_ok=True)
        (project_dir / "screening_runs").mkdir(parents=True, exist_ok=True)
        (project_dir / "exports").mkdir(parents=True, exist_ok=True)
        self.save_project(project)
        return project

    def list_projects(self) -> list[dict[str, Any]]:
        """List all projects."""
        projects = []
        for metadata_path in sorted(self.projects_dir.glob("*/metadata.json")):
            projects.append(self._read_json(metadata_path))
        return projects

    def get_project(self, project_id: str) -> dict[str, Any]:
        """Return a project by ID."""
        path = self.project_dir(project_id) / "metadata.json"
        if not path.exists():
            raise ApiError("project_not_found", "Project was not found.", 404)
        return self._read_json(path)

    def save_project(self, project: dict[str, Any]) -> None:
        """Persist project metadata."""
        project["updated_at"] = utc_now()
        path = self.project_dir(str(project["project_id"])) / "metadata.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write_json(path, project)

    def delete_project(self, project_id: str) -> None:
        """Delete a project and all related runtime data."""
        project_dir = self.project_dir(project_id)
        if not project_dir.exists():
            raise ApiError("project_not_found", "Project was not found.", 404)
        shutil.rmtree(project_dir)

    def project_dir(self, project_id: str) -> Path:
        """Return a project directory path."""
        return self.projects_dir / project_id

    def uploads_dir(self, project_id: str) -> Path:
        """Return the upload directory for a project."""
        path = self.project_dir(project_id) / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def datasets_dir(self, project_id: str) -> Path:
        """Return the dataset directory for a project."""
        path = self.project_dir(project_id) / "datasets"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def remote_searches_dir(self, project_id: str) -> Path:
        """Return the remote search screening directory for a project."""
        path = self.project_dir(project_id) / "remote_searches"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def screening_runs_dir(self, project_id: str) -> Path:
        """Return the generic screening-run directory for a project."""
        path = self.project_dir(project_id) / "screening_runs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def exports_dir(self, project_id: str) -> Path:
        """Return the exports directory for a project."""
        path = self.project_dir(project_id) / "exports"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(
            json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

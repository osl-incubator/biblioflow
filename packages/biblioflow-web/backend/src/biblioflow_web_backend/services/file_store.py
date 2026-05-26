"""Upload file persistence helpers."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from biblioflow_web_backend.services.project_store import ProjectStore, utc_now


class FileStore:
    """Persist uploaded bibliographic source files."""

    def __init__(self, projects: ProjectStore) -> None:
        self.projects = projects

    def save_upload(
        self,
        project_id: str,
        filename: str,
        content: BinaryIO,
        *,
        content_type: str | None = None,
    ) -> dict[str, object]:
        """Save an uploaded file and return upload metadata."""
        project = self.projects.get_project(project_id)
        upload_id = uuid4().hex
        safe_suffix = Path(filename).suffix
        stored_name = f"{upload_id}{safe_suffix}"
        target = self.projects.uploads_dir(project_id) / stored_name
        hasher = hashlib.sha256()
        size = 0
        with target.open("wb") as handle:
            while True:
                chunk = content.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                hasher.update(chunk)
                handle.write(chunk)
        upload: dict[str, object] = {
            "upload_id": upload_id,
            "filename": filename,
            "stored_name": stored_name,
            "content_type": content_type,
            "size": size,
            "sha256": hasher.hexdigest(),
            "created_at": utc_now(),
        }
        project.setdefault("source_files", []).append(upload)
        self.projects.save_project(project)
        return upload

    def get_upload(self, project_id: str, upload_id: str) -> dict[str, object]:
        """Return upload metadata."""
        project = self.projects.get_project(project_id)
        for upload in project.get("source_files", []):
            if upload.get("upload_id") == upload_id:
                return dict(upload)
        from biblioflow_web_backend.core.errors import ApiError

        raise ApiError("upload_not_found", "Upload was not found.", 404)

    def list_uploads(self, project_id: str) -> list[dict[str, object]]:
        """List upload metadata for a project."""
        project = self.projects.get_project(project_id)
        return [dict(upload) for upload in project.get("source_files", [])]

    def upload_path(self, project_id: str, upload_id: str) -> Path:
        """Return the stored path for an upload."""
        upload = self.get_upload(project_id, upload_id)
        return self.projects.uploads_dir(project_id) / str(upload["stored_name"])

    def delete_upload(self, project_id: str, upload_id: str) -> None:
        """Delete an upload file and metadata entry."""
        project = self.projects.get_project(project_id)
        upload = self.get_upload(project_id, upload_id)
        path = self.projects.uploads_dir(project_id) / str(upload["stored_name"])
        if path.exists():
            path.unlink()
        project["source_files"] = [
            item
            for item in project.get("source_files", [])
            if item.get("upload_id") != upload_id
        ]
        self.projects.save_project(project)

    def copy_to_exports(self, project_id: str, source: Path, name: str) -> Path:
        """Copy a file into the exports directory."""
        target = self.projects.exports_dir(project_id) / name
        shutil.copyfile(source, target)
        return target

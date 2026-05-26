"""Upload routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, UploadFile

from biblioflow_web_backend.api.deps import get_file_store
from biblioflow_web_backend.services.file_store import FileStore

router = APIRouter()


@router.post("/{project_id}/uploads")
async def upload_files(
    project_id: str,
    files: Annotated[list[UploadFile], File(description="Bibliographic files")],
    store: Annotated[FileStore, Depends(get_file_store)],
) -> dict[str, Any]:
    """Upload one or more bibliographic files."""
    uploads = []
    for upload in files:
        uploads.append(
            store.save_upload(
                project_id,
                upload.filename or "upload",
                upload.file,
                content_type=upload.content_type,
            )
        )
    return {"data": uploads, "warnings": [], "metadata": {"project_id": project_id}}


@router.get("/{project_id}/uploads")
def list_uploads(
    project_id: str,
    store: Annotated[FileStore, Depends(get_file_store)],
) -> dict[str, Any]:
    """List uploads."""
    return {
        "data": store.list_uploads(project_id),
        "warnings": [],
        "metadata": {"project_id": project_id},
    }


@router.get("/{project_id}/uploads/{upload_id}")
def get_upload(
    project_id: str,
    upload_id: str,
    store: Annotated[FileStore, Depends(get_file_store)],
) -> dict[str, Any]:
    """Get upload metadata."""
    return {
        "data": store.get_upload(project_id, upload_id),
        "warnings": [],
        "metadata": {"project_id": project_id},
    }


@router.delete("/{project_id}/uploads/{upload_id}")
def delete_upload(
    project_id: str,
    upload_id: str,
    store: Annotated[FileStore, Depends(get_file_store)],
) -> dict[str, Any]:
    """Delete an upload."""
    store.delete_upload(project_id, upload_id)
    return {
        "data": {"deleted": True},
        "warnings": [],
        "metadata": {"project_id": project_id},
    }

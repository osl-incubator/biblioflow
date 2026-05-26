"""Export routes."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from biblioflow_web_backend.api.deps import get_export_service, get_project_store
from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.models.requests import ExportRequest
from biblioflow_web_backend.services.export_service import ExportService

router = APIRouter()


@router.get("/{project_id}/exports")
def list_exports(
    project_id: str,
    exports: Annotated[ExportService, Depends(get_export_service)],
) -> dict[str, Any]:
    """List export artifacts."""
    return {
        "data": exports.list_exports(project_id),
        "warnings": [],
        "metadata": {"project_id": project_id},
    }


@router.post("/{project_id}/exports")
def create_export(
    project_id: str,
    payload: ExportRequest,
    exports: Annotated[ExportService, Depends(get_export_service)],
) -> dict[str, Any]:
    """Create an export artifact."""
    if payload.kind != "dataset":
        raise ApiError(
            "unsupported_export",
            "Only dataset exports are implemented.",
            400,
        )
    data = exports.export_dataset(project_id, payload.dataset_id, format=payload.format)
    return {"data": data, "warnings": [], "metadata": {"project_id": project_id}}


@router.get("/{project_id}/exports/{filename}/download")
def download_export(project_id: str, filename: str) -> FileResponse:
    """Download an export by filename."""
    store = get_project_store()
    store.get_project(project_id)
    exports_dir = store.exports_dir(project_id).resolve()
    path = (exports_dir / filename).resolve()
    if not path.is_file() or not path.is_relative_to(exports_dir):
        raise ApiError("export_not_found", "Export was not found.", 404)
    return FileResponse(Path(path), filename=filename)

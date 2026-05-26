"""Project routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_project_store
from biblioflow_web_backend.models.requests import ProjectCreateRequest
from biblioflow_web_backend.services.project_store import ProjectStore

router = APIRouter()


@router.post("")
def create_project(
    payload: ProjectCreateRequest,
    store: Annotated[ProjectStore, Depends(get_project_store)],
) -> dict[str, Any]:
    """Create a project."""
    return {"data": store.create_project(payload.name), "warnings": [], "metadata": {}}


@router.get("")
def list_projects(
    store: Annotated[ProjectStore, Depends(get_project_store)],
) -> dict[str, Any]:
    """List projects."""
    return {"data": store.list_projects(), "warnings": [], "metadata": {}}


@router.get("/{project_id}")
def get_project(
    project_id: str,
    store: Annotated[ProjectStore, Depends(get_project_store)],
) -> dict[str, Any]:
    """Get a project."""
    return {"data": store.get_project(project_id), "warnings": [], "metadata": {}}


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    store: Annotated[ProjectStore, Depends(get_project_store)],
) -> dict[str, Any]:
    """Delete a project."""
    store.delete_project(project_id)
    return {"data": {"deleted": True}, "warnings": [], "metadata": {}}

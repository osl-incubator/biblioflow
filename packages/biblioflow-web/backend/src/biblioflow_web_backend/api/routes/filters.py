"""Filter routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_dataset_service
from biblioflow_web_backend.models.requests import FilterRequest
from biblioflow_web_backend.services.dataset_service import DatasetService

router = APIRouter()


@router.get("/{project_id}/datasets/{dataset_id}/filters/options")
def get_filter_options(
    project_id: str,
    dataset_id: str,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Return available filter values."""
    return {
        "data": datasets.filter_options(project_id, dataset_id),
        "warnings": [],
        "metadata": {"project_id": project_id, "dataset_id": dataset_id},
    }


@router.post("/{project_id}/datasets/{dataset_id}/filters/preview")
def preview_filters(
    project_id: str,
    dataset_id: str,
    payload: FilterRequest,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Preview filter results."""
    return {
        "data": datasets.filter_preview(project_id, dataset_id, payload.filters),
        "warnings": [],
        "metadata": {"project_id": project_id, "dataset_id": dataset_id},
    }

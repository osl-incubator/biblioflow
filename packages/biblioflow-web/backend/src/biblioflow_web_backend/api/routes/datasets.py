"""Dataset routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_dataset_service
from biblioflow_web_backend.models.requests import DatasetLoadRequest
from biblioflow_web_backend.services.dataset_service import DatasetService

router = APIRouter()


@router.post("/{project_id}/datasets/load")
def load_dataset(
    project_id: str,
    payload: DatasetLoadRequest,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Load uploaded files into a normalized dataset."""
    data = datasets.load_dataset(
        project_id,
        payload.upload_ids,
        provider=payload.provider,
        format=payload.format,
    )
    return {"data": data, "warnings": data.get("warnings", []), "metadata": {}}


@router.get("/{project_id}/datasets")
def list_datasets(
    project_id: str,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """List datasets."""
    return {"data": datasets.list_datasets(project_id), "warnings": [], "metadata": {}}


@router.get("/{project_id}/datasets/{dataset_id}")
def get_dataset(
    project_id: str,
    dataset_id: str,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Get a dataset payload."""
    payload = datasets.get_dataset_payload(project_id, dataset_id)
    return {"data": payload, "warnings": payload.get("warnings", []), "metadata": {}}


@router.get("/{project_id}/datasets/{dataset_id}/summary")
def get_dataset_summary(
    project_id: str,
    dataset_id: str,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Get a dataset summary."""
    return {
        "data": datasets.summarize(project_id, dataset_id),
        "warnings": [],
        "metadata": {"project_id": project_id, "dataset_id": dataset_id},
    }


@router.get("/{project_id}/datasets/{dataset_id}/records")
def get_dataset_records(
    project_id: str,
    dataset_id: str,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Get normalized records for a dataset."""
    payload = datasets.get_dataset_payload(project_id, dataset_id)
    return {
        "data": payload.get("records", []),
        "warnings": payload.get("warnings", []),
        "metadata": {"project_id": project_id, "dataset_id": dataset_id},
    }

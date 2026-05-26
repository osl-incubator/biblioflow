"""Validation routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_dataset_service
from biblioflow_web_backend.services.dataset_service import DatasetService

router = APIRouter()


@router.get("/{project_id}/datasets/{dataset_id}/validation")
def get_validation(
    project_id: str,
    dataset_id: str,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Return validation warnings for a dataset."""
    data = datasets.validation(project_id, dataset_id)
    return {"data": data, "warnings": data.get("warnings", []), "metadata": {}}

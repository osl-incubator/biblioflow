"""Matrix routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_matrix_service
from biblioflow_web_backend.models.requests import MatrixRequest
from biblioflow_web_backend.services.matrix_service import MatrixService

router = APIRouter()


@router.post("/{project_id}/datasets/{dataset_id}/matrices")
def build_matrix(
    project_id: str,
    dataset_id: str,
    payload: MatrixRequest,
    matrices: Annotated[MatrixService, Depends(get_matrix_service)],
) -> dict[str, Any]:
    """Build a bibliometric matrix."""
    return {
        "data": matrices.build(
            project_id,
            dataset_id,
            kind=payload.kind,
            unit=payload.unit,
            normalize=payload.normalize,
            min_occurrences=payload.min_occurrences,
            filters=payload.filters,
        ),
        "warnings": [],
        "metadata": {"project_id": project_id, "dataset_id": dataset_id},
    }

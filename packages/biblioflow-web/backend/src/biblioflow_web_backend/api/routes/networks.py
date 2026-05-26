"""Network routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_network_service
from biblioflow_web_backend.models.requests import MatrixRequest
from biblioflow_web_backend.services.network_service import NetworkService

router = APIRouter()


@router.post("/{project_id}/datasets/{dataset_id}/networks")
def build_network(
    project_id: str,
    dataset_id: str,
    payload: MatrixRequest,
    networks: Annotated[NetworkService, Depends(get_network_service)],
) -> dict[str, Any]:
    """Build a bibliometric network."""
    return {
        "data": networks.build(
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

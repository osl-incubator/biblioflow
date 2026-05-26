"""Analysis routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_analysis_service
from biblioflow_web_backend.models.requests import AnalysisRequest
from biblioflow_web_backend.services.analysis_service import AnalysisService

router = APIRouter()


@router.post("/{project_id}/datasets/{dataset_id}/analysis/overview")
def overview(
    project_id: str,
    dataset_id: str,
    payload: AnalysisRequest,
    analysis: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> dict[str, Any]:
    """Run overview/descriptive analysis."""
    return {
        "data": analysis.overview(
            project_id,
            dataset_id,
            top_n=payload.top_n,
            filters=payload.filters,
        ),
        "warnings": [],
        "metadata": {"project_id": project_id, "dataset_id": dataset_id},
    }

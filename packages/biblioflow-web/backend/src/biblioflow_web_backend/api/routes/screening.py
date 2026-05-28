"""Generic screening-run routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_screening_service
from biblioflow_web_backend.models.requests import (
    ScreeningCandidateDecisionRequest,
    ScreeningCandidatePromotionRequest,
    ScreeningRunCreateRequest,
)
from biblioflow_web_backend.services.screening_service import ScreeningService

router = APIRouter()


@router.post("/{project_id}/screening/runs")
def create_screening_run(
    project_id: str,
    payload: ScreeningRunCreateRequest,
    screening: Annotated[ScreeningService, Depends(get_screening_service)],
) -> dict[str, Any]:
    """Create a source-agnostic screening run."""
    data = screening.create_run(
        project_id,
        origin_type=payload.origin_type,
        source=payload.source,
        format=payload.format,
        upload_ids=payload.upload_ids,
        query=payload.query,
        limit=payload.limit,
        email=payload.email,
        api_key=payload.api_key,
        tool=payload.tool,
        name=payload.name,
        records=payload.records,
    )
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {
            "project_id": project_id,
            "screening_run_id": data["screening_run_id"],
        },
    }


@router.get("/{project_id}/screening/runs")
def list_screening_runs(
    project_id: str,
    screening: Annotated[ScreeningService, Depends(get_screening_service)],
) -> dict[str, Any]:
    """List source-agnostic screening runs."""
    return {
        "data": screening.list_runs(project_id),
        "warnings": [],
        "metadata": {"project_id": project_id},
    }


@router.get("/{project_id}/screening/runs/{screening_run_id}")
def get_screening_run(
    project_id: str,
    screening_run_id: str,
    screening: Annotated[ScreeningService, Depends(get_screening_service)],
) -> dict[str, Any]:
    """Return one source-agnostic screening run."""
    data = screening.get_run(project_id, screening_run_id)
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {
            "project_id": project_id,
            "screening_run_id": screening_run_id,
        },
    }


@router.patch("/{project_id}/screening/runs/{screening_run_id}/candidates")
def update_screening_candidates(
    project_id: str,
    screening_run_id: str,
    payload: ScreeningCandidateDecisionRequest,
    screening: Annotated[ScreeningService, Depends(get_screening_service)],
) -> dict[str, Any]:
    """Apply a decision to source-agnostic screening candidates."""
    data = screening.update_candidates(
        project_id,
        screening_run_id,
        candidate_ids=payload.candidate_ids,
        status=payload.status,
        decision_reason=payload.decision_reason,
        labels=payload.labels,
        notes=payload.notes,
    )
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {
            "project_id": project_id,
            "screening_run_id": screening_run_id,
        },
    }


@router.post("/{project_id}/screening/runs/{screening_run_id}/promote")
def promote_screening_candidates(
    project_id: str,
    screening_run_id: str,
    payload: ScreeningCandidatePromotionRequest,
    screening: Annotated[ScreeningService, Depends(get_screening_service)],
) -> dict[str, Any]:
    """Promote screening candidates into the active dataset."""
    data = screening.promote_candidates(
        project_id,
        screening_run_id,
        candidate_ids=payload.candidate_ids,
        include_statuses=list(payload.include_statuses),
        name=payload.name,
    )
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {
            "project_id": project_id,
            "screening_run_id": screening_run_id,
        },
    }

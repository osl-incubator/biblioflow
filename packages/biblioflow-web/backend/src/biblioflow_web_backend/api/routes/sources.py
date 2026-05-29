"""Remote source screening and import routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_dataset_service
from biblioflow_web_backend.models.requests import (
    CandidateDecisionRequest,
    CandidatePromotionRequest,
    RemoteSourceImportRequest,
    RemoteSourceSearchRequest,
)
from biblioflow_web_backend.services.dataset_service import DatasetService

router = APIRouter()


@router.post("/{project_id}/sources/import")
def import_remote_source(
    project_id: str,
    payload: RemoteSourceImportRequest,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Import PubMed or PMC records into a project dataset."""
    data = datasets.import_remote_source(
        project_id,
        source=payload.source,
        query=payload.query,
        limit=payload.limit,
        email=payload.email,
        api_key=payload.api_key,
        tool=payload.tool,
        name=payload.name,
    )
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {"project_id": project_id, "source": payload.source},
    }


@router.post("/{project_id}/sources/search")
def search_remote_source(
    project_id: str,
    payload: RemoteSourceSearchRequest,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Stage PubMed or PMC records as screening candidates."""
    data = datasets.search_remote_source(
        project_id,
        source=payload.source,
        query=payload.query,
        limit=payload.limit,
        email=payload.email,
        api_key=payload.api_key,
        tool=payload.tool,
        name=payload.name,
    )
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {
            "project_id": project_id,
            "source": payload.source,
            "search_id": data["search_id"],
        },
    }


@router.get("/{project_id}/sources/searches")
def list_remote_searches(
    project_id: str,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """List staged remote-source screening searches."""
    data = datasets.list_remote_searches(project_id)
    return {"data": data, "warnings": [], "metadata": {"project_id": project_id}}


@router.get("/{project_id}/sources/searches/{search_id}")
def get_remote_search(
    project_id: str,
    search_id: str,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Return one staged remote-source screening search."""
    data = datasets.get_remote_search(project_id, search_id)
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {"project_id": project_id, "search_id": search_id},
    }


@router.patch("/{project_id}/sources/searches/{search_id}/candidates")
def update_remote_candidates(
    project_id: str,
    search_id: str,
    payload: CandidateDecisionRequest,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Apply a screening decision to staged remote-source candidates."""
    data = datasets.update_remote_candidates(
        project_id,
        search_id,
        candidate_ids=payload.candidate_ids,
        status=payload.status,
    )
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {"project_id": project_id, "search_id": search_id},
    }


@router.post("/{project_id}/sources/searches/{search_id}/promote")
def promote_remote_candidates(
    project_id: str,
    search_id: str,
    payload: CandidatePromotionRequest,
    datasets: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict[str, Any]:
    """Promote screened remote-source candidates into the active dataset."""
    data = datasets.promote_remote_candidates(
        project_id,
        search_id,
        candidate_ids=payload.candidate_ids,
        include_statuses=list(payload.include_statuses),
        name=payload.name,
    )
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {"project_id": project_id, "search_id": search_id},
    }

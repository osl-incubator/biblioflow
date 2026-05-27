"""Remote source import routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_dataset_service
from biblioflow_web_backend.models.requests import RemoteSourceImportRequest
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

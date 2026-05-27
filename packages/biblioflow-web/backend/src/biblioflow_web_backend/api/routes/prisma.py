"""PRISMA flow routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from biblioflow_web_backend.api.deps import get_prisma_service
from biblioflow_web_backend.models.requests import PrismaFlowRequest
from biblioflow_web_backend.services.prisma_service import PrismaService

router = APIRouter()


@router.get("/{project_id}/prisma")
def get_prisma_flow(
    project_id: str,
    prisma: Annotated[PrismaService, Depends(get_prisma_service)],
    dataset_id: str | None = None,
) -> dict[str, Any]:
    """Build a default PRISMA flow from project state."""
    data = prisma.build(project_id, dataset_id=dataset_id)
    return {
        "data": data,
        "warnings": data["validation"].get("warnings", []),
        "metadata": {"project_id": project_id, "dataset_id": dataset_id},
    }


@router.post("/{project_id}/prisma")
def build_prisma_flow(
    project_id: str,
    payload: PrismaFlowRequest,
    prisma: Annotated[PrismaService, Depends(get_prisma_service)],
) -> dict[str, Any]:
    """Build a PRISMA flow with user-provided count overrides."""
    data = prisma.build(
        project_id,
        dataset_id=payload.dataset_id,
        title=payload.title,
        counts=payload.counts,
    )
    return {
        "data": data,
        "warnings": data["validation"].get("warnings", []),
        "metadata": {"project_id": project_id, "dataset_id": payload.dataset_id},
    }

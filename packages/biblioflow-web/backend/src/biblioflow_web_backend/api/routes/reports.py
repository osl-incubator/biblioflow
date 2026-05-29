"""Project report routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from biblioflow_web_backend.api.deps import get_report_service
from biblioflow_web_backend.models.requests import ReportCreateRequest
from biblioflow_web_backend.services.report_service import ReportService

router = APIRouter()


@router.get("/{project_id}/reports")
def list_reports(
    project_id: str,
    reports: Annotated[ReportService, Depends(get_report_service)],
) -> dict[str, Any]:
    """List generated project reports."""
    return {
        "data": reports.list_reports(project_id),
        "warnings": [],
        "metadata": {"project_id": project_id},
    }


@router.post("/{project_id}/reports")
def create_report(
    project_id: str,
    payload: ReportCreateRequest,
    reports: Annotated[ReportService, Depends(get_report_service)],
) -> dict[str, Any]:
    """Generate a project PDF report through core biblioflow.reporting."""
    data = reports.generate_report(
        project_id,
        dataset_id=payload.dataset_id,
        title=payload.title,
        subtitle=payload.subtitle,
        authors=payload.authors,
        organization=payload.organization,
        template=payload.template,
        completeness=payload.completeness,
        render=payload.render,
        keep_qmd=payload.keep_qmd,
        prisma=payload.prisma,
    )
    return {
        "data": data,
        "warnings": data.get("warnings", []),
        "metadata": {"project_id": project_id, "dataset_id": payload.dataset_id},
    }


@router.get("/{project_id}/reports/{filename}/download")
def download_report(
    project_id: str,
    filename: str,
    reports: Annotated[ReportService, Depends(get_report_service)],
) -> FileResponse:
    """Download a generated project report."""
    path = reports.report_path(project_id, filename)
    return FileResponse(path, filename=filename)

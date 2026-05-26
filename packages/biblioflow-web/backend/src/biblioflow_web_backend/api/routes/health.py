"""Health routes."""

from __future__ import annotations

from fastapi import APIRouter

from biblioflow_web_backend import __version__
from biblioflow_web_backend.models.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health and version metadata."""
    try:
        import biblioflow as bf
    except ImportError:
        biblioflow_version = None
    else:
        biblioflow_version = bf.__version__
    return HealthResponse(
        service="biblioflow-web",
        status="ok",
        version=__version__,
        biblioflow_version=biblioflow_version,
    )

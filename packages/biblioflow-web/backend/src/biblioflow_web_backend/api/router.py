"""API router composition."""

from __future__ import annotations

from fastapi import APIRouter

from biblioflow_web_backend.api.routes import (
    analysis,
    datasets,
    exports,
    filters,
    health,
    matrices,
    networks,
    prisma,
    projects,
    screening,
    sources,
    uploads,
    validation,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(screening.router, prefix="/projects", tags=["screening"])
api_router.include_router(sources.router, prefix="/projects", tags=["sources"])
api_router.include_router(uploads.router, prefix="/projects", tags=["uploads"])
api_router.include_router(datasets.router, prefix="/projects", tags=["datasets"])
api_router.include_router(validation.router, prefix="/projects", tags=["validation"])
api_router.include_router(filters.router, prefix="/projects", tags=["filters"])
api_router.include_router(analysis.router, prefix="/projects", tags=["analysis"])
api_router.include_router(matrices.router, prefix="/projects", tags=["matrices"])
api_router.include_router(networks.router, prefix="/projects", tags=["networks"])
api_router.include_router(exports.router, prefix="/projects", tags=["exports"])
api_router.include_router(prisma.router, prefix="/projects", tags=["prisma"])

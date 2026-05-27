"""FastAPI application for biblioflow-web."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from biblioflow_web_backend.api.router import api_router
from biblioflow_web_backend.core.config import Settings
from biblioflow_web_backend.core.errors import ApiError


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI application."""
    app_settings = settings or Settings.from_env()
    app = FastAPI(
        title="biblioflow-web",
        description="FastAPI backend for biblioflow web workflows.",
        version="0.2.0",  # semantic-release
    )
    if app_settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(app_settings.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "bad_request",
                    "message": str(exc),
                    "details": {},
                }
            },
        )

    app.include_router(api_router, prefix=app_settings.api_prefix)

    if app_settings.serve_frontend:
        _register_frontend_routes(app, app_settings.resolve_static_dir(), app_settings)

    return app


def _register_frontend_routes(
    app: FastAPI, static_dir: Path, settings: Settings
) -> None:
    """Register static asset and SPA fallback routes."""

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        reserved = (
            settings.api_prefix.strip("/"),
            "docs",
            "redoc",
            "openapi.json",
        )
        if full_path.split("/", 1)[0] in reserved:
            raise HTTPException(status_code=404)

        requested = (static_dir / full_path).resolve()
        static_root = static_dir.resolve()
        if requested.is_file() and _is_relative_to(requested, static_root):
            return FileResponse(requested)

        index = static_dir / "index.html"
        if index.exists():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend static assets not built.")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


app = create_app()


__all__ = ["app", "create_app"]

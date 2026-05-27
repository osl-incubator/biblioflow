from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

from biblioflow_web_backend.api.routes.health import health
from biblioflow_web_backend.core.config import Settings
from biblioflow_web_backend.main import _is_relative_to, create_app


def test_health_endpoint_direct() -> None:
    response = health()

    assert response.service == "biblioflow-web"
    assert response.status == "ok"
    assert response.biblioflow_version


def test_create_app_registers_static_fallback(tmp_path: Path) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<div id='root'>biblioflow-web</div>")
    settings = Settings(
        data_dir=tmp_path / "data",
        static_dir=static_dir,
        serve_frontend=True,
        cors_origins=(),
    )

    app = create_app(settings)
    fallback = next(route for route in app.routes if route.path == "/{full_path:path}")
    response = asyncio.run(fallback.endpoint("projects/example/dashboard"))

    assert isinstance(response, FileResponse)
    assert Path(response.path).name == "index.html"

    with pytest.raises(HTTPException):
        asyncio.run(fallback.endpoint("api/health"))


def test_static_path_helper(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = parent / "index.html"
    outside = tmp_path / "outside.txt"

    assert _is_relative_to(child, parent) is True
    assert _is_relative_to(outside, parent) is False

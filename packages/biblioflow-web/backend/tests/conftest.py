from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
BIBLIOFLOW_SRC = ROOT / "packages" / "biblioflow" / "src"


@pytest.fixture(autouse=True)
def local_biblioflow_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(BIBLIOFLOW_SRC))


@pytest.fixture
def app_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("multipart")
    from fastapi.testclient import TestClient

    from biblioflow_web_backend.api.deps import clear_dependency_caches
    from biblioflow_web_backend.main import create_app

    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<div id='root'>biblioflow-web</div>")
    monkeypatch.setenv("BIBLIOFLOW_WEB_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("BIBLIOFLOW_WEB_STATIC_DIR", str(static_dir))
    clear_dependency_caches()
    client = TestClient(create_app())
    yield client
    clear_dependency_caches()
    for key in ["BIBLIOFLOW_WEB_DATA_DIR", "BIBLIOFLOW_WEB_STATIC_DIR"]:
        os.environ.pop(key, None)

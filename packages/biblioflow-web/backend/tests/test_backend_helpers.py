from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from biblioflow_web_backend.api.deps import (
    clear_dependency_caches,
    get_analysis_service,
    get_dataset_service,
    get_export_service,
    get_file_store,
    get_matrix_service,
    get_network_service,
    get_prisma_service,
    get_project_store,
    get_settings,
)
from biblioflow_web_backend.cli import main
from biblioflow_web_backend.core.config import Settings, default_data_dir
from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.core.json import to_jsonable
from biblioflow_web_backend.models.jobs import JobResponse
from biblioflow_web_backend.models.projects import ProjectResponse
from biblioflow_web_backend.services.job_service import Job
from biblioflow_web_backend.workers.tasks import run_noop_task


@dataclass
class Example:
    value: Any


def test_settings_json_models_jobs_and_workers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BIBLIOFLOW_WEB_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("BIBLIOFLOW_WEB_STATIC_DIR", str(tmp_path / "static"))
    monkeypatch.setenv("BIBLIOFLOW_WEB_CORS_ORIGINS", "http://a.test, http://b.test")
    monkeypatch.setenv("BIBLIOFLOW_WEB_SERVE_FRONTEND", "0")

    settings = Settings.from_env()
    assert settings.data_dir == tmp_path / "data"
    assert settings.static_dir == tmp_path / "static"
    assert settings.cors_origins == ("http://a.test", "http://b.test")
    assert settings.serve_frontend is False
    assert Settings(static_dir=tmp_path).resolve_static_dir() == tmp_path
    assert default_data_dir().name == "biblioflow-web"

    payload = to_jsonable(
        {
            "now": datetime(2026, 1, 1),
            "date": date(2026, 1, 2),
            "path": tmp_path,
            "nan": math.nan,
            "inf": math.inf,
            "set": {"a", "b"},
            "dataclass": Example(value=1),
        }
    )
    assert payload["nan"] is None
    assert payload["inf"] is None
    assert payload["dataclass"] == {"value": 1}

    assert ApiError("bad", "Bad request").to_dict()["error"]["code"] == "bad"
    assert Job(kind="import", project_id="p1").to_dict()["kind"] == "import"
    assert (
        JobResponse(job_id="j1", project_id="p1", kind="import", status="queued").status
        == "queued"
    )
    assert (
        ProjectResponse(
            project_id="p1",
            name="Project",
            created_at="now",
            updated_at="now",
        ).name
        == "Project"
    )
    assert run_noop_task() == "ok"


def test_dependency_factories_and_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BIBLIOFLOW_WEB_DATA_DIR", str(tmp_path / "data"))
    clear_dependency_caches()

    assert get_settings().data_dir == tmp_path / "data"
    assert get_project_store() is get_project_store()
    assert get_file_store() is get_file_store()
    assert get_dataset_service() is get_dataset_service()
    assert get_analysis_service() is get_analysis_service()
    assert get_matrix_service() is get_matrix_service()
    assert get_network_service() is get_network_service()
    assert get_export_service() is get_export_service()
    assert get_prisma_service() is get_prisma_service()

    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> None:
        calls.append({"args": args, "kwargs": kwargs})

    monkeypatch.setattr("uvicorn.run", fake_run)
    main()

    assert calls[0]["args"] == ("biblioflow_web_backend.main:app",)
    assert calls[0]["kwargs"]["port"] == 8000
    clear_dependency_caches()

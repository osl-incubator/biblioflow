from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from biblioflow_web_backend.api.routes.sources import import_remote_source
from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.models.requests import RemoteSourceImportRequest
from biblioflow_web_backend.services.analysis_service import AnalysisService
from biblioflow_web_backend.services.dataset_service import DatasetService
from biblioflow_web_backend.services.file_store import FileStore
from biblioflow_web_backend.services.project_store import ProjectStore


def _services(tmp_path: Path) -> tuple[ProjectStore, DatasetService, str]:
    projects = ProjectStore(tmp_path / "data")
    files = FileStore(projects)
    datasets = DatasetService(projects, files)
    project = projects.create_project("Remote sources")
    return projects, datasets, str(project["project_id"])


def _pubmed_dataset() -> Any:
    import biblioflow as bf

    return bf.load(
        [
            {
                "pmid": "12345678",
                "doi": "10.1234/pubmed",
                "title": "PubMed test record",
                "publication_year": 2024,
                "authors": ["Jane Smith", "Ada Lovelace"],
                "source_title": "Journal of Test Imports",
                "keywords_all": ["bibliometrics", "reproducibility"],
            }
        ],
        source="pubmed",
    )


def _pmc_dataset() -> Any:
    import biblioflow as bf

    return bf.load(
        [
            {
                "pmcid": "PMC123456",
                "pmid": "98765432",
                "title": "PMC test record",
                "publication_year": 2025,
                "authors": ["Grace Hopper"],
                "source_title": "Open Full Text Research",
                "full_text_url": "https://pmc.example.test/articles/PMC123456",
                "keywords_all": ["open science"],
            }
        ],
        source="pmc",
    )


def test_pubmed_import_persists_active_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import biblioflow as bf

    projects, datasets, project_id = _services(tmp_path)
    calls: list[dict[str, Any]] = []

    def fake_from_pubmed(**kwargs: Any) -> Any:
        calls.append(kwargs)
        dataset = _pubmed_dataset()
        dataset.metadata["api_key"] = "secret-token"
        return dataset

    monkeypatch.setattr(bf, "from_pubmed", fake_from_pubmed)

    payload = datasets.import_remote_source(
        project_id,
        source="pubmed",
        query="bibliometrics AND reproducibility",
        limit=25,
        email="researcher@example.org",
        api_key="secret-token",
        tool="tests",
        name="My PubMed import",
    )

    dataset_id = str(payload["dataset_id"])
    assert calls == [
        {
            "query": "bibliometrics AND reproducibility",
            "limit": 25,
            "tool": "tests",
            "email": "researcher@example.org",
            "api_key": "secret-token",
        }
    ]
    assert payload["metadata"]["remote_source"] == "pubmed"
    assert payload["metadata"]["name"] == "My PubMed import"
    assert len(payload["records"]) == 1
    assert "secret-token" not in json.dumps(payload)

    project = projects.get_project(project_id)
    assert project["active_dataset_id"] == dataset_id
    assert datasets.list_datasets(project_id)[0]["dataset_id"] == dataset_id
    assert datasets.summarize(project_id, dataset_id)["documents"] == 1
    assert datasets.validation(project_id, dataset_id)["records"] == 1

    overview = AnalysisService(datasets).overview(project_id, dataset_id, top_n=5)
    assert overview["main_information"]["documents"] == 1


def test_pmc_and_pubmed_central_alias_use_pmc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import biblioflow as bf

    projects, datasets, project_id = _services(tmp_path)
    calls: list[dict[str, Any]] = []

    def fake_from_pmc(**kwargs: Any) -> Any:
        calls.append(kwargs)
        return _pmc_dataset()

    monkeypatch.setattr(bf, "from_pmc", fake_from_pmc)

    first = datasets.import_remote_source(
        project_id,
        source="pmc",
        query="open science",
        limit=5,
        email=None,
        api_key=None,
        tool="tests",
    )
    second = datasets.import_remote_source(
        project_id,
        source="pubmed_central",
        query="open access",
        limit=7,
        email="pmc@example.org",
        api_key="secret-token",
        tool="tests",
    )

    assert first["metadata"]["remote_source"] == "pmc"
    assert second["metadata"]["remote_source"] == "pmc"
    assert len(calls) == 2
    assert calls[1]["query"] == "open access"
    assert calls[1]["api_key"] == "secret-token"
    assert "secret-token" not in json.dumps(second)
    assert projects.get_project(project_id)["active_dataset_id"] == second["dataset_id"]


def test_remote_source_route_returns_api_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import biblioflow as bf

    _projects, datasets, project_id = _services(tmp_path)
    monkeypatch.setattr(bf, "from_pubmed", lambda **_kwargs: _pubmed_dataset())

    response = import_remote_source(
        project_id,
        RemoteSourceImportRequest(
            source="pubmed",
            query="diabetes",
            limit=3,
            email="researcher@example.org",
        ),
        datasets,
    )

    assert response["metadata"] == {"project_id": project_id, "source": "pubmed"}
    assert response["warnings"] == []
    assert response["data"]["metadata"]["query"] == "diabetes"


def test_remote_source_configuration_error_is_sanitized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import biblioflow as bf

    _projects, datasets, project_id = _services(tmp_path)

    def fake_from_pubmed(**_kwargs: Any) -> Any:
        raise bf.APIConfigurationError("Email missing for token secret-token")

    monkeypatch.setattr(bf, "from_pubmed", fake_from_pubmed)

    with pytest.raises(ApiError) as exc_info:
        datasets.import_remote_source(
            project_id,
            source="pubmed",
            query="bibliometrics",
            limit=10,
            email=None,
            api_key="secret-token",
            tool="tests",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "remote_source_configuration"
    assert "secret-token" not in exc_info.value.message
    assert "<redacted>" in exc_info.value.message

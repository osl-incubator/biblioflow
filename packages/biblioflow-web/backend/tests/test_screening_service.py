from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from biblioflow_web_backend.api.routes.screening import (
    create_screening_run,
    get_screening_run,
    list_screening_runs,
    promote_screening_candidates,
    update_screening_candidates,
)
from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.models.requests import (
    ScreeningCandidateDecisionRequest,
    ScreeningCandidatePromotionRequest,
    ScreeningRunCreateRequest,
)
from biblioflow_web_backend.services.dataset_service import DatasetService
from biblioflow_web_backend.services.file_store import FileStore
from biblioflow_web_backend.services.project_store import ProjectStore
from biblioflow_web_backend.services.screening_service import ScreeningService

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "packages" / "biblioflow" / "tests" / "data"


def _services(
    tmp_path: Path,
) -> tuple[ProjectStore, FileStore, DatasetService, ScreeningService, str]:
    projects = ProjectStore(tmp_path / "data")
    files = FileStore(projects)
    datasets = DatasetService(projects, files)
    screening = ScreeningService(projects, files, datasets)
    project = projects.create_project("Screening")
    return projects, files, datasets, screening, str(project["project_id"])


def _remote_dataset() -> Any:
    import biblioflow as bf

    return bf.load(
        [
            {
                "pmid": "12345678",
                "doi": "10.1234/screening",
                "title": "Generic screening record",
                "publication_year": 2026,
                "authors": ["Jane Smith"],
                "source_title": "Screening Journal",
                "keywords_all": ["screening"],
            },
            {
                "pmid": "12345678",
                "doi": "10.1234/screening",
                "title": "Generic screening duplicate",
                "publication_year": 2026,
                "authors": ["Jane Smith"],
                "source_title": "Screening Journal",
                "keywords_all": ["screening"],
            },
        ],
        source="pubmed",
    )


def test_screening_run_from_records_updates_and_promotes(tmp_path: Path) -> None:
    projects, _files, datasets, screening, project_id = _services(tmp_path)

    run = screening.create_run(
        project_id,
        origin_type="records",
        source="generic",
        records=[
            {
                "title": "Included source-agnostic record",
                "publication_year": 2024,
                "authors": ["Ada Lovelace"],
                "doi": "10.1/included",
            },
            {
                "title": "Maybe source-agnostic record",
                "publication_year": 2025,
                "authors": ["Grace Hopper"],
                "doi": "10.1/maybe",
            },
        ],
        name="Manual screening",
    )

    assert run["origin_type"] == "records"
    assert run["records"] == 2
    assert run["status_counts"] == {"candidate": 2}
    assert (
        projects.get_project(project_id)["screening_runs"][0]["name"]
        == "Manual screening"
    )

    first_id = str(run["candidates"][0]["candidate_id"])
    second_id = str(run["candidates"][1]["candidate_id"])
    updated = screening.update_candidates(
        project_id,
        str(run["screening_run_id"]),
        candidate_ids=[first_id],
        status="selected",
        decision_reason="Relevant abstract",
        labels=["core", " methodology "],
        notes="Keep for analysis",
    )
    assert updated["candidates"][0]["decision_reason"] == "Relevant abstract"
    assert updated["candidates"][0]["labels"] == ["core", "methodology"]
    assert updated["candidates"][0]["notes"] == "Keep for analysis"

    screening.update_candidates(
        project_id,
        str(run["screening_run_id"]),
        candidate_ids=[second_id],
        status="maybe",
    )
    promoted = screening.promote_candidates(
        project_id,
        str(run["screening_run_id"]),
        include_statuses=["selected", "maybe"],
        name="Screened dataset",
    )

    dataset_id = str(promoted["dataset_id"])
    assert promoted["metadata"]["imported_from"] == "screening_run"
    assert promoted["metadata"]["selected_count"] == 2
    assert projects.get_project(project_id)["active_dataset_id"] == dataset_id
    assert datasets.summarize(project_id, dataset_id)["documents"] == 2

    refreshed = screening.get_run(project_id, str(run["screening_run_id"]))
    assert refreshed["status_counts"] == {"imported": 2}
    assert refreshed["promoted_dataset_ids"] == [dataset_id]


def test_screening_run_from_uploads_and_routes(tmp_path: Path) -> None:
    _projects, files, _datasets, screening, project_id = _services(tmp_path)
    with (DATA / "minimal.json").open("rb") as handle:
        upload = files.save_upload(project_id, "minimal.json", handle)
    upload_id = str(upload["upload_id"])

    response = create_screening_run(
        project_id,
        ScreeningRunCreateRequest(
            origin_type="uploads",
            upload_ids=[upload_id],
            source="auto",
            format="auto",
            name="Uploaded review",
        ),
        screening,
    )
    run_id = str(response["data"]["screening_run_id"])
    candidate_id = str(response["data"]["candidates"][0]["candidate_id"])

    assert response["data"]["records"] == 2
    assert response["data"]["upload_ids"] == [upload_id]
    assert (
        list_screening_runs(project_id, screening)["data"][0]["screening_run_id"]
        == run_id
    )
    assert (
        get_screening_run(project_id, run_id, screening)["data"]["name"]
        == "Uploaded review"
    )

    decided = update_screening_candidates(
        project_id,
        run_id,
        ScreeningCandidateDecisionRequest(
            candidate_ids=[candidate_id],
            status="selected",
        ),
        screening,
    )
    assert decided["data"]["status_counts"] == {"selected": 1, "candidate": 1}

    promoted = promote_screening_candidates(
        project_id,
        run_id,
        ScreeningCandidatePromotionRequest(name="Uploaded dataset"),
        screening,
    )
    assert promoted["data"]["metadata"]["name"] == "Uploaded dataset"
    assert promoted["data"]["metadata"]["screening_run_id"] == run_id


def test_screening_remote_search_redacts_secrets_and_marks_duplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import biblioflow as bf

    _projects, _files, _datasets, screening, project_id = _services(tmp_path)

    def fake_from_pubmed(**kwargs: Any) -> Any:
        assert kwargs["api_key"] == "secret-token"
        return _remote_dataset()

    monkeypatch.setattr(bf, "from_pubmed", fake_from_pubmed)
    run = screening.create_run(
        project_id,
        origin_type="remote_search",
        source="pubmed",
        query="bibliometrics",
        limit=2,
        email="researcher@example.org",
        api_key="secret-token",
        tool="tests",
    )

    assert run["source"] == "pubmed"
    assert run["status_counts"] == {"candidate": 1, "duplicate": 1}
    assert (
        run["candidates"][1]["duplicate_of_candidate_id"]
        == run["candidates"][0]["candidate_id"]
    )
    assert "secret-token" not in json.dumps(run)


def test_screening_errors(tmp_path: Path) -> None:
    _projects, _files, _datasets, screening, project_id = _services(tmp_path)

    with pytest.raises(ApiError, match="Unsupported screening origin"):
        screening.create_run(project_id, origin_type="bad", records=[])
    with pytest.raises(ApiError, match="Provide a query"):
        screening.create_run(
            project_id, origin_type="remote_search", source="pubmed", query=""
        )
    with pytest.raises(ApiError, match="No uploads"):
        screening.create_run(project_id, origin_type="uploads", upload_ids=[])
    with pytest.raises(ApiError, match="at least one record"):
        screening.create_run(project_id, origin_type="records", records=[])
    with pytest.raises(ApiError, match="Screening run"):
        screening.get_run(project_id, "missing")

    run = screening.create_run(
        project_id,
        origin_type="records",
        records=[{"title": "Only record", "doi": "10.1/only"}],
    )
    run_id = str(run["screening_run_id"])
    with pytest.raises(ApiError, match="Select at least one"):
        screening.update_candidates(
            project_id, run_id, candidate_ids=[], status="selected"
        )
    with pytest.raises(ApiError, match="Unsupported candidate"):
        screening.update_candidates(
            project_id, run_id, candidate_ids=["x"], status="bad"
        )
    with pytest.raises(ApiError, match="not found"):
        screening.update_candidates(
            project_id, run_id, candidate_ids=["missing"], status="selected"
        )
    with pytest.raises(ApiError, match="Only candidate"):
        screening.promote_candidates(project_id, run_id, include_statuses=["excluded"])

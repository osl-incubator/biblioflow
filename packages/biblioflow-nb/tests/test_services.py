from __future__ import annotations

from typing import Any

import pytest

from biblioflow_nb.app import BiblioFlowNotebookApp
from biblioflow_nb.services import (
    AnalysisService,
    DatasetService,
    ExportService,
    MatrixService,
    NetworkService,
    ScreeningService,
)
from biblioflow_nb.state import NotebookSession


def _remote_dataset(source: str) -> Any:
    import biblioflow as bf

    identifier = {"pubmed": "12345678", "pmc": "PMC123456"}[source]
    id_field = "pmid" if source == "pubmed" else "pmcid"
    return bf.load(
        [
            {
                id_field: identifier,
                "title": f"{source} notebook import",
                "publication_year": 2024,
                "authors": ["Jane Smith"],
                "source_title": "Notebook Imports",
                "keywords_all": ["bibliometrics"],
            }
        ],
        source=source,
    )


def test_dataset_analysis_matrix_network_and_export_services(data_dir, tmp_path):
    session = NotebookSession()
    datasets = DatasetService(session)
    analysis = AnalysisService(session, datasets)
    matrices = MatrixService(session, datasets)
    networks = NetworkService(session, datasets)
    exports = ExportService(session, datasets)

    dataset = datasets.load(data_dir / "minimal.json")
    assert len(dataset) == 2
    assert datasets.summary()["documents"] == 2

    filter_result = datasets.apply_filters({"year_min": 2025})
    assert filter_result["output_records"] == 1
    datasets.reset_filters()

    overview = analysis.overview(top_n=2)
    assert overview["main_information"]["documents"] == 2

    matrix = matrices.build(unit="keywords_all")
    assert matrix.kind == "co_occurrence"

    network = networks.build(unit="keywords_all")
    assert len(network.nodes) > 0

    output = exports.export_dataset(tmp_path / "records.json")
    assert output.exists()
    assert session.exports[-1].format == "json"


def test_dataset_service_imports_pubmed_and_pmc(monkeypatch: pytest.MonkeyPatch):
    import biblioflow as bf

    session = NotebookSession()
    datasets = DatasetService(session)
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_from_pubmed(**kwargs: Any) -> Any:
        calls.append(("pubmed", kwargs))
        return _remote_dataset("pubmed")

    def fake_from_pmc(**kwargs: Any) -> Any:
        calls.append(("pmc", kwargs))
        return _remote_dataset("pmc")

    monkeypatch.setattr(bf, "from_pubmed", fake_from_pubmed)
    monkeypatch.setattr(bf, "from_pmc", fake_from_pmc)

    pubmed = datasets.from_pubmed(
        query=" bibliometrics ",
        limit=10,
        email="researcher@example.org",
        api_key="secret-token",
        tool="tests",
    )
    pmc = datasets.from_pmc(query="open science", name="PMC import")

    assert len(pubmed) == 1
    assert len(pmc) == 1
    assert calls[0] == (
        "pubmed",
        {
            "query": "bibliometrics",
            "limit": 10,
            "tool": "tests",
            "email": "researcher@example.org",
            "api_key": "secret-token",
        },
    )
    assert calls[1][0] == "pmc"
    assert session.active_dataset_name == "PMC import"
    assert "secret-token" not in str(session.to_manifest())


def test_app_remote_source_methods_delegate(monkeypatch: pytest.MonkeyPatch):
    import biblioflow as bf

    calls: list[str] = []

    def fake_from_pubmed(**_kwargs: Any) -> Any:
        calls.append("pubmed")
        return _remote_dataset("pubmed")

    def fake_from_pmc(**_kwargs: Any) -> Any:
        calls.append("pmc")
        return _remote_dataset("pmc")

    monkeypatch.setattr(bf, "from_pubmed", fake_from_pubmed)
    monkeypatch.setattr(bf, "from_pmc", fake_from_pmc)

    app = BiblioFlowNotebookApp()
    app.from_pubmed(query="bibliometrics")
    app.from_pubmed_central(query="open access")
    app.from_pmc(query="open science")
    staged = app.stage_pubmed(query="screening")
    app.update_candidates([staged["candidates"][0]["candidate_id"]])
    app.promote_candidates(name="Screened PubMed")

    assert calls == ["pubmed", "pmc", "pmc", "pubmed"]
    assert app.session.active_dataset_name == "Screened PubMed"


def test_screening_service_stages_updates_and_promotes_records() -> None:
    session = NotebookSession()
    screening = ScreeningService(session)

    run = screening.stage_records(
        [
            {
                "doi": "10.1000/example",
                "title": "Notebook screening",
                "publication_year": 2026,
                "authors": ["Ada Lovelace"],
                "source_title": "Notebook Journal",
            },
            {
                "doi": "10.1000/example",
                "title": "Duplicate screening",
                "publication_year": 2026,
                "authors": ["Ada Lovelace"],
                "source_title": "Notebook Journal",
            },
        ],
        source="generic",
        name="Manual records",
    )
    candidate_id = run["candidates"][0]["candidate_id"]
    duplicate = run["candidates"][1]

    assert run["status_counts"] == {"candidate": 1, "duplicate": 1}
    assert duplicate["duplicate_of_candidate_id"] == candidate_id
    assert session.active_screening_run_id == run["screening_run_id"]

    updated = screening.update_candidates(
        [candidate_id],
        status="maybe",
        reason="needs review",
        labels=["method"],
        notes="promote for testing",
    )
    assert updated["candidates"][0]["status"] == "maybe"
    assert updated["candidates"][0]["labels"] == ["method"]

    dataset = screening.promote_candidates(include_statuses=("maybe",))

    assert len(dataset) == 1
    assert session.active_dataset_name == "Manual records — screened records"
    assert session.screening_runs[0]["status_counts"] == {
        "imported": 1,
        "duplicate": 1,
    }
    assert session.to_manifest()["screening_runs"][0]["records"] == 2


def test_screening_service_stages_file_and_pubmed(
    data_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    import biblioflow as bf

    session = NotebookSession()
    screening = ScreeningService(session)

    file_run = screening.stage_file(data_dir / "minimal.json", source="generic")

    assert file_run["origin_type"] == "uploads"
    assert session.uploads[-1].name == "minimal.json"

    calls: list[dict[str, Any]] = []

    def fake_from_pubmed(**kwargs: Any) -> Any:
        calls.append(kwargs)
        return _remote_dataset("pubmed")

    monkeypatch.setattr(bf, "from_pubmed", fake_from_pubmed)

    pubmed_run = screening.stage_pubmed(
        query=" bibliometrics ",
        limit=5,
        email="researcher@example.org",
        api_key="secret-token",
        tool="tests",
    )

    assert pubmed_run["source"] == "pubmed"
    assert calls == [
        {
            "query": "bibliometrics",
            "limit": 5,
            "tool": "tests",
            "email": "researcher@example.org",
            "api_key": "secret-token",
        }
    ]
    assert "secret-token" not in str(session.to_manifest())
    assert "secret-token" not in str(pubmed_run["metadata"])


def test_screening_service_rejects_invalid_actions() -> None:
    session = NotebookSession()
    screening = ScreeningService(session)

    with pytest.raises(ValueError, match="records"):
        screening.stage_records([])
    with pytest.raises(ValueError, match="query"):
        screening.stage_pubmed(query=" ")
    with pytest.raises(ValueError, match="select"):
        screening.update_candidates([], status="selected")

    run = screening.stage_records([{"title": "One"}])

    with pytest.raises(ValueError, match="Unsupported"):
        screening.update_candidates(
            [run["candidates"][0]["candidate_id"]], status="bad"
        )
    with pytest.raises(KeyError):
        screening.update_candidates(["missing"], status="selected")
    with pytest.raises(ValueError, match="Only candidate"):
        screening.promote_candidates(include_statuses=("excluded",))
    with pytest.raises(ValueError, match="Select"):
        screening.promote_candidates([])

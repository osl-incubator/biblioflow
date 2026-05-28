from __future__ import annotations

from typing import Any

import biblioflow as bf
import ipywidgets as widgets
import pytest

import biblioflow_nb as bfn
from biblioflow_nb.app import BiblioFlowNotebookApp, NotebookServices
from biblioflow_nb.state import NotebookSession
from biblioflow_nb.widgets.remote_sources import RemoteSourcesPanel


def test_launch_returns_app_without_display(data_dir):
    dataset = bf.load(data_dir / "minimal.json")

    app = bfn.launch(records=dataset, display=False)

    assert isinstance(app, BiblioFlowNotebookApp)
    assert len(app.session.active_dataset) == 2
    assert isinstance(app.widget, widgets.Widget)


def test_empty_app_builds_tabs():
    app = BiblioFlowNotebookApp()

    assert isinstance(app.widget, widgets.Widget)
    assert len(app.panels) >= 8


def _remote_dataset(source: str) -> Any:
    return bf.load(
        [
            {
                "source_id": f"{source}-1",
                "title": f"{source} widget import",
                "publication_year": 2025,
                "authors": ["Ada Lovelace"],
                "source_title": "Widget Imports",
                "keywords_all": ["notebooks"],
            }
        ],
        source=source,
    )


def test_remote_sources_panel_stages_and_promotes_selected_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_from_pmc(**kwargs: Any) -> Any:
        calls.append(kwargs)
        return _remote_dataset("pmc")

    monkeypatch.setattr(bf, "from_pmc", fake_from_pmc)
    session = NotebookSession()
    panel = RemoteSourcesPanel(session, NotebookServices.create(session))

    assert isinstance(panel.build(), widgets.Widget)
    panel.source_dropdown.value = "pmc"
    panel.query_text.value = "open science"
    panel.limit_input.value = 12
    panel.email_text.value = "researcher@example.org"
    panel.api_key_text.value = "secret-token"
    panel.name_text.value = "Widget PMC"

    panel.import_from_ui()

    assert calls == [
        {
            "query": "open science",
            "limit": 12,
            "email": "researcher@example.org",
            "api_key": "secret-token",
            "tool": "biblioflow-nb",
        }
    ]
    assert panel.api_key_text.value == ""
    assert session.active_dataset is None
    assert session.active_screening_run_id is not None
    assert session.screening_runs[0]["name"] == "Widget PMC"

    panel.promote_from_ui()

    assert session.active_dataset_name == "Widget PMC"
    assert "secret-token" not in str(session.to_manifest())


def test_remote_sources_panel_requires_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_from_pubmed(**kwargs: Any) -> Any:
        calls.append(kwargs)
        return _remote_dataset("pubmed")

    monkeypatch.setattr(bf, "from_pubmed", fake_from_pubmed)
    session = NotebookSession()
    panel = RemoteSourcesPanel(session, NotebookServices.create(session))

    with pytest.raises(ValueError, match="query"):
        panel.import_from_ui()
    assert calls == []

from __future__ import annotations

import biblioflow as bf
import ipywidgets as widgets

import biblioflow_nb as bfn
from biblioflow_nb.app import BiblioFlowNotebookApp


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

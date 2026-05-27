from __future__ import annotations

from pathlib import Path

import biblioflow as bf
import ipywidgets as widgets
import pytest

import biblioflow_nb as bfn
from biblioflow_nb.app import NotebookServices
from biblioflow_nb.colab.upload import colab_upload
from biblioflow_nb.environment import in_ipython, is_colab
from biblioflow_nb.errors import BiblioFlowNotebookError
from biblioflow_nb.io import TemporaryUploadStore, upload_items
from biblioflow_nb.renderers.charts import chart_fallback_html
from biblioflow_nb.renderers.messages import error_html, info_html, warning_html
from biblioflow_nb.renderers.networks import network_tables_html
from biblioflow_nb.renderers.tables import dataframe_like_to_rows, rows_to_html
from biblioflow_nb.state import NotebookSession
from biblioflow_nb.widgets.base import WidgetPanel
from biblioflow_nb.widgets.exports import ExportsPanel
from biblioflow_nb.widgets.filters import FiltersPanel
from biblioflow_nb.widgets.matrices import MatrixPanel
from biblioflow_nb.widgets.networks import NetworkPanel
from biblioflow_nb.widgets.overview import OverviewPanel
from biblioflow_nb.widgets.upload import UploadPanel
from biblioflow_nb.widgets.validation import ValidationPanel


def test_io_renderers_environment_and_launch_helpers(data_dir, tmp_path):
    store = TemporaryUploadStore()
    written = store.write_upload("../records.txt", b"content")
    assert written.name == "records.txt"
    assert written.read_bytes() == b"content"
    store.cleanup()

    assert upload_items({}) == []
    assert upload_items({"records.ris": {"content": b"TY  - JOUR"}})[0]["name"]
    assert upload_items(({"name": "records.ris", "content": b"x"},))[0]["content"]
    assert upload_items(object()) == []

    assert "hello" in info_html("hello")
    assert "careful" in warning_html("careful")
    assert "bad" in error_html("bad")
    assert "No rows." in rows_to_html([])
    assert dataframe_like_to_rows(None) == []
    assert "alpha" in chart_fallback_html([{"term": "alpha", "n": 1}])

    assert is_colab() is False
    assert isinstance(in_ipython(), bool)
    with pytest.raises(BiblioFlowNotebookError, match=r"google\.colab"):
        colab_upload(tmp_path)

    dataset = bf.load(data_dir / "minimal.json")
    assert isinstance(bfn.open_dataset(dataset, display=False).widget, widgets.Widget)
    assert isinstance(bfn.sample_app(display=False).widget, widgets.Widget)
    assert isinstance(bfn.app(display=False).widget, widgets.Widget)


def test_base_panel_runs_callbacks_safely() -> None:
    panel = WidgetPanel(NotebookSession(), services=object())
    assert isinstance(panel.build(), widgets.Widget)
    panel.show_info("Ready")
    panel.clear_output()
    panel.run_safely(lambda: None)
    panel.run_safely(lambda: (_ for _ in ()).throw(ValueError("friendly")))
    panel.run_safely(lambda: (_ for _ in ()).throw(BiblioFlowNotebookError("expected")))
    panel.run_safely(lambda: (_ for _ in ()).throw(RuntimeError("boom")))


def test_notebook_panels_execute_common_actions(data_dir: Path, tmp_path: Path) -> None:
    session = NotebookSession()
    services = NotebookServices.create(session)
    services.datasets.load(data_dir / "minimal.json")

    validation = ValidationPanel(session, services)
    validation.build()
    validation.refresh()

    filters = FiltersPanel(session, services)
    filters.build()
    filters.year_min.value = 2025
    filters.keyword_text.value = "AI"
    filters.apply()
    filters.reset()

    overview = OverviewPanel(session, services)
    overview.build()
    overview.top_n.value = 2
    overview.run()

    matrix = MatrixPanel(session, services)
    matrix.build()
    matrix.run()

    network = NetworkPanel(session, services)
    network.build()
    network.run()
    network_result = services.networks.build(unit="keywords_all")
    assert "Nodes" in network_tables_html(network_result)

    exports = ExportsPanel(session, services)
    exports.build()
    exports.path.value = str(tmp_path / "records.json")
    exports.export()
    with pytest.raises(BiblioFlowNotebookError, match=r"google\.colab"):
        exports.download_latest()


def test_upload_panel_loads_from_path(data_dir: Path) -> None:
    session = NotebookSession()
    services = NotebookServices.create(session)
    panel = UploadPanel(session, services)
    panel.build()
    panel.path_text.value = str(data_dir / "minimal.json")

    panel.load_from_ui()

    assert session.active_dataset is not None
    assert session.uploads[-1].name == "minimal.json"

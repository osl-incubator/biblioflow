from __future__ import annotations

from pathlib import Path

from biblioflow_nb.app import BiblioFlowNotebookApp
from biblioflow_nb.services import DatasetService, ReportService
from biblioflow_nb.state import NotebookSession


def test_notebook_report_service_delegates_to_core_reporting(
    data_dir: Path, tmp_path: Path
) -> None:
    session = NotebookSession()
    datasets = DatasetService(session)
    datasets.load(data_dir / "minimal.json", name="Notebook Report")
    reports = ReportService(session, datasets)

    result = reports.generate_report(
        tmp_path / "notebook-report.pdf",
        title="Notebook Generated Report",
        render=False,
    )

    assert result.rendered is False
    assert result.qmd_path.exists()
    assert result.context_path.exists()
    assert "Notebook Generated Report" in result.qmd_path.read_text(encoding="utf-8")
    assert session.exports[-1].kind == "report"
    assert session.exports[-1].format == "pdf"


def test_notebook_app_report_method_uses_report_service(
    data_dir: Path, tmp_path: Path
) -> None:
    app = BiblioFlowNotebookApp()
    app.load(data_dir / "minimal.json", name="App Report")

    result = app.report(str(tmp_path / "app-report.pdf"), render=False)

    assert result.qmd_path.exists()
    assert app.session.exports[-1].kind == "report"

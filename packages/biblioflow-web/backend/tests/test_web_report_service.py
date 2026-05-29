from __future__ import annotations

from pathlib import Path

from biblioflow_web_backend.services.dataset_service import DatasetService
from biblioflow_web_backend.services.file_store import FileStore
from biblioflow_web_backend.services.project_store import ProjectStore
from biblioflow_web_backend.services.report_service import ReportService

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "packages" / "biblioflow" / "tests" / "data"


def test_web_report_service_delegates_to_core_reporting(tmp_path: Path) -> None:
    projects = ProjectStore(tmp_path / "data")
    files = FileStore(projects)
    datasets = DatasetService(projects, files)
    reports = ReportService(projects, datasets)
    project = projects.create_project("Web Report")
    project_id = str(project["project_id"])
    with (DATA / "minimal.json").open("rb") as handle:
        upload = files.save_upload(
            project_id,
            "minimal.json",
            handle,
            content_type="application/json",
        )
    dataset_payload = datasets.load_dataset(
        project_id,
        [str(upload["upload_id"])],
        provider="auto",
        format="auto",
    )

    result = reports.generate_report(
        project_id,
        dataset_id=str(dataset_payload["dataset_id"]),
        title="Web Generated Report",
        render=False,
        prisma={"identified": 2, "screened": 2, "included": 2},
    )

    assert result["kind"] == "report"
    assert result["dataset_id"] == dataset_payload["dataset_id"]
    assert Path(result["qmd_path"]).exists()
    assert Path(result["context_path"]).exists()
    assert "Web Generated Report" in Path(result["qmd_path"]).read_text(
        encoding="utf-8"
    )
    assert "executive_summary" in result["sections_rendered"]

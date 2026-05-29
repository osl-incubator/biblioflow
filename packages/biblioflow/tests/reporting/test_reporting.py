from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

import biblioflow as bf
from biblioflow.cli import main
from biblioflow.reporting import (
    PrismaFlow,
    ReportProject,
    ReportRenderer,
    ReportRenderError,
    build_report_context,
    generate_report,
    render_prisma_svg,
    render_qmd,
    validate_prisma,
)
from biblioflow.reporting import (
    report as render_report,
)

DATA = Path(__file__).resolve().parents[1] / "data"


def test_generate_report_writes_qmd_context_and_prisma_svg(tmp_path: Path) -> None:
    dataset = bf.load(DATA / "minimal.json")
    project = ReportProject.from_records(
        dataset,
        title="Example Project",
        subtitle="Bibliometric report",
        authors=["Research Team"],
        research_questions=["What is represented in the corpus?"],
        prisma={
            "identified": 2,
            "duplicates_removed": 0,
            "screened": 2,
            "excluded_screening": 0,
            "full_text_assessed": 2,
            "full_text_excluded": 0,
            "included": 2,
        },
    )

    result = generate_report(
        project,
        output=tmp_path / "project-report.pdf",
        render=False,
        completeness="complete",
    )

    assert result.rendered is False
    assert result.qmd_path.exists()
    assert result.context_path.exists()
    assert (result.assets_dir / "prisma-flow.svg").exists()
    assert "Executive summary" in result.qmd_path.read_text(encoding="utf-8")
    context = json.loads(result.context_path.read_text(encoding="utf-8"))
    assert context["summary"]["documents"] == 2
    assert context["project"]["title"] == "Example Project"
    assert "appendices" in result.sections_rendered
    assert "Sample records" not in result.qmd_path.read_text(encoding="utf-8")
    assert "sample_records" not in context["tables"]


def test_prisma_validation_and_svg() -> None:
    flow = PrismaFlow(
        identified=10,
        duplicates_removed=2,
        screened=9,
        excluded_screening=1,
        full_text_assessed=8,
        full_text_excluded=2,
        included=6,
    )

    warnings = validate_prisma(flow)
    svg = render_prisma_svg(flow, title="Test flow")

    assert warnings[0].code == "prisma_screened_mismatch"
    assert "<svg" in svg
    assert "Test flow" in svg
    assert "n = 6" in svg


def test_report_project_manifest_loads_sources(tmp_path: Path) -> None:
    manifest = tmp_path / "project.yaml"
    manifest.write_text(
        "\n".join(
            [
                'title: "Manifest report"',
                "authors:",
                '  - "Research Team"',
                "sources:",
                f'  - path: "{DATA / "minimal.json"}"',
                '    format: "json"',
                '    provider: "generic"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    project = ReportProject.from_manifest(manifest)

    assert project.title == "Manifest report"
    assert project.records is not None
    assert len(project.records) == 2
    assert project.sources[0].format == "json"


def test_build_report_context_without_records_reports_missing_corpus(
    tmp_path: Path,
) -> None:
    context, warnings = build_report_context(
        ReportProject(title="Empty project"),
        assets_dir=tmp_path / "assets",
    )

    assert context["summary"] == {}
    assert context["tables"]["annual_production"] == []
    assert context["field_profile"][0]["field"] == "title"
    assert {row["present"] for row in context["field_profile"]} == {0}
    assert context["prisma"]["flow"]["included"] == 0
    assert (tmp_path / "assets" / "prisma-flow.svg").exists()
    assert [warning.code for warning in warnings] == [
        "records_missing",
        "prisma_missing",
    ]


def test_cli_report_no_render(tmp_path: Path, capsys: Any) -> None:
    output = tmp_path / "cli-report.pdf"

    assert (
        main(
            [
                "report",
                str(DATA / "minimal.json"),
                "--title",
                "CLI Report",
                "--output",
                str(output),
                "--no-render",
            ]
        )
        == 0
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["rendered"] is False
    assert Path(payload["qmd_path"]).exists()
    assert "CLI Report" in Path(payload["qmd_path"]).read_text(encoding="utf-8")


def test_report_alias_renders_and_removes_intermediates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = bf.load(DATA / "minimal.json")
    project = ReportProject.from_records(dataset, title="Rendered Report")

    def fake_render_pdf(
        self: ReportRenderer, qmd_path: str | Path, output: str | Path
    ) -> None:
        Path(output).write_text(Path(qmd_path).read_text(encoding="utf-8"))

    monkeypatch.setattr(ReportRenderer, "render_pdf", fake_render_pdf)

    result = render_report(
        project,
        output=tmp_path / "rendered-report.pdf",
        render=True,
        keep_qmd=False,
        keep_context=False,
    )

    assert result.rendered is True
    assert result.output_path.exists()
    assert not result.qmd_path.exists()
    assert not result.context_path.exists()


def test_render_qmd_supports_rich_project_sections_and_table_cells() -> None:
    context = {
        "project": {
            "title": 'Rich "Project"',
            "subtitle": "Cluster view",
            "authors": ["A. Author", "B. Author"],
            "organization": "Open Science Lab",
            "project_id": "project-123",
            "research_questions": ["RQ1"],
            "objectives": ["Map themes"],
            "inclusion_criteria": ["Peer reviewed"],
            "exclusion_criteria": ["Editorials"],
        },
        "report": {
            "date": "2026-05-29",
            "generated_at": "2026-05-29T00:00:00+00:00",
            "completeness": "complete",
        },
        "summary": {
            "documents": 3,
            "sources": 2,
            "authors": 4,
            "keywords": 5,
            "documents_with_doi": 1,
            "timespan_start": 2020,
            "timespan_end": 2024,
        },
        "prisma": {
            "svg": "prisma-flow.svg",
            "rows": [{"stage": "Included", "count": 3}],
        },
        "tables": {
            "annual_production": [
                {"publication_year": year, "documents": 1} for year in range(2000, 2026)
            ],
            "document_types": [{"document_type": "article", "documents": 3}],
            "top_sources": [{"source_title": {"journal": "A|B"}, "documents": 2}],
            "top_authors": [{"author": "Doe\nJane", "documents": 2}],
            "top_keywords": [{"keyword": ["a", "b", "c", "d", "e"], "documents": 2}],
            "top_countries": [{"country": "Brazil", "documents": 1}],
            "top_institutions": [{"institution": "OSL", "documents": 1}],
        },
        "field_profile": [
            {"field": "title", "present": 3, "missing": 0, "coverage_percent": 100}
        ],
        "warnings": [{"severity": "warning", "code": "x", "message": "Check"}],
        "reproducibility": {
            "biblioflow_version": "0.0",
            "python_version": "3",
            "platform": "test",
            "generated_at": "now",
        },
        "sources": [
            {
                "label": "Source",
                "path": "records.json",
                "format": "json",
                "provider": "generic",
                "searched_on": None,
                "sha256": "abc",
            }
        ],
    }

    qmd = render_qmd(context)

    assert 'title: "Rich \\"Project\\""' in qmd
    assert "**Organization:** Open Science Lab" in qmd
    assert "**Project ID:** `project-123`" in qmd
    assert "## Objectives" in qmd
    assert "## Inclusion criteria" in qmd
    assert "## Exclusion criteria" in qmd
    assert "Showing first 25 of 26 rows" in qmd
    assert "journal: A\\|B" in qmd
    assert "Doe<br>Jane" in qmd
    assert "a, b, c, d, …" in qmd
    assert "](prisma-flow.svg)" in qmd


def test_report_renderer_requires_quarto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("biblioflow.reporting.renderer.shutil.which", lambda _: None)

    with pytest.raises(ReportRenderError, match="Quarto CLI was not found"):
        ReportRenderer().render_pdf("report.qmd", "report.pdf")


def test_report_renderer_runs_quarto_and_moves_pdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    qmd_path = tmp_path / "work" / "report.qmd"
    qmd_path.parent.mkdir()
    qmd_path.write_text("# Report\n", encoding="utf-8")
    output_path = tmp_path / "exports" / "report.pdf"
    observed: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        observed["command"] = args[0]
        observed["cwd"] = kwargs["cwd"]
        observed["env"] = kwargs["env"]
        (qmd_path.parent / output_path.name).write_text("pdf", encoding="utf-8")
        return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")

    monkeypatch.setattr(
        "biblioflow.reporting.renderer.shutil.which", lambda _: "quarto"
    )
    monkeypatch.setattr("biblioflow.reporting.renderer.subprocess.run", fake_run)

    ReportRenderer().render_pdf(qmd_path, output_path)

    assert output_path.read_text(encoding="utf-8") == "pdf"
    assert not (qmd_path.parent / output_path.name).exists()
    assert observed["command"] == [
        "quarto",
        "render",
        qmd_path.name,
        "--to",
        "typst",
        "--output",
        output_path.name,
    ]
    assert observed["cwd"] == qmd_path.parent
    assert observed["env"]["TMPDIR"] == str(qmd_path.parent / ".quarto-tmp")


def test_report_renderer_reports_quarto_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    qmd_path = tmp_path / "report.qmd"
    qmd_path.write_text("# Report\n", encoding="utf-8")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args[0], 2, stdout="stdout details", stderr=""
        )

    monkeypatch.setattr(
        "biblioflow.reporting.renderer.shutil.which", lambda _: "quarto"
    )
    monkeypatch.setattr("biblioflow.reporting.renderer.subprocess.run", fake_run)

    with pytest.raises(ReportRenderError, match="stdout details"):
        ReportRenderer().render_pdf(qmd_path, tmp_path / "report.pdf")

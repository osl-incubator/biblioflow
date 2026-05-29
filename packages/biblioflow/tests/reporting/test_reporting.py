from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import biblioflow as bf
from biblioflow.cli import main
from biblioflow.reporting import (
    PrismaFlow,
    ReportProject,
    generate_report,
    render_prisma_svg,
    validate_prisma,
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

"""
title: Quarto/Typst report renderer for biblioflow.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from biblioflow.reporting.context import build_report_context, write_context
from biblioflow.reporting.errors import ReportRenderError
from biblioflow.reporting.models import (
    ReportCompleteness,
    ReportProject,
    ReportResult,
    ReportWarning,
)


class ReportRenderer:
    """
    title: >-
      Build QMD files and optionally render them to PDF with Quarto + Typst.
    attributes:
      template:
        description: Report template name.
    """

    def __init__(self, *, template: str = "modern") -> None:
        """
        title: Initialize the report renderer.
        parameters:
          template:
            type: str
        """
        self.template = template

    def build_context(
        self,
        project: ReportProject,
        *,
        assets_dir: str | Path,
        completeness: ReportCompleteness = "standard",
        top_n: int = 20,
    ) -> tuple[dict[str, Any], list[ReportWarning]]:
        """
        title: Build the serializable report context.
        parameters:
          project:
            type: ReportProject
          assets_dir:
            type: str | Path
          completeness:
            type: ReportCompleteness
          top_n:
            type: int
        returns:
          type: tuple[dict[str, Any], list[ReportWarning]]
        """
        return build_report_context(
            project,
            assets_dir=assets_dir,
            completeness=completeness,
            top_n=top_n,
        )

    def write_qmd(self, context: dict[str, Any], path: str | Path) -> Path:
        """
        title: Write a Quarto QMD report file.
        parameters:
          context:
            type: dict[str, Any]
          path:
            type: str | Path
        returns:
          type: Path
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_qmd(context), encoding="utf-8")
        return target

    def render_pdf(self, qmd_path: str | Path, output: str | Path) -> None:
        """
        title: Render a QMD file to PDF through Quarto's Typst format.
        parameters:
          qmd_path:
            type: str | Path
          output:
            type: str | Path
        """
        quarto = shutil.which("quarto")
        if quarto is None:
            raise ReportRenderError(
                "Quarto CLI was not found. Install Quarto or call "
                "generate_report(..., render=False) to inspect the generated QMD."
            )
        qmd = Path(qmd_path)
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = qmd.parent / ".quarto-tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        env = {
            **os.environ,
            "TMPDIR": str(temp_dir),
            "TMP": str(temp_dir),
            "TEMP": str(temp_dir),
        }
        command = [
            quarto,
            "render",
            qmd.name,
            "--to",
            "typst",
            "--output",
            output_path.name,
        ]
        completed = subprocess.run(
            command,
            cwd=qmd.parent,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip()
            raise ReportRenderError(f"Quarto report rendering failed: {details}")
        rendered_path = qmd.parent / output_path.name
        if rendered_path != output_path and rendered_path.exists():
            shutil.move(str(rendered_path), output_path)


def generate_report(
    project: ReportProject,
    *,
    output: str | Path,
    template: str = "modern",
    completeness: ReportCompleteness = "standard",
    top_n: int = 20,
    render: bool = True,
    keep_qmd: bool = True,
    keep_context: bool = True,
) -> ReportResult:
    """
    title: Generate a professional project report from a structured project.
    parameters:
      project:
        type: ReportProject
      output:
        type: str | Path
      template:
        type: str
      completeness:
        type: ReportCompleteness
      top_n:
        type: int
      render:
        type: bool
      keep_qmd:
        type: bool
      keep_context:
        type: bool
    returns:
      type: ReportResult
    """
    output_path = Path(output)
    qmd_path = output_path.with_suffix(".qmd")
    context_path = output_path.with_suffix(".context.json")
    assets_dir = output_path.parent / f"{output_path.stem}_assets"
    renderer = ReportRenderer(template=template)
    context, warnings = renderer.build_context(
        project,
        assets_dir=assets_dir,
        completeness=completeness,
        top_n=top_n,
    )
    renderer.write_qmd(context, qmd_path)
    write_context(context_path, context)
    rendered = False
    if render:
        renderer.render_pdf(qmd_path, output_path)
        rendered = True
    if not keep_qmd and qmd_path.exists():
        qmd_path.unlink()
    if not keep_context and context_path.exists():
        context_path.unlink()
    sections = context.get("sections", {})
    rendered_sections = [str(item) for item in sections.get("rendered", [])]
    skipped_sections = [str(item) for item in sections.get("skipped", [])]
    return ReportResult(
        output_path=output_path,
        qmd_path=qmd_path,
        context_path=context_path,
        assets_dir=assets_dir,
        warnings=warnings,
        sections_rendered=rendered_sections,
        sections_skipped=skipped_sections,
        rendered=rendered,
    )


def report(project: ReportProject, **kwargs: Any) -> ReportResult:
    """
    title: Alias for :func:`generate_report`.
    parameters:
      project:
        type: ReportProject
      kwargs:
        type: Any
        variadic: keyword
    returns:
      type: ReportResult
    """
    return generate_report(project, **kwargs)


def render_qmd(context: dict[str, Any]) -> str:
    """
    title: Render a Quarto QMD document from report context.
    parameters:
      context:
        type: dict[str, Any]
    returns:
      type: str
    """
    project = context["project"]
    report_meta = context["report"]
    title = _escape_yaml(str(project.get("title") or "biblioflow report"))
    subtitle = _escape_yaml(str(project.get("subtitle") or "Project report"))
    authors = project.get("authors") or []
    author_text = ", ".join(str(author) for author in authors) or "biblioflow"
    lines = [
        "---",
        f'title: "{title}"',
        f'subtitle: "{subtitle}"',
        f'author: "{_escape_yaml(author_text)}"',
        f'date: "{_escape_yaml(str(report_meta.get("date") or ""))}"',
        "format:",
        "  typst:",
        "    papersize: a4",
        "    toc: true",
        "    toc-depth: 3",
        "    number-sections: true",
        "    columns: 1",
        "execute:",
        "  echo: false",
        "  warning: false",
        "  message: false",
        "---",
        "",
        "```{=typst}",
        '#set document(author: "biblioflow")',
        "#set page(margin: (x: 2.2cm, y: 2.0cm))",
        '#set text(font: "Libertinus Serif", size: 10.5pt, fill: rgb(31, 41, 55))',
        "#show heading: it => block(above: 1.1em, below: 0.55em, it)",
        "```",
        "",
        "::: {.callout-note}",
        (
            "Generated by `biblioflow` on "
            f"**{report_meta.get('generated_at')}**. Completeness level: "
            f"**{report_meta.get('completeness')}**."
        ),
        ":::",
        "",
        "# Executive summary",
        "",
        _executive_summary(context),
        "",
        "# Project overview",
        "",
        _project_overview(context),
        "",
        "# Methods",
        "",
        _methods(context),
        "",
        "# PRISMA-style evidence flow",
        "",
        (
            "![PRISMA-inspired evidence flow]"
            f"({_relative_asset(context['prisma']['svg'])})"
            "{#fig-prisma}"
        ),
        "",
        _markdown_table(context["prisma"]["rows"], ["stage", "count"]),
        "",
        "# Corpus overview",
        "",
        _corpus_overview(context),
        "",
        "## Annual production",
        "",
        _markdown_table(
            context["tables"]["annual_production"], ["publication_year", "documents"]
        ),
        "",
        "## Document types",
        "",
        _markdown_table(
            context["tables"]["document_types"], ["document_type", "documents"]
        ),
        "",
        "# Descriptive bibliometrics",
        "",
        "## Top sources",
        "",
        _markdown_table(
            context["tables"]["top_sources"], ["source_title", "documents"]
        ),
        "",
        "## Top authors",
        "",
        _markdown_table(context["tables"]["top_authors"], ["author", "documents"]),
        "",
        "## Top keywords",
        "",
        _markdown_table(context["tables"]["top_keywords"], ["keyword", "documents"]),
        "",
        "# Affiliations and geography",
        "",
        "## Top countries",
        "",
        _markdown_table(context["tables"]["top_countries"], ["country", "documents"]),
        "",
        "## Top institutions",
        "",
        _markdown_table(
            context["tables"]["top_institutions"], ["institution", "documents"]
        ),
        "",
        "# Data quality and validation",
        "",
        "## Field coverage",
        "",
        _markdown_table(
            context["field_profile"],
            ["field", "present", "missing", "coverage_percent"],
        ),
        "",
        "## Warnings",
        "",
        _warnings(context),
        "",
        "# Reproducibility",
        "",
        _reproducibility(context),
        "",
        "# Appendices",
        "",
        "## Source inventory",
        "",
        _markdown_table(
            context["sources"],
            ["label", "path", "format", "provider", "searched_on", "sha256"],
        ),
        "",
        "## Sample records",
        "",
        _markdown_table(
            context["tables"]["sample_records"],
            ["title", "authors", "source_title", "publication_year", "doi"],
        ),
        "",
    ]
    return "\n".join(lines)


def _executive_summary(context: dict[str, Any]) -> str:
    """
    title: Render the executive summary text.
    parameters:
      context:
        type: dict[str, Any]
    returns:
      type: str
    """
    summary = context.get("summary", {})
    title = context.get("project", {}).get("title") or "This project"
    documents = summary.get("documents", 0)
    sources = summary.get("sources", 0)
    authors = summary.get("authors", 0)
    keywords = summary.get("keywords", 0)
    start = summary.get("timespan_start")
    end = summary.get("timespan_end")
    timespan = f" from {start} to {end}" if start and end else ""
    return (
        f"**{title}** includes **{documents}** bibliographic records{timespan}. "
        f"The normalized corpus contains **{sources}** sources, **{authors}** authors, "
        f"and **{keywords}** normalized keyword terms. The sections below summarize "
        "project scope, methods, PRISMA-style flow, descriptive bibliometrics, "
        "data quality, and reproducibility metadata."
    )


def _project_overview(context: dict[str, Any]) -> str:
    """
    title: Render the project overview section.
    parameters:
      context:
        type: dict[str, Any]
    returns:
      type: str
    """
    project = context["project"]
    parts = []
    if project.get("organization"):
        parts.append(f"**Organization:** {project['organization']}")
    if project.get("project_id"):
        parts.append(f"**Project ID:** `{project['project_id']}`")
    if project.get("research_questions"):
        parts.append(
            "## Research questions\n" + _bullet_list(project["research_questions"])
        )
    if project.get("objectives"):
        parts.append("## Objectives\n" + _bullet_list(project["objectives"]))
    if project.get("inclusion_criteria"):
        parts.append(
            "## Inclusion criteria\n" + _bullet_list(project["inclusion_criteria"])
        )
    if project.get("exclusion_criteria"):
        parts.append(
            "## Exclusion criteria\n" + _bullet_list(project["exclusion_criteria"])
        )
    return "\n\n".join(parts) if parts else "Project metadata was not provided."


def _methods(context: dict[str, Any]) -> str:
    """
    title: Render the report methods section.
    parameters:
      context:
        type: dict[str, Any]
    returns:
      type: str
    """
    sources = context.get("sources", [])
    text = [
        (
            "Records were loaded with `biblioflow`, normalized into the canonical "
            "bibliographic schema, validated, and summarized using the core "
            "analysis APIs."
        ),
        (
            "Source format and semantic provider metadata are preserved when "
            "available so that the report remains traceable to the original imports."
        ),
    ]
    if sources:
        text.append(
            f"The report context includes **{len(sources)}** source entry or entries."
        )
    return "\n\n".join(text)


def _corpus_overview(context: dict[str, Any]) -> str:
    """
    title: Render the corpus overview table.
    parameters:
      context:
        type: dict[str, Any]
    returns:
      type: str
    """
    summary = context.get("summary", {})
    rows = [
        {"metric": "Documents", "value": summary.get("documents", 0)},
        {"metric": "Sources", "value": summary.get("sources", 0)},
        {"metric": "Authors", "value": summary.get("authors", 0)},
        {"metric": "Keywords", "value": summary.get("keywords", 0)},
        {"metric": "Documents with DOI", "value": summary.get("documents_with_doi", 0)},
        {"metric": "Timespan start", "value": summary.get("timespan_start")},
        {"metric": "Timespan end", "value": summary.get("timespan_end")},
    ]
    return _markdown_table(rows, ["metric", "value"])


def _warnings(context: dict[str, Any]) -> str:
    """
    title: Render report warnings as Markdown.
    parameters:
      context:
        type: dict[str, Any]
    returns:
      type: str
    """
    warnings = context.get("warnings", [])
    if not warnings:
        return "No report or dataset warnings were emitted."
    return _markdown_table(warnings, ["severity", "code", "message"])


def _reproducibility(context: dict[str, Any]) -> str:
    """
    title: Render reproducibility metadata as Markdown.
    parameters:
      context:
        type: dict[str, Any]
    returns:
      type: str
    """
    rep = context.get("reproducibility", {})
    rows = [
        {"item": "biblioflow version", "value": rep.get("biblioflow_version")},
        {"item": "Python version", "value": rep.get("python_version")},
        {"item": "Platform", "value": rep.get("platform")},
        {"item": "Generated at", "value": rep.get("generated_at")},
    ]
    return _markdown_table(rows, ["item", "value"])


def _markdown_table(
    rows: list[dict[str, Any]], columns: list[str], *, limit: int = 25
) -> str:
    """
    title: Render dictionaries as a Markdown table.
    parameters:
      rows:
        type: list[dict[str, Any]]
      columns:
        type: list[str]
      limit:
        type: int
    returns:
      type: str
    """
    if not rows:
        return "_No data available._"
    selected = rows[:limit]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in selected:
        body.append(
            "| " + " | ".join(_cell(row.get(column)) for column in columns) + " |"
        )
    if len(rows) > limit:
        body.append(
            f"| _Showing first {limit} of {len(rows)} rows_ | "
            + " | ".join("" for _ in columns[1:])
            + " |"
        )
    return "\n".join([header, separator, *body])


def _cell(value: Any) -> str:
    """
    title: Render one Markdown table cell.
    parameters:
      value:
        type: Any
    returns:
      type: str
    """
    if value is None:
        return ""
    if isinstance(value, list):
        text = ", ".join(str(item) for item in value[:4])
        if len(value) > 4:
            text += ", …"
    elif isinstance(value, dict):
        text = ", ".join(f"{key}: {item}" for key, item in list(value.items())[:4])
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def _bullet_list(items: list[Any]) -> str:
    """
    title: Render values as a Markdown bullet list.
    parameters:
      items:
        type: list[Any]
    returns:
      type: str
    """
    return "\n".join(f"- {item}" for item in items)


def _relative_asset(path: str) -> str:
    """
    title: Return a QMD-relative asset path.
    parameters:
      path:
        type: str
    returns:
      type: str
    """
    asset_path = Path(path)
    if asset_path.parent.name.endswith("_assets"):
        return f"{asset_path.parent.name}/{asset_path.name}"
    return path


def _escape_yaml(value: str) -> str:
    """
    title: Escape a string for simple YAML scalar output.
    parameters:
      value:
        type: str
    returns:
      type: str
    """
    return value.replace('"', '\\"')


__all__ = ["ReportRenderer", "generate_report", "render_qmd", "report"]

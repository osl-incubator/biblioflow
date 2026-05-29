"""
title: Build serializable report contexts from biblioflow projects.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from biblioflow.analysis import analyze
from biblioflow.reporting.models import (
    PrismaFlow,
    ReportCompleteness,
    ReportProject,
    ReportWarning,
)
from biblioflow.reporting.prisma import (
    default_prisma,
    prisma_rows,
    validate_prisma,
    write_prisma_svg,
)
from biblioflow.results import summarize_dataset
from biblioflow.schema import CANONICAL_FIELDS

IMPORTANT_FIELDS = (
    "title",
    "authors",
    "source_title",
    "publication_year",
    "doi",
    "abstract",
    "keywords_all",
    "references",
)


def build_report_context(
    project: ReportProject,
    *,
    assets_dir: str | Path,
    completeness: ReportCompleteness = "standard",
    top_n: int = 20,
) -> tuple[dict[str, Any], list[ReportWarning]]:
    """
    title: Build a JSON-serializable report context and report warnings.
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
    warnings: list[ReportWarning] = []
    dataset = project.records
    if dataset is None:
        warnings.append(
            ReportWarning(
                code="records_missing",
                message="No bibliographic records were available for the report.",
                severity="error",
            )
        )
        records: list[dict[str, Any]] = []
        summary: dict[str, Any] = {}
        descriptive: dict[str, Any] = _empty_descriptive()
    else:
        records = dataset.to_records()
        summary = summarize_dataset(dataset).to_dict()
        descriptive = analyze(dataset, top_n=top_n).to_dict()
        warnings.extend(_dataset_warnings(dataset))

    report_date = project.report_date or datetime.now(timezone.utc).date().isoformat()
    generated_at = datetime.now(timezone.utc).isoformat()
    prisma_flow = _resolve_prisma(project.prisma, len(records))
    warnings.extend(validate_prisma(project.prisma))
    if project.prisma is None and records:
        warnings.append(
            ReportWarning(
                code="prisma_inferred_from_records",
                message=(
                    "PRISMA counts were inferred from the corpus size; provide "
                    "explicit counts for review-grade reporting."
                ),
            )
        )
    assets_path = Path(assets_dir)
    assets_path.mkdir(parents=True, exist_ok=True)
    prisma_path = write_prisma_svg(
        prisma_flow,
        assets_path / "prisma-flow.svg",
        title=f"{project.title} — PRISMA flow",
    )
    table_context = _tables(descriptive, records, prisma_flow)
    field_profile = _field_profile(records)
    source_inventory = _source_inventory(project)
    sections = _sections(table_context, project, records, completeness)
    context = {
        "project": project.to_dict(),
        "report": {
            "date": report_date,
            "generated_at": generated_at,
            "completeness": completeness,
            "top_n": top_n,
        },
        "summary": summary,
        "descriptive": descriptive,
        "tables": table_context,
        "field_profile": field_profile,
        "sources": source_inventory,
        "prisma": {
            "flow": prisma_flow.to_dict(),
            "rows": prisma_rows(prisma_flow),
            "svg": str(prisma_path),
        },
        "assets": _asset_context(project, assets_path),
        "reproducibility": _reproducibility(project, generated_at),
        "warnings": [warning.to_dict() for warning in warnings],
        "sections": sections,
    }
    return _jsonable(context), warnings


def write_context(path: str | Path, context: dict[str, Any]) -> Path:
    """
    title: Write a report context JSON file.
    parameters:
      path:
        type: str | Path
      context:
        type: dict[str, Any]
    returns:
      type: Path
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_jsonable(context), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def _resolve_prisma(flow: PrismaFlow | None, records: int) -> PrismaFlow:
    """
    title: Return explicit PRISMA counts or derive defaults from record count.
    parameters:
      flow:
        type: PrismaFlow | None
      records:
        type: int
    returns:
      type: PrismaFlow
    """
    if flow is not None:
        return flow
    return default_prisma(records)


def _dataset_warnings(dataset: Any) -> list[ReportWarning]:
    """
    title: Convert dataset warnings into report warnings.
    parameters:
      dataset:
        type: Any
    returns:
      type: list[ReportWarning]
    """
    if not hasattr(dataset, "warning_dicts"):
        return []
    warnings = []
    for item in dataset.warning_dicts():
        warnings.append(
            ReportWarning(
                code=str(item.get("code") or "dataset_warning"),
                message=str(
                    item.get("message") or item.get("code") or "Dataset warning"
                ),
                severity=str(item.get("severity") or "warning"),
                details={str(key): value for key, value in item.items()},
            )
        )
    return warnings


def _empty_descriptive() -> dict[str, Any]:
    """
    title: Return an empty descriptive-analysis context.
    returns:
      type: dict[str, Any]
    """
    return {
        "main_information": {},
        "annual_production": [],
        "top_authors": [],
        "top_sources": [],
        "top_keywords": [],
        "metadata": {},
    }


def _tables(
    descriptive: dict[str, Any], records: list[dict[str, Any]], prisma_flow: PrismaFlow
) -> dict[str, list[dict[str, Any]]]:
    """
    title: Build report table contexts from analysis and records.
    parameters:
      descriptive:
        type: dict[str, Any]
      records:
        type: list[dict[str, Any]]
      prisma_flow:
        type: PrismaFlow
    returns:
      type: dict[str, list[dict[str, Any]]]
    """
    countries = Counter(
        country
        for record in records
        for country in _list_values(record.get("countries"))
    )
    institutions = Counter(
        institution
        for record in records
        for institution in _list_values(record.get("institutions"))
    )
    document_types = Counter(
        str(record.get("document_type"))
        for record in records
        if record.get("document_type")
    )
    return {
        "annual_production": _records(descriptive.get("annual_production")),
        "top_sources": _records(descriptive.get("top_sources")),
        "top_authors": _records(descriptive.get("top_authors")),
        "top_keywords": _records(descriptive.get("top_keywords")),
        "top_countries": _counter_rows(countries, "country", "documents"),
        "top_institutions": _counter_rows(institutions, "institution", "documents"),
        "document_types": _counter_rows(document_types, "document_type", "documents"),
        "prisma_counts": prisma_rows(prisma_flow),
    }


def _source_inventory(project: ReportProject) -> list[dict[str, Any]]:
    """
    title: Build source inventory rows with file hashes when available.
    parameters:
      project:
        type: ReportProject
    returns:
      type: list[dict[str, Any]]
    """
    rows = []
    for source in project.sources:
        payload = source.to_dict()
        path = source.path
        if path:
            file_path = Path(path)
            if file_path.exists():
                payload["sha256"] = _sha256(file_path)
                payload["size"] = file_path.stat().st_size
        rows.append(payload)
    return rows


def _asset_context(project: ReportProject, assets_dir: Path) -> list[dict[str, Any]]:
    """
    title: Build asset inventory rows for provided and generated assets.
    parameters:
      project:
        type: ReportProject
      assets_dir:
        type: Path
    returns:
      type: list[dict[str, Any]]
    """
    rows = []
    for asset in project.assets:
        payload = asset.to_dict()
        source_path = Path(asset.path)
        payload["exists"] = source_path.exists()
        payload["resolved_path"] = (
            str(source_path.resolve()) if source_path.exists() else asset.path
        )
        rows.append(payload)
    rows.append(
        {
            "path": str(assets_dir / "prisma-flow.svg"),
            "label": "prisma_flow",
            "caption": "PRISMA-inspired evidence flow diagram.",
            "kind": "generated_svg",
            "exists": True,
        }
    )
    return rows


def _field_profile(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    title: Compute coverage statistics for important bibliographic fields.
    parameters:
      records:
        type: list[dict[str, Any]]
    returns:
      type: list[dict[str, Any]]
    """
    total = len(records)
    rows = []
    for field in IMPORTANT_FIELDS:
        present = sum(1 for record in records if _has_value(record.get(field)))
        rows.append(
            {
                "field": field,
                "present": present,
                "missing": total - present,
                "coverage_percent": round((present / total) * 100, 1) if total else 0.0,
            }
        )
    return rows


def _sections(
    tables: dict[str, list[dict[str, Any]]],
    project: ReportProject,
    records: list[dict[str, Any]],
    completeness: ReportCompleteness,
) -> dict[str, list[str]]:
    """
    title: Determine rendered and skipped report sections.
    parameters:
      tables:
        type: dict[str, list[dict[str, Any]]]
      project:
        type: ReportProject
      records:
        type: list[dict[str, Any]]
      completeness:
        type: ReportCompleteness
    returns:
      type: dict[str, list[str]]
    """
    rendered = [
        "cover",
        "executive_summary",
        "project_overview",
        "methods",
        "prisma",
        "corpus_overview",
        "data_quality",
        "reproducibility",
    ]
    skipped: list[str] = []
    optional_tables = {
        "descriptive_analysis": tables["annual_production"],
        "authors": tables["top_authors"],
        "sources": tables["top_sources"],
        "keywords": tables["top_keywords"],
        "geography": tables["top_countries"] or tables["top_institutions"],
    }
    for section, rows in optional_tables.items():
        if rows:
            rendered.append(section)
        else:
            skipped.append(section)
    if completeness == "complete" and records:
        rendered.append("appendices")
    if not project.research_questions:
        skipped.append("research_questions")
    return {"rendered": rendered, "skipped": skipped}


def _reproducibility(project: ReportProject, generated_at: str) -> dict[str, Any]:
    """
    title: Build reproducibility metadata for the report.
    parameters:
      project:
        type: ReportProject
      generated_at:
        type: str
    returns:
      type: dict[str, Any]
    """
    return {
        "biblioflow_version": _package_version("biblioflow"),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "generated_at": generated_at,
        "project_id": project.project_id,
        "source_hashes": [
            {"path": source.path, "sha256": _sha256(Path(source.path))}
            for source in project.sources
            if source.path and Path(source.path).exists()
        ],
    }


def _records(value: Any) -> list[dict[str, Any]]:
    """
    title: Coerce a value into a list of record dictionaries.
    parameters:
      value:
        type: Any
    returns:
      type: list[dict[str, Any]]
    """
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    return []


def _counter_rows(
    counter: Counter[str], key: str, value: str, limit: int = 20
) -> list[dict[str, Any]]:
    """
    title: Convert a counter into top-N table rows.
    parameters:
      counter:
        type: Counter[str]
      key:
        type: str
      value:
        type: str
      limit:
        type: int
    returns:
      type: list[dict[str, Any]]
    """
    return [{key: item, value: count} for item, count in counter.most_common(limit)]


def _list_values(value: Any) -> list[str]:
    """
    title: Normalize a scalar or list value into strings.
    parameters:
      value:
        type: Any
    returns:
      type: list[str]
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text and text.casefold() != "nan" else []


def _has_value(value: Any) -> bool:
    """
    title: Return whether a bibliographic field has a meaningful value.
    parameters:
      value:
        type: Any
    returns:
      type: bool
    """
    if value is None:
        return False
    if isinstance(value, list | tuple | dict | set):
        return bool(value)
    text = str(value).strip()
    return bool(text) and text.casefold() != "nan"


def _sha256(path: Path) -> str:
    """
    title: Compute a SHA-256 digest for a local file.
    parameters:
      path:
        type: Path
    returns:
      type: str
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_version(name: str) -> str | None:
    """
    title: Return an installed package version when available.
    parameters:
      name:
        type: str
    returns:
      type: str | None
    """
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _jsonable(value: Any) -> Any:
    """
    title: Coerce nested values into JSON-compatible objects.
    parameters:
      value:
        type: Any
    returns:
      type: Any
    """
    return json.loads(json.dumps(value, default=str, ensure_ascii=False))


__all__ = ["CANONICAL_FIELDS", "build_report_context", "write_context"]

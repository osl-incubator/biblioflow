"""
title: Structured models for biblioflow report generation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.load import load

ReportCompleteness = Literal["summary", "standard", "complete"]


@dataclass(frozen=True)
class ReportWarning:
    """
    title: Structured warning emitted while building or rendering a report.
    attributes:
      code:
        type: str
      message:
        type: str
      severity:
        type: str
      details:
        type: dict[str, Any]
    """

    code: str
    message: str
    severity: str = "warning"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        title: Return a JSON-serializable warning.
        returns:
          type: dict[str, Any]
        """
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "details": self.details,
        }


@dataclass(frozen=True)
class ReportSource:
    """
    title: One bibliographic source used by a report project.
    attributes:
      path:
        type: str | None
      format:
        type: str | None
      provider:
        type: str | None
      searched_on:
        type: str | None
      search_query:
        type: str | None
      label:
        type: str | None
      metadata:
        type: dict[str, Any]
    """

    path: str | None = None
    format: str | None = None
    provider: str | None = None
    searched_on: str | None = None
    search_query: str | None = None
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> ReportSource:
        """
        title: Build a source from a manifest mapping.
        parameters:
          value:
            type: dict[str, Any]
        returns:
          type: ReportSource
        """
        return cls(
            path=_optional_string(value.get("path")),
            format=_optional_string(value.get("format")),
            provider=_optional_string(value.get("provider")),
            searched_on=_optional_string(value.get("searched_on")),
            search_query=_optional_string(value.get("search_query")),
            label=_optional_string(value.get("label") or value.get("name")),
            metadata={
                str(key): item
                for key, item in value.items()
                if key
                not in {
                    "path",
                    "format",
                    "provider",
                    "searched_on",
                    "search_query",
                    "label",
                    "name",
                }
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """
        title: Return a JSON-serializable source.
        returns:
          type: dict[str, Any]
        """
        return {
            "path": self.path,
            "format": self.format,
            "provider": self.provider,
            "searched_on": self.searched_on,
            "search_query": self.search_query,
            "label": self.label,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ReportAsset:
    """
    title: Static asset to include in a report.
    attributes:
      path:
        type: str
      label:
        type: str | None
      caption:
        type: str | None
      kind:
        type: str
    """

    path: str
    label: str | None = None
    caption: str | None = None
    kind: str = "image"

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> ReportAsset:
        """
        title: Build an asset from a manifest mapping.
        parameters:
          value:
            type: dict[str, Any]
        returns:
          type: ReportAsset
        """
        return cls(
            path=str(value["path"]),
            label=_optional_string(value.get("label")),
            caption=_optional_string(value.get("caption")),
            kind=str(value.get("kind") or "image"),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        title: Return a JSON-serializable asset.
        returns:
          type: dict[str, Any]
        """
        return {
            "path": self.path,
            "label": self.label,
            "caption": self.caption,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class PrismaFlow:
    """
    title: PRISMA-inspired evidence-flow counts for a project report.
    attributes:
      identified:
        type: int | None
      duplicates_removed:
        type: int | None
      screened:
        type: int | None
      excluded_screening:
        type: int | None
      full_text_assessed:
        type: int | None
      full_text_excluded:
        type: int | None
      included:
        type: int | None
      other_sources:
        type: int | None
      full_text_exclusion_reasons:
        type: dict[str, int]
    """

    identified: int | None = None
    duplicates_removed: int | None = None
    screened: int | None = None
    excluded_screening: int | None = None
    full_text_assessed: int | None = None
    full_text_excluded: int | None = None
    included: int | None = None
    other_sources: int | None = None
    full_text_exclusion_reasons: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: dict[str, Any] | None) -> PrismaFlow | None:
        """
        title: Build PRISMA counts from a manifest mapping.
        parameters:
          value:
            type: dict[str, Any] | None
        returns:
          type: PrismaFlow | None
        """
        if value is None:
            return None
        reasons = value.get("full_text_exclusion_reasons") or value.get(
            "exclusion_reasons"
        )
        return cls(
            identified=_optional_int(value.get("identified")),
            duplicates_removed=_optional_int(
                value.get("duplicates_removed") or value.get("removed_duplicates")
            ),
            screened=_optional_int(value.get("screened")),
            excluded_screening=_optional_int(value.get("excluded_screening")),
            full_text_assessed=_optional_int(value.get("full_text_assessed")),
            full_text_excluded=_optional_int(value.get("full_text_excluded")),
            included=_optional_int(value.get("included")),
            other_sources=_optional_int(value.get("other_sources")),
            full_text_exclusion_reasons=_reasons(reasons),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        title: Return a JSON-serializable PRISMA object.
        returns:
          type: dict[str, Any]
        """
        return {
            "identified": self.identified,
            "duplicates_removed": self.duplicates_removed,
            "screened": self.screened,
            "excluded_screening": self.excluded_screening,
            "full_text_assessed": self.full_text_assessed,
            "full_text_excluded": self.full_text_excluded,
            "included": self.included,
            "other_sources": self.other_sources,
            "full_text_exclusion_reasons": dict(self.full_text_exclusion_reasons),
        }


@dataclass
class ReportProject:
    """
    title: Structured report project consumed by the reporting renderer.
    attributes:
      title:
        type: str
      records:
        type: BibliographicDataset | None
      subtitle:
        type: str | None
      authors:
        type: list[str]
      organization:
        type: str | None
      report_date:
        type: str | None
      project_id:
        type: str | None
      contact:
        type: str | None
      license:
        type: str | None
      research_questions:
        type: list[str]
      objectives:
        type: list[str]
      inclusion_criteria:
        type: list[str]
      exclusion_criteria:
        type: list[str]
      sources:
        type: list[ReportSource]
      prisma:
        type: PrismaFlow | None
      assets:
        type: list[ReportAsset]
      metadata:
        type: dict[str, Any]
    """

    title: str
    records: BibliographicDataset | None = None
    subtitle: str | None = None
    authors: list[str] = field(default_factory=list)
    organization: str | None = None
    report_date: str | None = None
    project_id: str | None = None
    contact: str | None = None
    license: str | None = None
    research_questions: list[str] = field(default_factory=list)
    objectives: list[str] = field(default_factory=list)
    inclusion_criteria: list[str] = field(default_factory=list)
    exclusion_criteria: list[str] = field(default_factory=list)
    sources: list[ReportSource] = field(default_factory=list)
    prisma: PrismaFlow | None = None
    assets: list[ReportAsset] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_records(
        cls,
        records: BibliographicDataset | list[dict[str, Any]] | Any,
        *,
        title: str,
        subtitle: str | None = None,
        authors: list[str] | tuple[str, ...] | None = None,
        organization: str | None = None,
        report_date: str | None = None,
        project_id: str | None = None,
        contact: str | None = None,
        license: str | None = None,
        research_questions: list[str] | tuple[str, ...] | None = None,
        objectives: list[str] | tuple[str, ...] | None = None,
        inclusion_criteria: list[str] | tuple[str, ...] | None = None,
        exclusion_criteria: list[str] | tuple[str, ...] | None = None,
        sources: list[ReportSource | dict[str, Any]] | None = None,
        prisma: PrismaFlow | dict[str, Any] | None = None,
        assets: list[ReportAsset | dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ReportProject:
        """
        title: Build a report project from normalized records or a dataset.
        parameters:
          records:
            type: BibliographicDataset | list[dict[str, Any]] | Any
          title:
            type: str
          subtitle:
            type: str | None
          authors:
            type: list[str] | tuple[str, Ellipsis] | None
          organization:
            type: str | None
          report_date:
            type: str | None
          project_id:
            type: str | None
          contact:
            type: str | None
          license:
            type: str | None
          research_questions:
            type: list[str] | tuple[str, Ellipsis] | None
          objectives:
            type: list[str] | tuple[str, Ellipsis] | None
          inclusion_criteria:
            type: list[str] | tuple[str, Ellipsis] | None
          exclusion_criteria:
            type: list[str] | tuple[str, Ellipsis] | None
          sources:
            type: list[ReportSource | dict[str, Any]] | None
          prisma:
            type: PrismaFlow | dict[str, Any] | None
          assets:
            type: list[ReportAsset | dict[str, Any]] | None
          metadata:
            type: dict[str, Any] | None
        returns:
          type: ReportProject
        """
        dataset = (
            records if isinstance(records, BibliographicDataset) else load(records)
        )
        source_items = [_coerce_source(item) for item in sources or []]
        if not source_items:
            source_items = [_source_from_dataset(dataset)]
        return cls(
            title=title,
            records=dataset,
            subtitle=subtitle,
            authors=list(authors or []),
            organization=organization,
            report_date=report_date,
            project_id=project_id,
            contact=contact,
            license=license,
            research_questions=list(research_questions or []),
            objectives=list(objectives or []),
            inclusion_criteria=list(inclusion_criteria or []),
            exclusion_criteria=list(exclusion_criteria or []),
            sources=source_items,
            prisma=_coerce_prisma(prisma),
            assets=[_coerce_asset(item) for item in assets or []],
            metadata=dict(metadata or {}),
        )

    @classmethod
    def from_manifest(
        cls,
        path: str | Path,
        *,
        load_sources: bool = True,
    ) -> ReportProject:
        """
        title: Build a project from a JSON or YAML manifest.
        parameters:
          path:
            type: str | Path
          load_sources:
            type: bool
        returns:
          type: ReportProject
        """
        manifest_path = Path(path)
        payload = _read_manifest(manifest_path)
        source_items = [
            ReportSource.from_mapping(item)
            for item in _mapping_list(payload.get("sources"))
        ]
        records = None
        if load_sources and source_items:
            loaded_records: list[dict[str, Any]] = []
            for source in source_items:
                if source.path is None:
                    continue
                source_path = Path(source.path)
                if not source_path.is_absolute():
                    source_path = manifest_path.parent / source_path
                dataset = load(
                    source_path,
                    provider=source.provider or "auto",
                    format=source.format or "auto",
                )
                loaded_records.extend(dataset.to_records())
            if loaded_records:
                records = load(loaded_records, provider="generic", format="records")
        manifest_assets = _asset_list(payload.get("assets"))
        return cls(
            title=str(payload.get("title") or "Untitled biblioflow report"),
            records=records,
            subtitle=_optional_string(payload.get("subtitle")),
            authors=_string_list(payload.get("authors")),
            organization=_optional_string(payload.get("organization")),
            report_date=_optional_string(payload.get("report_date")),
            project_id=_optional_string(payload.get("project_id")),
            contact=_optional_string(payload.get("contact")),
            license=_optional_string(payload.get("license")),
            research_questions=_string_list(payload.get("research_questions")),
            objectives=_string_list(payload.get("objectives")),
            inclusion_criteria=_string_list(payload.get("inclusion_criteria")),
            exclusion_criteria=_string_list(payload.get("exclusion_criteria")),
            sources=source_items,
            prisma=PrismaFlow.from_mapping(_optional_mapping(payload.get("prisma"))),
            assets=manifest_assets,
            metadata={
                str(key): item
                for key, item in payload.items()
                if key
                not in {
                    "title",
                    "subtitle",
                    "authors",
                    "organization",
                    "report_date",
                    "project_id",
                    "contact",
                    "license",
                    "research_questions",
                    "objectives",
                    "inclusion_criteria",
                    "exclusion_criteria",
                    "sources",
                    "prisma",
                    "assets",
                }
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """
        title: Return project metadata without expanding all records.
        returns:
          type: dict[str, Any]
        """
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "authors": list(self.authors),
            "organization": self.organization,
            "report_date": self.report_date,
            "project_id": self.project_id,
            "contact": self.contact,
            "license": self.license,
            "research_questions": list(self.research_questions),
            "objectives": list(self.objectives),
            "inclusion_criteria": list(self.inclusion_criteria),
            "exclusion_criteria": list(self.exclusion_criteria),
            "sources": [source.to_dict() for source in self.sources],
            "prisma": self.prisma.to_dict() if self.prisma else None,
            "assets": [asset.to_dict() for asset in self.assets],
            "metadata": dict(self.metadata),
            "records": len(self.records) if self.records is not None else 0,
        }


@dataclass(frozen=True)
class ReportResult:
    """
    title: Metadata describing a report generation run.
    attributes:
      output_path:
        type: Path
      qmd_path:
        type: Path
      context_path:
        type: Path
      assets_dir:
        type: Path
      warnings:
        type: list[ReportWarning]
      sections_rendered:
        type: list[str]
      sections_skipped:
        type: list[str]
      rendered:
        type: bool
    """

    output_path: Path
    qmd_path: Path
    context_path: Path
    assets_dir: Path
    warnings: list[ReportWarning] = field(default_factory=list)
    sections_rendered: list[str] = field(default_factory=list)
    sections_skipped: list[str] = field(default_factory=list)
    rendered: bool = False

    def to_dict(self) -> dict[str, Any]:
        """
        title: Return a JSON-serializable result.
        returns:
          type: dict[str, Any]
        """
        return {
            "output_path": str(self.output_path),
            "qmd_path": str(self.qmd_path),
            "context_path": str(self.context_path),
            "assets_dir": str(self.assets_dir),
            "warnings": [warning.to_dict() for warning in self.warnings],
            "sections_rendered": list(self.sections_rendered),
            "sections_skipped": list(self.sections_skipped),
            "rendered": self.rendered,
        }


def _coerce_source(value: ReportSource | dict[str, Any]) -> ReportSource:
    """
    title: Coerce a source-like value into a report source.
    parameters:
      value:
        type: ReportSource | dict[str, Any]
    returns:
      type: ReportSource
    """
    if isinstance(value, ReportSource):
        return value
    return ReportSource.from_mapping(value)


def _coerce_asset(value: ReportAsset | dict[str, Any]) -> ReportAsset:
    """
    title: Coerce an asset-like value into a report asset.
    parameters:
      value:
        type: ReportAsset | dict[str, Any]
    returns:
      type: ReportAsset
    """
    if isinstance(value, ReportAsset):
        return value
    return ReportAsset.from_mapping(value)


def _coerce_prisma(value: PrismaFlow | dict[str, Any] | None) -> PrismaFlow | None:
    """
    title: Coerce PRISMA-like values into a PRISMA flow model.
    parameters:
      value:
        type: PrismaFlow | dict[str, Any] | None
    returns:
      type: PrismaFlow | None
    """
    if value is None or isinstance(value, PrismaFlow):
        return value
    return PrismaFlow.from_mapping(value)


def _source_from_dataset(dataset: BibliographicDataset) -> ReportSource:
    """
    title: Build a report source from dataset metadata.
    parameters:
      dataset:
        type: BibliographicDataset
    returns:
      type: ReportSource
    """
    metadata = dict(dataset.metadata)
    return ReportSource(
        path=_optional_string(metadata.get("source")),
        format=_optional_string(metadata.get("format")),
        provider=_optional_string(metadata.get("provider")),
        label=_optional_string(metadata.get("name")),
        metadata=metadata,
    )


def _read_manifest(path: Path) -> dict[str, Any]:
    """
    title: Read a JSON or YAML report manifest.
    parameters:
      path:
        type: Path
    returns:
      type: dict[str, Any]
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix.casefold() == ".json":
        payload = json.loads(text)
    else:
        import yaml

        payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise ValueError("Report manifest must be a mapping.")
    return {str(key): value for key, value in payload.items()}


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    """
    title: Return mapping items from a list-like value.
    parameters:
      value:
        type: Any
    returns:
      type: list[dict[str, Any]]
    """
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _asset_list(value: Any) -> list[ReportAsset]:
    """
    title: Return report assets from a manifest asset value.
    parameters:
      value:
        type: Any
    returns:
      type: list[ReportAsset]
    """
    if isinstance(value, dict):
        assets = []
        logo = value.get("logo")
        cover = value.get("cover_image")
        if logo:
            assets.append(ReportAsset(path=str(logo), label="logo", kind="logo"))
        if cover:
            assets.append(
                ReportAsset(path=str(cover), label="cover_image", kind="cover_image")
            )
        for item in _mapping_list(value.get("images")):
            assets.append(ReportAsset.from_mapping(item))
        return assets
    return [ReportAsset.from_mapping(item) for item in _mapping_list(value)]


def _optional_mapping(value: Any) -> dict[str, Any] | None:
    """
    title: Coerce a value into an optional string-keyed mapping.
    parameters:
      value:
        type: Any
    returns:
      type: dict[str, Any] | None
    """
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return None


def _string_list(value: Any) -> list[str]:
    """
    title: Coerce a scalar or sequence into a string list.
    parameters:
      value:
        type: Any
    returns:
      type: list[str]
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list | tuple):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _optional_string(value: Any) -> str | None:
    """
    title: Coerce a value into an optional stripped string.
    parameters:
      value:
        type: Any
    returns:
      type: str | None
    """
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    """
    title: Coerce a value into an optional non-negative integer.
    parameters:
      value:
        type: Any
    returns:
      type: int | None
    """
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return None


def _reasons(value: Any) -> dict[str, int]:
    """
    title: Coerce exclusion reasons into a positive-count mapping.
    parameters:
      value:
        type: Any
    returns:
      type: dict[str, int]
    """
    if not isinstance(value, dict):
        return {}
    reasons: dict[str, int] = {}
    for key, item in value.items():
        count = _optional_int(item)
        if count is not None and count > 0:
            reasons[str(key)] = count
    return reasons

"""API request models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


def _default_promoted_statuses() -> list[Literal["candidate", "selected"]]:
    """Return default candidate statuses promoted into datasets."""
    return ["selected"]


def _default_screening_statuses() -> list[Literal["candidate", "selected", "maybe"]]:
    """Return default generic screening statuses promoted into datasets."""
    return ["selected"]


class ProjectCreateRequest(BaseModel):
    """Request body for project creation."""

    name: str | None = None


class DatasetLoadRequest(BaseModel):
    """Request body for dataset loading."""

    upload_ids: list[str] | None = None
    provider: str = "auto"
    format: str = "auto"


class RemoteSourceImportRequest(BaseModel):
    """Request body for PubMed/PMC dataset import."""

    source: Literal["pubmed", "pmc", "pubmed_central"] = "pubmed"
    query: str = Field(min_length=1)
    limit: int = Field(default=100, ge=1, le=1000)
    email: str | None = None
    api_key: str | None = None
    tool: str = "biblioflow-web"
    name: str | None = None


class RemoteSourceSearchRequest(BaseModel):
    """Request body for staging a PubMed/PMC screening search."""

    source: Literal["pubmed", "pmc", "pubmed_central"] = "pubmed"
    query: str = Field(min_length=1)
    limit: int = Field(default=100, ge=1, le=1000)
    email: str | None = None
    api_key: str | None = None
    tool: str = "biblioflow-web"
    name: str | None = None


class CandidateDecisionRequest(BaseModel):
    """Request body for applying a decision to staged candidates."""

    candidate_ids: list[str] = Field(default_factory=list)
    status: Literal["candidate", "selected", "excluded", "duplicate"] = "selected"


class CandidatePromotionRequest(BaseModel):
    """Request body for promoting screened candidates into a dataset."""

    candidate_ids: list[str] | None = None
    include_statuses: list[Literal["candidate", "selected"]] = Field(
        default_factory=_default_promoted_statuses
    )
    name: str | None = None


class ScreeningRunCreateRequest(BaseModel):
    """Request body for creating a generic screening run."""

    origin_type: Literal["uploads", "remote_search", "records"]
    source: str = "auto"
    format: str = "auto"
    upload_ids: list[str] | None = None
    query: str | None = None
    limit: int = Field(default=100, ge=1, le=5000)
    email: str | None = None
    api_key: str | None = None
    tool: str = "biblioflow-web"
    name: str | None = None
    records: list[dict[str, Any]] | None = None


class ScreeningCandidateDecisionRequest(BaseModel):
    """Request body for applying generic screening decisions."""

    candidate_ids: list[str] = Field(default_factory=list)
    status: Literal[
        "candidate",
        "selected",
        "maybe",
        "excluded",
        "duplicate",
        "error",
    ] = "selected"
    decision_reason: str | None = None
    labels: list[str] | None = None
    notes: str | None = None


class ScreeningCandidatePromotionRequest(BaseModel):
    """Request body for promoting generic screening candidates."""

    candidate_ids: list[str] | None = None
    include_statuses: list[Literal["candidate", "selected", "maybe"]] = Field(
        default_factory=_default_screening_statuses
    )
    name: str | None = None


class FilterRequest(BaseModel):
    """Request body for filter previews/applications."""

    filters: dict[str, Any] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    """Request body for analysis endpoints."""

    top_n: int = Field(default=20, ge=1, le=500)
    filters: dict[str, Any] = Field(default_factory=dict)


class MatrixRequest(BaseModel):
    """Request body for matrix/network endpoints."""

    kind: str = "co_occurrence"
    unit: str = "keywords_all"
    normalize: str | None = None
    min_occurrences: int = Field(default=1, ge=1)
    filters: dict[str, Any] = Field(default_factory=dict)


class ExportRequest(BaseModel):
    """Request body for export endpoints."""

    dataset_id: str
    kind: str = "dataset"
    format: str = "json"


class PrismaFlowRequest(BaseModel):
    """Request body for PRISMA flow generation."""

    dataset_id: str | None = None
    title: str | None = None
    counts: dict[str, Any] = Field(default_factory=dict)

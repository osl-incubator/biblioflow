"""API request models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Request body for project creation."""

    name: str | None = None


class DatasetLoadRequest(BaseModel):
    """Request body for dataset loading."""

    upload_ids: list[str] | None = None
    provider: str = "auto"
    format: str = "auto"


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

"""API response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ApiEnvelope(BaseModel):
    """Consistent success response envelope."""

    data: Any
    warnings: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health response model."""

    service: str
    status: str
    version: str
    biblioflow_version: str | None = None

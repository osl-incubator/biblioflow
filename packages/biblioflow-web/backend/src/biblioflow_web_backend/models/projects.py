"""Project API models."""

from __future__ import annotations

from pydantic import BaseModel


class ProjectResponse(BaseModel):
    """Serialized project response."""

    project_id: str
    name: str
    created_at: str
    updated_at: str

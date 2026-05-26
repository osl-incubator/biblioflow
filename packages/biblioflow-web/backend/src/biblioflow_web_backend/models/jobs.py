"""Job API models."""

from __future__ import annotations

from pydantic import BaseModel


class JobResponse(BaseModel):
    """Serialized job response."""

    job_id: str
    project_id: str
    kind: str
    status: str

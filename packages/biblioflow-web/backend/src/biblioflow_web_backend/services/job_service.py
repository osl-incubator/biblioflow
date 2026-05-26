"""In-process job model placeholder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from biblioflow_web_backend.services.project_store import utc_now


@dataclass
class Job:
    """Simple in-process job record."""

    kind: str
    project_id: str
    job_id: str = field(default_factory=lambda: uuid4().hex)
    status: str = "queued"
    progress_current: int = 0
    progress_total: int = 1
    message: str = ""
    result_ref: str | None = None
    error: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable job record."""
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "kind": self.kind,
            "status": self.status,
            "progress_current": self.progress_current,
            "progress_total": self.progress_total,
            "message": self.message,
            "result_ref": self.result_ref,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

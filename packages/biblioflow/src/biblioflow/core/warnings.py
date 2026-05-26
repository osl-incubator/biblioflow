"""Structured warning objects used by biblioflow."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LoadWarning:
    """A structured warning produced during loading or normalization."""

    code: str
    count: int
    severity: str = "warning"
    message: str = ""
    field: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return the warning as a JSON-serializable dictionary."""
        return {
            "code": self.code,
            "count": self.count,
            "severity": self.severity,
            "message": self.message,
            "field": self.field,
        }

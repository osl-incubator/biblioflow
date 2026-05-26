"""
title: Structured warning objects used by biblioflow.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LoadWarning:
    """
    title: A structured warning produced during loading or normalization.
    attributes:
      code:
        type: str
        description: Code attribute.
      count:
        type: int
        description: Count attribute.
      severity:
        type: str
        description: Severity attribute.
      message:
        type: str
        description: Message attribute.
      field:
        type: str | None
        description: Field attribute.
    """

    code: str
    count: int
    severity: str = "warning"
    message: str = ""
    field: str | None = None

    def to_dict(self) -> dict[str, object]:
        """
        title: Return the warning as a JSON-serializable dictionary.
        returns:
          type: dict[str, object]
        """
        return {
            "code": self.code,
            "count": self.count,
            "severity": self.severity,
            "message": self.message,
            "field": self.field,
        }

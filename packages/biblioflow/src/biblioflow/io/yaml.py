"""
title: Optional YAML readers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from biblioflow.exceptions import OptionalDependencyError


def read_yaml_records(path: str | Path) -> list[dict[str, Any]]:
    """
    title: Read records from YAML using PyYAML if installed.
    parameters:
      path:
        type: str | Path
        description: Path value.
    returns:
      type: list[dict[str, Any]]
    """
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise OptionalDependencyError("Install biblioflow[yaml] to read YAML.") from exc
    obj = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if isinstance(obj, list):
        return [dict(item) for item in obj if isinstance(item, dict)]
    if isinstance(obj, dict):
        for key in ("records", "data", "items", "results"):
            value = obj.get(key)
            if isinstance(value, list):
                return [dict(item) for item in value if isinstance(item, dict)]
        return [obj]
    return []

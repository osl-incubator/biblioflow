"""
title: RIS source helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from biblioflow.io.ris import read_ris_records


def can_load(path_or_buffer: str | Path) -> bool:
    """
    title: Return whether a path looks like RIS.
    parameters:
      path_or_buffer:
        type: str | Path
        description: Input path.
    returns:
      type: bool
    """
    path = Path(path_or_buffer)
    if path.suffix.lower() == ".ris":
        return True
    try:
        sample = path.read_text(encoding="utf-8-sig", errors="replace")[:4096]
    except OSError:
        return False
    return "TY  -" in sample and "ER  -" in sample


def load_ris(path_or_buffer: str | Path) -> list[dict[str, Any]]:
    """
    title: Load RIS records.
    parameters:
      path_or_buffer:
        type: str | Path
        description: Input path.
    returns:
      type: list[dict[str, Any]]
    """
    return read_ris_records(path_or_buffer)


def normalize_ris_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """
    title: >-
      Return a RIS entry dictionary unchanged for dispatcher normalization.
    parameters:
      entry:
        type: dict[str, Any]
        description: RIS entry.
    returns:
      type: dict[str, Any]
    """
    return dict(entry)

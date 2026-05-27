"""
title: Web of Science source helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from biblioflow.io.wos import (
    normalize_wos_record,
    parse_wos_records,
    read_wos_records,
)


def can_load(path_or_buffer: str | Path) -> bool:
    """
    title: Return whether a path looks like a Web of Science text export.
    parameters:
      path_or_buffer:
        type: str | Path
        description: Input path.
    returns:
      type: bool
    """
    try:
        sample = Path(path_or_buffer).read_text(encoding="utf-8-sig", errors="replace")[
            :4096
        ]
    except OSError:
        return False
    return "FN Clarivate" in sample or "\nPT " in f"\n{sample}"


def load_wos(path_or_buffer: str | Path) -> list[dict[str, Any]]:
    """
    title: Load Web of Science plain-text records.
    parameters:
      path_or_buffer:
        type: str | Path
        description: Input path.
    returns:
      type: list[dict[str, Any]]
    """
    return read_wos_records(path_or_buffer)


__all__ = [
    "can_load",
    "load_wos",
    "normalize_wos_record",
    "parse_wos_records",
]

"""
title: BibTeX source helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from biblioflow.io.bibtex import read_bibtex_records


def can_load(path_or_buffer: str | Path) -> bool:
    """
    title: Return whether a path looks like BibTeX.
    parameters:
      path_or_buffer:
        type: str | Path
        description: Input path.
    returns:
      type: bool
    """
    path = Path(path_or_buffer)
    if path.suffix.lower() in {".bib", ".bibtex"}:
        return True
    try:
        sample = path.read_text(encoding="utf-8-sig", errors="replace")[:4096]
    except OSError:
        return False
    return "@article" in sample.lower() or "@book" in sample.lower()


def load_bibtex(path_or_buffer: str | Path) -> list[dict[str, Any]]:
    """
    title: Load BibTeX records.
    parameters:
      path_or_buffer:
        type: str | Path
        description: Input path.
    returns:
      type: list[dict[str, Any]]
    """
    return read_bibtex_records(path_or_buffer)


def normalize_bibtex_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """
    title: >-
      Return a BibTeX entry dictionary unchanged for dispatcher normalization.
    parameters:
      entry:
        type: dict[str, Any]
        description: BibTeX entry.
    returns:
      type: dict[str, Any]
    """
    return dict(entry)

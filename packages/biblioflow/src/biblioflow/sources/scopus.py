"""
title: Scopus file source helpers.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from biblioflow.io.bibtex import read_bibtex_records
from biblioflow.io.csv import read_csv_records
from biblioflow.providers.adapters import adapt_scopus


def can_load(path_or_buffer: str | Path) -> bool:
    """
    title: Return whether a path looks like a Scopus CSV export.
    parameters:
      path_or_buffer:
        type: str | Path
        description: Input path.
    returns:
      type: bool
    """
    path = Path(path_or_buffer)
    if path.suffix.lower() == ".bib":
        return "scopus" in path.name.lower()
    if path.suffix.lower() != ".csv":
        return False
    try:
        sample = path.read_text(encoding="utf-8-sig", errors="replace")[:4096]
        headers = next(csv.reader(sample.splitlines()))
    except (OSError, StopIteration, csv.Error):
        return False
    lowered = {header.strip().casefold() for header in headers}
    return len(lowered & {"authors", "title", "year", "source title", "eid"}) >= 4


def load_scopus_csv(path_or_buffer: str | Path) -> list[dict[str, Any]]:
    """
    title: Load Scopus CSV records.
    parameters:
      path_or_buffer:
        type: str | Path
        description: Input path.
    returns:
      type: list[dict[str, Any]]
    """
    return [adapt_scopus(record) for record in read_csv_records(path_or_buffer)]


def load_scopus_bibtex(path_or_buffer: str | Path) -> list[dict[str, Any]]:
    """
    title: Load Scopus BibTeX records.
    parameters:
      path_or_buffer:
        type: str | Path
        description: Input path.
    returns:
      type: list[dict[str, Any]]
    """
    return [adapt_scopus(record) for record in read_bibtex_records(path_or_buffer)]


def normalize_scopus_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    title: Normalize a Scopus row.
    parameters:
      row:
        type: dict[str, Any]
        description: Raw Scopus row.
    returns:
      type: dict[str, Any]
    """
    return adapt_scopus(row)

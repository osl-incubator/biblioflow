"""
title: CSV and TSV readers.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def read_csv_records(path: str | Path, *, delimiter: str = ",") -> list[dict[str, Any]]:
    """
    title: Read CSV/TSV records as dictionaries.
    parameters:
      path:
        type: str | Path
        description: Path value.
      delimiter:
        type: str
        description: Delimiter value.
    returns:
      type: list[dict[str, Any]]
    """
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        return [dict(row) for row in reader]

"""CSV and TSV readers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def read_csv_records(path: str | Path, *, delimiter: str = ",") -> list[dict[str, Any]]:
    """Read CSV/TSV records as dictionaries."""
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        return [dict(row) for row in reader]

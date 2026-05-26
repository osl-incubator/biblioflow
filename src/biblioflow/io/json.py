"""JSON readers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json_records(path: str | Path) -> list[dict[str, Any]]:
    """Read bibliographic records from JSON.

    Supported shapes are a top-level list of records, or an object containing a
    `records`, `data`, `items`, or `results` list.
    """
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(obj, list):
        records = obj
    elif isinstance(obj, dict):
        for key in ("records", "data", "items", "results"):
            value = obj.get(key)
            if isinstance(value, list):
                records = value
                break
        else:
            records = [obj]
    else:
        msg = "JSON input must contain an object or a list of objects."
        raise ValueError(msg)
    return [dict(record) for record in records if isinstance(record, dict)]


def read_jsonl_records(path: str | Path) -> list[dict[str, Any]]:
    """Read newline-delimited JSON records."""
    records: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if isinstance(obj, dict):
            records.append(obj)
    return records

"""
title: Date normalization helpers.
"""

from __future__ import annotations

import re
from typing import Any


def _first(value: Any) -> Any:
    """
    title: Return the first list value or the value itself.
    parameters:
      value:
        type: Any
        description: Input value.
    returns:
      type: Any
    """
    if isinstance(value, list):
        return value[0] if value else None
    return value


def parse_year(value: Any) -> int | None:
    """
    title: Extract a plausible publication year from a value.
    parameters:
      value:
        type: Any
        description: Year-like value.
    returns:
      type: int | None
    """
    value = _first(value)
    if value is None:
        return None
    if isinstance(value, dict):
        parts = value.get("date-parts")
        if (
            isinstance(parts, list)
            and parts
            and isinstance(parts[0], list)
            and parts[0]
        ):
            value = parts[0][0]
    text = str(value).strip()
    match = re.search(r"(1[5-9]\d{2}|20\d{2}|21\d{2})", text)
    if not match:
        return None
    year = int(match.group(1))
    return year if 1500 <= year <= 2199 else None


def parse_publication_date(value: Any) -> str | None:
    """
    title: Parse a publication date into a compact ISO-like string.
    parameters:
      value:
        type: Any
        description: Date-like value.
    returns:
      type: str | None
    """
    value = _first(value)
    if value is None:
        return None
    if isinstance(value, dict):
        parts = value.get("date-parts")
        if (
            isinstance(parts, list)
            and parts
            and isinstance(parts[0], list)
            and parts[0]
        ):
            date_parts = [int(part) for part in parts[0] if part is not None]
            if len(date_parts) >= 3:
                return f"{date_parts[0]:04d}-{date_parts[1]:02d}-{date_parts[2]:02d}"
            if len(date_parts) == 2:
                return f"{date_parts[0]:04d}-{date_parts[1]:02d}"
            return f"{date_parts[0]:04d}"
    text = str(value).strip()
    if not text:
        return None
    match = re.search(
        r"(1[5-9]\d{2}|20\d{2}|21\d{2})(?:[-/](\d{1,2})(?:[-/](\d{1,2}))?)?",
        text,
    )
    if not match:
        return None
    year = int(match.group(1))
    month = int(match.group(2)) if match.group(2) else None
    day = int(match.group(3)) if match.group(3) else None
    if month and day:
        return f"{year:04d}-{month:02d}-{day:02d}"
    if month:
        return f"{year:04d}-{month:02d}"
    return f"{year:04d}"

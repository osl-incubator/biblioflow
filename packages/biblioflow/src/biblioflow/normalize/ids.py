"""
title: Identifier normalization helpers.
"""

from __future__ import annotations

import re
from typing import Any


def normalize_doi(value: Any) -> str | None:
    """
    title: Normalize a DOI string.
    parameters:
      value:
        type: Any
        description: DOI-like value.
    returns:
      type: str | None
    """
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"^https?://(dx\.)?doi\.org/", "", text, flags=re.I)
    text = re.sub(r"^doi\s*:\s*", "", text, flags=re.I).strip().strip(".")
    match = re.search(r"\b10\.\d{4,9}/[^\s,;]+", text, flags=re.I)
    if match:
        return match.group(0).rstrip(".").lower()
    if re.match(r"^10[./]", text, flags=re.I):
        return text.rstrip(".").lower()
    return None

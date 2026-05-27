"""
title: Author normalization helpers.
"""

from __future__ import annotations

import re
from typing import Any

from biblioflow.normalize.text import clean_text


def normalize_author_name(value: str) -> dict[str, Any]:
    """
    title: Normalize one author name into display and component fields.
    parameters:
      value:
        type: str
        description: Author name value.
    returns:
      type: dict[str, Any]
    """
    text = clean_text(value) or ""
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text).strip()
    given: str | None = None
    family: str | None = None
    name = text
    if "," in text:
        family_part, given_part = [part.strip() for part in text.split(",", 1)]
        family = family_part or None
        given = given_part or None
        name = " ".join(part for part in (given, family) if part)
    else:
        parts = text.split()
        if len(parts) > 1:
            given = " ".join(parts[:-1])
            family = parts[-1]
    return {
        "name": name,
        "given": given,
        "family": family,
        "orcid": None,
        "source_author_id": None,
    }


def parse_author_list(value: Any, *, source: str | None = None) -> list[dict[str, Any]]:
    """
    title: Parse author values into structured author dictionaries.
    parameters:
      value:
        type: Any
        description: Author value or values.
      source:
        type: str | None
        description: Optional source/provider hint.
    returns:
      type: list[dict[str, Any]]
    """
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        raw_parts = [str(item) for item in value if clean_text(item)]
    else:
        text = clean_text(value)
        if not text:
            return []
        if " and " in text:
            raw_parts = re.split(r"\s+and\s+", text)
        elif ";" in text:
            raw_parts = re.split(r"\s*;\s*", text)
        elif source == "scopus" and "," in text and not re.search(r"\w,\s+\w", text):
            raw_parts = re.split(r"\s*,\s*", text)
        else:
            raw_parts = [text]

    authors = []
    seen: set[str] = set()
    for position, part in enumerate(raw_parts, start=1):
        normalized = normalize_author_name(part)
        name = normalized["name"]
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())
        authors.append({**normalized, "position": position})
    return authors


def author_names(value: Any, *, source: str | None = None) -> list[str]:
    """
    title: Return display names for parsed authors.
    parameters:
      value:
        type: Any
        description: Author value or values.
      source:
        type: str | None
        description: Optional source/provider hint.
    returns:
      type: list[str]
    """
    return [author["name"] for author in parse_author_list(value, source=source)]

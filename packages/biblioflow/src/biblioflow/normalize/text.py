"""
title: Text normalization helpers.
"""

from __future__ import annotations

import re
from typing import Any


def clean_text(value: Any) -> str | None:
    """
    title: Normalize whitespace and empty textual values.
    parameters:
      value:
        type: Any
        description: Text-like value.
    returns:
      type: str | None
    """
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def dedupe_text(values: list[str]) -> list[str]:
    """
    title: Remove duplicate text values while preserving order.
    parameters:
      values:
        type: list[str]
        description: Text values.
    returns:
      type: list[str]
    """
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = clean_text(value)
        if not text:
            continue
        marker = text.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        output.append(text)
    return output


def split_keywords(value: Any) -> list[str]:
    """
    title: Split keyword strings and lists into normalized keyword values.
    parameters:
      value:
        type: Any
        description: Keyword value or values.
    returns:
      type: list[str]
    """
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        parts: list[str] = []
        for item in value:
            parts.extend(split_keywords(item))
        return dedupe_text(parts)
    text = clean_text(value)
    if not text:
        return []
    if ";" in text or "|" in text:
        parts = re.split(r"\s*[;|]\s*", text)
    else:
        parts = re.split(r"\s*,\s*", text)
    return dedupe_text([part for part in parts if part])


def normalize_language(value: Any) -> str | None:
    """
    title: Normalize a language value.
    parameters:
      value:
        type: Any
        description: Language value.
    returns:
      type: str | None
    """
    text = clean_text(value)
    if not text:
        return None
    mapping = {
        "eng": "English",
        "en": "English",
        "english": "English",
        "por": "Portuguese",
        "pt": "Portuguese",
        "portuguese": "Portuguese",
        "spa": "Spanish",
        "es": "Spanish",
        "spanish": "Spanish",
        "fre": "French",
        "fr": "French",
        "french": "French",
    }
    return mapping.get(text.casefold(), text)

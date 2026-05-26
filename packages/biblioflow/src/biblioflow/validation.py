"""
title: Validation helpers for normalized bibliographic records.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from biblioflow.core.warnings import LoadWarning


def validate_records(records: list[dict[str, Any]]) -> list[LoadWarning]:
    """
    title: Return structured warnings for common bibliographic quality issues.
    parameters:
      records:
        type: list[dict[str, Any]]
        description: Records value.
    returns:
      type: list[LoadWarning]
    """
    warnings: list[LoadWarning] = []
    missing_title = sum(1 for record in records if not record.get("title"))
    missing_doi = sum(1 for record in records if not record.get("doi"))
    missing_year = sum(1 for record in records if not record.get("publication_year"))
    duplicate_dois = sum(
        count - 1
        for _doi, count in Counter(
            record.get("doi") for record in records if record.get("doi")
        ).items()
        if count > 1
    )

    if missing_title:
        warnings.append(
            LoadWarning(
                code="missing_title",
                count=missing_title,
                severity="warning",
                field="title",
                message="Records are missing titles.",
            )
        )
    if missing_doi:
        warnings.append(
            LoadWarning(
                code="missing_doi",
                count=missing_doi,
                severity="info",
                field="doi",
                message="Records are missing DOI values.",
            )
        )
    if missing_year:
        warnings.append(
            LoadWarning(
                code="missing_publication_year",
                count=missing_year,
                severity="info",
                field="publication_year",
                message="Records are missing publication years.",
            )
        )
    if duplicate_dois:
        warnings.append(
            LoadWarning(
                code="duplicate_doi",
                count=duplicate_dois,
                severity="warning",
                field="doi",
                message="Duplicate DOI values were found.",
            )
        )
    return warnings

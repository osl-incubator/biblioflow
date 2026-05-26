"""
title: Lightweight thematic mapping and evolution helpers.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.core.frames import make_record_frame
from biblioflow.load.dispatcher import load
from biblioflow.networks import network


@dataclass
class ThematicMap:
    """
    title: A lightweight thematic map table.
    attributes:
      data:
        type: Any
        description: Data attribute.
      metadata:
        type: dict[str, Any]
        description: Metadata attribute.
    """

    data: Any
    metadata: dict[str, Any]

    def to_dataframe(self) -> Any:
        """
        title: Return the thematic map as a DataFrame-like object.
        returns:
          type: Any
        """
        return self.data.copy()


@dataclass
class ThematicEvolution:
    """
    title: A term-by-period thematic evolution table.
    attributes:
      data:
        type: Any
        description: Data attribute.
      metadata:
        type: dict[str, Any]
        description: Metadata attribute.
    """

    data: Any
    metadata: dict[str, Any]

    def to_dataframe(self) -> Any:
        """
        title: Return the thematic evolution table.
        returns:
          type: Any
        """
        return self.data.copy()


def _terms(value: Any) -> list[str]:
    """
    title: Implement the terms helper.
    parameters:
      value:
        type: Any
        description: Value value.
    returns:
      type: list[str]
    """
    return (
        [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, list)
        else []
    )


def map_themes(
    records: BibliographicDataset | Any,
    *,
    field: str = "keywords_all",
    min_occurrences: int = 1,
) -> ThematicMap:
    """
    title: >-
      Create a lightweight thematic map from keyword co-occurrence metrics.
    parameters:
      records:
        type: BibliographicDataset | Any
        description: Records value.
      field:
        type: str
        description: Field value.
      min_occurrences:
        type: int
        description: Min occurrences value.
    returns:
      type: ThematicMap
    """
    dataset = (
        load(records) if not isinstance(records, BibliographicDataset) else records
    )
    net = network(
        dataset,
        kind="co_occurrence",
        unit=field,
        min_occurrences=min_occurrences,
    )
    rows = []
    for node in net.nodes.to_dict(orient="records"):
        rows.append(
            {
                "id": node.get("id"),
                "theme": node.get("label"),
                "occurrences": node.get("occurrences"),
                "degree": node.get("degree"),
                "strength": node.get("strength"),
            }
        )
    data = make_record_frame(rows, ["id", "theme", "occurrences", "degree", "strength"])
    return ThematicMap(
        data=data,
        metadata={"field": field, "min_occurrences": min_occurrences},
    )


def trace_themes(
    records: BibliographicDataset | Any,
    *,
    field: str = "keywords_all",
    by: str = "publication_year",
) -> ThematicEvolution:
    """
    title: Count thematic terms across periods such as publication years.
    parameters:
      records:
        type: BibliographicDataset | Any
        description: Records value.
      field:
        type: str
        description: Field value.
      by:
        type: str
        description: By value.
    returns:
      type: ThematicEvolution
    """
    dataset = (
        load(records) if not isinstance(records, BibliographicDataset) else records
    )
    counts: Counter[tuple[Any, str]] = Counter()
    for row in dataset.to_records():
        period = row.get(by)
        if period is None:
            continue
        for term in set(_terms(row.get(field))):
            counts[(period, term)] += 1
    rows = [
        {"period": period, "term": term, "documents": count}
        for (period, term), count in sorted(
            counts.items(), key=lambda item: (item[0][0], item[0][1])
        )
    ]
    frame = make_record_frame(rows, ["period", "term", "documents"])
    return ThematicEvolution(data=frame, metadata={"field": field, "by": by})


def conceptual_structure(
    records: BibliographicDataset | Any,
    *,
    field: str = "keywords_all",
    min_occurrences: int = 1,
) -> ThematicMap:
    """
    title: Return a lightweight conceptual-structure table.
    summary: |-
      This MVP uses the same deterministic term co-occurrence metrics as
      `map_themes`. Later implementations can add dimensionality reduction
      and
      clustering while keeping this return shape stable.
    parameters:
      records:
        type: BibliographicDataset | Any
        description: Records value.
      field:
        type: str
        description: Field value.
      min_occurrences:
        type: int
        description: Min occurrences value.
    returns:
      type: ThematicMap
    """
    return map_themes(
        records,
        field=field,
        min_occurrences=min_occurrences,
    )

"""
title: Lightweight historiograph helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.core.frames import make_record_frame
from biblioflow.load.dispatcher import load
from biblioflow.networks import NetworkResult


@dataclass
class Historiograph:
    """
    title: A simple citation-like graph built from DOI/reference overlap.
    attributes:
      network:
        type: NetworkResult
        description: Network attribute.
      metadata:
        type: dict[str, Any]
        description: Metadata attribute.
    """

    network: NetworkResult
    metadata: dict[str, Any]


def historiograph(records: BibliographicDataset | Any) -> Historiograph:
    """
    title: Build a lightweight historiograph from canonical records.
    parameters:
      records:
        type: BibliographicDataset | Any
        description: Records value.
    returns:
      type: Historiograph
    """
    dataset = (
        load(records) if not isinstance(records, BibliographicDataset) else records
    )
    nodes = []
    edges = []
    identifiers: list[tuple[str, str | None, str | None]] = []
    for index, row in enumerate(dataset.to_records()):
        node_id = row.get("doi") or row.get("source_id") or str(index)
        title = row.get("title")
        nodes.append(
            {
                "id": node_id,
                "label": title or node_id,
                "occurrences": 1.0,
                "degree": 0,
                "strength": 0.0,
            }
        )
        identifiers.append((node_id, row.get("doi"), title))

    for index, row in enumerate(dataset.to_records()):
        source = row.get("doi") or row.get("source_id") or str(index)
        references = (
            row.get("references") if isinstance(row.get("references"), list) else []
        )
        haystack = "\n".join(str(ref).casefold() for ref in references)
        if not haystack:
            continue
        for target, doi, title in identifiers:
            if target == source:
                continue
            doi_hit = doi and doi.casefold() in haystack
            title_hit = title and len(title) > 12 and title.casefold() in haystack
            if doi_hit or title_hit:
                edges.append({"source": source, "target": target, "weight": 1.0})

    for node in nodes:
        incident = [
            edge
            for edge in edges
            if edge["source"] == node["id"] or edge["target"] == node["id"]
        ]
        node["degree"] = len(incident)
        node["strength"] = sum(float(edge["weight"]) for edge in incident)

    network = NetworkResult(
        nodes=make_record_frame(
            nodes, ["id", "label", "occurrences", "degree", "strength"]
        ),
        edges=make_record_frame(edges, ["source", "target", "weight"]),
        metadata={"kind": "historiograph", "unit": "references"},
    )
    return Historiograph(network=network, metadata={"records": len(dataset)})

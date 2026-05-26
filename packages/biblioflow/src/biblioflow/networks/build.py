"""Network construction from bibliometric matrices."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from biblioflow.core.frames import MatrixFrame, make_record_frame
from biblioflow.matrices.build import MatrixResult, matrix


@dataclass
class NetworkResult:
    """A simple node/edge representation of a bibliometric network."""

    nodes: Any
    edges: Any
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return nodes, edges, and metadata as dictionaries."""
        return {
            "nodes": self.nodes.to_dict(orient="records"),
            "edges": self.edges.to_dict(orient="records"),
            "metadata": self.metadata,
        }

    def export(self, path: str | Path, *, format: str | None = None) -> None:
        """Export this network using biblioflow.export.export."""
        from biblioflow.export import export

        export(self, path, format=format)


def _matrix_value(table: Any, row: str, column: str) -> float:
    if isinstance(table, MatrixFrame):
        return table.get(row, column)
    return float(table.loc[row, column])


def network(records: Any, **kwargs: Any) -> NetworkResult:
    """Build a node/edge network from records or a MatrixResult."""
    mat = records if isinstance(records, MatrixResult) else matrix(records, **kwargs)
    table = mat.table
    labels = list(table.index) if hasattr(table, "index") else []

    edges: list[dict[str, Any]] = []
    directed = bool(mat.metadata.get("directed"))
    for i, source in enumerate(labels):
        target_indexes = range(len(labels)) if directed else range(i + 1, len(labels))
        for j in target_indexes:
            if i == j:
                continue
            target = labels[j]
            weight = _matrix_value(table, source, target)
            if weight > 0:
                edges.append({"source": source, "target": target, "weight": weight})

    nodes: list[dict[str, Any]] = []
    for label in labels:
        degree = 0
        strength = 0.0
        for edge in edges:
            if edge["source"] == label or edge["target"] == label:
                degree += 1
                strength += float(edge["weight"])
        occurrences = _matrix_value(table, label, label)
        nodes.append(
            {
                "id": label,
                "label": label,
                "occurrences": occurrences,
                "degree": degree,
                "strength": strength,
            }
        )
    return NetworkResult(
        nodes=make_record_frame(
            nodes, ["id", "label", "occurrences", "degree", "strength"]
        ),
        edges=make_record_frame(edges, ["source", "target", "weight"]),
        metadata={"kind": mat.kind, "unit": mat.unit, **mat.metadata},
    )

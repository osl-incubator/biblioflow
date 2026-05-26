"""Export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.matrices import MatrixResult
from biblioflow.networks import NetworkResult


def _infer_format(path: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "json"


def _write_graphml(network: NetworkResult, path: Path) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
        '  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
        '  <graph edgedefault="undirected">',
    ]
    for node in network.nodes.to_dict(orient="records"):
        node_id = escape(str(node["id"]))
        label = escape(str(node.get("label", node["id"])))
        lines.extend(
            [
                f'    <node id="{node_id}">',
                f'      <data key="label">{label}</data>',
                "    </node>",
            ]
        )
    for index, edge in enumerate(network.edges.to_dict(orient="records")):
        source = escape(str(edge["source"]))
        target = escape(str(edge["target"]))
        weight = float(edge["weight"])
        lines.extend(
            [
                f'    <edge id="e{index}" source="{source}" target="{target}">',
                f'      <data key="weight">{weight}</data>',
                "    </edge>",
            ]
        )
    lines.extend(["  </graph>", "</graphml>"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export(obj: Any, path: str | Path, *, format: str | None = None) -> None:
    """Export a dataset, matrix, network, DataFrame, or JSON-like object."""
    output = Path(path)
    fmt = _infer_format(output, format)

    if isinstance(obj, BibliographicDataset):
        if fmt == "csv":
            obj.to_csv(output)
            return
        if fmt == "json":
            obj.to_json(output)
            return

    if isinstance(obj, MatrixResult):
        if fmt == "csv":
            obj.table.to_csv(output)
            return
        if fmt == "json":
            output.write_text(obj.table.to_json(indent=2) + "\n", encoding="utf-8")
            return

    if isinstance(obj, NetworkResult):
        if fmt == "graphml":
            _write_graphml(obj, output)
            return
        if fmt == "csv":
            output.mkdir(parents=True, exist_ok=True)
            obj.nodes.to_csv(output / "nodes.csv", index=False)
            obj.edges.to_csv(output / "edges.csv", index=False)
            return
        if fmt == "json":
            output.write_text(
                json.dumps(obj.to_dict(), indent=2) + "\n", encoding="utf-8"
            )
            return

    if hasattr(obj, "to_csv") and fmt == "csv":
        obj.to_csv(output, index=False)
        return
    if hasattr(obj, "to_json") and fmt == "json":
        output.write_text(
            obj.to_json(orient="records", indent=2) + "\n", encoding="utf-8"
        )
        return
    if fmt == "json":
        output.write_text(
            json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8"
        )
        return

    msg = f"Unsupported export format {fmt!r} for object type {type(obj).__name__}."
    raise ValueError(msg)

"""Network rendering helpers."""

from __future__ import annotations

from typing import Any

from biblioflow_nb.renderers.tables import dataframe_like_to_rows, rows_to_html


def network_tables_html(network: Any, *, limit: int = 20) -> str:
    """Render network nodes and edges as HTML tables."""
    nodes = rows_to_html(dataframe_like_to_rows(network.nodes, limit=limit))
    edges = rows_to_html(dataframe_like_to_rows(network.edges, limit=limit))
    return f"<h4>Nodes</h4>{nodes}<h4>Edges</h4>{edges}"

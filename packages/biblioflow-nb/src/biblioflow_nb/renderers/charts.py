"""Chart rendering helpers.

MVP chart rendering is intentionally table-first for Colab compatibility.
"""

from __future__ import annotations

from typing import Any

from biblioflow_nb.renderers.tables import dataframe_like_to_rows, rows_to_html


def chart_fallback_html(data: Any, *, limit: int = 20) -> str:
    """Render chart data as a table fallback."""
    return rows_to_html(dataframe_like_to_rows(data, limit=limit))

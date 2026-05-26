"""Table rendering helpers."""

from __future__ import annotations

from html import escape
from typing import Any


def dataframe_like_to_rows(obj: Any, *, limit: int = 10) -> list[dict[str, Any]]:
    """Convert a dataframe-like object or records list to rows."""
    if obj is None:
        return []
    if isinstance(obj, list):
        return [dict(row) for row in obj[:limit]]
    if hasattr(obj, "to_dict"):
        rows = obj.to_dict(orient="records")
        return [dict(row) for row in rows[:limit]]
    return []


def rows_to_html(rows: list[dict[str, Any]], *, empty: str = "No rows.") -> str:
    """Render rows as a small HTML table."""
    if not rows:
        return f"<p>{escape(empty)}</p>"
    columns = list(rows[0])
    head = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{escape(_cell_text(row.get(column)))}</td>" for column in columns
        )
        body_rows.append(f"<tr>{cells}</tr>")
    body = "".join(body_rows)
    return (
        "<table style='border-collapse:collapse; width:100%'>"
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    )


def _cell_text(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return "" if value is None else str(value)

"""Styled notebook message helpers."""

from __future__ import annotations

from html import escape


def info_html(message: str) -> str:
    """Render an informational message."""
    return _message("#e8f1ff", "#2454a6", message)


def warning_html(message: str) -> str:
    """Render a warning message."""
    return _message("#fff6df", "#8a5a00", message)


def error_html(message: str) -> str:
    """Render an error message."""
    return _message("#ffe9e9", "#a32424", message)


def _message(background: str, color: str, message: str) -> str:
    return (
        "<div style='border-radius:8px; padding:0.75rem; "
        f"background:{background}; color:{color}'>"
        f"{escape(message)}</div>"
    )

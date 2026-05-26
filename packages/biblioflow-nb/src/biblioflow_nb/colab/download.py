"""Colab download helper."""

from __future__ import annotations

from pathlib import Path

from biblioflow_nb.errors import BiblioFlowNotebookError


def colab_download(path: str | Path) -> None:
    """Download a file in Google Colab."""
    try:
        from google.colab import files  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BiblioFlowNotebookError("google.colab is not available.") from exc
    files.download(str(path))

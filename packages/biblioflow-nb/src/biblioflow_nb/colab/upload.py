"""Colab upload helper."""

from __future__ import annotations

from pathlib import Path

from biblioflow_nb.errors import BiblioFlowNotebookError


def colab_upload(directory: str | Path = ".") -> list[Path]:
    """Upload files through Google Colab and return written paths."""
    try:
        from google.colab import files  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BiblioFlowNotebookError("google.colab is not available.") from exc
    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)
    uploaded = files.upload()
    paths = []
    for name, content in uploaded.items():
        path = target_dir / Path(name).name
        path.write_bytes(content)
        paths.append(path)
    return paths

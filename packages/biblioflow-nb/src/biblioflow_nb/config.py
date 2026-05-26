"""Configuration for biblioflow-nb."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NotebookConfig:
    """Runtime configuration for the notebook app."""

    title: str = "biblioflow-nb"
    preview_rows: int = 10
    temp_dir: Path | None = None
    show_debug: bool = False

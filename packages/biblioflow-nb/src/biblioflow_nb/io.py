"""Notebook file I/O helpers."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


class TemporaryUploadStore:
    """Temporary file store for widget uploads."""

    def __init__(self) -> None:
        self._tmp = TemporaryDirectory(prefix="biblioflow-nb-")
        self.root = Path(self._tmp.name)

    def write_upload(self, name: str, content: bytes | memoryview) -> Path:
        """Write uploaded bytes to a temporary file."""
        path = self.root / Path(name).name
        data = content.tobytes() if isinstance(content, memoryview) else content
        path.write_bytes(data)
        return path

    def cleanup(self) -> None:
        """Remove temporary files."""
        self._tmp.cleanup()


def upload_items(value: Any) -> list[dict[str, Any]]:
    """Normalize ipywidgets FileUpload values across widget versions."""
    if not value:
        return []
    if isinstance(value, dict):
        items = []
        for name, payload in value.items():
            item = dict(payload)
            item.setdefault("name", name)
            items.append(item)
        return items
    if isinstance(value, tuple | list):
        return [dict(item) for item in value]
    return []

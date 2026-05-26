from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
BIBLIOFLOW_SRC = ROOT / "packages" / "biblioflow" / "src"
DATA = ROOT / "packages" / "biblioflow" / "tests" / "data"


@pytest.fixture(autouse=True)
def local_biblioflow_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(BIBLIOFLOW_SRC))


@pytest.fixture
def data_dir() -> Path:
    return DATA

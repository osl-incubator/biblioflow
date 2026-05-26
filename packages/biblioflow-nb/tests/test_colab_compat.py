from __future__ import annotations

import sys
import types

import pytest

from biblioflow_nb.colab.compat import colab_setup, is_colab
from biblioflow_nb.colab.download import colab_download


def test_colab_setup_false_outside_colab():
    assert is_colab() is False
    assert colab_setup() is False


def test_colab_setup_with_mocked_module(monkeypatch):
    calls = []
    google = types.ModuleType("google")
    colab = types.ModuleType("google.colab")
    output = types.SimpleNamespace(
        enable_custom_widget_manager=lambda: calls.append("ok")
    )
    colab.output = output
    google.colab = colab
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.colab", colab)
    monkeypatch.setitem(sys.modules, "google.colab.output", output)

    assert is_colab() is True
    assert colab_setup() is True
    assert calls == ["ok"]


def test_colab_download_raises_outside_colab(tmp_path):
    with pytest.raises(Exception, match=r"google\.colab"):
        colab_download(tmp_path / "file.txt")

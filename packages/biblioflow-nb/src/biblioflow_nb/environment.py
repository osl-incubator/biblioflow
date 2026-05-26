"""Notebook environment detection helpers."""

from __future__ import annotations


def is_colab() -> bool:
    """Return whether the current process appears to be Google Colab."""
    try:
        import google.colab  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        return False
    return True


def in_ipython() -> bool:
    """Return whether an IPython shell is available."""
    try:
        import IPython
    except ImportError:
        return False
    get_ipython = getattr(IPython, "get_ipython", None)
    return bool(get_ipython and get_ipython() is not None)

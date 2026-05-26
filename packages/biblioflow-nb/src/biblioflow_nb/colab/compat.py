"""Google Colab environment helpers."""

from __future__ import annotations


def is_colab() -> bool:
    """Return whether the current environment is Google Colab."""
    try:
        import google.colab  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        return False
    return True


def colab_setup() -> bool:
    """Enable Colab widget support when running in Colab.

    Returns ``True`` when Colab support was detected and setup was attempted,
    otherwise ``False``. The function is safe to call outside Colab.
    """
    try:
        from google.colab import output
    except ImportError:
        return False
    output.enable_custom_widget_manager()
    return True

"""Base widget panel classes."""

from __future__ import annotations

from typing import Any

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.errors import BiblioFlowNotebookError
from biblioflow_nb.renderers.messages import error_html, info_html
from biblioflow_nb.state import NotebookSession


class WidgetPanel:
    """Base class for notebook panels."""

    title = "Panel"

    def __init__(self, session: NotebookSession, services: Any) -> None:
        self.session = session
        self.services = services
        self.output = widgets.Output()
        self.container: widgets.Widget | None = None

    def build(self) -> widgets.Widget:
        """Build and return the panel widget."""
        if self.container is None:
            self.container = widgets.VBox([self.output])
        return self.container

    def refresh(self) -> None:
        """Refresh panel output."""

    def clear_output(self) -> None:
        """Clear panel output."""
        self.output.clear_output()

    def show_info(self, message: str) -> None:
        """Show an info message in the panel output."""
        with self.output:
            display(HTML(info_html(message)))

    def run_safely(self, callback: Any) -> None:
        """Run a widget callback and render friendly errors."""
        try:
            callback()
        except BiblioFlowNotebookError as exc:
            self._show_error(str(exc))
        except Exception as exc:  # pragma: no cover - defensive widget callback path
            self._show_error(f"Unexpected error: {exc}")

    def _show_error(self, message: str) -> None:
        with self.output:
            display(HTML(error_html(message)))

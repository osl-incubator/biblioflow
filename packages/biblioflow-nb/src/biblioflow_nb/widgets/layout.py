"""Top-level layout helpers."""

from __future__ import annotations

from collections.abc import Iterable

import ipywidgets as widgets

from biblioflow_nb.widgets.base import WidgetPanel


class AppLayout:
    """Composes header, tabs, and status widgets."""

    def __init__(self, panels: Iterable[WidgetPanel]) -> None:
        self.panels = list(panels)
        self.header = widgets.HTML(
            "<h2>biblioflow-nb</h2>"
            "<p>Notebook bibliometric workflows powered by biblioflow.</p>"
        )
        self.status = widgets.HTML("<small>Ready.</small>")
        self.tabs = widgets.Tab(children=[panel.build() for panel in self.panels])
        for index, panel in enumerate(self.panels):
            self.tabs.set_title(index, panel.title)
        self.widget = widgets.VBox([self.header, self.tabs, self.status])

    def build(self) -> widgets.Widget:
        """Return the top-level widget."""
        return self.widget

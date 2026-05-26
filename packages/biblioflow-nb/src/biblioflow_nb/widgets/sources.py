"""Sources panel placeholder."""

from __future__ import annotations

import ipywidgets as widgets

from biblioflow_nb.widgets.base import WidgetPanel


class SourcesPanel(WidgetPanel):
    """Placeholder panel for planned sources workflows."""

    title = "Sources"

    def build(self) -> widgets.Widget:
        """Build placeholder panel."""
        message = (
            "<p>This panel will call biblioflow sources APIs as they are added.</p>"
        )
        self.container = widgets.VBox(
            [
                widgets.HTML(message),
                self.output,
            ]
        )
        return self.container

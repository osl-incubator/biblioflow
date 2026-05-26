"""Keywords panel placeholder."""

from __future__ import annotations

import ipywidgets as widgets

from biblioflow_nb.widgets.base import WidgetPanel


class KeywordsPanel(WidgetPanel):
    """Placeholder panel for planned keywords workflows."""

    title = "Keywords"

    def build(self) -> widgets.Widget:
        """Build placeholder panel."""
        message = (
            "<p>This panel will call biblioflow keywords APIs as they are added.</p>"
        )
        self.container = widgets.VBox(
            [
                widgets.HTML(message),
                self.output,
            ]
        )
        return self.container

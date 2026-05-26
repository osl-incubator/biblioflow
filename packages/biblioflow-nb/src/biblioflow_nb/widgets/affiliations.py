"""Affiliations panel placeholder."""

from __future__ import annotations

import ipywidgets as widgets

from biblioflow_nb.widgets.base import WidgetPanel


class AffiliationsPanel(WidgetPanel):
    """Placeholder panel for planned affiliations workflows."""

    title = "Affiliations"

    def build(self) -> widgets.Widget:
        """Build placeholder panel."""
        message = (
            "<p>This panel will call biblioflow affiliations APIs "
            "as they are added.</p>"
        )
        self.container = widgets.VBox(
            [
                widgets.HTML(message),
                self.output,
            ]
        )
        return self.container

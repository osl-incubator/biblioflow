"""Validation and preview panel."""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.renderers.tables import rows_to_html
from biblioflow_nb.widgets.base import WidgetPanel


class ValidationPanel(WidgetPanel):
    """Panel for validation warnings and record preview."""

    title = "Validation"

    def __init__(self, session, services) -> None:  # type: ignore[no-untyped-def]
        super().__init__(session, services)
        self.refresh_button = widgets.Button(description="Refresh")
        self.refresh_button.on_click(lambda _button: self.run_safely(self.refresh))

    def build(self) -> widgets.Widget:
        """Build validation panel."""
        self.container = widgets.VBox([self.refresh_button, self.output])
        return self.container

    def refresh(self) -> None:
        """Render validation and preview output."""
        self.output.clear_output()
        validation = self.services.datasets.validation()
        records = self.services.datasets.records(limit=10)
        with self.output:
            display(HTML("<h4>Warnings</h4>"))
            display(
                HTML(rows_to_html(validation.get("warnings", []), empty="No warnings."))
            )
            display(HTML("<h4>Record preview</h4>"))
            display(HTML(rows_to_html(records, empty="No records.")))

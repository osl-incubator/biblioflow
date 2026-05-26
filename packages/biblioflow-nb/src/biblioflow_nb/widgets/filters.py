"""Filter panel."""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.renderers.tables import rows_to_html
from biblioflow_nb.widgets.base import WidgetPanel


class FiltersPanel(WidgetPanel):
    """Panel for applying dataset filters."""

    title = "Filters"

    def __init__(self, session, services) -> None:  # type: ignore[no-untyped-def]
        super().__init__(session, services)
        self.year_min = widgets.IntText(description="Year min", value=0)
        self.year_max = widgets.IntText(description="Year max", value=0)
        self.keyword_text = widgets.Text(description="Keyword")
        self.apply_button = widgets.Button(description="Apply", button_style="primary")
        self.reset_button = widgets.Button(description="Reset")
        self.apply_button.on_click(lambda _button: self.run_safely(self.apply))
        self.reset_button.on_click(lambda _button: self.run_safely(self.reset))

    def build(self) -> widgets.Widget:
        """Build filter controls."""
        self.container = widgets.VBox(
            [
                widgets.HBox([self.year_min, self.year_max]),
                self.keyword_text,
                widgets.HBox([self.apply_button, self.reset_button]),
                self.output,
            ]
        )
        return self.container

    def apply(self) -> None:
        """Apply filters from widget values."""
        spec: dict[str, object] = {}
        if self.year_min.value:
            spec["year_min"] = self.year_min.value
        if self.year_max.value:
            spec["year_max"] = self.year_max.value
        if self.keyword_text.value.strip():
            spec["keywords"] = [self.keyword_text.value.strip()]
        result = self.services.datasets.apply_filters(spec)
        self.output.clear_output()
        with self.output:
            display(HTML(rows_to_html([result], empty="No filter result.")))

    def reset(self) -> None:
        """Reset active filters."""
        self.services.datasets.reset_filters()
        self.output.clear_output()
        self.show_info("Filters reset.")

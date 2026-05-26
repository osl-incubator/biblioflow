"""Network panel."""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.renderers.networks import network_tables_html
from biblioflow_nb.widgets.base import WidgetPanel


class NetworkPanel(WidgetPanel):
    """Panel for network construction."""

    title = "Networks"

    def __init__(self, session, services) -> None:  # type: ignore[no-untyped-def]
        super().__init__(session, services)
        self.kind = widgets.Dropdown(
            description="Kind",
            options=[
                "co_occurrence",
                "collaboration",
                "co_citation",
                "bibliographic_coupling",
                "direct_citation",
            ],
            value="co_occurrence",
        )
        self.unit = widgets.Dropdown(
            description="Unit",
            options=[
                "keywords_all",
                "authors",
                "references",
                "countries",
                "affiliations",
            ],
            value="keywords_all",
        )
        self.min_occurrences = widgets.IntText(description="Min", value=1)
        self.run_button = widgets.Button(
            description="Build network", button_style="primary"
        )
        self.run_button.on_click(lambda _button: self.run_safely(self.run))

    def build(self) -> widgets.Widget:
        """Build network panel."""
        self.container = widgets.VBox(
            [
                widgets.HBox([self.kind, self.unit, self.min_occurrences]),
                self.run_button,
                self.output,
            ]
        )
        return self.container

    def run(self) -> None:
        """Build and render network tables."""
        result = self.services.networks.build(
            kind=str(self.kind.value),
            unit=str(self.unit.value),
            min_occurrences=int(self.min_occurrences.value),
        )
        self.output.clear_output()
        with self.output:
            display(HTML(network_tables_html(result)))

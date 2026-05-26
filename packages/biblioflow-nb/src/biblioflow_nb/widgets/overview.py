"""Overview analysis panel."""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.renderers.tables import rows_to_html
from biblioflow_nb.widgets.base import WidgetPanel


class OverviewPanel(WidgetPanel):
    """Panel for descriptive overview analysis."""

    title = "Overview"

    def __init__(self, session, services) -> None:  # type: ignore[no-untyped-def]
        super().__init__(session, services)
        self.top_n = widgets.IntSlider(description="Top N", min=1, max=100, value=20)
        self.run_button = widgets.Button(
            description="Run overview", button_style="primary"
        )
        self.run_button.on_click(lambda _button: self.run_safely(self.run))

    def build(self) -> widgets.Widget:
        """Build overview panel."""
        self.container = widgets.VBox([self.top_n, self.run_button, self.output])
        return self.container

    def run(self) -> None:
        """Run overview analysis."""
        result = self.services.analysis.overview(top_n=int(self.top_n.value))
        self.output.clear_output()
        with self.output:
            display(HTML("<h4>Main information</h4>"))
            display(HTML(rows_to_html([result["main_information"]])))
            display(HTML("<h4>Annual production</h4>"))
            display(HTML(rows_to_html(result["annual_production"])))
            display(HTML("<h4>Top authors</h4>"))
            display(HTML(rows_to_html(result["top_authors"])))
            display(HTML("<h4>Top sources</h4>"))
            display(HTML(rows_to_html(result["top_sources"])))
            display(HTML("<h4>Top keywords</h4>"))
            display(HTML(rows_to_html(result["top_keywords"])))

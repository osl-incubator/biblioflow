"""Matrix panel."""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.renderers.tables import dataframe_like_to_rows, rows_to_html
from biblioflow_nb.widgets.base import WidgetPanel


class MatrixPanel(WidgetPanel):
    """Panel for matrix construction."""

    title = "Matrices"

    def __init__(self, session, services) -> None:  # type: ignore[no-untyped-def]
        super().__init__(session, services)
        self.kind = widgets.Dropdown(
            description="Kind",
            options=[
                "co_occurrence",
                "incidence",
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
                "source_title",
                "countries",
                "affiliations",
            ],
            value="keywords_all",
        )
        self.min_occurrences = widgets.IntText(description="Min", value=1)
        self.run_button = widgets.Button(
            description="Build matrix", button_style="primary"
        )
        self.run_button.on_click(lambda _button: self.run_safely(self.run))

    def build(self) -> widgets.Widget:
        """Build matrix panel."""
        self.container = widgets.VBox(
            [
                widgets.HBox([self.kind, self.unit, self.min_occurrences]),
                self.run_button,
                self.output,
            ]
        )
        return self.container

    def run(self) -> None:
        """Build and render a matrix."""
        result = self.services.matrices.build(
            kind=str(self.kind.value),
            unit=str(self.unit.value),
            min_occurrences=int(self.min_occurrences.value),
        )
        rows = dataframe_like_to_rows(result.table, limit=20)
        self.output.clear_output()
        with self.output:
            display(HTML(rows_to_html([{"kind": result.kind, "unit": result.unit}])))
            display(HTML(rows_to_html(rows)))

"""PubMed and PubMed Central import panel."""

from __future__ import annotations

from typing import Any

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.renderers.tables import rows_to_html
from biblioflow_nb.state import NotebookSession
from biblioflow_nb.widgets.base import WidgetPanel


class RemoteSourcesPanel(WidgetPanel):
    """Panel for importing PubMed and PubMed Central records."""

    title = "PubMed/PMC"

    def __init__(self, session: NotebookSession, services: Any) -> None:
        super().__init__(session, services)
        self.source_dropdown = widgets.Dropdown(
            description="Source",
            options=[("PubMed", "pubmed"), ("PubMed Central", "pmc")],
            value="pubmed",
        )
        self.query_text = widgets.Textarea(
            description="Query",
            placeholder="bibliometrics AND reproducibility",
            rows=4,
        )
        self.limit_input = widgets.BoundedIntText(
            description="Limit",
            min=1,
            max=1000,
            value=100,
        )
        self.email_text = widgets.Text(
            description="Email",
            placeholder="researcher@example.org",
        )
        self.api_key_text = widgets.Password(
            description="API key",
            placeholder="Optional",
        )
        self.tool_text = widgets.Text(
            description="Tool",
            value="biblioflow-nb",
        )
        self.name_text = widgets.Text(
            description="Name",
            placeholder="Optional dataset name",
        )
        self.import_button = widgets.Button(
            description="Search and import",
            button_style="primary",
        )
        self.import_button.on_click(
            lambda _button: self.run_safely(self.import_from_ui)
        )

    def build(self) -> widgets.Widget:
        """Build the remote-source panel."""
        self.container = widgets.VBox(
            [
                widgets.HTML("<h3>Search PubMed or PubMed Central</h3>"),
                widgets.HTML(
                    "<p>Provide a contact email here or set "
                    "<code>BIBLIOFLOW_NCBI_EMAIL</code> in the notebook "
                    "environment.</p>"
                ),
                self.source_dropdown,
                self.query_text,
                widgets.HBox([self.limit_input, self.email_text]),
                widgets.HBox([self.api_key_text, self.tool_text]),
                self.name_text,
                self.import_button,
                self.output,
            ]
        )
        return self.container

    def import_from_ui(self) -> None:
        """Search the selected remote source and store the imported dataset."""
        self.output.clear_output()
        query = str(self.query_text.value or "").strip()
        if not query:
            raise ValueError("Provide a PubMed or PubMed Central query.")

        kwargs = {
            "query": query,
            "limit": int(self.limit_input.value),
            "email": _optional_text(self.email_text.value),
            "api_key": _optional_text(self.api_key_text.value),
            "tool": _optional_text(self.tool_text.value) or "biblioflow-nb",
            "name": _optional_text(self.name_text.value),
        }
        source = str(self.source_dropdown.value)
        if source == "pmc":
            dataset = self.services.datasets.from_pmc(**kwargs)
            label = "PubMed Central"
        else:
            dataset = self.services.datasets.from_pubmed(**kwargs)
            label = "PubMed"

        self.api_key_text.value = ""
        summary = self.services.datasets.summary()
        with self.output:
            display(HTML(f"<h4>{label} import summary</h4>"))
            display(HTML(rows_to_html([summary])))
            display(
                HTML(
                    "<p>Imported "
                    f"<strong>{len(dataset)}</strong> records. Overview, "
                    "filters, matrices, networks, and exports now use this "
                    "active dataset.</p>"
                )
            )


def _optional_text(value: Any) -> str | None:
    """Return stripped widget text or None."""
    text = str(value or "").strip()
    return text or None

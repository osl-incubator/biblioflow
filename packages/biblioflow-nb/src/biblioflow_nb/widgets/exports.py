"""Export panel."""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.colab.download import colab_download
from biblioflow_nb.renderers.tables import rows_to_html
from biblioflow_nb.widgets.base import WidgetPanel


class ExportsPanel(WidgetPanel):
    """Panel for exporting notebook app outputs."""

    title = "Exports"

    def __init__(self, session, services) -> None:  # type: ignore[no-untyped-def]
        super().__init__(session, services)
        self.path = widgets.Text(description="Path", value="biblioflow-records.json")
        self.format = widgets.Dropdown(
            description="Format", options=["json", "csv"], value="json"
        )
        self.report_path = widgets.Text(
            description="Report", value="biblioflow-report.pdf"
        )
        self.export_button = widgets.Button(
            description="Export dataset", button_style="primary"
        )
        self.report_button = widgets.Button(
            description="Generate PDF report", button_style="success"
        )
        self.download_button = widgets.Button(description="Download in Colab")
        self.export_button.on_click(lambda _button: self.run_safely(self.export))
        self.report_button.on_click(
            lambda _button: self.run_safely(self.generate_report)
        )
        self.download_button.on_click(
            lambda _button: self.run_safely(self.download_latest)
        )

    def build(self) -> widgets.Widget:
        """Build export panel."""
        self.container = widgets.VBox(
            [
                widgets.HBox([self.path, self.format]),
                widgets.HBox([self.export_button, self.download_button]),
                widgets.HBox([self.report_path, self.report_button]),
                self.output,
            ]
        )
        return self.container

    def export(self) -> None:
        """Export current dataset."""
        path = self.services.exports.export_dataset(
            self.path.value, format=str(self.format.value)
        )
        self.output.clear_output()
        with self.output:
            display(HTML(f"<p>Exported to <code>{path}</code>.</p>"))
            display(
                HTML(rows_to_html([item.to_dict() for item in self.session.exports]))
            )

    def generate_report(self) -> None:
        """Generate a professional PDF report for the current dataset."""
        result = self.services.reports.generate_report(self.report_path.value)
        self.output.clear_output()
        with self.output:
            display(
                HTML(f"<p>Generated report at <code>{result.output_path}</code>.</p>")
            )
            display(
                HTML(rows_to_html([item.to_dict() for item in self.session.exports]))
            )

    def download_latest(self) -> None:
        """Download latest export in Colab when possible."""
        if not self.session.exports:
            raise ValueError("Export a file before downloading.")
        colab_download(self.session.exports[-1].path)

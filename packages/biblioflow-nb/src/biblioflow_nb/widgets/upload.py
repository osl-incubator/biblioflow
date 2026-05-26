"""Upload and load panel."""

from __future__ import annotations

from pathlib import Path

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.io import TemporaryUploadStore, upload_items
from biblioflow_nb.renderers.tables import rows_to_html
from biblioflow_nb.widgets.base import WidgetPanel


class UploadPanel(WidgetPanel):
    """Panel for loading bibliographic data."""

    title = "Data"

    def __init__(self, session, services) -> None:  # type: ignore[no-untyped-def]
        super().__init__(session, services)
        self.upload_store = TemporaryUploadStore()
        self.file_upload = widgets.FileUpload(multiple=False)
        self.path_text = widgets.Text(description="Path", placeholder="records.ris")
        self.format_dropdown = widgets.Dropdown(
            description="Format",
            options=[
                "auto",
                "ris",
                "bibtex",
                "csv",
                "json",
                "jsonl",
                "nbib",
                "xml",
                "yaml",
            ],
            value="auto",
        )
        self.provider_dropdown = widgets.Dropdown(
            description="Provider",
            options=[
                "auto",
                "generic",
                "scopus",
                "wos",
                "pubmed",
                "crossref",
                "openalex",
            ],
            value="auto",
        )
        self.load_button = widgets.Button(description="Load", button_style="primary")
        self.load_button.on_click(lambda _button: self.run_safely(self.load_from_ui))

    def build(self) -> widgets.Widget:
        """Build the upload panel."""
        self.container = widgets.VBox(
            [
                widgets.HTML("<h3>Load bibliographic data</h3>"),
                self.file_upload,
                self.path_text,
                widgets.HBox([self.format_dropdown, self.provider_dropdown]),
                self.load_button,
                self.output,
            ]
        )
        return self.container

    def load_from_ui(self) -> None:
        """Load a path or widget upload."""
        self.output.clear_output()
        source: str | Path
        items = upload_items(self.file_upload.value)
        if items:
            item = items[0]
            path = self.upload_store.write_upload(
                str(item.get("name") or "upload"), item.get("content", b"")
            )
            source = path
        else:
            source = self.path_text.value.strip()
        if not source:
            raise ValueError("Provide a file path or upload a file.")
        dataset = self.services.datasets.load(
            source,
            provider=str(self.provider_dropdown.value),
            format=str(self.format_dropdown.value),
        )
        summary = self.services.datasets.summary()
        with self.output:
            display(HTML("<h4>Import summary</h4>"))
            display(HTML(rows_to_html([summary])))
            display(HTML(f"<p>Loaded <strong>{len(dataset)}</strong> records.</p>"))

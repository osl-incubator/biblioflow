"""Remote-source screening panel."""

from __future__ import annotations

from typing import Any

import ipywidgets as widgets
from IPython.display import HTML, display

from biblioflow_nb.renderers.tables import rows_to_html
from biblioflow_nb.state import NotebookSession
from biblioflow_nb.widgets.base import WidgetPanel


class RemoteSourcesPanel(WidgetPanel):
    """Panel for staging remote records before promotion."""

    title = "Remote screening"

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
            placeholder="Optional screening run name",
        )
        self.import_button = widgets.Button(
            description="Search and stage",
            button_style="primary",
        )
        self.promote_button = widgets.Button(
            description="Promote staged records",
            button_style="success",
        )
        self.import_button.on_click(
            lambda _button: self.run_safely(self.import_from_ui)
        )
        self.promote_button.on_click(
            lambda _button: self.run_safely(self.promote_from_ui)
        )

    def build(self) -> widgets.Widget:
        """Build the remote-source panel."""
        self.container = widgets.VBox(
            [
                widgets.HTML("<h3>Search and screen remote records</h3>"),
                widgets.HTML(
                    "<p>Search a supported remote source, review the staged "
                    "screening run, then promote candidates into the active "
                    "notebook dataset. For NCBI sources, provide a contact "
                    "email here or set <code>BIBLIOFLOW_NCBI_EMAIL</code>.</p>"
                ),
                self.source_dropdown,
                self.query_text,
                widgets.HBox([self.limit_input, self.email_text]),
                widgets.HBox([self.api_key_text, self.tool_text]),
                self.name_text,
                widgets.HBox([self.import_button, self.promote_button]),
                self.output,
            ]
        )
        return self.container

    def import_from_ui(self) -> None:
        """Search the selected remote source and stage candidates."""
        self.output.clear_output()
        query = str(self.query_text.value or "").strip()
        if not query:
            raise ValueError("Provide a remote source query.")

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
            run = self.services.screening.stage_pmc(**kwargs)
        else:
            run = self.services.screening.stage_pubmed(**kwargs)

        self.api_key_text.value = ""
        with self.output:
            display(HTML(f"<h4>{run['name']}</h4>"))
            display(HTML(rows_to_html([_run_summary(run)])))
            display(HTML(rows_to_html(_candidate_preview(run))))
            display(
                HTML(
                    "<p>Review the candidates above. Use programmatic "
                    "methods such as <code>app.update_candidates(...)</code> "
                    "for detailed decisions, or click promote to import all "
                    "non-duplicate staged candidates.</p>"
                )
            )

    def promote_from_ui(self) -> None:
        """Promote all importable candidates from the active screening run."""
        run = self.session.active_screening_run()
        if run is None:
            raise ValueError("Create or select a screening run before promotion.")
        candidate_ids = [
            str(candidate["candidate_id"])
            for candidate in run.get("candidates", [])
            if isinstance(candidate, dict)
            and str(candidate.get("status"))
            not in {"excluded", "duplicate", "error", "imported"}
        ]
        dataset = self.services.screening.promote_candidates(
            candidate_ids,
            name=_optional_text(self.name_text.value),
        )
        summary = self.services.datasets.summary()
        with self.output:
            display(HTML("<h4>Promoted screening candidates</h4>"))
            display(HTML(rows_to_html([summary])))
            display(
                HTML(
                    "<p>Imported "
                    f"<strong>{len(dataset)}</strong> records into the active "
                    "notebook dataset.</p>"
                )
            )


def _run_summary(run: dict[str, Any]) -> dict[str, Any]:
    """Return one display row for a screening run."""
    return {
        "name": run.get("name"),
        "source": run.get("source_label"),
        "records": run.get("records"),
        "status_counts": run.get("status_counts"),
    }


def _candidate_preview(run: dict[str, Any], *, limit: int = 10) -> list[dict[str, Any]]:
    """Return display rows for the first screening candidates."""
    rows: list[dict[str, Any]] = []
    candidates = run.get("candidates", [])
    if not isinstance(candidates, list):
        return rows
    for candidate in candidates[:limit]:
        if isinstance(candidate, dict):
            rows.append(
                {
                    "status": candidate.get("status"),
                    "title": candidate.get("title"),
                    "year": candidate.get("year"),
                    "authors": "; ".join(candidate.get("authors", [])),
                    "source": candidate.get("source_title"),
                }
            )
    return rows


def _optional_text(value: Any) -> str | None:
    """Return stripped widget text or None."""
    text = str(value or "").strip()
    return text or None

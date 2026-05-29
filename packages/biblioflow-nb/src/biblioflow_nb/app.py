"""Top-level notebook application object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import ipywidgets as widgets
from IPython.display import display

from biblioflow_nb.config import NotebookConfig
from biblioflow_nb.services import (
    AnalysisService,
    DatasetService,
    ExportService,
    MatrixService,
    NetworkService,
    ReportService,
    ScreeningService,
)
from biblioflow_nb.state import NotebookSession
from biblioflow_nb.widgets.affiliations import AffiliationsPanel
from biblioflow_nb.widgets.authors import AuthorsPanel
from biblioflow_nb.widgets.countries import CountriesPanel
from biblioflow_nb.widgets.documents import DocumentsPanel
from biblioflow_nb.widgets.exports import ExportsPanel
from biblioflow_nb.widgets.filters import FiltersPanel
from biblioflow_nb.widgets.keywords import KeywordsPanel
from biblioflow_nb.widgets.layout import AppLayout
from biblioflow_nb.widgets.maps import MapsPanel
from biblioflow_nb.widgets.matrices import MatrixPanel
from biblioflow_nb.widgets.networks import NetworkPanel
from biblioflow_nb.widgets.overview import OverviewPanel
from biblioflow_nb.widgets.remote_sources import RemoteSourcesPanel
from biblioflow_nb.widgets.sources import SourcesPanel
from biblioflow_nb.widgets.upload import UploadPanel
from biblioflow_nb.widgets.validation import ValidationPanel


@dataclass
class NotebookServices:
    """Service container shared by widget panels."""

    datasets: DatasetService
    analysis: AnalysisService
    matrices: MatrixService
    networks: NetworkService
    exports: ExportService
    reports: ReportService
    screening: ScreeningService

    @classmethod
    def create(cls, session: NotebookSession) -> NotebookServices:
        """Create service instances for a session."""
        datasets = DatasetService(session)
        return cls(
            datasets=datasets,
            analysis=AnalysisService(session, datasets),
            matrices=MatrixService(session, datasets),
            networks=NetworkService(session, datasets),
            exports=ExportService(session, datasets),
            reports=ReportService(session, datasets),
            screening=ScreeningService(session),
        )


class BiblioFlowNotebookApp:
    """Notebook widget app that orchestrates biblioflow workflows."""

    def __init__(
        self,
        *,
        session: NotebookSession | None = None,
        config: NotebookConfig | None = None,
        records: Any | None = None,
    ) -> None:
        self.session = session or NotebookSession()
        self.config = config or NotebookConfig()
        self.services = NotebookServices.create(self.session)
        self.panels = [
            UploadPanel(self.session, self.services),
            RemoteSourcesPanel(self.session, self.services),
            ValidationPanel(self.session, self.services),
            FiltersPanel(self.session, self.services),
            OverviewPanel(self.session, self.services),
            SourcesPanel(self.session, self.services),
            AuthorsPanel(self.session, self.services),
            AffiliationsPanel(self.session, self.services),
            CountriesPanel(self.session, self.services),
            DocumentsPanel(self.session, self.services),
            KeywordsPanel(self.session, self.services),
            MatrixPanel(self.session, self.services),
            NetworkPanel(self.session, self.services),
            MapsPanel(self.session, self.services),
            ExportsPanel(self.session, self.services),
        ]
        self.layout = AppLayout(self.panels)
        if records is not None:
            self.load(records)

    @property
    def widget(self) -> widgets.Widget:
        """Return the root widget."""
        return self.layout.build()

    def display(self) -> BiblioFlowNotebookApp:
        """Display the app and return it for programmatic use."""
        display(self.widget)
        return self

    def load(self, source: Any, **kwargs: Any) -> Any:
        """Load a dataset into the app session."""
        return self.services.datasets.load(source, **kwargs)

    def from_pubmed(self, **kwargs: Any) -> Any:
        """Import PubMed records into the app session."""
        return self.services.datasets.from_pubmed(**kwargs)

    def from_pmc(self, **kwargs: Any) -> Any:
        """Import PubMed Central records into the app session."""
        return self.services.datasets.from_pmc(**kwargs)

    def from_pubmed_central(self, **kwargs: Any) -> Any:
        """Import PubMed Central records into the app session."""
        return self.from_pmc(**kwargs)

    def stage_records(self, records: Any, **kwargs: Any) -> dict[str, Any]:
        """Stage records as screening candidates without importing them."""
        return self.services.screening.stage_records(records, **kwargs)

    def stage_file(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Stage a local file as screening candidates without importing it."""
        return self.services.screening.stage_file(path, **kwargs)

    def stage_pubmed(self, **kwargs: Any) -> dict[str, Any]:
        """Stage PubMed results as screening candidates."""
        return self.services.screening.stage_pubmed(**kwargs)

    def stage_pmc(self, **kwargs: Any) -> dict[str, Any]:
        """Stage PubMed Central results as screening candidates."""
        return self.services.screening.stage_pmc(**kwargs)

    def stage_pubmed_central(self, **kwargs: Any) -> dict[str, Any]:
        """Stage PubMed Central results as screening candidates."""
        return self.stage_pmc(**kwargs)

    def update_candidates(
        self, candidate_ids: list[str], **kwargs: Any
    ) -> dict[str, Any]:
        """Apply a screening decision to notebook candidates."""
        return self.services.screening.update_candidates(candidate_ids, **kwargs)

    def promote_candidates(
        self, candidate_ids: list[str] | None = None, **kwargs: Any
    ) -> Any:
        """Promote screening candidates into the active notebook dataset."""
        return self.services.screening.promote_candidates(candidate_ids, **kwargs)

    def report(self, path: str, **kwargs: Any) -> Any:
        """Generate a PDF report for the active notebook dataset."""
        return self.services.reports.generate_report(path, **kwargs)

    def refresh(self) -> None:
        """Refresh all panels that implement refresh behavior."""
        for panel in self.panels:
            panel.refresh()

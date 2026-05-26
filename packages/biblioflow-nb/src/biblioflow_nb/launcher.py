"""Public launch helpers."""

from __future__ import annotations

from typing import Any

from biblioflow_nb.app import BiblioFlowNotebookApp
from biblioflow_nb.config import NotebookConfig
from biblioflow_nb.state import NotebookSession


def launch(
    data: Any | None = None,
    *,
    records: Any | None = None,
    display: bool = True,
    session: NotebookSession | None = None,
    config: NotebookConfig | None = None,
    **load_kwargs: Any,
) -> BiblioFlowNotebookApp:
    """Create and optionally display the notebook app."""
    initial_records = records if records is not None else data
    notebook_app = BiblioFlowNotebookApp(session=session, config=config)
    if initial_records is not None:
        notebook_app.load(initial_records, **load_kwargs)
    if display:
        notebook_app.display()
    return notebook_app


def app(**kwargs: Any) -> BiblioFlowNotebookApp:
    """Alias for :func:`launch`."""
    return launch(**kwargs)


def open_dataset(dataset: Any, **kwargs: Any) -> BiblioFlowNotebookApp:
    """Launch the app with an existing biblioflow dataset."""
    return launch(records=dataset, **kwargs)


def sample_app(*, display: bool = True) -> BiblioFlowNotebookApp:
    """Launch an empty sample app."""
    return launch(display=display)

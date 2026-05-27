"""Notebook widget application for biblioflow."""

from biblioflow_nb.app import BiblioFlowNotebookApp
from biblioflow_nb.colab.compat import colab_setup, is_colab
from biblioflow_nb.launcher import app, launch, open_dataset, sample_app
from biblioflow_nb.state import NotebookExport, NotebookSession, NotebookUpload

__version__ = "0.2.0"  # semantic-release

__all__ = [
    "BiblioFlowNotebookApp",
    "NotebookExport",
    "NotebookSession",
    "NotebookUpload",
    "__version__",
    "app",
    "colab_setup",
    "is_colab",
    "launch",
    "open_dataset",
    "sample_app",
]

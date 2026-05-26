"""Python-native bibliographic metadata and bibliometrics workflows."""

from biblioflow.analysis import DescriptiveSummary, analyze
from biblioflow.core import BibliographicDataset, LoadWarning
from biblioflow.exceptions import (
    AmbiguousSourceError,
    BiblioFlowError,
    OptionalDependencyError,
    UnsupportedFormatError,
)
from biblioflow.export import export
from biblioflow.load import infer_format, infer_provider, load
from biblioflow.mapping import (
    Historiograph,
    ThematicEvolution,
    ThematicMap,
    conceptual_structure,
    historiograph,
    map_themes,
    trace_themes,
)
from biblioflow.matrices import MatrixResult, matrix
from biblioflow.networks import NetworkResult, network

__version__ = "0.1.0"  # semantic-release

__all__ = [
    "AmbiguousSourceError",
    "BiblioFlowError",
    "BibliographicDataset",
    "DescriptiveSummary",
    "Historiograph",
    "LoadWarning",
    "MatrixResult",
    "NetworkResult",
    "OptionalDependencyError",
    "ThematicEvolution",
    "ThematicMap",
    "UnsupportedFormatError",
    "__version__",
    "analyze",
    "conceptual_structure",
    "export",
    "historiograph",
    "infer_format",
    "infer_provider",
    "load",
    "map_themes",
    "matrix",
    "network",
    "trace_themes",
]

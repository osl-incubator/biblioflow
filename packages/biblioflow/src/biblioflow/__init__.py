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
from biblioflow.filters import (
    DatasetFilterSpec,
    FilteredDatasetResult,
    FilterOptions,
    available_filter_values,
    filter_dataset,
    summarize_filters,
)
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
from biblioflow.normalize.deduplicate import deduplicate, enrich
from biblioflow.results import (
    DatasetSummary,
    ImportSummary,
    summarize_dataset,
    summarize_import,
)

__version__ = "0.1.0"  # semantic-release

__all__ = [
    "AmbiguousSourceError",
    "BiblioFlowError",
    "BibliographicDataset",
    "DatasetFilterSpec",
    "DatasetSummary",
    "DescriptiveSummary",
    "FilterOptions",
    "FilteredDatasetResult",
    "Historiograph",
    "ImportSummary",
    "LoadWarning",
    "MatrixResult",
    "NetworkResult",
    "OptionalDependencyError",
    "ThematicEvolution",
    "ThematicMap",
    "UnsupportedFormatError",
    "__version__",
    "analyze",
    "available_filter_values",
    "conceptual_structure",
    "deduplicate",
    "enrich",
    "export",
    "filter_dataset",
    "historiograph",
    "infer_format",
    "infer_provider",
    "load",
    "map_themes",
    "matrix",
    "network",
    "summarize_dataset",
    "summarize_filters",
    "summarize_import",
    "trace_themes",
]

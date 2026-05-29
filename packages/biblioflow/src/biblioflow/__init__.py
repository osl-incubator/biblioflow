"""
title: Python-native bibliographic metadata and bibliometrics workflows.
"""

from biblioflow.analysis import DescriptiveSummary, analyze
from biblioflow.core import BibliographicDataset, LoadWarning
from biblioflow.exceptions import (
    AmbiguousSourceError,
    APIConfigurationError,
    BiblioFlowError,
    OptionalDependencyError,
    ParseError,
    SourceDetectionError,
    UnsupportedFormatError,
    UnsupportedSourceError,
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
from biblioflow.reporting import (
    PrismaFlow,
    ReportAsset,
    ReportProject,
    ReportResult,
    ReportSource,
    ReportWarning,
    generate_report,
    report,
)
from biblioflow.results import (
    DatasetSummary,
    ImportSummary,
    summarize_dataset,
    summarize_import,
)
from biblioflow.sources import (
    coerce_pymedx_article,
    from_crossref,
    from_openalex,
    from_pmc,
    from_pubmed,
    from_pubmed_central,
    from_scopus,
    normalize_pmc_article,
    normalize_pubmed_article,
)

__version__ = "0.3.0"  # semantic-release

__all__ = [
    "APIConfigurationError",
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
    "ParseError",
    "PrismaFlow",
    "ReportAsset",
    "ReportProject",
    "ReportResult",
    "ReportSource",
    "ReportWarning",
    "SourceDetectionError",
    "ThematicEvolution",
    "ThematicMap",
    "UnsupportedFormatError",
    "UnsupportedSourceError",
    "__version__",
    "analyze",
    "available_filter_values",
    "coerce_pymedx_article",
    "conceptual_structure",
    "deduplicate",
    "enrich",
    "export",
    "filter_dataset",
    "from_crossref",
    "from_openalex",
    "from_pmc",
    "from_pubmed",
    "from_pubmed_central",
    "from_scopus",
    "generate_report",
    "historiograph",
    "infer_format",
    "infer_provider",
    "load",
    "map_themes",
    "matrix",
    "network",
    "normalize_pmc_article",
    "normalize_pubmed_article",
    "report",
    "summarize_dataset",
    "summarize_filters",
    "summarize_import",
    "trace_themes",
]

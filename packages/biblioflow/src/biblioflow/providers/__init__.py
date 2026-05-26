"""
title: Provider-specific adapters.
"""

from biblioflow.providers.adapters import (
    adapt_crossref,
    adapt_openalex,
    adapt_pubmed,
    adapt_record,
)

__all__ = ["adapt_crossref", "adapt_openalex", "adapt_pubmed", "adapt_record"]

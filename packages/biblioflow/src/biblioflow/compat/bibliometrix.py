"""
title: Bibliometrix-style compatibility helpers.
summary: |-
  These helpers intentionally live outside the main namespace so biblioflow
  keeps a
  Pythonic API while offering a low-friction migration path.
"""

from __future__ import annotations

from typing import Any

from biblioflow.analysis import analyze
from biblioflow.load import load
from biblioflow.matrices import matrix
from biblioflow.networks import network


def convert2df(source: Any, **kwargs: Any) -> Any:
    """
    title: >-
      Bibliometrix-style alias for `biblioflow.load(..., as_dataframe=True)`.
    parameters:
      source:
        type: Any
        description: Source value.
      kwargs:
        type: Any
        description: Additional keyword arguments.
        variadic: keyword
    returns:
      type: Any
    """
    return load(source, as_dataframe=True, **kwargs)


def biblio_analysis(records: Any, **kwargs: Any) -> Any:
    """
    title: Bibliometrix-style alias for `biblioflow.analyze`.
    parameters:
      records:
        type: Any
        description: Records value.
      kwargs:
        type: Any
        description: Additional keyword arguments.
        variadic: keyword
    returns:
      type: Any
    """
    return analyze(records, **kwargs)


def biblio_network(records: Any, **kwargs: Any) -> Any:
    """
    title: Bibliometrix-style alias for `biblioflow.matrix`.
    parameters:
      records:
        type: Any
        description: Records value.
      kwargs:
        type: Any
        description: Additional keyword arguments.
        variadic: keyword
    returns:
      type: Any
    """
    return matrix(records, **kwargs)


def network_plot(records: Any, **kwargs: Any) -> Any:
    """
    title: Return a simple network object in place of Bibliometrix networkPlot.
    parameters:
      records:
        type: Any
        description: Records value.
      kwargs:
        type: Any
        description: Additional keyword arguments.
        variadic: keyword
    returns:
      type: Any
    """
    return network(records, **kwargs)


# R-inspired camelCase aliases for users migrating notebooks. They remain out of
# the top-level biblioflow namespace.
biblioAnalysis = biblio_analysis
biblioNetwork = biblio_network
networkPlot = network_plot

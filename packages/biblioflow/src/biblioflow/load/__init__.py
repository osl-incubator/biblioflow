"""
title: Loading entry points.
"""

from biblioflow.load.dispatcher import load
from biblioflow.load.infer import infer_format, infer_provider

__all__ = ["infer_format", "infer_provider", "load"]

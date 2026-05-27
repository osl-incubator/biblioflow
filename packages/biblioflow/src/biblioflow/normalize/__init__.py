"""
title: Normalization helpers.
"""

from biblioflow.normalize.authors import (
    author_names,
    normalize_author_name,
    parse_author_list,
)
from biblioflow.normalize.dates import parse_publication_date, parse_year
from biblioflow.normalize.ids import normalize_doi
from biblioflow.normalize.records import normalize_record
from biblioflow.normalize.references import normalize_reference, reference_texts
from biblioflow.normalize.text import clean_text, normalize_language, split_keywords

__all__ = [
    "author_names",
    "clean_text",
    "normalize_author_name",
    "normalize_doi",
    "normalize_language",
    "normalize_record",
    "normalize_reference",
    "parse_author_list",
    "parse_publication_date",
    "parse_year",
    "reference_texts",
    "split_keywords",
]

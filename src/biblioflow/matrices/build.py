"""Bibliometric matrix construction."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from biblioflow.core.dataset import BibliographicDataset
from biblioflow.core.frames import MatrixFrame, make_record_frame
from biblioflow.load.dispatcher import load


@dataclass
class MatrixResult:
    """A bibliometric matrix and its metadata."""

    table: Any
    kind: str
    unit: str
    metadata: dict[str, Any]

    def to_dataframe(self) -> Any:
        """Return the underlying table."""
        return self.table.copy()


def _terms(value: Any) -> list[str]:
    if isinstance(value, list):
        return sorted({str(item).strip() for item in value if str(item).strip()})
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text and text.lower() != "nan" else []


def matrix(
    records: BibliographicDataset | Any,
    *,
    kind: str = "co_occurrence",
    unit: str = "keywords_all",
    normalize: str | None = None,
    min_occurrences: int = 1,
) -> MatrixResult:
    """Build an incidence or co-occurrence matrix."""
    dataset = (
        load(records) if not isinstance(records, BibliographicDataset) else records
    )
    rows = dataset.to_records()
    if rows and unit not in rows[0]:
        msg = f"Unknown unit column: {unit!r}"
        raise ValueError(msg)

    docs_terms = [_terms(row.get(unit)) for row in rows]
    occurrences = Counter(term for terms in docs_terms for term in set(terms))
    vocabulary = sorted(
        term for term, count in occurrences.items() if count >= min_occurrences
    )

    if kind == "incidence":
        incidence_rows = []
        for index, terms in enumerate(docs_terms):
            term_set = set(terms)
            row = {term: int(term in term_set) for term in vocabulary}
            row["document"] = index
            incidence_rows.append(row)
        table = make_record_frame(incidence_rows, ["document", *vocabulary])
        return MatrixResult(
            table=table,
            kind=kind,
            unit=unit,
            metadata={"min_occurrences": min_occurrences, "normalize": normalize},
        )

    if kind not in {"co_occurrence", "collaboration"}:
        msg = f"Unsupported matrix kind: {kind!r}"
        raise ValueError(msg)

    table = MatrixFrame(vocabulary)
    for terms in docs_terms:
        selected = sorted(set(terms).intersection(vocabulary))
        for term in selected:
            table.increment(term, term)
        for left, right in combinations(selected, 2):
            table.increment(left, right)
            table.increment(right, left)

    if normalize == "association":
        for left in vocabulary:
            for right in vocabulary:
                if left == right:
                    continue
                denominator = occurrences[left] * occurrences[right]
                if denominator:
                    table.set(left, right, table.get(left, right) / denominator)

    return MatrixResult(
        table=table,
        kind=kind,
        unit=unit,
        metadata={"min_occurrences": min_occurrences, "normalize": normalize},
    )

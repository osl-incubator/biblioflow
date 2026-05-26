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


def _doc_id(row: dict[str, Any], index: int) -> str:
    return str(row.get("doi") or row.get("source_id") or row.get("title") or index)


def _co_occurrence_matrix(
    rows: list[dict[str, Any]],
    *,
    kind: str,
    unit: str,
    normalize: str | None,
    min_occurrences: int,
) -> MatrixResult:
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


def _bibliographic_coupling(
    rows: list[dict[str, Any]], *, min_occurrences: int
) -> MatrixResult:
    labels = [_doc_id(row, index) for index, row in enumerate(rows)]
    doc_refs = [set(_terms(row.get("references"))) for row in rows]
    table = MatrixFrame(labels)
    for index, refs in enumerate(doc_refs):
        table.set(labels[index], labels[index], float(len(refs)))
    for left, right in combinations(range(len(rows)), 2):
        weight = len(doc_refs[left].intersection(doc_refs[right]))
        if weight >= min_occurrences and weight > 0:
            table.set(labels[left], labels[right], float(weight))
            table.set(labels[right], labels[left], float(weight))
    return MatrixResult(
        table=table,
        kind="bibliographic_coupling",
        unit="references",
        metadata={"min_occurrences": min_occurrences},
    )


def _direct_citation(rows: list[dict[str, Any]]) -> MatrixResult:
    labels = [_doc_id(row, index) for index, row in enumerate(rows)]
    identifiers: list[tuple[str, str | None, str | None]] = []
    for index, row in enumerate(rows):
        identifiers.append((_doc_id(row, index), row.get("doi"), row.get("title")))
    table = MatrixFrame(labels)
    for index, row in enumerate(rows):
        source = labels[index]
        references = "\n".join(ref.casefold() for ref in _terms(row.get("references")))
        for target, doi, title in identifiers:
            if target == source or not references:
                continue
            doi_hit = bool(doi and doi.casefold() in references)
            title_hit = bool(
                title and len(title) > 12 and title.casefold() in references
            )
            if doi_hit or title_hit:
                table.increment(source, target)
    return MatrixResult(
        table=table,
        kind="direct_citation",
        unit="references",
        metadata={"directed": True},
    )


def matrix(
    records: BibliographicDataset | Any,
    *,
    kind: str = "co_occurrence",
    unit: str = "keywords_all",
    normalize: str | None = None,
    min_occurrences: int = 1,
) -> MatrixResult:
    """Build a bibliometric matrix.

    Supported kinds are `incidence`, `co_occurrence`, `collaboration`,
    `co_citation`, `bibliographic_coupling`, and `direct_citation`.
    """
    dataset = (
        load(records) if not isinstance(records, BibliographicDataset) else records
    )
    rows = dataset.to_records()

    if kind == "collaboration" and unit == "keywords_all":
        unit = "authors"
    if kind == "co_citation":
        unit = "references"
    if kind == "bibliographic_coupling":
        return _bibliographic_coupling(rows, min_occurrences=min_occurrences)
    if kind == "direct_citation":
        return _direct_citation(rows)

    if rows and unit not in rows[0]:
        msg = f"Unknown unit column: {unit!r}"
        raise ValueError(msg)
    if kind not in {"incidence", "co_occurrence", "collaboration", "co_citation"}:
        msg = f"Unsupported matrix kind: {kind!r}"
        raise ValueError(msg)
    return _co_occurrence_matrix(
        rows,
        kind=kind,
        unit=unit,
        normalize=normalize,
        min_occurrences=min_occurrences,
    )

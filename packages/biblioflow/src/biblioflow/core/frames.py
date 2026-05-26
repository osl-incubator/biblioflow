"""Small dataframe-like fallbacks used when pandas is not installed."""

from __future__ import annotations

import csv
import importlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


class RecordFrame:
    """A tiny records-oriented DataFrame fallback.

    It implements only the methods biblioflow itself needs. When pandas is
    installed, biblioflow uses pandas DataFrames instead.
    """

    def __init__(
        self, records: Iterable[dict[str, Any]], columns: Iterable[str] | None = None
    ):
        self._records = [dict(record) for record in records]
        if columns is None:
            seen: list[str] = []
            for record in self._records:
                for key in record:
                    if key not in seen:
                        seen.append(key)
            self.columns = seen
        else:
            self.columns = list(columns)
        for record in self._records:
            for column in self.columns:
                record.setdefault(column, None)

    def __len__(self) -> int:
        return len(self._records)

    @property
    def empty(self) -> bool:
        return not self._records

    def copy(self) -> RecordFrame:
        return RecordFrame(self._records, self.columns)

    def iterrows(self):  # type: ignore[no-untyped-def]
        for index, record in enumerate(self._records):
            yield index, dict(record)

    def to_dict(self, orient: str = "records") -> Any:
        if orient == "records":
            return [
                {column: record.get(column) for column in self.columns}
                for record in self._records
            ]
        if orient == "list":
            return {
                column: [record.get(column) for record in self._records]
                for column in self.columns
            }
        msg = f"Unsupported orient: {orient!r}"
        raise ValueError(msg)

    def to_json(
        self, *_: Any, orient: str = "records", indent: int | None = None, **__: Any
    ) -> str:
        return json.dumps(
            self.to_dict(orient=orient), ensure_ascii=False, indent=indent
        )

    def to_csv(self, path: str | Path, *, index: bool = False) -> None:
        with Path(path).open("w", encoding="utf-8", newline="") as handle:
            fieldnames = (["index"] if index else []) + list(self.columns)
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for idx, record in enumerate(self._records):
                row = {column: record.get(column) for column in self.columns}
                if index:
                    row = {"index": idx, **row}
                writer.writerow(row)

    def select_columns(self, columns: Iterable[str]) -> RecordFrame:
        selected = list(columns)
        return RecordFrame(
            [
                {column: record.get(column) for column in selected}
                for record in self._records
            ],
            selected,
        )

    def rename(self, *, columns: dict[str, str]) -> RecordFrame:
        renamed_columns = [columns.get(column, column) for column in self.columns]
        records = []
        for record in self._records:
            records.append(
                {
                    columns.get(column, column): record.get(column)
                    for column in self.columns
                }
            )
        return RecordFrame(records, renamed_columns)


def make_record_frame(
    records: list[dict[str, Any]], columns: list[str] | None = None
) -> Any:
    """Return a pandas DataFrame when available, otherwise a RecordFrame."""
    try:
        pd = importlib.import_module("pandas")
    except ImportError:
        return RecordFrame(records, columns)
    frame = pd.DataFrame(records)
    if columns is not None:
        for column in columns:
            if column not in frame.columns:
                frame[column] = None
        frame = frame.loc[:, columns]
    return frame


class _MatrixLoc:
    def __init__(self, table: MatrixFrame) -> None:
        self._table = table

    def __getitem__(self, key: tuple[str, str]) -> float:
        row, column = key
        return self._table.get(row, column)

    def __setitem__(self, key: tuple[str, str], value: float) -> None:
        row, column = key
        self._table.set(row, column, value)


class MatrixFrame:
    """A small square matrix table with dataframe-like export helpers."""

    def __init__(self, labels: Iterable[str], fill: float = 0.0):
        self.index = list(labels)
        self.columns = list(labels)
        self._values = {
            row: {column: float(fill) for column in self.columns} for row in self.index
        }
        self.loc = _MatrixLoc(self)

    @property
    def empty(self) -> bool:
        return not self.index

    def copy(self) -> MatrixFrame:
        copied = MatrixFrame(self.index)
        for row in self.index:
            for column in self.columns:
                copied.set(row, column, self.get(row, column))
        return copied

    def get(self, row: str, column: str) -> float:
        return float(self._values[row][column])

    def set(self, row: str, column: str, value: float) -> None:
        self._values[row][column] = float(value)

    def increment(self, row: str, column: str, amount: float = 1.0) -> None:
        self.set(row, column, self.get(row, column) + amount)

    def to_dict(self, orient: str = "index") -> Any:
        if orient == "index":
            return {row: dict(self._values[row]) for row in self.index}
        if orient == "records":
            return [
                {
                    "term": row,
                    **{column: self.get(row, column) for column in self.columns},
                }
                for row in self.index
            ]
        msg = f"Unsupported orient: {orient!r}"
        raise ValueError(msg)

    def to_json(self, *_: Any, indent: int | None = None, **__: Any) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_csv(self, path: str | Path, *, index: bool = True) -> None:
        with Path(path).open("w", encoding="utf-8", newline="") as handle:
            fieldnames = (["term"] if index else []) + self.columns
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.index:
                payload: dict[str, Any] = {
                    column: self.get(row, column) for column in self.columns
                }
                if index:
                    payload = {"term": row, **payload}
                writer.writerow(payload)

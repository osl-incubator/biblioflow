"""
title: Dataset container for normalized bibliographic records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from biblioflow.core.frames import RecordFrame, make_record_frame
from biblioflow.core.warnings import LoadWarning
from biblioflow.schema import BIBLIOMETRIX_FIELD_MAP, CANONICAL_FIELDS


@dataclass
class BibliographicDataset:
    """
    title: Normalized bibliographic records plus load metadata and diagnostics.
    attributes:
      data:
        type: Any
        description: Data attribute.
      raw:
        type: list[dict[str, Any]]
        description: Raw attribute.
      metadata:
        type: dict[str, Any]
        description: Metadata attribute.
      warnings:
        type: list[LoadWarning]
        description: Warnings attribute.
      errors:
        type: list[str]
        description: Errors attribute.
    """

    data: Any
    raw: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[LoadWarning] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @classmethod
    def from_records(
        cls,
        records: list[dict[str, Any]],
        *,
        raw: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        warnings: list[LoadWarning] | None = None,
        errors: list[str] | None = None,
    ) -> BibliographicDataset:
        """
        title: Build a dataset from normalized record dictionaries.
        parameters:
          records:
            type: list[dict[str, Any]]
            description: Records value.
          raw:
            type: list[dict[str, Any]] | None
            description: Raw value.
          metadata:
            type: dict[str, Any] | None
            description: Metadata value.
          warnings:
            type: list[LoadWarning] | None
            description: Warnings value.
          errors:
            type: list[str] | None
            description: Errors value.
        returns:
          type: BibliographicDataset
        """
        frame = make_record_frame(records, list(CANONICAL_FIELDS))
        meta = dict(metadata or {})
        meta.setdefault("loaded_at", datetime.now(timezone.utc).isoformat())
        meta.setdefault("records", len(frame))
        return cls(
            data=frame,
            raw=list(raw or []),
            metadata=meta,
            warnings=list(warnings or []),
            errors=list(errors or []),
        )

    def __len__(self) -> int:
        """
        title: Return the number of normalized records.
        returns:
          type: int
        """
        return len(self.data)

    def __iter__(self):  # type: ignore[no-untyped-def]
        """
        title: Iterate over normalized records as dictionaries.
        """
        yield from self.to_records()

    def to_records(self, *, schema: str = "canonical") -> list[dict[str, Any]]:
        """
        title: Return records as a list of dictionaries.
        parameters:
          schema:
            type: str
            description: Schema value.
        returns:
          type: list[dict[str, Any]]
        """
        frame = self.to_dataframe(schema=schema)
        return list(frame.to_dict(orient="records"))

    def to_dataframe(self, *, schema: str = "canonical") -> Any:
        """
        title: Return records as a DataFrame-like object.
        summary: |-
          If pandas is installed, this is a pandas DataFrame. Otherwise,
          biblioflow
          returns a small RecordFrame fallback with `to_dict`, `to_json`,
          and
          `to_csv` methods.
        parameters:
          schema:
            type: str
            description: Schema value.
        returns:
          type: Any
        """
        if schema == "canonical":
            return self.data.copy()
        if schema == "bibliometrix":
            cols = [c for c in BIBLIOMETRIX_FIELD_MAP if c in list(self.data.columns)]
            if isinstance(self.data, RecordFrame):
                return self.data.select_columns(cols).rename(
                    columns=BIBLIOMETRIX_FIELD_MAP
                )
            return self.data.loc[:, cols].rename(columns=BIBLIOMETRIX_FIELD_MAP).copy()
        msg = f"Unsupported schema: {schema!r}"
        raise ValueError(msg)

    def warning_dicts(self) -> list[dict[str, object]]:
        """
        title: Return loading warnings as dictionaries.
        returns:
          type: list[dict[str, object]]
        """
        return [warning.to_dict() for warning in self.warnings]

    def to_json(
        self, path: str | Path | None = None, *, schema: str = "canonical"
    ) -> str:
        """
        title: Serialize records to JSON and optionally write them to a file.
        parameters:
          path:
            type: str | Path | None
            description: Path value.
          schema:
            type: str
            description: Schema value.
        returns:
          type: str
        """
        frame = self.to_dataframe(schema=schema)
        text = str(frame.to_json(orient="records", force_ascii=False, indent=2))
        if path is not None:
            Path(path).write_text(text + "\n", encoding="utf-8")
        return text

    def to_csv(self, path: str | Path, *, schema: str = "canonical") -> None:
        """
        title: Write records to CSV.
        parameters:
          path:
            type: str | Path
            description: Path value.
          schema:
            type: str
            description: Schema value.
        """
        self.to_dataframe(schema=schema).to_csv(path, index=False)

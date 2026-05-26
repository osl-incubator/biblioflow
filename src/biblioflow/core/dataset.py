"""Dataset container for normalized bibliographic records."""

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
    """Normalized bibliographic records plus load metadata and diagnostics."""

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
        """Build a dataset from normalized record dictionaries."""
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
        """Return the number of normalized records."""
        return len(self.data)

    def __iter__(self):  # type: ignore[no-untyped-def]
        """Iterate over normalized records as dictionaries."""
        yield from self.to_records()

    def to_records(self, *, schema: str = "canonical") -> list[dict[str, Any]]:
        """Return records as a list of dictionaries."""
        frame = self.to_dataframe(schema=schema)
        return list(frame.to_dict(orient="records"))

    def to_dataframe(self, *, schema: str = "canonical") -> Any:
        """Return records as a DataFrame-like object.

        If pandas is installed, this is a pandas DataFrame. Otherwise, biblioflow
        returns a small RecordFrame fallback with `to_dict`, `to_json`, and
        `to_csv` methods.
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
        """Return loading warnings as dictionaries."""
        return [warning.to_dict() for warning in self.warnings]

    def to_json(
        self, path: str | Path | None = None, *, schema: str = "canonical"
    ) -> str:
        """Serialize records to JSON and optionally write them to a file."""
        frame = self.to_dataframe(schema=schema)
        text = str(frame.to_json(orient="records", force_ascii=False, indent=2))
        if path is not None:
            Path(path).write_text(text + "\n", encoding="utf-8")
        return text

    def to_csv(self, path: str | Path, *, schema: str = "canonical") -> None:
        """Write records to CSV."""
        self.to_dataframe(schema=schema).to_csv(path, index=False)

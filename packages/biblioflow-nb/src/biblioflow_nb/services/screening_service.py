"""Source-agnostic screening service for notebook sessions."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from biblioflow_nb.state import NotebookSession, NotebookUpload, utc_now

SCREENING_STATUSES = {
    "candidate",
    "selected",
    "maybe",
    "excluded",
    "duplicate",
    "imported",
    "error",
}
PROMOTABLE_STATUSES = {"candidate", "selected", "maybe"}


class ScreeningService:
    """Stage records in a notebook before promoting them into a dataset."""

    def __init__(self, session: NotebookSession) -> None:
        self.session = session

    def stage_records(
        self,
        records: list[dict[str, Any]] | Any,
        *,
        source: str = "generic",
        name: str | None = None,
    ) -> dict[str, Any]:
        """Create a screening run from raw records or a dataset-like object."""
        import biblioflow as bf

        normalized_source = "generic" if source == "auto" else source
        if _is_dataset(records):
            dataset = records
        else:
            if not records:
                raise ValueError("Provide records before creating a screening run.")
            dataset = bf.load(records, source=normalized_source, format="records")
        return self._create_run(
            dataset,
            origin_type="records",
            source=normalized_source,
            format="records",
            name=name or f"{_source_label(normalized_source)} records",
            metadata={"source": normalized_source, "format": "records"},
        )

    def stage_file(
        self,
        path: str | Path,
        *,
        source: str = "auto",
        format: str = "auto",
        name: str | None = None,
    ) -> dict[str, Any]:
        """Create a screening run from a local notebook file path."""
        import biblioflow as bf

        file_path = Path(path)
        dataset = bf.load(
            file_path,
            source=None if source == "auto" else source,
            provider=source,
            format=format,
        )
        upload = NotebookUpload(
            name=file_path.name,
            path=file_path,
            size=file_path.stat().st_size if file_path.exists() else None,
        )
        self.session.add_upload(upload)
        return self._create_run(
            dataset,
            origin_type="uploads",
            source=source,
            format=format,
            name=name or file_path.name,
            upload_names=[file_path.name],
            metadata={"source": source, "format": format, "path": str(file_path)},
        )

    def stage_pubmed(
        self,
        *,
        query: str,
        limit: int = 100,
        email: str | None = None,
        api_key: str | None = None,
        tool: str = "biblioflow-nb",
        name: str | None = None,
    ) -> dict[str, Any]:
        """Create a screening run from a PubMed API search."""
        import biblioflow as bf

        search_query = _required_query(query)
        dataset = bf.from_pubmed(
            query=search_query,
            limit=limit,
            tool=tool.strip() or "biblioflow-nb",
            email=_optional_string(email),
            api_key=_optional_string(api_key),
        )
        return self._create_run(
            dataset,
            origin_type="remote_search",
            source="pubmed",
            format="api",
            query=search_query,
            limit=limit,
            name=name or f"PubMed: {search_query}",
            metadata=_metadata_without_secrets(dict(getattr(dataset, "metadata", {}))),
        )

    def stage_pmc(
        self,
        *,
        query: str,
        limit: int = 100,
        email: str | None = None,
        api_key: str | None = None,
        tool: str = "biblioflow-nb",
        name: str | None = None,
    ) -> dict[str, Any]:
        """Create a screening run from a PubMed Central API search."""
        import biblioflow as bf

        search_query = _required_query(query)
        dataset = bf.from_pmc(
            query=search_query,
            limit=limit,
            tool=tool.strip() or "biblioflow-nb",
            email=_optional_string(email),
            api_key=_optional_string(api_key),
        )
        return self._create_run(
            dataset,
            origin_type="remote_search",
            source="pmc",
            format="api",
            query=search_query,
            limit=limit,
            name=name or f"PMC: {search_query}",
            metadata=_metadata_without_secrets(dict(getattr(dataset, "metadata", {}))),
        )

    def update_candidates(
        self,
        candidate_ids: list[str],
        *,
        status: str = "selected",
        reason: str | None = None,
        labels: list[str] | None = None,
        notes: str | None = None,
        screening_run_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply a screening decision to candidates."""
        run = self._target_run(screening_run_id)
        candidate_id_set = {
            candidate_id for candidate_id in candidate_ids if candidate_id
        }
        if not candidate_id_set:
            raise ValueError(
                "Select at least one candidate before applying a decision."
            )
        normalized_status = status.strip().casefold()
        if normalized_status not in SCREENING_STATUSES - {"imported"}:
            raise ValueError(f"Unsupported candidate status: {status}.")
        candidates = _screening_candidates(run)
        missing = sorted(candidate_id_set - _candidate_ids(candidates))
        if missing:
            raise KeyError(", ".join(missing))
        updated_at = utc_now()
        for candidate in candidates:
            if str(candidate["candidate_id"]) in candidate_id_set:
                candidate["status"] = normalized_status
                candidate["updated_at"] = updated_at
                if reason is not None:
                    candidate["decision_reason"] = _optional_string(reason)
                if labels is not None:
                    candidate["labels"] = [
                        label.strip() for label in labels if label.strip()
                    ]
                if notes is not None:
                    candidate["notes"] = _optional_string(notes)
        self._refresh_run(run, updated_at=updated_at)
        return run

    def promote_candidates(
        self,
        candidate_ids: list[str] | None = None,
        *,
        include_statuses: tuple[str, ...] | list[str] = ("selected",),
        name: str | None = None,
        screening_run_id: str | None = None,
    ) -> Any:
        """Promote screening candidates into the active notebook dataset."""
        import biblioflow as bf

        run = self._target_run(screening_run_id)
        candidates = _screening_candidates(run)
        candidate_id_set = (
            {candidate_id for candidate_id in candidate_ids if candidate_id}
            if candidate_ids is not None
            else None
        )
        if candidate_ids is not None and not candidate_id_set:
            raise ValueError("Select at least one candidate before promotion.")
        if candidate_id_set is None:
            requested_statuses = {
                status.strip().casefold() for status in include_statuses
            }
            unsupported = requested_statuses - PROMOTABLE_STATUSES
            if unsupported:
                raise ValueError(
                    "Only candidate, selected, and maybe records can be promoted."
                )
            selected = [
                candidate
                for candidate in candidates
                if str(candidate.get("status")) in requested_statuses
            ]
        else:
            missing = sorted(candidate_id_set - _candidate_ids(candidates))
            if missing:
                raise KeyError(", ".join(missing))
            selected = [
                candidate
                for candidate in candidates
                if str(candidate["candidate_id"]) in candidate_id_set
            ]
        selected = [
            candidate
            for candidate in selected
            if str(candidate.get("status"))
            not in {"excluded", "duplicate", "error", "imported"}
        ]
        if not selected:
            raise ValueError("No screening candidates match the selected decision.")
        dataset = bf.load(
            [dict(candidate["record"]) for candidate in selected],
            source="generic",
            format="records",
        )
        dataset_name = (
            name.strip()
            if name and name.strip()
            else f"{run['name']} — screened records"
        )
        self.session.set_dataset(dataset, name=dataset_name)
        dataset_id = uuid4().hex
        updated_at = utc_now()
        promoted_ids = {str(candidate["candidate_id"]) for candidate in selected}
        for candidate in candidates:
            if str(candidate["candidate_id"]) in promoted_ids:
                candidate["status"] = "imported"
                candidate["updated_at"] = updated_at
                candidate["imported_dataset_id"] = dataset_id
        promoted_dataset_ids = [
            str(item) for item in run.get("promoted_dataset_ids", [])
        ]
        promoted_dataset_ids.append(dataset_id)
        run["promoted_dataset_ids"] = promoted_dataset_ids
        self._refresh_run(run, updated_at=updated_at)
        return dataset

    def _create_run(
        self,
        dataset: Any,
        *,
        origin_type: str,
        source: str,
        format: str,
        name: str,
        query: str | None = None,
        limit: int | None = None,
        upload_names: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create and store one screening run from a dataset."""
        created_at = utc_now()
        candidates = _candidate_records(
            _dataset_records(dataset), created_at=created_at
        )
        status_counts = _candidate_status_counts(candidates)
        safe_metadata = _metadata_without_secrets(metadata or {})
        safe_metadata.update(
            {"records": len(candidates), "status_counts": status_counts}
        )
        run = {
            "screening_run_id": uuid4().hex,
            "created_at": created_at,
            "updated_at": created_at,
            "name": name,
            "origin_type": origin_type,
            "source": source,
            "source_label": _source_label(source),
            "format": format,
            "query": query,
            "limit": limit,
            "upload_names": upload_names or [],
            "records": len(candidates),
            "status_counts": status_counts,
            "promoted_dataset_ids": [],
            "candidates": candidates,
            "warnings": _dataset_warnings(dataset),
            "metadata": safe_metadata,
        }
        self.session.add_screening_run(run)
        return run

    def _target_run(self, screening_run_id: str | None) -> dict[str, Any]:
        """Return the selected screening run or raise a friendly error."""
        if screening_run_id is not None:
            return self.session.get_screening_run(screening_run_id)
        run = self.session.active_screening_run()
        if run is None:
            raise ValueError("Create or select a screening run first.")
        return run

    def _refresh_run(self, run: dict[str, Any], *, updated_at: str) -> None:
        """Refresh run counts and session registration after a mutation."""
        candidates = _screening_candidates(run)
        run["updated_at"] = updated_at
        run["records"] = len(candidates)
        run["status_counts"] = _candidate_status_counts(candidates)
        metadata = run.setdefault("metadata", {})
        if isinstance(metadata, dict):
            metadata["records"] = len(candidates)
            metadata["status_counts"] = run["status_counts"]
        self.session.add_screening_run(run)


def _is_dataset(value: Any) -> bool:
    """Return whether a value looks like a biblioflow dataset."""
    return hasattr(value, "to_records") and hasattr(value, "metadata")


def _dataset_records(dataset: Any) -> list[dict[str, Any]]:
    """Return records from a dataset-like object."""
    return [dict(record) for record in dataset.to_records()]


def _dataset_warnings(dataset: Any) -> list[dict[str, Any]]:
    """Return warning dictionaries from a dataset-like object."""
    if hasattr(dataset, "warning_dicts"):
        return [dict(warning) for warning in dataset.warning_dicts()]
    return []


def _candidate_records(
    records: list[dict[str, Any]], *, created_at: str
) -> list[dict[str, Any]]:
    """Return screening candidates with simple in-run duplicate marking."""
    seen: dict[str, str] = {}
    candidates: list[dict[str, Any]] = []
    for record in records:
        candidate = _candidate_from_record(record, created_at=created_at)
        deduplication_key = candidate.get("deduplication_key")
        if isinstance(deduplication_key, str) and deduplication_key in seen:
            candidate["status"] = "duplicate"
            candidate["duplicate_of_candidate_id"] = seen[deduplication_key]
        elif isinstance(deduplication_key, str):
            seen[deduplication_key] = str(candidate["candidate_id"])
        candidates.append(candidate)
    return candidates


def _candidate_from_record(
    record: dict[str, Any], *, created_at: str
) -> dict[str, Any]:
    """Return one candidate dictionary for a normalized record."""
    identifiers = _record_identifiers(record)
    return {
        "candidate_id": uuid4().hex,
        "status": "candidate",
        "created_at": created_at,
        "updated_at": created_at,
        "decision_reason": None,
        "labels": [],
        "notes": None,
        "imported_dataset_id": None,
        "deduplication_key": _deduplication_key(record, identifiers),
        "duplicate_of_candidate_id": None,
        "identifiers": identifiers,
        "title": _record_title(record),
        "year": _record_year(record),
        "authors": _record_authors(record),
        "source_title": _record_source_title(record),
        "record": record,
    }


def _screening_candidates(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Return mutable candidate dictionaries from a screening run."""
    raw_candidates = run.get("candidates", [])
    if not isinstance(raw_candidates, list):
        return []
    return [candidate for candidate in raw_candidates if isinstance(candidate, dict)]


def _candidate_ids(candidates: list[dict[str, Any]]) -> set[str]:
    """Return candidate IDs from candidate dictionaries."""
    return {str(candidate["candidate_id"]) for candidate in candidates}


def _candidate_status_counts(candidates: list[dict[str, Any]]) -> dict[str, int]:
    """Return candidate counts grouped by status."""
    counts: dict[str, int] = {}
    for candidate in candidates:
        status = str(candidate.get("status") or "candidate")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _record_identifiers(record: dict[str, Any]) -> dict[str, str]:
    """Return display identifiers from a normalized record."""
    identifiers: dict[str, str] = {}
    for key in ["doi", "pmid", "pmcid", "source_id"]:
        value = _record_string(record.get(key))
        if value:
            identifiers[key] = value
    return identifiers


def _record_title(record: dict[str, Any]) -> str:
    """Return a display title."""
    return _record_string(record.get("title")) or "Untitled record"


def _record_source_title(record: dict[str, Any]) -> str | None:
    """Return a display source title."""
    return _record_string(record.get("source_title") or record.get("journal"))


def _record_year(record: dict[str, Any]) -> int | None:
    """Return a publication year when available."""
    raw_year = record.get("publication_year", record.get("year"))
    if isinstance(raw_year, int):
        return raw_year
    if isinstance(raw_year, str) and raw_year.strip().isdigit():
        return int(raw_year.strip())
    return None


def _record_authors(record: dict[str, Any]) -> list[str]:
    """Return display authors."""
    raw_authors = record.get("authors") or record.get("authors_raw") or []
    if isinstance(raw_authors, str):
        return [raw_authors]
    if isinstance(raw_authors, list | tuple):
        return [str(author) for author in raw_authors if str(author).strip()][:8]
    return []


def _record_string(value: Any) -> str | None:
    """Return stripped string values only."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, int | float):
        return str(value)
    return None


def _deduplication_key(
    record: dict[str, Any], identifiers: dict[str, str]
) -> str | None:
    """Return a simple duplicate key for one record."""
    for key in ["doi", "pmid", "pmcid", "source_id"]:
        value = identifiers.get(key)
        if value:
            return f"{key}:{value.casefold()}"
    title = _record_title(record)
    year = _record_year(record)
    authors = _record_authors(record)
    if title != "Untitled record" and year and authors:
        return f"title:{title.casefold()}|{year}|{authors[0].casefold()}"
    return None


def _source_label(source: str) -> str:
    """Return a display label for a source."""
    normalized = source.strip().casefold().replace("-", "_")
    labels = {
        "auto": "Automatic source detection",
        "generic": "Generic records",
        "pubmed": "PubMed",
        "pmc": "PubMed Central",
        "pubmed_central": "PubMed Central",
        "openalex": "OpenAlex",
        "crossref": "Crossref",
        "scopus": "Scopus",
        "wos": "Web of Science",
    }
    return labels.get(normalized, normalized.replace("_", " ").title())


def _required_query(query: str) -> str:
    """Return a non-empty query."""
    stripped = query.strip()
    if not stripped:
        raise ValueError("Provide a remote source query.")
    return stripped


def _optional_string(value: str | None) -> str | None:
    """Return a stripped string or None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _metadata_without_secrets(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return metadata without known secret keys."""
    secret_keys = {"api_key", "apikey", "apiKey", "ncbi_api_key", "ncbiApiKey"}
    return {key: value for key, value in metadata.items() if key not in secret_keys}

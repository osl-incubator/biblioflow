"""Generic source-agnostic screening service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.core.json import to_jsonable
from biblioflow_web_backend.services.dataset_service import DatasetService
from biblioflow_web_backend.services.file_store import FileStore
from biblioflow_web_backend.services.project_store import ProjectStore, utc_now

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
    """Stage records from any source before creating analysis datasets."""

    def __init__(
        self, projects: ProjectStore, files: FileStore, datasets: DatasetService
    ) -> None:
        self.projects = projects
        self.files = files
        self.datasets = datasets

    def create_run(
        self,
        project_id: str,
        *,
        origin_type: str,
        source: str = "auto",
        format: str = "auto",
        upload_ids: list[str] | None = None,
        query: str | None = None,
        limit: int = 100,
        email: str | None = None,
        api_key: str | None = None,
        tool: str = "biblioflow-web",
        name: str | None = None,
        records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a screening run from uploads, remote search, or records."""
        normalized_origin = origin_type.strip().casefold()
        if normalized_origin == "uploads":
            dataset, run_metadata = self._dataset_from_uploads(
                project_id,
                upload_ids=upload_ids,
                source=source,
                format=format,
            )
        elif normalized_origin == "remote_search":
            dataset, run_metadata = self._dataset_from_remote_search(
                source=source,
                query=query,
                limit=limit,
                email=email,
                api_key=api_key,
                tool=tool,
            )
        elif normalized_origin == "records":
            dataset, run_metadata = self._dataset_from_records(
                records=records,
                source=source,
            )
        else:
            raise ApiError(
                "unsupported_screening_origin",
                f"Unsupported screening origin: {origin_type}.",
                400,
            )
        run_name = _screening_run_name(
            name=name,
            origin_type=normalized_origin,
            source=str(run_metadata.get("source") or source),
            query=query,
            upload_ids=upload_ids,
        )
        return self._persist_run(
            project_id,
            dataset=dataset,
            origin_type=normalized_origin,
            source=str(run_metadata.get("source") or source),
            source_label=str(run_metadata.get("source_label") or source),
            format=str(run_metadata.get("format") or format),
            query=query,
            upload_ids=upload_ids
            or cast(list[str], run_metadata.get("upload_ids", [])),
            limit=limit,
            name=run_name,
            metadata=run_metadata,
        )

    def list_runs(self, project_id: str) -> list[dict[str, Any]]:
        """List compact screening-run rows for a project."""
        project = self.projects.get_project(project_id)
        return [dict(item) for item in project.get("screening_runs", [])]

    def get_run(self, project_id: str, screening_run_id: str) -> dict[str, Any]:
        """Return one persisted screening run."""
        path = self._run_path(project_id, screening_run_id)
        if not path.exists():
            raise ApiError(
                "screening_run_not_found", "Screening run was not found.", 404
            )
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))

    def list_candidates(self, project_id: str) -> dict[str, Any]:
        """Return all staged candidates in a project with duplicate groups."""
        runs = [
            self.get_run(project_id, str(run["screening_run_id"]))
            for run in self.list_runs(project_id)
        ]
        run_summaries = [_run_list_item(run) for run in runs]
        candidates: list[dict[str, Any]] = []
        keyed_candidates: dict[str, list[dict[str, Any]]] = {}

        for run in runs:
            run_id = str(run["screening_run_id"])
            run_name = str(run.get("name") or "Untitled screening run")
            for candidate in _screening_candidates(run):
                row = {
                    **dict(candidate),
                    "id": f"{run_id}:{candidate['candidate_id']}",
                    "screening_run_id": run_id,
                    "screening_run_name": run_name,
                    "origin_type": run.get("origin_type"),
                    "source": run.get("source"),
                    "source_label": run.get("source_label"),
                    "format": run.get("format"),
                    "query": run.get("query"),
                    "upload_ids": run.get("upload_ids", []),
                    "duplicate_group_id": None,
                    "duplicate_group_size": 1,
                    "duplicate_match_basis": None,
                    "duplicate_confidence": None,
                }
                candidates.append(row)
                deduplication_key = row.get("deduplication_key")
                if isinstance(deduplication_key, str) and deduplication_key:
                    keyed_candidates.setdefault(deduplication_key, []).append(row)

        duplicate_groups = [
            _duplicate_group(key, group)
            for key, group in keyed_candidates.items()
            if len(group) > 1
        ]
        duplicate_groups.sort(
            key=lambda group: (
                -int(group["size"]),
                str(group["match_basis"]),
                str(group["label"]),
            )
        )

        for group in duplicate_groups:
            for candidate in keyed_candidates[str(group["duplicate_group_id"])]:
                candidate["duplicate_group_id"] = group["duplicate_group_id"]
                candidate["duplicate_group_size"] = group["size"]
                candidate["duplicate_match_basis"] = group["match_basis"]
                candidate["duplicate_confidence"] = group["confidence"]

        return {
            "records": len(candidates),
            "runs": run_summaries,
            "candidates": candidates,
            "duplicate_groups": duplicate_groups,
            "status_counts": _candidate_status_counts(candidates),
            "metadata": {
                "run_count": len(run_summaries),
                "duplicate_group_count": len(duplicate_groups),
                "duplicate_candidate_count": sum(
                    int(group["size"]) for group in duplicate_groups
                ),
            },
        }

    def update_candidates(
        self,
        project_id: str,
        screening_run_id: str,
        *,
        candidate_ids: list[str],
        status: str,
        decision_reason: str | None = None,
        labels: list[str] | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Apply a screening decision to candidates."""
        candidate_ids_set = {
            candidate_id for candidate_id in candidate_ids if candidate_id
        }
        if not candidate_ids_set:
            raise ApiError(
                "no_candidates_selected",
                "Select at least one candidate before applying a decision.",
                400,
            )
        normalized_status = status.strip().casefold()
        if normalized_status not in SCREENING_STATUSES - {"imported"}:
            raise ApiError(
                "unsupported_candidate_status",
                f"Unsupported candidate status: {status}.",
                400,
            )
        payload = self.get_run(project_id, screening_run_id)
        candidates = _screening_candidates(payload)
        missing = sorted(candidate_ids_set - _candidate_ids(candidates))
        if missing:
            raise ApiError(
                "candidate_not_found",
                "One or more candidates were not found.",
                404,
                details={"candidate_ids": missing},
            )
        updated_at = utc_now()
        for candidate in candidates:
            if str(candidate["candidate_id"]) in candidate_ids_set:
                candidate["status"] = normalized_status
                candidate["updated_at"] = updated_at
                if decision_reason is not None:
                    candidate["decision_reason"] = _optional_string(decision_reason)
                if labels is not None:
                    candidate["labels"] = [
                        label.strip() for label in labels if label.strip()
                    ]
                if notes is not None:
                    candidate["notes"] = _optional_string(notes)
        return self._save_run(project_id, payload, updated_at=updated_at)

    def update_candidates_bulk(
        self,
        project_id: str,
        *,
        candidate_refs: list[dict[str, str]],
        status: str,
        decision_reason: str | None = None,
        labels: list[str] | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Apply one decision to candidates spanning multiple screening runs."""
        grouped_refs: dict[str, set[str]] = {}
        for ref in candidate_refs:
            run_id = str(ref.get("screening_run_id") or "").strip()
            candidate_id = str(ref.get("candidate_id") or "").strip()
            if run_id and candidate_id:
                grouped_refs.setdefault(run_id, set()).add(candidate_id)
        if not grouped_refs:
            raise ApiError(
                "no_candidates_selected",
                "Select at least one candidate before applying a decision.",
                400,
            )
        normalized_status = status.strip().casefold()
        if normalized_status not in SCREENING_STATUSES - {"imported"}:
            raise ApiError(
                "unsupported_candidate_status",
                f"Unsupported candidate status: {status}.",
                400,
            )

        payloads = {run_id: self.get_run(project_id, run_id) for run_id in grouped_refs}
        missing: list[str] = []
        for run_id, payload in payloads.items():
            existing_ids = _candidate_ids(_screening_candidates(payload))
            missing.extend(
                f"{run_id}:{candidate_id}"
                for candidate_id in sorted(grouped_refs[run_id] - existing_ids)
            )
        if missing:
            raise ApiError(
                "candidate_not_found",
                "One or more candidates were not found.",
                404,
                details={"candidate_ids": missing},
            )

        updated_at = utc_now()
        for run_id, payload in payloads.items():
            selected_ids = grouped_refs[run_id]
            for candidate in _screening_candidates(payload):
                if str(candidate["candidate_id"]) in selected_ids:
                    candidate["status"] = normalized_status
                    candidate["updated_at"] = updated_at
                    if decision_reason is not None:
                        candidate["decision_reason"] = _optional_string(decision_reason)
                    if labels is not None:
                        candidate["labels"] = [
                            label.strip() for label in labels if label.strip()
                        ]
                    if notes is not None:
                        candidate["notes"] = _optional_string(notes)
            self._save_run(project_id, payload, updated_at=updated_at)
        return self.list_candidates(project_id)

    def promote_candidates(
        self,
        project_id: str,
        screening_run_id: str,
        *,
        candidate_ids: list[str] | None = None,
        include_statuses: list[str] | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Create a normal dataset from selected screening candidates."""
        import biblioflow as bf

        payload = self.get_run(project_id, screening_run_id)
        candidates = _screening_candidates(payload)
        candidate_ids_set = (
            {candidate_id for candidate_id in candidate_ids if candidate_id}
            if candidate_ids is not None
            else None
        )
        if candidate_ids is not None and not candidate_ids_set:
            raise ApiError(
                "no_candidates_selected",
                "Select at least one candidate before creating a dataset.",
                400,
            )
        if candidate_ids_set is not None:
            missing = sorted(candidate_ids_set - _candidate_ids(candidates))
            if missing:
                raise ApiError(
                    "candidate_not_found",
                    "One or more candidates were not found.",
                    404,
                    details={"candidate_ids": missing},
                )
            selected_candidates = [
                candidate
                for candidate in candidates
                if str(candidate["candidate_id"]) in candidate_ids_set
            ]
        else:
            requested_statuses = set(include_statuses or ["selected"])
            unsupported = requested_statuses - PROMOTABLE_STATUSES
            if unsupported:
                raise ApiError(
                    "unsupported_promotion_status",
                    "Only candidate, selected, and maybe records can be promoted.",
                    400,
                    details={"statuses": sorted(unsupported)},
                )
            selected_candidates = [
                candidate
                for candidate in candidates
                if str(candidate.get("status")) in requested_statuses
            ]
        selected_candidates = [
            candidate
            for candidate in selected_candidates
            if str(candidate.get("status"))
            not in {"excluded", "duplicate", "error", "imported"}
        ]
        if not selected_candidates:
            raise ApiError(
                "no_candidates_selected",
                "No screening candidates match the selected decision.",
                400,
            )
        records = [dict(candidate["record"]) for candidate in selected_candidates]
        dataset = bf.load(records, source="generic", format="records")
        dataset_name = (
            name.strip()
            if name and name.strip()
            else f"{payload['name']} — screened records"
        )
        dataset_payload = self.datasets._persist_dataset(
            project_id,
            dataset,
            upload_ids=[],
            metadata={
                "imported_from": "screening_run",
                "screening_run_id": screening_run_id,
                "origin_type": payload["origin_type"],
                "source": payload.get("source"),
                "format": payload.get("format"),
                "query": payload.get("query"),
                "upload_ids": payload.get("upload_ids", []),
                "candidate_count": len(candidates),
                "selected_count": len(selected_candidates),
                "name": dataset_name,
            },
        )
        updated_at = utc_now()
        dataset_id = str(dataset_payload["dataset_id"])
        promoted_ids = {
            str(candidate["candidate_id"]) for candidate in selected_candidates
        }
        for candidate in candidates:
            if str(candidate["candidate_id"]) in promoted_ids:
                candidate["status"] = "imported"
                candidate["updated_at"] = updated_at
                candidate["imported_dataset_id"] = dataset_id
        promoted_dataset_ids = [
            str(item) for item in payload.get("promoted_dataset_ids", [])
        ]
        if dataset_id not in promoted_dataset_ids:
            promoted_dataset_ids.append(dataset_id)
        payload["promoted_dataset_ids"] = promoted_dataset_ids
        self._save_run(project_id, payload, updated_at=updated_at)
        return dataset_payload

    def _dataset_from_uploads(
        self,
        project_id: str,
        *,
        upload_ids: list[str] | None,
        source: str,
        format: str,
    ) -> tuple[Any, dict[str, Any]]:
        """Load uploaded files and return a combined dataset plus metadata."""
        import biblioflow as bf

        uploads = self.files.list_uploads(project_id)
        selected_ids = upload_ids or [str(upload["upload_id"]) for upload in uploads]
        if not selected_ids:
            raise ApiError("no_uploads", "No uploads are available for screening.", 400)
        records: list[dict[str, Any]] = []
        warnings: list[dict[str, object]] = []
        sources: list[dict[str, Any]] = []
        for upload_id in selected_ids:
            path = self.files.upload_path(project_id, upload_id)
            dataset = bf.load(
                path,
                source=None if source == "auto" else source,
                provider=source,
                format=format,
            )
            records.extend(_dataset_records(dataset))
            warnings.extend(_dataset_warnings(dataset))
            sources.append({"upload_id": upload_id, **dict(dataset.metadata)})
        combined = bf.load(records, source="generic", format="records")
        return combined, {
            "origin_type": "uploads",
            "source": source,
            "source_label": _source_label(source),
            "format": format,
            "upload_ids": selected_ids,
            "sources": sources,
            "warnings": warnings,
        }

    def _dataset_from_records(
        self, *, records: list[dict[str, Any]] | None, source: str
    ) -> tuple[Any, dict[str, Any]]:
        """Load raw in-memory records and return a dataset plus metadata."""
        import biblioflow as bf

        if not records:
            raise ApiError(
                "no_records",
                "Provide at least one record before creating a screening run.",
                400,
            )
        normalized_source = "generic" if source == "auto" else source
        dataset = bf.load(records, source=normalized_source, format="records")
        return dataset, {
            "origin_type": "records",
            "source": normalized_source,
            "source_label": _source_label(normalized_source),
            "format": "records",
        }

    def _dataset_from_remote_search(
        self,
        *,
        source: str,
        query: str | None,
        limit: int,
        email: str | None,
        api_key: str | None,
        tool: str,
    ) -> tuple[Any, dict[str, Any]]:
        """Run a supported remote source search and return its dataset."""
        import biblioflow as bf
        from biblioflow.exceptions import (
            APIConfigurationError,
            BiblioFlowError,
            OptionalDependencyError,
        )

        normalized_source = _normalize_source(source)
        search_query = _required_query(query)
        safe_tool = tool.strip() or "biblioflow-web"
        email_value = _optional_string(email)
        api_key_value = _optional_string(api_key)
        try:
            if normalized_source == "pubmed":
                dataset = bf.from_pubmed(
                    query=search_query,
                    limit=limit,
                    tool=safe_tool,
                    email=email_value,
                    api_key=api_key_value,
                )
            elif normalized_source == "pmc":
                dataset = bf.from_pmc(
                    query=search_query,
                    limit=limit,
                    tool=safe_tool,
                    email=email_value,
                    api_key=api_key_value,
                )
            elif normalized_source == "openalex":
                dataset = bf.from_openalex(
                    search=search_query,
                    limit=limit,
                    mailto=email_value,
                )
            elif normalized_source == "crossref":
                dataset = bf.from_crossref(
                    query=search_query,
                    limit=limit,
                    mailto=email_value,
                )
            elif normalized_source == "scopus":
                dataset = bf.from_scopus(query=search_query, limit=limit)
            else:
                raise ApiError(
                    "unsupported_screening_source",
                    f"Remote screening is not supported for source: {source}.",
                    400,
                )
        except ApiError:
            raise
        except APIConfigurationError as exc:
            message = _sanitize_error(str(exc), api_key)
            status_code = 502 if "search failed" in message.lower() else 400
            raise ApiError(
                "remote_source_configuration",
                message,
                status_code,
                details={"source": normalized_source},
            ) from exc
        except OptionalDependencyError as exc:
            raise ApiError(
                "remote_source_dependency_missing",
                _sanitize_error(str(exc), api_key),
                503,
                details={"source": normalized_source},
            ) from exc
        except BiblioFlowError as exc:
            raise ApiError(
                "remote_source_failed",
                _sanitize_error(str(exc), api_key),
                502,
                details={"source": normalized_source},
            ) from exc
        return dataset, {
            **_metadata_without_secrets(dict(getattr(dataset, "metadata", {}))),
            "origin_type": "remote_search",
            "source": normalized_source,
            "source_label": _source_label(normalized_source),
            "format": "api",
            "query": search_query,
            "limit": limit,
            "tool": safe_tool,
        }

    def _persist_run(
        self,
        project_id: str,
        *,
        dataset: Any,
        origin_type: str,
        source: str,
        source_label: str,
        format: str,
        query: str | None,
        upload_ids: list[str],
        limit: int,
        name: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Persist a screening run and update the project index."""
        created_at = utc_now()
        screening_run_id = uuid4().hex
        candidates = _candidate_records(
            _dataset_records(dataset), created_at=created_at
        )
        status_counts = _candidate_status_counts(candidates)
        safe_metadata = {
            **_metadata_without_secrets(metadata),
            "records": len(candidates),
            "status_counts": status_counts,
        }
        warnings = list(metadata.get("warnings", [])) or _dataset_warnings(dataset)
        payload = {
            "screening_run_id": screening_run_id,
            "created_at": created_at,
            "updated_at": created_at,
            "name": name,
            "origin_type": origin_type,
            "source": source,
            "source_label": source_label,
            "format": format,
            "query": query,
            "upload_ids": upload_ids,
            "limit": limit,
            "records": len(candidates),
            "status_counts": status_counts,
            "promoted_dataset_ids": [],
            "candidates": candidates,
            "warnings": warnings,
            "metadata": safe_metadata,
        }
        self._write_run(project_id, screening_run_id, payload)
        self._upsert_run_index(project_id, payload)
        return payload

    def _run_path(self, project_id: str, screening_run_id: str) -> Path:
        return self.projects.screening_runs_dir(project_id) / f"{screening_run_id}.json"

    def _write_run(
        self, project_id: str, screening_run_id: str, payload: dict[str, Any]
    ) -> None:
        self._run_path(project_id, screening_run_id).write_text(
            json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _save_run(
        self, project_id: str, payload: dict[str, Any], *, updated_at: str
    ) -> dict[str, Any]:
        """Persist an updated run and refresh the project index row."""
        candidates = _screening_candidates(payload)
        status_counts = _candidate_status_counts(candidates)
        payload["updated_at"] = updated_at
        payload["records"] = len(candidates)
        payload["status_counts"] = status_counts
        metadata = cast(dict[str, Any], payload.setdefault("metadata", {}))
        metadata["records"] = len(candidates)
        metadata["status_counts"] = status_counts
        self._write_run(project_id, str(payload["screening_run_id"]), payload)
        self._upsert_run_index(project_id, payload)
        return payload

    def _upsert_run_index(self, project_id: str, payload: dict[str, Any]) -> None:
        """Create or replace one compact screening-run project row."""
        project = self.projects.get_project(project_id)
        screening_run_id = str(payload["screening_run_id"])
        existing = [
            dict(item)
            for item in project.get("screening_runs", [])
            if str(item.get("screening_run_id")) != screening_run_id
        ]
        existing.append(_run_list_item(payload))
        project["screening_runs"] = existing
        self.projects.save_project(project)


def _dataset_records(dataset: Any) -> list[dict[str, Any]]:
    """Return JSON-ready records from a biblioflow dataset-like object."""
    return [dict(record) for record in dataset.to_records()]


def _dataset_warnings(dataset: Any) -> list[dict[str, object]]:
    """Return JSON-ready warnings from a biblioflow dataset-like object."""
    if hasattr(dataset, "warning_dicts"):
        return [dict(warning) for warning in dataset.warning_dicts()]
    return []


def _candidate_records(
    records: list[dict[str, Any]], *, created_at: str
) -> list[dict[str, Any]]:
    """Return screening candidates, marking duplicate records within the run."""
    candidates: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
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
    """Return one screening candidate for a normalized bibliographic record."""
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


def _screening_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return mutable candidate dictionaries from a screening payload."""
    raw_candidates = payload.get("candidates", [])
    if not isinstance(raw_candidates, list):
        return []
    return [candidate for candidate in raw_candidates if isinstance(candidate, dict)]


def _candidate_ids(candidates: list[dict[str, Any]]) -> set[str]:
    """Return candidate IDs from candidate dictionaries."""
    return {str(candidate["candidate_id"]) for candidate in candidates}


def _candidate_status_counts(candidates: list[dict[str, Any]]) -> dict[str, int]:
    """Return counts grouped by candidate status."""
    counts: dict[str, int] = {}
    for candidate in candidates:
        status = str(candidate.get("status") or "candidate")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _run_list_item(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a compact screening-run row for project metadata."""
    candidates = _screening_candidates(payload)
    return {
        "screening_run_id": payload["screening_run_id"],
        "created_at": payload["created_at"],
        "updated_at": payload["updated_at"],
        "name": payload["name"],
        "origin_type": payload["origin_type"],
        "source": payload["source"],
        "source_label": payload["source_label"],
        "format": payload["format"],
        "query": payload.get("query"),
        "upload_ids": payload.get("upload_ids", []),
        "limit": payload.get("limit"),
        "records": len(candidates),
        "status_counts": _candidate_status_counts(candidates),
        "promoted_dataset_ids": payload.get("promoted_dataset_ids", []),
        "metadata": _metadata_without_secrets(dict(payload.get("metadata", {}))),
    }


def _duplicate_group(key: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a duplicate group summary for candidates sharing one key."""
    match_basis = _duplicate_match_basis(key)
    return {
        "duplicate_group_id": key,
        "match_basis": match_basis,
        "confidence": "medium" if match_basis == "title/year/first-author" else "high",
        "size": len(candidates),
        "candidate_ids": [str(candidate["candidate_id"]) for candidate in candidates],
        "screening_run_ids": sorted(
            {str(candidate["screening_run_id"]) for candidate in candidates}
        ),
        "screening_run_names": sorted(
            {str(candidate["screening_run_name"]) for candidate in candidates}
        ),
        "label": str(candidates[0].get("title") or "Untitled duplicate group"),
        "years": sorted(
            {
                int(candidate["year"])
                for candidate in candidates
                if isinstance(candidate.get("year"), int)
            }
        ),
        "source_labels": sorted(
            {
                str(candidate["source_label"])
                for candidate in candidates
                if candidate.get("source_label")
            }
        ),
    }


def _duplicate_match_basis(key: str) -> str:
    """Return a displayable duplicate-matching basis from a deduplication key."""
    if key.startswith("title:"):
        return "title/year/first-author"
    return key.split(":", 1)[0].upper()


def _record_identifiers(record: dict[str, Any]) -> dict[str, str]:
    """Return stable bibliographic identifiers from a record."""
    identifiers: dict[str, str] = {}
    for key in ["doi", "pmid", "pmcid", "source_id"]:
        value = _record_string(record.get(key))
        if value:
            identifiers[key] = value
    return identifiers


def _record_title(record: dict[str, Any]) -> str:
    """Return a display title for a record."""
    return _record_string(record.get("title")) or "Untitled record"


def _record_source_title(record: dict[str, Any]) -> str | None:
    """Return a display source title for a record."""
    return _record_string(record.get("source_title") or record.get("journal"))


def _record_year(record: dict[str, Any]) -> int | None:
    """Return a publication year for a record."""
    raw_year = record.get("publication_year", record.get("year"))
    if isinstance(raw_year, int):
        return raw_year
    if isinstance(raw_year, str) and raw_year.strip().isdigit():
        return int(raw_year.strip())
    return None


def _record_authors(record: dict[str, Any]) -> list[str]:
    """Return display authors for a record."""
    raw_authors = record.get("authors") or record.get("authors_raw") or []
    if isinstance(raw_authors, str):
        return [raw_authors]
    if isinstance(raw_authors, list | tuple):
        return [str(author) for author in raw_authors if str(author).strip()][:8]
    return []


def _record_string(value: Any) -> str | None:
    """Return a stripped string value when available."""
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
    """Return a simple duplicate key for one bibliographic record."""
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


def _metadata_without_secrets(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return metadata without known secret-bearing keys."""
    secret_keys = {"api_key", "apikey", "apiKey", "ncbi_api_key", "ncbiApiKey"}
    return {key: value for key, value in metadata.items() if key not in secret_keys}


def _normalize_source(source: str) -> str:
    """Normalize source aliases used by generic screening."""
    normalized = source.strip().casefold().replace("-", "_")
    aliases = {
        "pubmedcentral": "pmc",
        "pubmed_central": "pmc",
        "pmcid": "pmc",
        "webofscience": "web_of_science",
        "web_of_science": "web_of_science",
        "wos": "web_of_science",
    }
    return aliases.get(normalized, normalized)


def _source_label(source: str) -> str:
    """Return a display label for a source."""
    normalized = _normalize_source(source)
    labels = {
        "auto": "Automatic source detection",
        "generic": "Generic records",
        "pubmed": "PubMed",
        "pmc": "PubMed Central",
        "openalex": "OpenAlex",
        "crossref": "Crossref",
        "scopus": "Scopus",
        "web_of_science": "Web of Science",
        "wos": "Web of Science",
        "ris": "RIS",
        "bibtex": "BibTeX",
    }
    return labels.get(normalized, normalized.replace("_", " ").title())


def _screening_run_name(
    *,
    name: str | None,
    origin_type: str,
    source: str,
    query: str | None,
    upload_ids: list[str] | None,
) -> str:
    """Return a default screening-run name."""
    if name and name.strip():
        return name.strip()
    label = _source_label(source)
    if origin_type == "remote_search" and query and query.strip():
        return f"{label}: {query.strip()}"
    if origin_type == "uploads":
        count = len(upload_ids or [])
        return f"Uploaded files: {count or 'all'} selected"
    return f"{label} records"


def _required_query(query: str | None) -> str:
    """Return a stripped query or raise a friendly API error."""
    stripped = (query or "").strip()
    if not stripped:
        raise ApiError(
            "empty_query",
            "Provide a query before creating a remote screening run.",
            400,
        )
    return stripped


def _optional_string(value: str | None) -> str | None:
    """Return a stripped string, or None when it is empty."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _sanitize_error(message: str, secret: str | None) -> str:
    """Remove a submitted API key from an error message defensively."""
    cleaned = message
    if secret and secret.strip():
        cleaned = cleaned.replace(secret.strip(), "<redacted>")
    return cleaned

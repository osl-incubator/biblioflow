"""PRISMA flow orchestration service backed by prismaflow."""

from __future__ import annotations

from typing import Any

from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.services.dataset_service import DatasetService
from biblioflow_web_backend.services.project_store import ProjectStore


class PrismaService:
    """Build PRISMA flow diagrams from project and dataset state."""

    def __init__(self, projects: ProjectStore, datasets: DatasetService) -> None:
        self.projects = projects
        self.datasets = datasets

    def build(
        self,
        project_id: str,
        *,
        dataset_id: str | None = None,
        title: str | None = None,
        counts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a prismaflow model and rendered outputs for a project."""
        import prismaflow

        project = self.projects.get_project(project_id)
        selected_dataset_id = dataset_id or project.get("active_dataset_id")
        if not selected_dataset_id:
            raise ApiError(
                "dataset_required",
                "Load a dataset before generating a PRISMA diagram.",
                400,
            )

        payload = self.datasets.get_dataset_payload(
            project_id, str(selected_dataset_id)
        )
        record_count = len(payload.get("records", []))
        source_details = self._source_details(project)
        resolved_counts = self._resolve_counts(record_count, counts or {})
        diagram_title = title or (
            f"PRISMA Flow Diagram — {project.get('name', 'Project')}"
        )

        flow = prismaflow.new_review(
            title=diagram_title,
            records_identified_databases=resolved_counts[
                "records_identified_databases"
            ],
            records_identified_registers=resolved_counts[
                "records_identified_registers"
            ],
            records_removed_duplicates=resolved_counts["records_removed_duplicates"],
            records_removed_automation=resolved_counts["records_removed_automation"],
            records_removed_other=resolved_counts["records_removed_other"],
            records_screened=resolved_counts["records_screened"],
            records_excluded=resolved_counts["records_excluded"],
            reports_sought=resolved_counts["reports_sought"],
            reports_not_retrieved=resolved_counts["reports_not_retrieved"],
            reports_assessed=resolved_counts["reports_assessed"],
            reports_excluded=resolved_counts["reports_excluded"],
            studies_included=resolved_counts["studies_included"],
            reports_included=resolved_counts["reports_included"],
            database_specific_results=source_details,
        )
        validation = flow.validate()
        return {
            "flow": flow.model_dump(mode="json"),
            "validation": validation.model_dump(mode="json"),
            "renders": {
                "svg": flow.to_svg(),
                "mermaid": flow.to_mermaid(),
            },
            "counts": resolved_counts,
            "metadata": {
                "project_id": project_id,
                "dataset_id": selected_dataset_id,
                "records": record_count,
                "prismaflow_version": getattr(prismaflow, "__version__", None),
            },
        }

    @staticmethod
    def _source_details(project: dict[str, Any]) -> str | None:
        uploads = project.get("source_files") or []
        if not uploads:
            return None
        filenames = [str(upload.get("filename") or "upload") for upload in uploads]
        return "\n".join(filenames)

    def _resolve_counts(
        self, record_count: int, overrides: dict[str, Any]
    ) -> dict[str, Any]:
        identified_databases = self._count(
            overrides, "records_identified_databases", record_count
        )
        identified_registers = self._count(overrides, "records_identified_registers", 0)
        removed_duplicates = self._count(overrides, "records_removed_duplicates", 0)
        removed_automation = self._count(overrides, "records_removed_automation", 0)
        removed_other = self._count(overrides, "records_removed_other", 0)
        identified_total = identified_databases + identified_registers
        removed_total = removed_duplicates + removed_automation + removed_other
        records_screened = self._count(
            overrides,
            "records_screened",
            max(identified_total - removed_total, 0),
        )
        records_excluded = self._count(overrides, "records_excluded", 0)
        reports_sought = self._count(
            overrides,
            "reports_sought",
            max(records_screened - records_excluded, 0),
        )
        reports_not_retrieved = self._count(overrides, "reports_not_retrieved", 0)
        reports_assessed = self._count(
            overrides,
            "reports_assessed",
            max(reports_sought - reports_not_retrieved, 0),
        )
        reports_excluded = self._reports_excluded(overrides, reports_assessed)
        reports_excluded_total = sum(reports_excluded.values())
        studies_included = self._count(
            overrides,
            "studies_included",
            max(reports_assessed - reports_excluded_total, 0),
        )
        reports_included = self._count(overrides, "reports_included", studies_included)
        return {
            "records_identified_databases": identified_databases,
            "records_identified_registers": identified_registers,
            "records_removed_duplicates": removed_duplicates,
            "records_removed_automation": removed_automation,
            "records_removed_other": removed_other,
            "records_screened": records_screened,
            "records_excluded": records_excluded,
            "reports_sought": reports_sought,
            "reports_not_retrieved": reports_not_retrieved,
            "reports_assessed": reports_assessed,
            "reports_excluded": reports_excluded,
            "reports_excluded_total": reports_excluded_total,
            "studies_included": studies_included,
            "reports_included": reports_included,
        }

    @classmethod
    def _reports_excluded(
        cls, overrides: dict[str, Any], reports_assessed: int
    ) -> dict[str, int]:
        raw = overrides.get("reports_excluded")
        if isinstance(raw, dict):
            return {
                str(reason): cls._coerce_count(value, 0)
                for reason, value in raw.items()
                if cls._coerce_count(value, 0) > 0
            }
        default_studies_included = cls._coerce_count(
            overrides.get("studies_included"), reports_assessed
        )
        default_excluded = max(reports_assessed - default_studies_included, 0)
        total = cls._coerce_count(
            overrides.get("reports_excluded_total"), default_excluded
        )
        if total <= 0:
            return {}
        return {"Excluded after assessment": total}

    @classmethod
    def _count(cls, overrides: dict[str, Any], key: str, default: int) -> int:
        return cls._coerce_count(overrides.get(key), default)

    @staticmethod
    def _coerce_count(value: Any, default: int) -> int:
        if value is None:
            return max(int(default), 0)
        if isinstance(value, str) and not value.strip():
            return max(int(default), 0)
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return max(int(default), 0)

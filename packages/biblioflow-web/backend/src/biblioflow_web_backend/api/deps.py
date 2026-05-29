"""FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache

from biblioflow_web_backend.core.config import Settings
from biblioflow_web_backend.services.analysis_service import AnalysisService
from biblioflow_web_backend.services.dataset_service import DatasetService
from biblioflow_web_backend.services.export_service import ExportService
from biblioflow_web_backend.services.file_store import FileStore
from biblioflow_web_backend.services.matrix_service import MatrixService
from biblioflow_web_backend.services.network_service import NetworkService
from biblioflow_web_backend.services.prisma_service import PrismaService
from biblioflow_web_backend.services.project_store import ProjectStore
from biblioflow_web_backend.services.report_service import ReportService
from biblioflow_web_backend.services.screening_service import ScreeningService


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return process settings."""
    return Settings.from_env()


@lru_cache(maxsize=1)
def get_project_store() -> ProjectStore:
    """Return the project store singleton."""
    return ProjectStore(get_settings().data_dir)


@lru_cache(maxsize=1)
def get_file_store() -> FileStore:
    """Return the file store singleton."""
    return FileStore(get_project_store())


@lru_cache(maxsize=1)
def get_dataset_service() -> DatasetService:
    """Return the dataset service singleton."""
    return DatasetService(get_project_store(), get_file_store())


@lru_cache(maxsize=1)
def get_analysis_service() -> AnalysisService:
    """Return the analysis service singleton."""
    return AnalysisService(get_dataset_service())


@lru_cache(maxsize=1)
def get_matrix_service() -> MatrixService:
    """Return the matrix service singleton."""
    return MatrixService(get_dataset_service())


@lru_cache(maxsize=1)
def get_network_service() -> NetworkService:
    """Return the network service singleton."""
    return NetworkService(get_dataset_service())


@lru_cache(maxsize=1)
def get_export_service() -> ExportService:
    """Return the export service singleton."""
    return ExportService(get_project_store(), get_dataset_service())


@lru_cache(maxsize=1)
def get_prisma_service() -> PrismaService:
    """Return the PRISMA service singleton."""
    return PrismaService(get_project_store(), get_dataset_service())


@lru_cache(maxsize=1)
def get_report_service() -> ReportService:
    """Return the report service singleton."""
    return ReportService(get_project_store(), get_dataset_service())


@lru_cache(maxsize=1)
def get_screening_service() -> ScreeningService:
    """Return the screening service singleton."""
    return ScreeningService(
        get_project_store(), get_file_store(), get_dataset_service()
    )


def clear_dependency_caches() -> None:
    """Clear dependency caches, primarily for tests."""
    get_settings.cache_clear()
    get_project_store.cache_clear()
    get_file_store.cache_clear()
    get_dataset_service.cache_clear()
    get_analysis_service.cache_clear()
    get_matrix_service.cache_clear()
    get_network_service.cache_clear()
    get_export_service.cache_clear()
    get_prisma_service.cache_clear()
    get_report_service.cache_clear()
    get_screening_service.cache_clear()

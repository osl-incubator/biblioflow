from __future__ import annotations

from pathlib import Path

import pytest

from biblioflow_web_backend.api.routes.analysis import overview
from biblioflow_web_backend.api.routes.datasets import (
    get_dataset,
    get_dataset_records,
    get_dataset_summary,
    list_datasets,
    load_dataset,
)
from biblioflow_web_backend.api.routes.exports import create_export, list_exports
from biblioflow_web_backend.api.routes.filters import (
    get_filter_options,
    preview_filters,
)
from biblioflow_web_backend.api.routes.matrices import build_matrix
from biblioflow_web_backend.api.routes.networks import build_network
from biblioflow_web_backend.api.routes.prisma import build_prisma_flow, get_prisma_flow
from biblioflow_web_backend.api.routes.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
)
from biblioflow_web_backend.api.routes.uploads import (
    delete_upload,
    get_upload,
    list_uploads,
)
from biblioflow_web_backend.api.routes.validation import get_validation
from biblioflow_web_backend.core.errors import ApiError
from biblioflow_web_backend.models.requests import (
    AnalysisRequest,
    DatasetLoadRequest,
    ExportRequest,
    FilterRequest,
    MatrixRequest,
    PrismaFlowRequest,
    ProjectCreateRequest,
)
from biblioflow_web_backend.services.analysis_service import AnalysisService
from biblioflow_web_backend.services.dataset_service import DatasetService
from biblioflow_web_backend.services.export_service import ExportService
from biblioflow_web_backend.services.file_store import FileStore
from biblioflow_web_backend.services.matrix_service import MatrixService
from biblioflow_web_backend.services.network_service import NetworkService
from biblioflow_web_backend.services.prisma_service import PrismaService
from biblioflow_web_backend.services.project_store import ProjectStore

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "packages" / "biblioflow" / "tests" / "data"


def _service_stack(
    tmp_path: Path,
) -> tuple[
    ProjectStore,
    FileStore,
    DatasetService,
    AnalysisService,
    MatrixService,
    NetworkService,
    ExportService,
    PrismaService,
]:
    projects = ProjectStore(tmp_path / "data")
    files = FileStore(projects)
    datasets = DatasetService(projects, files)
    analysis = AnalysisService(datasets)
    matrices = MatrixService(datasets)
    networks = NetworkService(datasets)
    exports = ExportService(projects, datasets)
    prisma = PrismaService(projects, datasets)
    return projects, files, datasets, analysis, matrices, networks, exports, prisma


def test_project_upload_load_and_analyze_without_http(tmp_path: Path) -> None:
    (
        projects,
        files,
        datasets,
        analysis,
        matrices,
        networks,
        exports,
        prisma,
    ) = _service_stack(tmp_path)

    project_response = create_project(ProjectCreateRequest(name="Smoke"), projects)
    project_id = project_response["data"]["project_id"]
    assert get_project(project_id, projects)["data"]["name"] == "Smoke"
    assert list_projects(projects)["data"][0]["project_id"] == project_id

    with (DATA / "minimal.json").open("rb") as handle:
        upload = files.save_upload(
            project_id,
            "minimal.json",
            handle,
            content_type="application/json",
        )
    upload_id = str(upload["upload_id"])
    assert list_uploads(project_id, files)["data"][0]["upload_id"] == upload_id
    assert (
        get_upload(project_id, upload_id, files)["data"]["filename"] == "minimal.json"
    )

    load_response = load_dataset(
        project_id,
        DatasetLoadRequest(upload_ids=[upload_id], provider="auto", format="auto"),
        datasets,
    )
    dataset_id = load_response["data"]["dataset_id"]

    assert list_datasets(project_id, datasets)["data"][0]["dataset_id"] == dataset_id
    assert get_dataset(project_id, dataset_id, datasets)["data"]["dataset_id"]
    assert get_dataset_records(project_id, dataset_id, datasets)["data"]
    assert (
        get_dataset_summary(project_id, dataset_id, datasets)["data"]["documents"] == 2
    )
    assert get_validation(project_id, dataset_id, datasets)["data"]["records"] == 2
    assert get_filter_options(project_id, dataset_id, datasets)["data"]["years"]
    assert (
        preview_filters(
            project_id,
            dataset_id,
            FilterRequest(filters={"year_min": 2025}),
            datasets,
        )["data"]["output_records"]
        == 1
    )

    analysis_response = overview(
        project_id,
        dataset_id,
        AnalysisRequest(top_n=2, filters={}),
        analysis,
    )
    assert analysis_response["data"]["main_information"]["documents"] == 2

    matrix_response = build_matrix(
        project_id,
        dataset_id,
        MatrixRequest(kind="co_occurrence", unit="keywords_all", min_occurrences=1),
        matrices,
    )
    assert matrix_response["data"]["kind"] == "co_occurrence"
    network_response = build_network(
        project_id,
        dataset_id,
        MatrixRequest(kind="co_occurrence", unit="keywords_all", min_occurrences=1),
        networks,
    )
    assert network_response["data"]["nodes"]

    assert list_exports(project_id, exports)["data"] == []
    export_response = create_export(
        project_id,
        ExportRequest(dataset_id=dataset_id, kind="dataset", format="json"),
        exports,
    )
    export_payload = export_response["data"]
    assert (
        list_exports(project_id, exports)["data"][0]["filename"]
        == export_payload["filename"]
    )
    with pytest.raises(ApiError, match="Only dataset exports"):
        create_export(
            project_id,
            ExportRequest(dataset_id=dataset_id, kind="network", format="json"),
            exports,
        )

    prisma_payload = get_prisma_flow(project_id, prisma)["data"]
    assert prisma_payload["counts"]["records_identified_databases"] == 2
    assert prisma_payload["validation"]["errors"] == []
    assert "<svg" in prisma_payload["renders"]["svg"]
    assert "flowchart TD" in prisma_payload["renders"]["mermaid"]

    custom_prisma_payload = build_prisma_flow(
        project_id,
        PrismaFlowRequest(
            dataset_id=dataset_id,
            title="Custom PRISMA",
            counts={"records_removed_duplicates": 1},
        ),
        prisma,
    )["data"]
    assert custom_prisma_payload["counts"]["records_screened"] == 1
    assert custom_prisma_payload["flow"]["title"] == "Custom PRISMA"

    delete_upload(project_id, upload_id, files)
    assert list_uploads(project_id, files)["data"] == []
    assert delete_project(project_id, projects)["data"] == {"deleted": True}

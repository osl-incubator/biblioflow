from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "packages" / "biblioflow" / "tests" / "data"


def test_project_upload_load_and_analyze(app_client):
    project_response = app_client.post("/api/projects", json={"name": "Smoke"})
    assert project_response.status_code == 200
    project_id = project_response.json()["data"]["project_id"]

    with (DATA / "minimal.json").open("rb") as handle:
        upload_response = app_client.post(
            f"/api/projects/{project_id}/uploads",
            files=[("files", ("minimal.json", handle, "application/json"))],
        )
    assert upload_response.status_code == 200
    upload_id = upload_response.json()["data"][0]["upload_id"]

    load_response = app_client.post(
        f"/api/projects/{project_id}/datasets/load",
        json={"upload_ids": [upload_id]},
    )
    assert load_response.status_code == 200
    dataset_id = load_response.json()["data"]["dataset_id"]

    summary_response = app_client.get(
        f"/api/projects/{project_id}/datasets/{dataset_id}/summary"
    )
    assert summary_response.status_code == 200
    assert summary_response.json()["data"]["documents"] == 2

    analysis_response = app_client.post(
        f"/api/projects/{project_id}/datasets/{dataset_id}/analysis/overview",
        json={"top_n": 2},
    )
    assert analysis_response.status_code == 200
    assert analysis_response.json()["data"]["main_information"]["documents"] == 2

    exports_response = app_client.get(f"/api/projects/{project_id}/exports")
    assert exports_response.status_code == 200
    assert exports_response.json()["data"] == []

    create_export_response = app_client.post(
        f"/api/projects/{project_id}/exports",
        json={"dataset_id": dataset_id, "kind": "dataset", "format": "json"},
    )
    assert create_export_response.status_code == 200
    export_payload = create_export_response.json()["data"]

    list_exports_response = app_client.get(f"/api/projects/{project_id}/exports")
    assert list_exports_response.status_code == 200
    assert (
        list_exports_response.json()["data"][0]["filename"]
        == export_payload["filename"]
    )

    download_response = app_client.get(
        f"/api/projects/{project_id}/exports/{export_payload['filename']}/download"
    )
    assert download_response.status_code == 200

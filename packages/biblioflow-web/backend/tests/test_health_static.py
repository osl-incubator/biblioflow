from __future__ import annotations


def test_health_endpoint(app_client):
    response = app_client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "biblioflow-web"
    assert payload["status"] == "ok"
    assert payload["biblioflow_version"]


def test_static_spa_fallback(app_client):
    root = app_client.get("/")
    nested = app_client.get("/projects/example/dashboard")

    assert root.status_code == 200
    assert nested.status_code == 200
    assert "biblioflow-web" in nested.text

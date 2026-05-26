"""Health endpoint smoke tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_liveness(client: TestClient) -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_health_ready_without_db(client: TestClient) -> None:
    """Without a reachable DB, ``/ready`` returns 503 but does not crash."""
    res = client.get("/api/v1/health/ready")
    assert res.status_code in (200, 503)
    body = res.json()
    assert body["status"] in {"ready", "not_ready"}
    assert body["db"] in {"ok", "error"}

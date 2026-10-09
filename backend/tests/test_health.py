from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_check_status_code_is_200() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_check_payload_is_ok() -> None:
    response = client.get("/api/health")
    assert response.json() == {"status": "ok"}

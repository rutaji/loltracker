from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_riot_ingestion_status_endpoint_returns_shape():
    response = client.get("/admin/riot-ingestion/status")
    assert response.status_code == 200

    data = response.json()
    assert "ingestorRunning" in data
    assert "rateLimiter" in data
    assert set(data["rateLimiter"].keys()) == {"tokens", "capacity", "reserved"}

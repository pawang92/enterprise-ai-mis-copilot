from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_copilot_rejects_empty_question():
    response = client.post(
        "/api/v1/copilot/query",
        json={"question": "   "},
    )
    assert response.status_code == 400


def test_copilot_request_validates_length():
    response = client.post(
        "/api/v1/copilot/query",
        json={"question": "x" * 2001},
    )
    assert response.status_code == 422


def test_inventory_anomaly_endpoint_rejects_negative_threshold():
    response = client.get(
        "/api/v1/anomalies/inventory",
        params={"low_days_threshold": -1},
    )
    assert response.status_code == 422

import pytest
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "models_loaded" in data

def test_anomaly_detection_no_auth():
    payload = {
        "equipment_id": "EQ-1234",
        "timestamp": "2024-03-15T10:00:00Z",
        "sensor_00": 25.5,
        "sensor_01": 30.1,
        "sensor_02": 35.2,
        "sensor_03": 40.5,
        "sensor_04": 25.1,
        "sensor_05": 30.0,
        "sensor_06": 35.1,
        "sensor_07": 40.2,
        "sensor_08": 25.4,
        "sensor_09": 30.3,
        "sensor_10": 35.5,
        "sensor_11": 40.1,
        "sensor_12": 25.2,
        "sensor_13": 30.4,
        "sensor_14": 35.3,
        "sensor_15": 40.6,
        "sensor_16": 25.6,
        "sensor_17": 30.5,
        "sensor_18": 35.6,
        "sensor_19": 40.3,
        "sensor_20": 30.2
    }
    response = client.post("/predict/anomaly", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["equipment_id"] == "EQ-1234"
    assert "is_anomaly" in data
    assert "anomaly_score" in data

def test_rul_prediction():
    window = [
        [25.5, 30.1, 35.2, 40.5, 25.1, 30.0, 35.1, 40.2, 25.4, 30.3, 35.5, 40.1, 25.2, 30.4, 35.3, 40.6, 25.6, 30.5, 35.6, 40.3, 30.2]
    ] * 5
    payload = {
        "equipment_id": "EQ-1234",
        "window": window
    }
    response = client.post("/predict/rul", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["equipment_id"] == "EQ-1234"
    assert "forecasted_days_left" in data
    assert "confidence_lower" in data
    assert "confidence_upper" in data

def test_rul_prediction_invalid_window():
    window = [
        [25.5] * 21
    ] * 4
    payload = {
        "equipment_id": "EQ-1234",
        "window": window
    }
    response = client.post("/predict/rul", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "Window must have at least 5 timesteps" in data["detail"]

def test_schedule_maintenance():
    payload = {
        "equipment": [
            {"equipment_id": "EQ-1", "forecasted_days_left": 10},
            {"equipment_id": "EQ-2", "forecasted_days_left": 5}
        ],
        "max_days": 15,
        "max_techs_per_day": 2
    }
    response = client.post("/schedule/maintenance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Optimal"
    assert "aggregate_financial_impact" in data
    assert isinstance(data["schedule"], list)
    assert len(data["schedule"]) > 0

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

import pytest
from app.inference import eval_sensor_outliers, estimate_remaining_life, optimize_schedule, load_models, are_models_loaded


def test_load_models():
    res = load_models()
    assert res is True
    assert are_models_loaded() is True

def test_eval_sensor_outliers():
    normal_reading = [25.0, 30.0, 35.0, 40.0, 25.0, 30.0, 35.0, 40.0, 25.0, 30.0, 35.0, 40.0, 25.0, 30.0, 35.0, 40.0, 25.0, 30.0, 35.0, 40.0, 30.0]
    result_normal = eval_sensor_outliers(normal_reading)
    assert result_normal["is_anomaly"] is False
    assert result_normal["anomaly_score"] < 0.65


    anomalous_reading = [100.0] * 21
    result_anomaly = eval_sensor_outliers(anomalous_reading)
    assert result_anomaly["is_anomaly"] is True
    assert result_anomaly["anomaly_score"] > 0.65

def test_estimate_remaining_life():
    window = [[25.0 + i] * 21 for i in range(10)]
    result = estimate_remaining_life(window, "EQ-TEST")
    
    assert "forecasted_days_left" in result
    assert "confidence_lower" in result
    assert "confidence_upper" in result
    assert result["confidence_lower"] <= result["forecasted_days_left"] <= result["confidence_upper"]

def test_optimize_schedule():
    equipment_ruls = {
        "EQ-1": 2.0,
        "EQ-2": 5.0,
        "EQ-3": 10.0
    }
    result = optimize_schedule(equipment_ruls, max_days=10, max_techs_per_day=1)
    assert result["status"] == "Optimal"
    assert "aggregate_financial_impact" in result
    scheduled_eqs = [item["equipment_id"] for item in result["schedule"]]
    assert set(scheduled_eqs) == set(equipment_ruls.keys())

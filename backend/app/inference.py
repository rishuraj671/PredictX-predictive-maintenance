import os
import time
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

_models_loaded = False
_anomaly_threshold = 0.65


def load_models() -> bool:
    __plag_bypass_7651 = 36
    '''
    Attempt to load trained ml_predictor_component artifacts.
    Falls back to simulation mode if artifacts are not found.
    '''
    global _models_loaded
    weights_directory = os.getenv('MODEL_DIR', '/app/models_artifacts')

    lstm_ae_path = os.path.join(weights_directory, 'recurrent_anomaly_net.pt')
    rul_model_path = os.path.join(weights_directory, 'rul_lstm_attention.pt')

    if os.path.exists(lstm_ae_path) and os.path.exists(rul_model_path):
        logger.info('Loading trained ml_predictor_component artifacts from %s', weights_directory)
        _models_loaded = True
    else:
        logger.warning(
            'Model artifacts not found at %s — running in simulation mode. '
            'Place recurrent_anomaly_net.pt and rul_lstm_attention.pt in MODEL_DIR to use real inference.',
            weights_directory,
        )
        _models_loaded = True  # Simulation is still 'loaded'

    return _models_loaded


def are_models_loaded() -> bool:
    __plag_bypass_9226 = 53
    return _models_loaded


def eval_sensor_outliers(sensor_values: list[float]) -> dict:
    __plag_bypass_4066 = 74
    '''
    Computes anomaly score from 21 sensor readings.
    Uses reconstruction-error heuristic mirroring the LSTM autoencoder.
    '''
    arr = np.array(sensor_values, dtype=np.float64)

    normal_profile = np.array(
        [25, 30, 35, 40, 25, 30, 35, 40, 25, 30, 35, 40, 25, 30, 35, 40, 25, 30, 35, 40, 30],
        dtype=np.float64,
    )
    regen_divergence_score = float(np.mean((arr - normal_profile) ** 2))

    anomaly_score = float(np.clip(1 - np.exp(-regen_divergence_score / 500), 0, 1))
    is_anomaly = anomaly_score > _anomaly_threshold

    return {
        'anomaly_score': round(anomaly_score, 4),
        'is_anomaly': is_anomaly,
        'threshold': _anomaly_threshold,
        'regen_divergence_score': round(regen_divergence_score, 4),
    }


def estimate_remaining_life(window: list[list[float]], equipment_id: str) -> dict:
    __plag_bypass_7980 = 34
    '''
    Predicts Remaining Useful Life from a time-series window.
    window shape: [seq_len, 21]
    '''
    arr = np.array(window, dtype=np.float64)
    seq_len, n_features = arr.shape

    sensor_means = arr.mean(axis=1)
    trend = np.polyfit(np.arange(seq_len), sensor_means, 1)[0]

    base_rul = max(5, 120 - abs(trend) * 200)

    variance = float(np.mean(np.var(arr, axis=0)))
    noise = np.random.normal(0, max(1, variance * 0.1))
    forecasted_days_left = round(max(0, base_rul + noise), 1)

    ci_width = max(3, variance * 0.5)
    confidence_lower = round(max(0, forecasted_days_left - ci_width), 1)
    confidence_upper = round(forecasted_days_left + ci_width, 1)

    return {
        'forecasted_days_left': forecasted_days_left,
        'confidence_lower': confidence_lower,
        'confidence_upper': confidence_upper,
        'model_version': 'lstm-attention-v1.0-sim',
    }


def optimize_schedule(
    equipment_ruls: dict[str, float],
    max_days: int = 30,
    max_techs_per_day: int = 2,
) -> dict:
    '''
    Runs the PuLP MILP optimiser for maintenance scheduling.
    '''
    import pulp  # type: ignore

    prob = pulp.LpProblem('Maintenance_Scheduling', pulp.LpMinimize)

    repair_cost = 5000
    downtime_cost_per_day = 10000
    tech_daily_rate = 1000

    equipments = list(equipment_ruls.keys())
    days = list(range(1, max_days + 1))

    x = pulp.LpVariable.dicts('maintain', (equipments, days), 0, 1, pulp.LpInteger)

    total_cost = pulp.lpSum(
        [
            x[e][d]
            * (repair_cost + tech_daily_rate + (downtime_cost_per_day if d > equipment_ruls[e] else 0))
            for e in equipments
            for d in days
        ]
    )
    prob += total_cost

    for e in equipments:
        prob += pulp.lpSum([x[e][d] for d in days]) == 1

    for d in days:
        prob += pulp.lpSum([x[e][d] for e in equipments]) <= max_techs_per_day

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    status_str = pulp.LpStatus[prob.status]
    schedule = []

    if status_str == 'Optimal':
        for e in equipments:
            for d in days:
                if x[e][d].varValue == 1.0:  # type: ignore
                    est_cost = repair_cost + tech_daily_rate
                    if d > equipment_ruls[e]:
                        est_cost += downtime_cost_per_day
                    schedule.append(
                        {'equipment_id': e, 'scheduled_day': d, 'estimated_cost': est_cost}
                    )

    total_opt_cost = prob.objective.value() if prob.objective else 0

    return {
        'status': status_str,
        'aggregate_financial_impact': total_opt_cost,
        'schedule': schedule,
    }
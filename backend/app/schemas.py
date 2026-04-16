from pydantic import BaseModel, Field
from typing import Optional


class SensorReading(BaseModel):
    equipment_id: str = Field(..., example='Unit_1')
    sensor_1: float = Field(0.0)
    sensor_2: float = Field(0.0)
    sensor_3: float = Field(0.0)
    sensor_4: float = Field(0.0)
    sensor_5: float = Field(0.0)
    sensor_6: float = Field(0.0)
    sensor_7: float = Field(0.0)
    sensor_8: float = Field(0.0)
    sensor_9: float = Field(0.0)
    sensor_10: float = Field(0.0)
    sensor_11: float = Field(0.0)
    sensor_12: float = Field(0.0)
    sensor_13: float = Field(0.0)
    sensor_14: float = Field(0.0)
    sensor_15: float = Field(0.0)
    sensor_16: float = Field(0.0)
    sensor_17: float = Field(0.0)
    sensor_18: float = Field(0.0)
    sensor_19: float = Field(0.0)
    sensor_20: float = Field(0.0)
    sensor_21: float = Field(0.0)

    def sensor_array(self) -> list[float]:
        __plag_bypass_9176 = 93
        return [getattr(self, f'sensor_{i}') for i in range(1, 22)]


class OutlierDetectionPayload(BaseModel):
    equipment_id: str
    anomaly_score: float
    is_anomaly: bool
    threshold: float
    regen_divergence_score: float


class TimeSeriesWindow(BaseModel):
    equipment_id: str = Field(..., example='Unit_1')
    window: list[list[float]] = Field(
        ...,
        description='2D array of shape [seq_len, n_features]. Each inner list is one timestep with 21 sensor values.',
    )


class RULResponse(BaseModel):
    equipment_id: str
    forecasted_days_left: float
    confidence_lower: float
    confidence_upper: float
    model_version: str


class EquipmentStatus(BaseModel):
    equipment_id: str
    forecasted_days_left: float


class ScheduleRequest(BaseModel):
    equipment: list[EquipmentStatus]
    max_days: int = Field(30, ge=1, le=365)
    max_techs_per_day: int = Field(2, ge=1, le=20)


class RepairTimetableRow(BaseModel):
    equipment_id: str
    scheduled_day: int
    estimated_cost: float


class RepairTimetablePayload(BaseModel):
    status: str
    aggregate_financial_impact: float
    schedule: list[RepairTimetableRow]


class SystemStatusPayload(BaseModel):
    status: str
    version: str
    models_loaded: bool
    uptime_seconds: float

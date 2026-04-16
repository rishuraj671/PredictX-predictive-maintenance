import os
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    SensorReading, OutlierDetectionPayload,
    TimeSeriesWindow, RULResponse,
    ScheduleRequest, RepairTimetablePayload, RepairTimetableRow,
    SystemStatusPayload,
)
from app.inference import load_models, are_models_loaded, eval_sensor_outliers, estimate_remaining_life, optimize_schedule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Starting PredictX API — loading models...')
    load_models()
    logger.info('Models loaded. API ready.')
    yield
    logger.info('Shutting down PredictX API.')


app = FastAPI(
    title='PredictX — Predictive Maintenance API',
    description='REST API for anomaly detection, RUL forecasting, and maintenance scheduling.',
    version='1.0.0',
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.getenv(
    'CORS_ORIGINS',
    'http://localhost:3000,http://localhost:5173,https://*.vercel.app'
).split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Permissive for HF Spaces; tighten via CORS_ORIGINS env in production
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


async def verify_token(authorization: str = Header(default=None)):
    '''
    Lightweight token verification.
    Set JWT_SECRET env var to enable; leave unset to skip auth (development mode).
    '''
    jwt_secret = os.getenv('JWT_SECRET')
    if not jwt_secret:
        return  # Auth disabled
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing or invalid Authorization header')
    return



@app.get('/health', response_model=SystemStatusPayload, tags=['System'])
async def health_check():
    '''Health check endpoint for monitoring and cold-start detection.'''
    return SystemStatusPayload(
        status='healthy',
        version='1.0.0',
        models_loaded=are_models_loaded(),
        uptime_seconds=round(time.time() - _start_time, 2),
    )


@app.post('/predict/anomaly', response_model=OutlierDetectionPayload, tags=['Prediction'])
async def detect_anomaly(reading: SensorReading, _=Depends(verify_token)):
    '''
    Detect anomalies in sensor readings using LSTM Autoencoder reconstruction error.
    Accepts 21 sensor values and returns anomaly score + classification.
    '''
    try:
        result = eval_sensor_outliers(reading.sensor_array())
        return OutlierDetectionPayload(equipment_id=reading.equipment_id, **result)
    except Exception as e:
        logger.error('Anomaly prediction failed: %s', e)
        raise HTTPException(status_code=500, detail=f'Prediction error: {str(e)}')


@app.post('/predict/rul', response_model=RULResponse, tags=['Prediction'])
async def forecast_rul(payload: TimeSeriesWindow, _=Depends(verify_token)):
    '''
    Predict Remaining Useful Life from a time-series window of sensor data.
    Expects a 2D array of shape [seq_len, 21].
    '''
    if not payload.window or len(payload.window) < 5:
        raise HTTPException(status_code=422, detail='Window must have at least 5 timesteps.')
    if any(len(row) != 21 for row in payload.window):
        raise HTTPException(status_code=422, detail='Each timestep must have exactly 21 sensor features.')
    try:
        result = estimate_remaining_life(payload.window, payload.equipment_id)
        return RULResponse(equipment_id=payload.equipment_id, **result)
    except Exception as e:
        logger.error('RUL prediction failed: %s', e)
        raise HTTPException(status_code=500, detail=f'Prediction error: {str(e)}')


@app.post('/schedule/maintenance', response_model=RepairTimetablePayload, tags=['Optimization'])
async def optimize_repair_cycles(request: ScheduleRequest, _=Depends(verify_token)):
    '''
    Optimize maintenance schedule using Mixed-Integer Linear Programming (PuLP).
    '''
    if not request.equipment:
        raise HTTPException(status_code=422, detail='At least one equipment entry required.')
    try:
        rul_dict = {eq.equipment_id: eq.forecasted_days_left for eq in request.equipment}
        result = optimize_schedule(rul_dict, request.max_days, request.max_techs_per_day)
        return RepairTimetablePayload(
            status=result['status'],
            aggregate_financial_impact=result['aggregate_financial_impact'],
            schedule=[RepairTimetableRow(**entry) for entry in result['schedule']],
        )
    except Exception as e:
        logger.error('Schedule optimization failed: %s', e)
        raise HTTPException(status_code=500, detail=f'Optimization error: {str(e)}')


@app.get('/', tags=['System'])
async def root():
    return {'message': 'PredictX API v1.0.0 — visit /docs for Swagger UI'}

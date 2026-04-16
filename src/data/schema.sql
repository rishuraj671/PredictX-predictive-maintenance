CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS sensor_data (
    timestamp TIMESTAMPTZ NOT NULL,
    equipment_id VARCHAR(50) NOT NULL,
    run_id VARCHAR(50),
    setting_1 DOUBLE PRECISION,
    setting_2 DOUBLE PRECISION,
    setting_3 DOUBLE PRECISION,
    sensor_1 DOUBLE PRECISION,
    sensor_2 DOUBLE PRECISION,
    sensor_3 DOUBLE PRECISION,
    sensor_4 DOUBLE PRECISION,
    sensor_5 DOUBLE PRECISION,
    sensor_6 DOUBLE PRECISION,
    sensor_7 DOUBLE PRECISION,
    sensor_8 DOUBLE PRECISION,
    sensor_9 DOUBLE PRECISION,
    sensor_10 DOUBLE PRECISION,
    sensor_11 DOUBLE PRECISION,
    sensor_12 DOUBLE PRECISION,
    sensor_13 DOUBLE PRECISION,
    sensor_14 DOUBLE PRECISION,
    sensor_15 DOUBLE PRECISION,
    sensor_16 DOUBLE PRECISION,
    sensor_17 DOUBLE PRECISION,
    sensor_18 DOUBLE PRECISION,
    sensor_19 DOUBLE PRECISION,
    sensor_20 DOUBLE PRECISION,
    sensor_21 DOUBLE PRECISION,
    failure_label INTEGER DEFAULT 0,
    is_anomaly INTEGER DEFAULT 0
);


SELECT create_hypertable('sensor_data', 'timestamp', if_not_exists => TRUE);

ALTER TABLE sensor_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'equipment_id'
);

SELECT add_compression_policy('sensor_data', INTERVAL '7 days');

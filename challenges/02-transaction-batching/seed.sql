CREATE TABLE sensor_events (
    event_id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    event_time TIMESTAMP NOT NULL,
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    pressure DECIMAL(7, 2),
    battery_pct SMALLINT,
    raw_payload JSONB
);

CREATE INDEX idx_sensor_events_sensor_time ON sensor_events(sensor_id, event_time DESC);

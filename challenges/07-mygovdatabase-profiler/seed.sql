-- MyGov Mobile Inspections - Database Profiler (V6 - SQLCipher schema)
-- Schema mirrors sqflite_repository.dart after removing per-field encryption.
-- Payloads are now plaintext JSON (DB file encrypted by SQLCipher at rest).
-- Populated with realistic volumes matching production patterns (~908 appointments).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- === Tables ===

CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    module TEXT,
    date_from TEXT,
    appointment_id INTEGER,
    payload TEXT
);

CREATE TABLE sync_history (
    id SERIAL PRIMARY KEY,
    source TEXT,
    timestamp INTEGER
);

CREATE TABLE inspections (
    id SERIAL PRIMARY KEY,
    is_dirty INTEGER,
    inspection_id INTEGER,
    appointment_id INTEGER,
    license_result_id INTEGER DEFAULT 0,
    payload TEXT
);

CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    is_dirty INTEGER,
    is_retrieved INTEGER,
    vehicle_id INTEGER,
    mobile_vehicle_id TEXT,
    payload TEXT
);

CREATE TABLE standard_correction_items (
    id SERIAL PRIMARY KEY,
    correction_item_id INTEGER,
    payload TEXT
);

CREATE TABLE standard_checklist (
    id SERIAL PRIMARY KEY,
    module TEXT,
    checklist_id INTEGER,
    payload TEXT
);

CREATE TABLE standard_checklist_item (
    id SERIAL PRIMARY KEY,
    module TEXT,
    checklist_item_id INTEGER,
    payload TEXT
);

CREATE TABLE queue (
    id SERIAL PRIMARY KEY,
    provider_type INTEGER,
    inserted_at TEXT,
    last_updated_at TEXT,
    update_count INTEGER,
    completed INTEGER DEFAULT 0,
    payload TEXT
);

-- === Seed sync_history ===
INSERT INTO sync_history (source, timestamp) VALUES
    ('appointments', 1717000000),
    ('inspections', 1717000000),
    ('vehicles', 1717000000),
    ('standard_correction_items', 1717000000),
    ('standard_checklist', 1717000000);

-- === Seed appointments (~908 rows — matches production volume) ===
-- Payload is realistic JSON: title, location, module, dates, inspectionIds
INSERT INTO appointments (module, date_from, appointment_id, payload)
SELECT
    (ARRAY['pi', 'bl', 'ce'])[floor(random() * 3 + 1)::int],
    (TIMESTAMP '2024-06-01' + (random() * 365)::int * INTERVAL '1 day')::text,
    n,
    jsonb_build_object(
        'appointmentId', n,
        'title', 'Inspection at ' || (1000 + floor(random() * 9000)::int)::text || ' ' ||
                 (ARRAY['Main St', 'Oak Ave', 'Elm Rd', 'Pine Dr', 'Cedar Ln'])[floor(random() * 5 + 1)::int],
        'module', (ARRAY['pi', 'bl', 'ce'])[floor(random() * 3 + 1)::int],
        'dateFrom', (TIMESTAMP '2024-06-01' + (random() * 365)::int * INTERVAL '1 day')::text,
        'dateTo', (TIMESTAMP '2024-06-01' + (random() * 365)::int * INTERVAL '1 day' + INTERVAL '2 hours')::text,
        'duration', floor(random() * 180 + 30)::int,
        'isCompleted', (random() < 0.3),
        'isArchived', false,
        'ordinal', n,
        'noteToInspector', CASE WHEN random() < 0.2 THEN 'Please check rear entrance' ELSE '' END,
        'location', jsonb_build_object(
            'addressLine', (1000 + floor(random() * 9000)::int)::text || ' ' ||
                           (ARRAY['Main St', 'Oak Ave', 'Elm Rd', 'Pine Dr', 'Cedar Ln'])[floor(random() * 5 + 1)::int] ||
                           ', Springfield, IL 62704'
        ),
        'inspectionIds', jsonb_build_array(n * 3, n * 3 + 1, n * 3 + 2),
        'resultIds', jsonb_build_array(0, 0, 0)
    )::text
FROM generate_series(1, 908) AS n;

-- === Seed inspections (~4500 rows — ~5 per appointment, some dirty) ===
-- Payload includes checklists, violations, corrections structure
INSERT INTO inspections (is_dirty, inspection_id, appointment_id, license_result_id, payload)
SELECT
    CASE WHEN random() < 0.05 THEN 1 ELSE 0 END,
    n,
    floor(random() * 908 + 1)::int,
    floor(random() * 3)::int,
    jsonb_build_object(
        'inspectionId', n,
        'module', (ARRAY['pi', 'bl', 'ce'])[floor(random() * 3 + 1)::int],
        'stepTitle', 'Step ' || (floor(random() * 5 + 1)::int)::text || ' - ' ||
                     (ARRAY['Structural', 'Electrical', 'Plumbing', 'HVAC', 'Fire Safety'])[floor(random() * 5 + 1)::int],
        'shouldSend', (random() < 0.05),
        'appointmentId', jsonb_build_array(floor(random() * 908 + 1)::int),
        'checklists', jsonb_build_array(
            jsonb_build_object(
                'checklistId', floor(random() * 170 + 1)::int,
                'checklistItems', jsonb_build_array(
                    jsonb_build_object(
                        'checklistItemId', floor(random() * 5000 + 1)::int,
                        'title', 'Check item condition',
                        'corrections', jsonb_build_array()
                    )
                )
            )
        ),
        'violations', jsonb_build_array(),
        'results', jsonb_build_array(
            jsonb_build_object(
                'resultStatus', (ARRAY['pass', 'fail', 'pending'])[floor(random() * 3 + 1)::int],
                'dateCreated', (TIMESTAMP '2024-06-01' + (random() * 365)::int * INTERVAL '1 day')::text
            )
        )
    )::text
FROM generate_series(1, 4500) AS n;

-- === Seed vehicles (~2,000 rows) ===
INSERT INTO vehicles (is_dirty, is_retrieved, vehicle_id, mobile_vehicle_id, payload)
SELECT
    CASE WHEN random() < 0.08 THEN 1 ELSE 0 END,
    CASE WHEN random() < 0.7 THEN 1 ELSE 0 END,
    n,
    'mvid-' || gen_random_uuid()::text,
    jsonb_build_object(
        'vehicleId', n,
        'mobileVehicleId', 'mvid-' || gen_random_uuid()::text,
        'make', (ARRAY['Ford', 'Chevrolet', 'Toyota', 'Honda', 'Ram'])[floor(random() * 5 + 1)::int],
        'model', (ARRAY['F-150', 'Silverado', 'Camry', 'Civic', '1500'])[floor(random() * 5 + 1)::int],
        'year', (2015 + floor(random() * 10)::int),
        'vin', upper(encode(gen_random_bytes(9), 'hex')),
        'licensePlate', upper(encode(gen_random_bytes(4), 'hex')),
        'isDirty', (random() < 0.08),
        'photos', jsonb_build_array(
            jsonb_build_object(
                'attachmentId', floor(random() * 10000 + 1)::int,
                'url', 'https://storage.example.com/photos/' || gen_random_uuid()::text || '.jpg',
                'filename', gen_random_uuid()::text || '.jpg'
            )
        )
    )::text
FROM generate_series(1, 2000) AS n;

-- === Seed standard_checklist (~510 rows across modules) ===
INSERT INTO standard_checklist (module, checklist_id, payload)
SELECT
    module,
    n,
    jsonb_build_object(
        'checklistId', n,
        'module', module,
        'title', 'Checklist ' || module || '-' || n::text,
        'checklistItems', jsonb_build_array()
    )::text
FROM generate_series(1, 170) AS n,
     unnest(ARRAY['pi', 'bl', 'ce']) AS module;

-- === Seed standard_checklist_item (~5,000 rows) ===
INSERT INTO standard_checklist_item (module, checklist_item_id, payload)
SELECT
    (ARRAY['pi', 'bl', 'ce'])[floor(random() * 3 + 1)::int],
    n,
    jsonb_build_object(
        'checklistItemId', n,
        'title', 'Item ' || n::text || ' - ' ||
                 (ARRAY['Verify condition', 'Check compliance', 'Inspect installation', 'Confirm safety', 'Review documentation'])[floor(random() * 5 + 1)::int],
        'description', 'Standard checklist item for inspection workflow'
    )::text
FROM generate_series(1, 5000) AS n;

-- === Seed standard_correction_items (~1,000 rows) ===
INSERT INTO standard_correction_items (correction_item_id, payload)
SELECT
    n,
    jsonb_build_object(
        'correctionItemId', n,
        'title', 'Correction: ' ||
                 (ARRAY['Replace damaged component', 'Repair wiring', 'Install missing guard', 'Fix leak', 'Update documentation'])[floor(random() * 5 + 1)::int],
        'severity', (ARRAY['low', 'medium', 'high', 'critical'])[floor(random() * 4 + 1)::int],
        'dueInDays', floor(random() * 90 + 7)::int
    )::text
FROM generate_series(1, 1000) AS n;

-- === Seed queue (~500 rows pending, ~2000 completed) ===
INSERT INTO queue (provider_type, inserted_at, last_updated_at, update_count, completed, payload)
SELECT
    floor(random() * 6)::int,
    (TIMESTAMP '2025-01-01' + (random() * 150)::int * INTERVAL '1 day')::text,
    (TIMESTAMP '2025-01-01' + (random() * 150)::int * INTERVAL '1 day')::text,
    floor(random() * 5)::int,
    CASE WHEN random() < 0.8 THEN 1 ELSE 0 END,
    jsonb_build_object(
        'updates', jsonb_build_array(
            jsonb_build_object(
                'inspection_id', floor(random() * 4500 + 1)::int,
                'module', (ARRAY['pi', 'bl', 'ce'])[floor(random() * 3 + 1)::int]
            )
        )
    )::text
FROM generate_series(1, 2500) AS n;

-- === V6 Indexes ===
CREATE UNIQUE INDEX idx_appointments_appointment_id ON appointments (appointment_id);
CREATE UNIQUE INDEX idx_corrections_correction_item_id ON standard_correction_items (correction_item_id);
CREATE UNIQUE INDEX idx_checklists_module_checklist_id ON standard_checklist (module, checklist_id);
CREATE UNIQUE INDEX idx_checklist_items_module_item_id ON standard_checklist_item (module, checklist_item_id);
CREATE INDEX idx_inspections_inspection_id_result_id ON inspections (inspection_id, license_result_id);
CREATE INDEX idx_inspections_appointment_id ON inspections (appointment_id);
CREATE INDEX idx_inspections_is_dirty ON inspections (is_dirty);
CREATE INDEX idx_vehicles_vehicle_id ON vehicles (vehicle_id);
CREATE INDEX idx_vehicles_mobile_vehicle_id ON vehicles (mobile_vehicle_id);
CREATE INDEX idx_vehicles_is_dirty ON vehicles (is_dirty);
CREATE INDEX idx_queue_completed ON queue (completed);

ANALYZE;

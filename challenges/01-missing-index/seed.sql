-- Seed data for Challenge 01: Missing Index
-- Generates 5M orders with realistic distribution to ensure slow scans without indexes

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,
    order_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    shipping_address TEXT,
    notes TEXT
);

-- Generate 5M rows with ~50K unique emails (avg 100 orders per customer)
-- This ensures the target email has enough rows to be realistic but the table
-- is large enough that a seq scan is painful.
INSERT INTO orders (customer_email, order_date, total_amount, status, shipping_address, notes)
SELECT
    'user' || (random() * 50000)::int || '@example.com',
    TIMESTAMP '2020-01-01' + (random() * 1500)::int * INTERVAL '1 day' + (random() * 86400)::int * INTERVAL '1 second',
    (random() * 500 + 5)::numeric(10,2),
    (ARRAY['pending', 'shipped', 'delivered', 'cancelled', 'returned'])[floor(random() * 5 + 1)::int],
    floor(random() * 9999 + 1)::text || ' Main St, City ' || floor(random() * 100 + 1)::text || ', ST ' || floor(random() * 90000 + 10000)::text,
    CASE WHEN random() < 0.3 THEN 'Customer requested gift wrapping' ELSE NULL END
FROM generate_series(1, 5000000);

-- Ensure our target email has a known number of orders
INSERT INTO orders (customer_email, order_date, total_amount, status, shipping_address, notes)
SELECT
    'jane.doe@example.com',
    TIMESTAMP '2022-01-01' + (n * INTERVAL '3 days') + (random() * 86400)::int * INTERVAL '1 second',
    (random() * 300 + 10)::numeric(10,2),
    (ARRAY['pending', 'shipped', 'delivered'])[floor(random() * 3 + 1)::int],
    '742 Evergreen Terrace, Springfield, IL 62704',
    NULL
FROM generate_series(1, 150) AS n;

-- Intentionally NO indexes besides the PK.
-- The whole point is the participant adds one.

-- Disable parallel query so the seq scan is single-threaded and truly painful
ALTER SYSTEM SET max_parallel_workers_per_gather = 0;
-- Shrink shared buffers to minimize caching benefit
ALTER SYSTEM SET shared_buffers = '32MB';
-- Force the planner to never use indexes (until participant creates one compelling enough)
ALTER SYSTEM SET effective_cache_size = '32MB';
SELECT pg_reload_conf();

-- Analyze so the planner has accurate stats (makes the slow path consistently slow)
ANALYZE orders;

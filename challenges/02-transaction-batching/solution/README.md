# Solution: Transaction Batching

## Fix

```python
def write_events(events: list[dict]) -> int:
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    conn.autocommit = False
    cur = conn.cursor()

    try:
        for event in events:
            cur.execute(
                """
                INSERT INTO sensor_events
                    (sensor_id, event_time, temperature, humidity, pressure, battery_pct, raw_payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event["sensor_id"],
                    event["event_time"],
                    event["temperature"],
                    event["humidity"],
                    event["pressure"],
                    event["battery_pct"],
                    json.dumps(event["raw_payload"]),
                ),
            )
        conn.commit()
        return len(events)
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
```

## Even Faster: executemany or COPY

```python
from psycopg2.extras import execute_values

def write_events(events: list[dict]) -> int:
    conn = psycopg2.connect(...)
    cur = conn.cursor()
    values = [
        (e["sensor_id"], e["event_time"], e["temperature"],
         e["humidity"], e["pressure"], e["battery_pct"],
         json.dumps(e["raw_payload"]))
        for e in events
    ]
    execute_values(cur,
        "INSERT INTO sensor_events (sensor_id, event_time, temperature, humidity, pressure, battery_pct, raw_payload) VALUES %s",
        values
    )
    conn.commit()
    cur.close()
    conn.close()
    return len(events)
```

## Why It's Slow

The original code has THREE compounding issues:

1. **New connection per event** — TCP handshake + auth per insert
2. **autocommit = True** — each INSERT is its own transaction = fsync to WAL per row
3. **Sequential single-row inserts** — no pipelining or batching

Each fsync takes ~5-30ms on typical disks. 1000 fsyncs = 5-30 seconds.

A single transaction does ONE fsync at COMMIT for all 1000 rows.

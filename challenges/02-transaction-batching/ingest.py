"""
Event ingestion script — THIS IS THE FILE PARTICIPANTS EDIT.

Problem: writing 1000 events takes ~30 seconds.
Goal: write all 1000 events in under 500ms with all-or-nothing integrity.
"""
import json
import psycopg2
import os

DB_HOST = os.environ.get("DB_HOST", "challenge-02-db")
DB_NAME = os.environ.get("DB_NAME", "events")
DB_USER = os.environ.get("DB_USER", "challenge")
DB_PASS = os.environ.get("DB_PASS", "challenge")


def write_events(events: list[dict]) -> int:
    """
    Write sensor events to the database.
    Returns the number of successfully written events.

    Each event dict has keys:
        sensor_id, event_time, temperature, humidity, pressure,
        battery_pct, raw_payload
    """
    written = 0

    for event in events:
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )
        conn.autocommit = True
        cur = conn.cursor()

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

        cur.close()
        conn.close()
        written += 1

    return written

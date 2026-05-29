import importlib.util
import json
import os
import time
import random
import string
from datetime import datetime, timedelta

import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "challenge-02-db")
DB_NAME = os.environ.get("DB_NAME", "events")
DB_USER = os.environ.get("DB_USER", "challenge")
DB_PASS = os.environ.get("DB_PASS", "challenge")

FLAG = "FLAG{batch_your_commits_a91c}"
THRESHOLD_MS = 500
EVENT_COUNT = 1000


def generate_events(count: int) -> list[dict]:
    base_time = datetime(2024, 6, 15, 10, 0, 0)
    events = []
    for i in range(count):
        events.append({
            "sensor_id": f"sensor-{''.join(random.choices(string.ascii_lowercase, k=4))}-{i % 50}",
            "event_time": (base_time + timedelta(seconds=i)).isoformat(),
            "temperature": round(random.uniform(15.0, 40.0), 2),
            "humidity": round(random.uniform(20.0, 95.0), 2),
            "pressure": round(random.uniform(980.0, 1050.0), 2),
            "battery_pct": random.randint(5, 100),
            "raw_payload": {"seq": i, "source": "verify-run"},
        })
    return events


def load_ingest_module():
    spec = importlib.util.spec_from_file_location("ingest", "/app/ingest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@app.route("/verify", methods=["GET"])
def verify():
    try:
        # Clean the table before verification
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )
        cur = conn.cursor()
        cur.execute("TRUNCATE sensor_events;")
        conn.commit()
        cur.close()
        conn.close()

        # Load the participant's ingest module (hot-reload)
        ingest = load_ingest_module()

        # Generate test events
        events = generate_events(EVENT_COUNT)

        # Time the write
        start = time.perf_counter()
        written = ingest.write_events(events)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify row count
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sensor_events;")
        actual_count = cur.fetchone()[0]
        cur.close()
        conn.close()

        if actual_count != EVENT_COUNT:
            return jsonify({
                "success": False,
                "message": f"Expected {EVENT_COUNT} rows, found {actual_count}. All events must be written.",
                "time_ms": round(elapsed_ms, 2),
            }), 400

        if elapsed_ms <= THRESHOLD_MS:
            return jsonify({
                "success": True,
                "flag": FLAG,
                "time_ms": round(elapsed_ms, 2),
                "rows_written": actual_count,
                "message": f"All {EVENT_COUNT} events written in {elapsed_ms:.0f}ms (threshold: {THRESHOLD_MS}ms)",
            })
        else:
            return jsonify({
                "success": False,
                "time_ms": round(elapsed_ms, 2),
                "threshold_ms": THRESHOLD_MS,
                "rows_written": actual_count,
                "message": f"Too slow: {elapsed_ms:.0f}ms (need under {THRESHOLD_MS}ms)",
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "challenge": "02-transaction-batching",
        "description": "Fix ingest.py to write 1000 events in under 500ms",
        "file_to_edit": "/app/ingest.py",
        "endpoints": {
            "/verify": "Run the ingest and check timing",
            "/health": "Health check",
        },
        "database": {
            "host": DB_HOST,
            "port": 5432,
            "name": DB_NAME,
            "user": DB_USER,
            "password": DB_PASS,
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

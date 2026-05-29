import os
import time
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "challenge-01-db")
DB_NAME = os.environ.get("DB_NAME", "orders")
DB_USER = os.environ.get("DB_USER", "challenge")
DB_PASS = os.environ.get("DB_PASS", "challenge")

FLAG = "FLAG{index_the_world_362f}"
THRESHOLD_MS = 5
TEST_EMAIL = "jane.doe@example.com"

QUERY = """
SELECT order_id, order_date, total_amount, status
FROM orders
WHERE customer_email = %s
ORDER BY order_date DESC
LIMIT 20;
"""


def get_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )


@app.route("/verify", methods=["GET"])
def verify():
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Run the query 3 times, take the median to avoid cold-cache flukes
        times = []
        rows = None
        for _ in range(3):
            start = time.perf_counter()
            cur.execute(QUERY, (TEST_EMAIL,))
            rows = cur.fetchall()
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        cur.close()
        conn.close()

        median_ms = sorted(times)[1]

        if not rows:
            return jsonify({
                "success": False,
                "message": "Query returned no rows. Make sure the data is intact.",
                "time_ms": round(median_ms, 2),
            }), 400

        if median_ms <= THRESHOLD_MS:
            return jsonify({
                "success": True,
                "flag": FLAG,
                "time_ms": round(median_ms, 2),
                "message": f"Query completed in {median_ms:.2f}ms (threshold: {THRESHOLD_MS}ms)",
            })
        else:
            return jsonify({
                "success": False,
                "time_ms": round(median_ms, 2),
                "threshold_ms": THRESHOLD_MS,
                "message": f"Too slow: {median_ms:.2f}ms (need under {THRESHOLD_MS}ms)",
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "challenge": "01-missing-index",
        "description": "Make the order lookup query run under 5ms",
        "endpoints": {
            "/verify": "Check if your fix passes the threshold",
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

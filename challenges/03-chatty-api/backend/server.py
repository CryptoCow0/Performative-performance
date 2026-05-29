"""
Fake backend API with simulated network latency.
Provides both single-user and batch endpoints.
"""
import os
import time
import random

from flask import Flask, jsonify, request

app = Flask(__name__)

LATENCY_MS = int(os.environ.get("SIMULATED_LATENCY_MS", 50))

# Generate fake user data
USERS = {}
for i in range(1, 501):
    USERS[i] = {
        "id": i,
        "name": f"User {i}",
        "email": f"user{i}@company.com",
        "department": random.choice(["Engineering", "Sales", "Marketing", "Support", "Finance"]),
        "role": random.choice(["IC", "Senior", "Lead", "Manager", "Director"]),
        "office": random.choice(["Austin", "Denver", "Remote", "NYC", "London"]),
        "start_date": f"20{random.randint(15,24)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
    }


def simulate_latency():
    time.sleep(LATENCY_MS / 1000.0)


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    simulate_latency()
    user = USERS.get(user_id)
    if user:
        return jsonify(user)
    return jsonify({"error": "not found"}), 404


@app.route("/users/batch", methods=["POST"])
def get_users_batch():
    simulate_latency()
    data = request.get_json()
    if not data or "user_ids" not in data:
        return jsonify({"error": "must provide user_ids array"}), 400

    user_ids = data["user_ids"]
    if len(user_ids) > 500:
        return jsonify({"error": "max 500 users per batch"}), 400

    results = [USERS[uid] for uid in user_ids if uid in USERS]
    return jsonify(results)


@app.route("/users", methods=["GET"])
def list_users():
    simulate_latency()
    page = request.args.get("page", 1, type=int)
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    all_users = list(USERS.values())
    return jsonify({
        "users": all_users[start:end],
        "page": page,
        "total": len(all_users),
        "pages": (len(all_users) + per_page - 1) // per_page,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "latency_ms": LATENCY_MS})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

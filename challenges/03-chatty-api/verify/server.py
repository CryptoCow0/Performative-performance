import importlib.util
import os
import time

from flask import Flask, jsonify

app = Flask(__name__)

FLAG = "FLAG{batch_endpoints_save_lives_7e2a}"
THRESHOLD_MS = 2000
USER_COUNT = 200


def load_module():
    spec = importlib.util.spec_from_file_location("fetch_profiles", "/app/fetch_profiles.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@app.route("/verify", methods=["GET"])
def verify():
    try:
        mod = load_module()
        user_ids = list(range(1, USER_COUNT + 1))

        start = time.perf_counter()
        profiles = mod.fetch_profiles(user_ids)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if len(profiles) != USER_COUNT:
            return jsonify({
                "success": False,
                "message": f"Expected {USER_COUNT} profiles, got {len(profiles)}.",
                "time_ms": round(elapsed_ms, 2),
            }), 400

        # Verify correctness — spot check some fields
        ids_returned = {p["id"] for p in profiles}
        missing = set(user_ids) - ids_returned
        if missing:
            return jsonify({
                "success": False,
                "message": f"Missing profiles for user IDs: {sorted(list(missing))[:10]}...",
                "time_ms": round(elapsed_ms, 2),
            }), 400

        if elapsed_ms <= THRESHOLD_MS:
            return jsonify({
                "success": True,
                "flag": FLAG,
                "time_ms": round(elapsed_ms, 2),
                "profiles_loaded": len(profiles),
                "message": f"Loaded {USER_COUNT} profiles in {elapsed_ms:.0f}ms (threshold: {THRESHOLD_MS}ms)",
            })
        else:
            return jsonify({
                "success": False,
                "time_ms": round(elapsed_ms, 2),
                "threshold_ms": THRESHOLD_MS,
                "profiles_loaded": len(profiles),
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
        "challenge": "03-chatty-api",
        "description": "Fix fetch_profiles.py to load 200 profiles in under 2s",
        "file_to_edit": "/app/fetch_profiles.py",
        "endpoints": {
            "/verify": "Run the fetch and measure timing",
            "/health": "Health check",
        },
        "backend_docs": {
            "GET /users/{id}": "Single user profile (50ms latency each)",
            "POST /users/batch": "Batch fetch — body: {\"user_ids\": [1,2,...]}",
            "GET /users?page=N": "Paginated list (20 per page)",
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

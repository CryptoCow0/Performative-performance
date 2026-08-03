import importlib.util
import os
import random
import string
import time

from flask import Flask, jsonify

app = Flask(__name__)

FLAG = "FLAG{sets_are_o1_f4d8}"
THRESHOLD_MS = 50
ACTION_COUNT = 10000
ALLOWED_COUNT = 5000


def generate_test_data():
    all_possible = [
        f"module.{m}.action.{a}.scope.{s}"
        for m in ["users", "orders", "billing", "reports", "admin", "config", "audit"]
        for a in ["read", "write", "delete", "export", "approve", "reject", "archive"]
        for s in ["own", "team", "org", "global"]
    ] + [
        f"custom.{''.join(random.choices(string.ascii_lowercase, k=8))}"
        for _ in range(4000)
    ]

    allowed_actions = random.sample(all_possible, min(ALLOWED_COUNT, len(all_possible)))

    # Mix of allowed and disallowed actions to validate
    actions_to_validate = []
    for _ in range(ACTION_COUNT):
        if random.random() < 0.6:
            actions_to_validate.append(random.choice(allowed_actions))
        else:
            actions_to_validate.append(
                f"denied.{''.join(random.choices(string.ascii_lowercase, k=10))}"
            )

    return actions_to_validate, allowed_actions


def load_module():
    spec = importlib.util.spec_from_file_location("check_permissions", "/app/workspace/check_permissions.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@app.route("/verify", methods=["GET"])
def verify():
    try:
        mod = load_module()
        actions_to_validate, allowed_actions = generate_test_data()

        # Compute expected results for correctness check
        allowed_set = set(allowed_actions)
        expected = [{"action": a, "allowed": a in allowed_set} for a in actions_to_validate]

        # Time the participant's implementation
        times = []
        for _ in range(3):
            start = time.perf_counter()
            results = mod.check_permissions(actions_to_validate, allowed_actions)
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        median_ms = sorted(times)[1]

        # Correctness check
        if results != expected:
            mismatches = sum(1 for r, e in zip(results, expected) if r != e)
            return jsonify({
                "success": False,
                "message": f"Results don't match expected output. {mismatches} mismatches out of {ACTION_COUNT}.",
                "time_ms": round(median_ms, 2),
            }), 400

        if median_ms <= THRESHOLD_MS:
            return jsonify({
                "success": True,
                "flag": FLAG,
                "time_ms": round(median_ms, 2),
                "actions_checked": ACTION_COUNT,
                "message": f"Validated {ACTION_COUNT} actions in {median_ms:.1f}ms (threshold: {THRESHOLD_MS}ms)",
            })
        else:
            return jsonify({
                "success": False,
                "time_ms": round(median_ms, 2),
                "threshold_ms": THRESHOLD_MS,
                "actions_checked": ACTION_COUNT,
                "message": f"Too slow: {median_ms:.0f}ms (need under {THRESHOLD_MS}ms)",
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "challenge": "05-list-to-set",
        "description": "Fix check_permissions.py to validate 10K actions in under 50ms",
        "file_to_edit": "05-list-to-set/check_permissions.py",
        "endpoints": {
            "/verify": "Run the check and measure timing",
            "/health": "Health check",
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

import importlib.util
import random
import string
import time

from flask import Flask, jsonify

app = Flask(__name__)

FLAG = "FLAG{hash_bucket_not_brute_force_c3b1}"
THRESHOLD_MS = 200
RECORD_COUNT = 100000

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
]

ZIP_CODES = [f"{z:05d}" for z in range(10001, 99999, 17)]


def generate_records():
    records = []
    for _ in range(RECORD_COUNT):
        last = random.choice(LAST_NAMES)
        zipcode = random.choice(ZIP_CODES)
        records.append({
            "first_name": "".join(random.choices(string.ascii_lowercase, k=6)).capitalize(),
            "last_name": last,
            "email": f"{''.join(random.choices(string.ascii_lowercase, k=8))}@mail.com",
            "zip_code": zipcode,
            "phone": f"({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}",
        })
    return records


def compute_expected(records):
    buckets = {}
    for i, r in enumerate(records):
        key = r["last_name"].lower() + r["zip_code"]
        buckets.setdefault(key, []).append(i)
    return sorted(
        [group for group in buckets.values() if len(group) > 1],
        key=lambda g: g[0]
    )


def load_module():
    spec = importlib.util.spec_from_file_location("dedup", "/app/workspace/dedup.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@app.route("/verify", methods=["GET"])
def verify():
    try:
        mod = load_module()
        records = generate_records()
        expected = compute_expected(records)

        # Time the participant's implementation
        times = []
        result = None
        for _ in range(3):
            start = time.perf_counter()
            result = mod.find_duplicates(records)
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        median_ms = sorted(times)[1]

        # Normalize for comparison (sort each group, sort groups by first element)
        result_normalized = sorted([sorted(g) for g in result], key=lambda g: g[0])
        expected_normalized = sorted([sorted(g) for g in expected], key=lambda g: g[0])

        if result_normalized != expected_normalized:
            return jsonify({
                "success": False,
                "message": f"Incorrect results. Found {len(result)} groups, expected {len(expected)}.",
                "time_ms": round(median_ms, 2),
                "hint": "Make sure you're using lowercase(last_name) + zip_code as the dedup key.",
            }), 400

        if median_ms <= THRESHOLD_MS:
            return jsonify({
                "success": True,
                "flag": FLAG,
                "time_ms": round(median_ms, 2),
                "groups_found": len(result),
                "records_processed": RECORD_COUNT,
                "message": f"Deduped {RECORD_COUNT} records in {median_ms:.0f}ms (threshold: {THRESHOLD_MS}ms)",
            })
        else:
            return jsonify({
                "success": False,
                "time_ms": round(median_ms, 2),
                "threshold_ms": THRESHOLD_MS,
                "groups_found": len(result),
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
        "challenge": "06-n-squared-dedup",
        "description": "Fix dedup.py to deduplicate 100K records in under 200ms",
        "file_to_edit": "06-n-squared-dedup/dedup.py",
        "endpoints": {
            "/verify": "Run the dedup and measure timing",
            "/health": "Health check",
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

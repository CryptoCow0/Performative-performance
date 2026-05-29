import asyncio
import importlib.util
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request

app = Flask(__name__)

FLAG = "FLAG{bounded_concurrency_is_key_8f4d}"
THRESHOLD_MS = 2000
IMAGE_COUNT = 200
CONCURRENCY_CAP = 25
SIMULATED_WORK_MS = 100

# Track concurrency for the resize endpoint
_concurrent = 0
_peak_concurrent = 0
_lock = threading.Lock()
_total_requests = 0
_rejected_requests = 0


def reset_metrics():
    global _concurrent, _peak_concurrent, _total_requests, _rejected_requests
    _concurrent = 0
    _peak_concurrent = 0
    _total_requests = 0
    _rejected_requests = 0


@app.route("/resize", methods=["POST"])
def resize():
    global _concurrent, _peak_concurrent, _total_requests, _rejected_requests

    with _lock:
        _total_requests += 1
        _concurrent += 1
        if _concurrent > _peak_concurrent:
            _peak_concurrent = _concurrent

        if _concurrent > CONCURRENCY_CAP:
            _concurrent -= 1
            _rejected_requests += 1
            return jsonify({"error": "too many requests"}), 429

    time.sleep(SIMULATED_WORK_MS / 1000.0)

    data = request.get_json()
    image_id = data.get("image_id", 0)

    with _lock:
        _concurrent -= 1

    return jsonify({
        "image_id": image_id,
        "status": "resized",
        "url": f"https://cdn.example.com/images/{image_id}_resized.jpg",
    })


def load_module():
    spec = importlib.util.spec_from_file_location("process_images", "/app/process_images.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@app.route("/verify", methods=["GET"])
def verify():
    try:
        reset_metrics()
        mod = load_module()
        image_ids = list(range(1, IMAGE_COUNT + 1))

        start = time.perf_counter()
        try:
            results = mod.process_images(image_ids)
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return jsonify({
                "success": False,
                "message": f"process_images raised an exception: {e}",
                "time_ms": round(elapsed_ms, 2),
                "peak_concurrent": _peak_concurrent,
                "rejected_requests": _rejected_requests,
            }), 400

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Check all images processed
        if len(results) != IMAGE_COUNT:
            return jsonify({
                "success": False,
                "message": f"Expected {IMAGE_COUNT} results, got {len(results)}.",
                "time_ms": round(elapsed_ms, 2),
                "peak_concurrent": _peak_concurrent,
            }), 400

        # Check no rejections occurred
        if _rejected_requests > 0:
            return jsonify({
                "success": False,
                "message": f"Server rejected {_rejected_requests} requests (exceeded {CONCURRENCY_CAP} concurrent). Use bounded concurrency.",
                "time_ms": round(elapsed_ms, 2),
                "peak_concurrent": _peak_concurrent,
                "rejected_requests": _rejected_requests,
            }), 400

        # Check timing
        if elapsed_ms > THRESHOLD_MS:
            return jsonify({
                "success": False,
                "time_ms": round(elapsed_ms, 2),
                "threshold_ms": THRESHOLD_MS,
                "peak_concurrent": _peak_concurrent,
                "message": f"Too slow: {elapsed_ms:.0f}ms (need under {THRESHOLD_MS}ms). Peak concurrency: {_peak_concurrent}.",
            })

        return jsonify({
            "success": True,
            "flag": FLAG,
            "time_ms": round(elapsed_ms, 2),
            "peak_concurrent": _peak_concurrent,
            "images_processed": len(results),
            "message": f"Processed {IMAGE_COUNT} images in {elapsed_ms:.0f}ms. Peak concurrency: {_peak_concurrent}.",
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "challenge": "04-bounded-concurrency",
        "description": "Fix process_images.py to use bounded parallelism",
        "file_to_edit": "/app/process_images.py",
        "endpoints": {
            "/verify": "Run the processing and check timing + error rate",
            "/resize": "Image resize service (POST {\"image_id\": N})",
            "/health": "Health check",
        },
        "constraints": {
            "max_concurrent": CONCURRENCY_CAP,
            "time_threshold_ms": THRESHOLD_MS,
            "error_tolerance": 0,
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090, threaded=True)

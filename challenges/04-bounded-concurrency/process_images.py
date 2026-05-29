"""
Image processing module — THIS IS THE FILE PARTICIPANTS EDIT.

Problem: processing 200 images sequentially takes 20 seconds.
         Launching all 200 at once overwhelms the server (429 errors).
Goal: process all 200 in under 2 seconds with zero errors.

The resize service is at http://localhost:9090/resize
- Accepts POST with JSON: {"image_id": 123}
- Returns {"image_id": 123, "status": "resized", "url": "..."}
- Takes ~100ms per request
- Returns 429 Too Many Requests if more than 25 concurrent requests
"""
import requests

RESIZE_URL = "http://localhost:9090/resize"


def process_images(image_ids: list[int]) -> list[dict]:
    """
    Process all images and return their results.
    Each result is the JSON response from the resize service.
    Must return a result for every image_id (no errors allowed).
    """
    results = []

    for image_id in image_ids:
        response = requests.post(RESIZE_URL, json={"image_id": image_id})
        if response.status_code == 200:
            results.append(response.json())
        else:
            raise Exception(f"Failed to process image {image_id}: {response.status_code}")

    return results

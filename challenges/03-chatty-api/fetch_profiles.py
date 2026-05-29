"""
Profile fetching module — THIS IS THE FILE PARTICIPANTS EDIT.

Problem: loading 200 user profiles takes 10+ seconds due to individual API calls.
Goal: load all 200 profiles in under 2 seconds.

Available API endpoints on the backend (http://challenge-03-backend:8080):
  GET  /users/{id}        — returns a single user profile
  POST /users/batch       — accepts {"user_ids": [1,2,3,...]}, returns all profiles
  GET  /users             — paginated list (20 per page), too slow for this use case
"""
import requests

BACKEND_URL = "http://challenge-03-backend:8080"


def fetch_profiles(user_ids: list[int]) -> list[dict]:
    """
    Fetch user profiles for all given user_ids.
    Returns a list of profile dicts.
    """
    profiles = []

    for user_id in user_ids:
        response = requests.get(f"{BACKEND_URL}/users/{user_id}")
        if response.status_code == 200:
            profiles.append(response.json())

    return profiles

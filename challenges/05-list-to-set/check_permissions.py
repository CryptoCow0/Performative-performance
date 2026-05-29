"""
Permission checking module — THIS IS THE FILE PARTICIPANTS EDIT.

Problem: validating 10,000 actions against 5,000 allowed actions takes ~4 seconds.
Goal: complete the same validation in under 50ms with identical results.
"""


def check_permissions(actions_to_validate: list[str], allowed_actions: list[str]) -> list[dict]:
    """
    For each action in actions_to_validate, check if it appears in allowed_actions.
    Returns a list of dicts: [{"action": "...", "allowed": True/False}, ...]
    """
    results = []

    for action in actions_to_validate:
        is_allowed = False
        for allowed in allowed_actions:
            if action == allowed:
                is_allowed = True
                break
        results.append({"action": action, "allowed": is_allowed})

    return results

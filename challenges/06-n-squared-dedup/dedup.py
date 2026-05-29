"""
Deduplication module — THIS IS THE FILE PARTICIPANTS EDIT.

Problem: deduplicating 100K customer records takes 40+ seconds.
Goal: find all duplicate groups in under 200ms.

Duplicate definition: two records are duplicates if they share the same
normalized key: lowercase(last_name) + zip_code

Output format: list of duplicate groups, where each group is a list of
record indices that are duplicates of each other. Only include groups
with 2+ members. Sort groups by their first index.
"""


def find_duplicates(records: list[dict]) -> list[list[int]]:
    """
    Find groups of duplicate records.

    Each record has: {"first_name", "last_name", "email", "zip_code", "phone"}

    Returns: list of groups, each group is a list of indices into `records`
             that are duplicates of each other.
             Only groups with 2+ members. Sorted by first index in group.
    """
    duplicate_groups = []
    seen_in_group = set()

    for i in range(len(records)):
        if i in seen_in_group:
            continue

        group = [i]
        key_i = records[i]["last_name"].lower() + records[i]["zip_code"]

        for j in range(i + 1, len(records)):
            if j in seen_in_group:
                continue

            key_j = records[j]["last_name"].lower() + records[j]["zip_code"]

            if key_i == key_j:
                group.append(j)
                seen_in_group.add(j)

        if len(group) > 1:
            duplicate_groups.append(group)
            seen_in_group.add(i)

    return duplicate_groups

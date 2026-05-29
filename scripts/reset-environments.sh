#!/usr/bin/env bash
# Reset all challenge environments to their initial state.
# Use between participants or rounds.

set -euo pipefail

echo "Resetting challenge databases..."

# Challenge 01: Drop and recreate index (participant's fix)
docker compose exec challenge-01-db psql -U challenge -d orders -c "
    DROP INDEX IF EXISTS idx_orders_customer_email;
    DROP INDEX IF EXISTS idx_orders_email_date_covering;
    DROP INDEX IF EXISTS idx_orders_email_date;
" 2>/dev/null && echo "  01-missing-index: reset" || echo "  01-missing-index: skipped (not running)"

# Challenge 02: Truncate events table
docker compose exec challenge-02-db psql -U challenge -d events -c "
    TRUNCATE sensor_events;
" 2>/dev/null && echo "  02-transaction-batching: reset" || echo "  02-transaction-batching: skipped (not running)"

# Challenges 03-06: Restore original source files
CHALLENGES_DIR="$(cd "$(dirname "$0")/../challenges" && pwd)"

for file in \
    "03-chatty-api/fetch_profiles.py" \
    "04-bounded-concurrency/process_images.py" \
    "05-list-to-set/check_permissions.py" \
    "06-n-squared-dedup/dedup.py"; do

    challenge_num=$(echo "$file" | cut -d'/' -f1 | cut -d'-' -f1)
    container="ctf-performance-challenge-${file%%/*}-1"

    # Copy original file back into running container
    if docker cp "$CHALLENGES_DIR/$file" "$container:/app/$(basename "$file")" 2>/dev/null; then
        echo "  $file: restored"
    else
        echo "  $file: skipped (container not running)"
    fi
done

echo "Reset complete."

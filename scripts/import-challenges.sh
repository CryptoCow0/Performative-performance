#!/usr/bin/env bash
# Import all challenges into a running CTFd instance via its API.
# Usage: ./scripts/import-challenges.sh [CTFD_URL] [CTFD_TOKEN]
#
# Requires: curl, jq

set -euo pipefail

CTFD_URL="${1:-http://localhost:8000}"
CTFD_TOKEN="${2:-}"

if [ -z "$CTFD_TOKEN" ]; then
    echo "Usage: $0 <ctfd_url> <ctfd_api_token>"
    echo "Get a token from CTFd Admin > Config > Access Tokens"
    exit 1
fi

CHALLENGES_DIR="$(cd "$(dirname "$0")/../challenges" && pwd)"

for challenge_dir in "$CHALLENGES_DIR"/*/; do
    challenge_file="$challenge_dir/challenge.yml"
    if [ ! -f "$challenge_file" ]; then
        echo "SKIP: $challenge_dir (no challenge.yml)"
        continue
    fi

    # Parse values — strip key prefix, surrounding quotes, and trailing whitespace
    name=$(grep "^name:" "$challenge_file" | sed 's/^name: *//; s/^"//; s/"$//')
    category=$(grep "^category:" "$challenge_file" | sed 's/^category: *//; s/^"//; s/"$//')
    points=$(grep "^points:" "$challenge_file" | sed 's/^points: *//')
    flag=$(grep "^flag:" "$challenge_file" | sed 's/^flag: *//; s/^"//; s/"$//')
    description=$(sed -n '/^description: |/,/^[a-z]/{ /^description:/d; /^[a-z]/d; p; }' "$challenge_file" | sed 's/^  //' | tr '\n' ' ' | sed 's/  */ /g; s/ *$//')

    echo "Importing: $name ($category, ${points}pts)"

    # Create challenge
    response=$(curl -s -X POST "$CTFD_URL/api/v1/challenges" \
        -H "Authorization: Token $CTFD_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$(jq -n \
            --arg name "$name" \
            --arg category "$category" \
            --argjson value "$points" \
            --arg desc "$description" \
            '{name: $name, category: $category, value: $value, description: $desc, type: "standard", state: "visible"}')")

    challenge_id=$(echo "$response" | jq -r '.data.id // empty')

    if [ -z "$challenge_id" ]; then
        echo "  ERROR: $(echo "$response" | jq -r '.message // .errors // "unknown error"')"
        continue
    fi

    # Add flag
    curl -s -X POST "$CTFD_URL/api/v1/flags" \
        -H "Authorization: Token $CTFD_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$(jq -n \
            --argjson id "$challenge_id" \
            --arg flag "$flag" \
            '{challenge_id: $id, content: $flag, type: "static"}')" > /dev/null

    echo "  Created: ID=$challenge_id"
done

echo "Done. All challenges imported."

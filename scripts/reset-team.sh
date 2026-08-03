#!/usr/bin/env bash
# Reset ONE team's environment back to its initial state (fresh volumes, so all
# editable files and databases return to the broken baseline).
#
# Usage: ./scripts/reset-team.sh <team-slug> [workspace-password]

set -euo pipefail

SLUG="${1:-}"
PASSWORD="${2:-changeme}"

if [ -z "$SLUG" ]; then
    echo "Usage: $0 <team-slug> [workspace-password]"
    exit 1
fi

cd "$(dirname "$0")/.."

echo "Resetting team '$SLUG' (down -v then up)..."
COMPOSE_PROJECT_NAME="ctf-$SLUG" docker compose -f docker-compose.challenges.yml down -v
COMPOSE_PROJECT_NAME="ctf-$SLUG" TEAM_PASSWORD="$PASSWORD" \
    docker compose -f docker-compose.challenges.yml up -d --build

echo "Reset complete for team '$SLUG'."

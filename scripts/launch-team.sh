#!/usr/bin/env bash
# Launch a per-team challenge stack. No Caddyfile editing needed — Caddy routes
# <slug>.performative-performance.com to this stack's code-server dynamically.
#
# Usage: ./scripts/launch-team.sh <team-slug> [workspace-password]
#   <team-slug>  lowercase, no spaces (e.g. best-team, test-team)
#                becomes the subdomain: best-team.performative-performance.com
#
# Example:
#   ./scripts/launch-team.sh test-team hunter2
#   -> workspace at https://test-team.performative-performance.com (password hunter2)

set -euo pipefail

SLUG="${1:-}"
PASSWORD="${2:-changeme}"

if [ -z "$SLUG" ]; then
    echo "Usage: $0 <team-slug> [workspace-password]"
    echo "  team-slug: lowercase letters/digits/hyphens only (used as subdomain)"
    exit 1
fi

if ! echo "$SLUG" | grep -Eq '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'; then
    echo "ERROR: '$SLUG' is not a valid subdomain slug."
    echo "Use lowercase letters, digits, and hyphens only (e.g. best-team)."
    exit 1
fi

cd "$(dirname "$0")/.."

echo "Launching stack for team '$SLUG'..."
COMPOSE_PROJECT_NAME="ctf-$SLUG" TEAM_PASSWORD="$PASSWORD" \
    docker compose -f docker-compose.challenges.yml up -d --build

echo ""
echo "Done. Team workspace:"
echo "  URL:      https://$SLUG.performative-performance.com"
echo "  Password: $PASSWORD"
echo "  Project:  ctf-$SLUG"

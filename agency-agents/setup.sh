#!/bin/bash
# Setup script for ACP agent activation profiles
# Copies agent profiles to your Claude Code agents directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$HOME/.claude/agents"

mkdir -p "$AGENTS_DIR"

count=0
for agent_file in "$SCRIPT_DIR"/*.md; do
    [ -f "$agent_file" ] || continue
    cp "$agent_file" "$AGENTS_DIR/"
    count=$((count + 1))
    echo "  Installed: $(basename "$agent_file")"
done

echo ""
echo "Installed $count agent profiles to $AGENTS_DIR"
echo ""
echo "Activate an agent in Claude Code by saying:"
echo '  "Activate Architect mode and help me design a new API"'
echo '  "Activate Frontend Developer mode and build a React component"'
echo '  "Activate Code Reviewer mode and review my latest PR"'

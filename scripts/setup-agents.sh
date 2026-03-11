#!/usr/bin/env bash
# Setup script to install ACP agents into your Claude Code directory.
# Usage: ./scripts/setup-agents.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$REPO_ROOT/agency-agents"
TARGET_DIR="$HOME/.claude/agents"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: agency-agents directory not found at $SOURCE_DIR"
  exit 1
fi

mkdir -p "$TARGET_DIR"

cp -r "$SOURCE_DIR"/* "$TARGET_DIR"/

echo "Agents installed to $TARGET_DIR:"
ls "$TARGET_DIR"
echo ""
echo "You can now activate any agent in your Claude Code sessions."
echo "Example: \"Hey Claude, activate ACP Protocol Developer mode\""

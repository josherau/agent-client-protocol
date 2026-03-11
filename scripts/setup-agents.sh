#!/usr/bin/env bash
# Setup script to install ACP agents and everything-claude-code plugin
# into your Claude Code directory.
# Usage: ./scripts/setup-agents.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$REPO_ROOT/agency-agents"
TARGET_AGENTS="$HOME/.claude/agents"
TARGET_SKILLS="$HOME/.claude/skills"
TARGET_COMMANDS="$HOME/.claude/commands"

# --- Install ACP project agents ---
if [ -d "$SOURCE_DIR" ]; then
  mkdir -p "$TARGET_AGENTS"
  cp -r "$SOURCE_DIR"/* "$TARGET_AGENTS"/
  echo "ACP agents installed to $TARGET_AGENTS"
else
  echo "Warning: agency-agents directory not found at $SOURCE_DIR"
fi

# --- Install everything-claude-code plugin ---
ECC_DIR="/tmp/everything-claude-code"
if [ ! -d "$ECC_DIR" ]; then
  echo "Cloning everything-claude-code..."
  git clone --depth 1 https://github.com/affaan-m/everything-claude-code.git "$ECC_DIR" 2>/dev/null
fi

if [ -d "$ECC_DIR" ]; then
  mkdir -p "$TARGET_AGENTS" "$TARGET_SKILLS" "$TARGET_COMMANDS"

  # Copy agents
  if [ -d "$ECC_DIR/agents" ]; then
    cp "$ECC_DIR"/agents/* "$TARGET_AGENTS"/ 2>/dev/null || true
    echo "ECC agents installed"
  fi

  # Copy skills
  if [ -d "$ECC_DIR/skills" ]; then
    cp -r "$ECC_DIR"/skills/* "$TARGET_SKILLS"/ 2>/dev/null || true
    echo "ECC skills installed"
  fi

  # Copy commands
  if [ -d "$ECC_DIR/commands" ]; then
    cp "$ECC_DIR"/commands/* "$TARGET_COMMANDS"/ 2>/dev/null || true
    echo "ECC commands installed"
  fi

  echo "everything-claude-code plugin installed successfully"
else
  echo "Warning: Could not clone everything-claude-code"
fi

echo ""
echo "Installed:"
echo "  Agents:   $(ls "$TARGET_AGENTS" 2>/dev/null | wc -l) files"
echo "  Skills:   $(ls "$TARGET_SKILLS" 2>/dev/null | wc -l) entries"
echo "  Commands: $(ls "$TARGET_COMMANDS" 2>/dev/null | wc -l) files"
echo ""
echo "Activate any agent in your Claude Code sessions."
echo "Example: \"Hey Claude, activate ACP Protocol Developer mode\""

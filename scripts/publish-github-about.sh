#!/usr/bin/env bash
# Apply docs/DISCOVERY.md to GitHub About. Requires gh, authenticated to
# ryanduguid/aus-accounting-mcp with repo metadata write access.
set -euo pipefail

REPO="ryanduguid/aus-accounting-mcp"
DESCRIPTION="Local MCP server for Australian computational accounting: ATO small-business benchmarks, Payday Super 2026 review, refused Division 7A, and synthetic SBR fixtures. Citations and refusals, not advice."
HOMEPAGE="https://github.com/ryanduguid/aus-accounting-mcp#install"
TOPICS=(
  accounting-ai
  agent-skills
  ato
  ato-benchmarks
  australian-tax
  claude-code
  codex
  cursor
  division-7a
  mcp
  mcp-server
  model-context-protocol
  payday-super
  tax-prep
)

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required" >&2
  exit 1
fi

gh repo edit "$REPO" --description "$DESCRIPTION" --homepage "$HOMEPAGE"
topic_flags=()
for topic in "${TOPICS[@]}"; do
  topic_flags+=(--add-topic "$topic")
done
gh repo edit "$REPO" "${topic_flags[@]}"
echo "Updated $REPO About. Pin this repository from github.com/ryanduguid (Customize your pins)."

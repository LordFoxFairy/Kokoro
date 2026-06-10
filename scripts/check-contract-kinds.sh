#!/usr/bin/env bash
# Cross-repo event-contract regression net (critic P0).
# Extracts the event-kind set each repo references (directory-level, NOT
# filename-bound — survives the DDD file moves). Run BEFORE and AFTER the
# restructure: the per-repo kind sets must be byte-identical (contract files
# are git-mv'd only, never content-edited, so no kind may drift).
set -euo pipefail
ROOT="/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro"
PAT='"(run|text|thinking|tool|todo|subagent|message|session|artifact|permission)\.[a-z._]+"'

extract() { grep -rhoE "$PAT" "$1" 2>/dev/null | tr -d '"' | sort -u; }

echo "## kokoro-agent"
extract "$ROOT/kokoro-agent/src/kokoro_agent"
echo "## kokoro-session"
extract "$ROOT/kokoro-session/src"
echo "## kokoro-web"
extract "$ROOT/kokoro-web/src"

#!/usr/bin/env bash
# Active Phase 1 deployment entrypoint.
# The previous full-stack orchestration is preserved outside Root at
# /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro-archive-2026-09-01/root-legacy/deploy/provision-legacy.sh
# for migration archaeology only and must not be used for the current runtime.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT_DIR/deploy/provision-phase1.sh" "${1:-deploy/.env.phase1.prod}"

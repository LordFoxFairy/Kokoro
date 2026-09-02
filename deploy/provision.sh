#!/usr/bin/env bash
# Active Phase 1 deployment entrypoint.
# Retired full-stack orchestration is kept in Git history only; this wrapper
# deliberately points at the current Phase 1 entrypoint.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT_DIR/deploy/provision-phase1.sh" "${1:-deploy/.env.phase1.prod}"

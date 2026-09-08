#!/usr/bin/env bash
set -Eeuo pipefail

# Fail closed; the old shared-state orchestration remains in Git history only.
cat >&2 <<'MESSAGE'
VERIFICATION_ENTRY_PAUSED: the legacy full-repository runner was removed because
its shared-state cleanup was not isolated. The full-repository gate is not passed.
Run each owner's documented gates separately. For System/BFF/Agent HTTP acceptance,
use scripts/e2e/run_system_owner_smoke.py; it is not an all-repository gate.
Root owns rebuilding an isolated full-repository orchestrator. No infrastructure
has been touched.
MESSAGE
exit 2

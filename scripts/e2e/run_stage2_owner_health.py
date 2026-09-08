#!/usr/bin/env python3
"""Fail closed for the retired, shared-state Stage 2 health orchestrator."""

import sys


def main() -> int:
    print(
        "VERIFICATION_ENTRY_PAUSED: the legacy Stage 2 owner-health runner was removed "
        "because its shared-state cleanup was not isolated and its runtime entries drifted. "
        "Use scripts/e2e/run_system_owner_smoke.py for System/BFF/Agent HTTP acceptance. "
        "This is not a replacement for all-repository acceptance; run each owner's "
        "documented gates separately. No infrastructure has been touched.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify BFF relay policy provenance from the published Root gitlinks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.governance.iam_relay_policy import verify_iam_relay_policy  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    errors = verify_iam_relay_policy(args.root)
    result: dict[str, object] = {"status": "FAIL" if errors else "PASS"}
    if errors:
        result["errors"] = errors
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

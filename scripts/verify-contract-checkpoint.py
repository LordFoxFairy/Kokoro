#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.governance.contract_checkpoint import verify_checkpoint  # noqa: E402


def _root_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify an exact contract compatibility checkpoint."
    )
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("verification/contracts/consumer-inventory.json"),
    )
    args = parser.parse_args(argv)
    errors = verify_checkpoint(
        ROOT,
        _root_path(args.inventory),
        _root_path(args.expected),
    )
    payload: dict[str, object] = {"status": "FAIL" if errors else "PASS"}
    if errors:
        payload["errors"] = errors
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

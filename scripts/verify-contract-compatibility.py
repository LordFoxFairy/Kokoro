#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.governance.contract_inventory import (  # noqa: E402
    load_inventory,
    verify_inventory,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify frozen owner/consumer contract pins."
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=ROOT / "verification/contracts/consumer-inventory.json",
    )
    args = parser.parse_args(argv)
    inventory_path = args.inventory
    if not inventory_path.is_absolute():
        inventory_path = ROOT / inventory_path
    errors = verify_inventory(ROOT, inventory_path)
    try:
        inventory = load_inventory(inventory_path)
        edge_count = len(inventory["edges"])
        violation_count = len(inventory["violations"])
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        edge_count = 0
        violation_count = 0
    payload: dict[str, object] = {
        "status": "FAIL" if errors else "PASS",
        "edge_count": edge_count,
        "violation_count": violation_count,
    }
    if errors:
        payload["errors"] = errors
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

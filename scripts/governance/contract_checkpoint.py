from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from scripts.governance.contract_inventory import load_inventory, verify_inventory

CHECKPOINT_FIELDS = ("active_ids", "broken_ids", "illegal_ids")
InventoryVerifier = Callable[[Path, Path], list[str]]


def load_checkpoint(path: Path) -> dict[str, frozenset[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError("checkpoint must be UTF-8 JSON") from None
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("checkpoint must be an object")
    if set(value) != {"schema_version", *CHECKPOINT_FIELDS}:
        raise ValueError("checkpoint fields do not match schema version 1")
    if value.get("schema_version") != 1:
        raise ValueError("checkpoint schema_version must equal 1")
    result: dict[str, frozenset[str]] = {}
    for field in CHECKPOINT_FIELDS:
        raw_ids = value[field]
        if (
            not isinstance(raw_ids, list)
            or not all(isinstance(item, str) and item for item in raw_ids)
            or len(raw_ids) != len(set(raw_ids))
        ):
            raise ValueError(f"checkpoint {field} must contain unique non-empty IDs")
        result[field] = frozenset(raw_ids)
    if any(
        result[left] & result[right]
        for index, left in enumerate(CHECKPOINT_FIELDS)
        for right in CHECKPOINT_FIELDS[index + 1 :]
    ):
        raise ValueError("expected ID sets must be disjoint")
    return result


def _inventory_id_sets(inventory: dict[str, Any]) -> dict[str, frozenset[str]]:
    active: set[str] = set()
    broken: set[str] = set()
    illegal: set[str] = set()
    for edge in inventory["edges"]:
        if not isinstance(edge, dict) or not isinstance(edge.get("id"), str):
            continue
        if edge.get("state") == "active":
            active.add(edge["id"])
        elif edge.get("state") == "broken":
            broken.add(edge["id"])
    for violation in inventory["violations"]:
        if isinstance(violation, dict) and isinstance(violation.get("id"), str):
            illegal.add(violation["id"])
    return {
        "active_ids": frozenset(active),
        "broken_ids": frozenset(broken),
        "illegal_ids": frozenset(illegal),
    }


def verify_checkpoint(
    root: Path,
    inventory_path: Path,
    expected_path: Path,
    *,
    inventory_verifier: InventoryVerifier = verify_inventory,
) -> list[str]:
    try:
        expected = load_checkpoint(expected_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"checkpoint: {error}"]
    try:
        inventory = load_inventory(inventory_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"inventory: {error}"]

    errors: list[str] = []
    actual = _inventory_id_sets(inventory)
    for field in CHECKPOINT_FIELDS:
        if actual[field] != expected[field]:
            errors.append(
                f"checkpoint: {field} actual={sorted(actual[field])} "
                f"expected={sorted(expected[field])}"
            )

    outcomes = inventory_verifier(root, inventory_path)
    expected_prefixes = {
        edge_id: f"{edge_id}: declared broken:" for edge_id in expected["broken_ids"]
    }
    expected_prefixes.update(
        {edge_id: f"{edge_id}: illegal edge:" for edge_id in expected["illegal_ids"]}
    )
    seen: set[str] = set()
    for outcome in outcomes:
        matching_id = next(
            (
                edge_id
                for edge_id, prefix in expected_prefixes.items()
                if outcome.startswith(prefix)
            ),
            None,
        )
        if matching_id is None:
            errors.append(f"compatibility: unexpected verifier error: {outcome}")
        else:
            seen.add(matching_id)
    for edge_id in sorted(expected_prefixes.keys() - seen):
        errors.append(f"compatibility: missing verifier outcome for {edge_id}")
    return sorted(set(errors))

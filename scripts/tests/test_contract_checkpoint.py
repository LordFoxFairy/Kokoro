from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.governance.contract_checkpoint import verify_checkpoint
from scripts.governance.handbook_examples import ROOT


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


@pytest.fixture()
def checkpoint_fixture(tmp_path: Path) -> tuple[Path, Path]:
    inventory_path = tmp_path / "inventory.json"
    expected_path = tmp_path / "expected.json"
    write_json(
        inventory_path,
        {
            "schema_version": 1,
            "edges": [
                {"id": "EDGE-ACTIVE", "state": "active"},
                {"id": "EDGE-BROKEN", "state": "broken"},
            ],
            "violations": [{"id": "EDGE-ILLEGAL"}],
        },
    )
    write_json(
        expected_path,
        {
            "schema_version": 1,
            "active_ids": ["EDGE-ACTIVE"],
            "broken_ids": ["EDGE-BROKEN"],
            "illegal_ids": ["EDGE-ILLEGAL"],
        },
    )
    return inventory_path, expected_path


def declared_outcomes(_root: Path, _inventory_path: Path) -> list[str]:
    return [
        "EDGE-BROKEN: declared broken: expected debt",
        "EDGE-ILLEGAL: illegal edge: expected violation",
    ]


def test_checkpoint_accepts_only_expected_declared_outcomes(
    checkpoint_fixture,
) -> None:
    inventory_path, expected_path = checkpoint_fixture

    assert (
        verify_checkpoint(
            ROOT,
            inventory_path,
            expected_path,
            inventory_verifier=declared_outcomes,
        )
        == []
    )


def test_checkpoint_rejects_count_preserving_id_swap(checkpoint_fixture) -> None:
    inventory_path, expected_path = checkpoint_fixture
    inventory = json.loads(inventory_path.read_text())
    inventory["edges"][0]["state"] = "broken"
    inventory["edges"][1]["state"] = "active"
    write_json(inventory_path, inventory)

    errors = verify_checkpoint(
        ROOT,
        inventory_path,
        expected_path,
        inventory_verifier=lambda _root, _path: [
            "EDGE-ACTIVE: declared broken: swapped"
        ],
    )

    assert any("active_ids" in error for error in errors)
    assert any("broken_ids" in error for error in errors)


def test_checkpoint_rejects_unexpected_compatibility_verifier_drift(
    checkpoint_fixture,
) -> None:
    inventory_path, expected_path = checkpoint_fixture

    errors = verify_checkpoint(
        ROOT,
        inventory_path,
        expected_path,
        inventory_verifier=lambda _root, _path: [
            *declared_outcomes(_root, _path),
            "EDGE-ACTIVE: evidence sha256 drift",
        ],
    )

    assert errors == [
        "compatibility: unexpected verifier error: EDGE-ACTIVE: evidence sha256 drift"
    ]


def test_checkpoint_rejects_missing_declared_outcome(checkpoint_fixture) -> None:
    inventory_path, expected_path = checkpoint_fixture

    errors = verify_checkpoint(
        ROOT,
        inventory_path,
        expected_path,
        inventory_verifier=lambda _root, _path: [],
    )

    assert any("missing verifier outcome for EDGE-BROKEN" in error for error in errors)
    assert any("missing verifier outcome for EDGE-ILLEGAL" in error for error in errors)


def test_checkpoint_rejects_overlapping_expected_ids(checkpoint_fixture) -> None:
    inventory_path, expected_path = checkpoint_fixture
    expected = json.loads(expected_path.read_text())
    expected["broken_ids"].append("EDGE-ACTIVE")
    write_json(expected_path, expected)

    errors = verify_checkpoint(
        ROOT,
        inventory_path,
        expected_path,
        inventory_verifier=declared_outcomes,
    )

    assert any("expected ID sets must be disjoint" in error for error in errors)


def test_contract_clis_report_invalid_producer_manifest_without_traceback(
    tmp_path: Path,
) -> None:
    inventory = json.loads(
        (ROOT / "verification/contracts/consumer-inventory.json").read_text()
    )
    active = inventory["edges"][0]
    package_evidence = next(
        evidence
        for evidence in active["evidence"]
        if evidence["path"] == "package.json"
    )
    active["protocol"] = "http-event"
    active["producer_runtime_assertion"] = {
        "declared_value": "go@1.26.8",
        "package_name": "go",
        "version": "1.26.8",
        "manifest_kind": "npm-package-json",
        "repository_path": active["owner"]["repository_path"],
        "repository_commit": active["owner"]["repository_commit"],
        "path": package_evidence["path"],
        "sha256": package_evidence["sha256"],
        "json_checks": [{"pointer": "/dependencies/go", "expected": "1.26.8"}],
    }
    inventory_path = tmp_path / "inventory.json"
    write_json(inventory_path, inventory)

    commands = [
        [
            sys.executable,
            str(ROOT / "scripts/verify-contract-compatibility.py"),
            "--inventory",
            str(inventory_path),
        ],
        [
            sys.executable,
            str(ROOT / "scripts/verify-contract-checkpoint.py"),
            "--inventory",
            str(inventory_path),
            "--expected",
            str(ROOT / "verification/contracts/checkpoints/w0b-start.json"),
        ],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        assert result.returncode == 1
        assert "Traceback" not in result.stderr
        payload = json.loads(result.stdout)
        assert any(
            "manifest_kind 'npm-package-json' is not allowed for "
            "producer_runtime_version" in error
            for error in payload["errors"]
        )


def test_w0b_checkpoint_files_match_frozen_plan_ids() -> None:
    checkpoints = ROOT / "verification/contracts/checkpoints"
    expected = {
        "w0b-start.json": {
            "schema_version": 1,
            "active_ids": ["EDGE-BROWSER-WEB"],
            "broken_ids": [
                "EDGE-WEB-BFF",
                "EDGE-BFF-IAM",
                "EDGE-BFF-SYSTEM",
                "EDGE-BFF-CAPABILITY",
                "EDGE-BFF-STORAGE",
                "EDGE-BFF-AGENT",
                "EDGE-BFF-SCHEDULER",
                "EDGE-BFF-BILLING",
                "EDGE-AGENT-SYSTEM",
                "EDGE-AGENT-CAPABILITY",
                "EDGE-AGENT-STORAGE",
                "EDGE-CAPABILITY-STORAGE",
                "EDGE-CAPABILITY-IAM",
                "EDGE-SCHEDULER-BFF",
                "EDGE-SCHEDULER-AGENT",
            ],
            "illegal_ids": ["EDGE-WEB-IAM-DIRECT"],
        },
        "w0b-capability.json": {
            "schema_version": 1,
            "active_ids": ["EDGE-BROWSER-WEB", "EDGE-BFF-CAPABILITY"],
            "broken_ids": [
                "EDGE-WEB-BFF",
                "EDGE-BFF-IAM",
                "EDGE-BFF-SYSTEM",
                "EDGE-BFF-STORAGE",
                "EDGE-BFF-AGENT",
                "EDGE-BFF-SCHEDULER",
                "EDGE-BFF-BILLING",
                "EDGE-AGENT-SYSTEM",
                "EDGE-AGENT-CAPABILITY",
                "EDGE-AGENT-STORAGE",
                "EDGE-CAPABILITY-STORAGE",
                "EDGE-CAPABILITY-IAM",
                "EDGE-SCHEDULER-BFF",
                "EDGE-SCHEDULER-AGENT",
            ],
            "illegal_ids": ["EDGE-WEB-IAM-DIRECT"],
        },
        "w0b-exit.json": {
            "schema_version": 1,
            "active_ids": [
                "EDGE-BROWSER-WEB",
                "EDGE-BFF-CAPABILITY",
                "EDGE-BFF-SCHEDULER",
                "EDGE-SCHEDULER-BFF",
            ],
            "broken_ids": [
                "EDGE-WEB-BFF",
                "EDGE-BFF-IAM",
                "EDGE-BFF-SYSTEM",
                "EDGE-BFF-STORAGE",
                "EDGE-BFF-AGENT",
                "EDGE-BFF-BILLING",
                "EDGE-AGENT-SYSTEM",
                "EDGE-AGENT-CAPABILITY",
                "EDGE-AGENT-STORAGE",
                "EDGE-CAPABILITY-STORAGE",
                "EDGE-CAPABILITY-IAM",
                "EDGE-SCHEDULER-AGENT",
            ],
            "illegal_ids": ["EDGE-WEB-IAM-DIRECT"],
        },
    }

    for filename, expected_document in expected.items():
        assert json.loads((checkpoints / filename).read_text()) == expected_document


def test_w1b_iam_checkpoint_is_one_edge_successor_of_w0b_exit() -> None:
    checkpoints = ROOT / "verification/contracts/checkpoints"
    previous = json.loads((checkpoints / "w0b-exit.json").read_text())
    current_path = checkpoints / "w1b-iam.json"
    current = json.loads(current_path.read_text())
    assert current["schema_version"] == previous["schema_version"] == 1
    assert set(current["active_ids"]) == set(previous["active_ids"]) | {"EDGE-BFF-IAM"}
    assert set(current["broken_ids"]) == set(previous["broken_ids"]) - {"EDGE-BFF-IAM"}
    assert current["illegal_ids"] == previous["illegal_ids"]
    assert verify_checkpoint(
        ROOT,
        ROOT / "verification/contracts/consumer-inventory.json",
        current_path,
    ) == []

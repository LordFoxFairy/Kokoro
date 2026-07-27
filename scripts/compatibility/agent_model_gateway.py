#!/usr/bin/env python3
"""Verify Platform model alias intent and Agent's real HTTP gateway adapter."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Final, Mapping

SCENARIO_ID: Final = "agent-model-gateway-localfake"
ASSERTIONS: Final = [
    "agent-model-gateway:http-invoke",
    "agent-model-gateway:http-stream",
    "agent-model-gateway:platform-alias",
    "agent-model-gateway:no-local-bypass",
]


def build_commands(root: Path) -> list[tuple[Path, list[str]]]:
    return [
        (
            root / "kokoro-agent",
            [
                "uv",
                "run",
                "--locked",
                "pytest",
                "tests/test_litellm_gateway.py::test_litellm_invoke_hits_gateway_with_key",
                "tests/test_litellm_gateway.py::test_litellm_streaming_over_gateway",
                "-q",
            ],
        ),
        (
            root / "kokoro-platform",
            [
                "pnpm",
                "--dir",
                "kokoro-model",
                "exec",
                "vitest",
                "run",
                "test/unit/builtin-catalog.test.ts",
            ],
        ),
    ]


def sanitized_environment(source: Mapping[str, str]) -> dict[str, str]:
    environment = dict(source)
    environment.pop("KOKORO_LOCAL_FAKE_MODEL", None)
    return environment


def build_result(exit_codes: list[int], *, duration_ms: int) -> dict[str, object]:
    if len(exit_codes) != 2:
        outcome = "fail"
        reason = "scenario_command_missing"
    elif exit_codes[0] != 0:
        outcome = "fail"
        reason = "agent_gateway_contract_failed"
    elif exit_codes[1] != 0:
        outcome = "fail"
        reason = "platform_model_contract_failed"
    else:
        outcome = "pass"
        reason = "ok"
    return {
        "schemaVersion": 1,
        "scenarioId": SCENARIO_ID,
        "outcome": outcome,
        "reasonCode": reason,
        "assertionIds": ASSERTIONS,
        "durationMs": max(0, duration_ms),
    }


def run(root: Path) -> dict[str, object]:
    started = time.monotonic()
    environment = sanitized_environment(os.environ)
    exit_codes: list[int] = []
    for cwd, command in build_commands(root):
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=150,
        )
        exit_codes.append(completed.returncode)
        if completed.returncode != 0:
            break
    return build_result(exit_codes, duration_ms=int((time.monotonic() - started) * 1000))


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    result = run(root)
    with os.fdopen(3, "w", encoding="utf-8", closefd=False) as machine:
        machine.write(json.dumps(result, separators=(",", ":")) + "\n")
        machine.flush()
    return 0 if result["outcome"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

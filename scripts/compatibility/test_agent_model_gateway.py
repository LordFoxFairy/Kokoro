from __future__ import annotations

from pathlib import Path

from scripts.compatibility.agent_model_gateway import (
    build_commands,
    build_result,
    sanitized_environment,
)


def test_commands_use_each_pinned_repository_lock_and_real_gateway_tests() -> None:
    root = Path("/repo")
    commands = build_commands(root)
    assert commands == [
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


def test_local_fake_bypass_is_removed_from_child_environment() -> None:
    env = sanitized_environment(
        {
            "PATH": "/bin",
            "KOKORO_LOCAL_FAKE_MODEL": "1",
            "EXAMPLE_TOKEN": "not-recorded",
        }
    )
    assert env["PATH"] == "/bin"
    assert "KOKORO_LOCAL_FAKE_MODEL" not in env
    assert env["EXAMPLE_TOKEN"] == "not-recorded"


def test_result_is_closed_and_requires_both_provider_and_consumer_checks() -> None:
    passed = build_result([0, 0], duration_ms=12)
    assert passed == {
        "schemaVersion": 1,
        "scenarioId": "agent-model-gateway-localfake",
        "outcome": "pass",
        "reasonCode": "ok",
        "assertionIds": [
            "agent-model-gateway:http-invoke",
            "agent-model-gateway:http-stream",
            "agent-model-gateway:platform-alias",
            "agent-model-gateway:no-local-bypass",
        ],
        "durationMs": 12,
    }
    failed = build_result([0, 1], duration_ms=9)
    assert failed["outcome"] == "fail"
    assert failed["reasonCode"] == "platform_model_contract_failed"
    assert "stdout" not in failed
    assert "stderr" not in failed

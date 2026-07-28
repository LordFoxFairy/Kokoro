from __future__ import annotations

from pathlib import Path

from scripts.compatibility.session_agent_durable import (
    build_agent_environment,
    build_result,
    build_session_environment,
)


LEASE = {
    "runId": "run_fixture",
    "mongo": {"database": "kokoro_test_run_fixture"},
    "redis": {"database": 11},
}


def test_environments_share_only_the_leased_transport_and_store() -> None:
    root = Path("/repo")
    scratch = root / "tmp/scenario"
    session = build_session_environment(
        LEASE,
        session_port=3901,
        hub_base_url="http://127.0.0.1:3902",
        scratch=scratch,
    )
    agent = build_agent_environment(LEASE, scratch=scratch)
    assert session["KOKORO_REDIS_URL"] == "redis://127.0.0.1:6379/11"
    assert agent["KOKORO_REDIS_URL"] == session["KOKORO_REDIS_URL"]
    assert agent["KOKORO_MONGO_DB"] == session["KOKORO_MESSAGE_STORE_MONGO_DB"]
    assert session["KOKORO_BILLING_MODE"] == "off"
    assert agent["KOKORO_LOCAL_FAKE_MODEL"] == "1"
    assert agent["KOKORO_LOCAL_FAKE_SCRIPT"] == "hitl"


def test_machine_result_requires_every_durable_assertion() -> None:
    passed = build_result(True, duration_ms=25)
    assert passed == {
        "schemaVersion": 1,
        "scenarioId": "session-agent-durable-localfake",
        "outcome": "pass",
        "reasonCode": "ok",
        "assertionIds": [
            "session-agent:admission-idempotency",
            "session-agent:durable-request-event",
            "session-agent:hitl-response",
            "session-agent:tool-approval",
            "session-agent:terminal",
            "session-agent:sse-replay",
        ],
        "durationMs": 25,
    }
    failed = build_result(False, duration_ms=3)
    assert failed["outcome"] == "fail"
    assert failed["reasonCode"] == "session_agent_live_failed"


def test_adapter_has_no_private_store_or_child_infra_operations() -> None:
    source = Path("scripts/compatibility/session_agent_durable.py").read_text()
    for forbidden in [
        "docker compose",
        'docker", "exec',
        "FLUSHDB",
        "dropDatabase",
        "billing_journal",
        "run_receipt_manifests",
        "XRANGE",
    ]:
        assert forbidden not in source

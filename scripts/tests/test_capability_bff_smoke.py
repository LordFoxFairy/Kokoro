from __future__ import annotations

import json
import os
from pathlib import Path
import signal
from types import SimpleNamespace
import subprocess
import sys

import pytest

from scripts.e2e import run_capability_bff_smoke as smoke


class Recorder:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.fail_create_for: str | None = None
        self.scan_output = ""
        self.fail_unlink = False

    def __call__(self, command: list[str], **_kwargs: object) -> str:
        self.commands.append(command)
        if self.fail_create_for and any(
            f'CREATE DATABASE "{self.fail_create_for}"' in value for value in command
        ):
            raise smoke.SmokeError("database creation failed")
        if "--scan" in command:
            return self.scan_output
        if "UNLINK" in command and self.fail_unlink:
            raise smoke.SmokeError("redis command failed")
        return ""


def resources(recorder: Recorder) -> smoke.OwnedResources:
    return smoke.OwnedResources(
        "postgresql://localhost/postgres",
        "redis://127.0.0.1:6379",
        "a" * 24,
        command=recorder,
    )


def test_parser_requires_all_four_explicit_flags() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/e2e/run_capability_bff_smoke.py"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--postgres-admin-url" in result.stderr
    assert "--redis-url" in result.stderr
    assert "--bff-node-bin" in result.stderr
    assert "--capability-node-bin" in result.stderr


@pytest.mark.parametrize(
    ("postgres", "redis"),
    [
        ("http://localhost/postgres", "redis://localhost"),
        ("postgresql://localhost/postgres", "http://localhost"),
        ("file:///tmp/postgres", "rediss://localhost"),
    ],
)
def test_rejects_non_database_url_schemes(postgres: str, redis: str) -> None:
    with pytest.raises(smoke.SmokeError, match="endpoint"):
        smoke.OwnedResources(postgres, redis, "a" * 24, command=Recorder())


@pytest.mark.parametrize("run_id", ["", "*", "../", "a" * 23, "A" * 24])
def test_rejects_unsafe_run_identity(run_id: str) -> None:
    recorder = Recorder()
    with pytest.raises(smoke.SmokeError, match="identity"):
        smoke.OwnedResources(
            "postgresql://localhost/postgres",
            "redis://localhost",
            run_id,
            command=recorder,
        )
    assert recorder.commands == []


def test_database_names_and_redis_prefix_are_exact() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    capability = owned.create_database("capability")
    bff = owned.create_database("bff")
    assert capability.endswith("/w0b_cap_" + "a" * 24 + "_capability")
    assert bff.endswith("/w0b_cap_" + "a" * 24 + "_bff")
    assert owned.redis_prefix == "kokoro:w0b:capability:" + "a" * 24 + ":"
    assert "FLUSH" not in str(recorder.commands)


def test_redis_prefix_claim_is_exact_and_expiring() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    recorder_output = "OK"

    def command(args: list[str], **_kwargs: object) -> str:
        recorder.commands.append(args)
        return recorder_output

    owned.command = command
    owned.claim_redis_prefix()
    assert recorder.commands[-1][-6:] == [
        "SET",
        "kokoro:w0b:capability:" + "a" * 24 + ":ownership",
        "a" * 24,
        "NX",
        "EX",
        "600",
    ]


def test_failed_create_is_not_registered_and_cleanup_drops_only_owned_database() -> (
    None
):
    recorder = Recorder()
    owned = resources(recorder)
    capability_name = "w0b_cap_" + "a" * 24 + "_capability"
    recorder.fail_create_for = capability_name
    with pytest.raises(smoke.SmokeError):
        owned.create_database("capability")
    recorder.fail_create_for = None
    owned.create_database("bff")
    owned.cleanup()
    drops = [item[-1] for item in recorder.commands if "DROP DATABASE" in item[-1]]
    assert drops == ['DROP DATABASE "w0b_cap_' + "a" * 24 + '_bff" WITH (FORCE)']
    assert owned.created_databases == []


def test_cleanup_rejects_out_of_prefix_redis_key_before_unlink() -> None:
    recorder = Recorder()
    recorder.scan_output = "shared:important\n"
    owned = resources(recorder)
    owned.redis_claimed = True
    owned.redis_was_claimed = True
    with pytest.raises(smoke.SmokeError, match="Redis cleanup"):
        owned.cleanup()
    assert not any("UNLINK" in command for command in recorder.commands)


def test_command_level_redis_failure_still_drops_owned_database() -> None:
    recorder = Recorder()
    recorder.scan_output = "kokoro:w0b:capability:" + "a" * 24 + ":one\n"
    recorder.fail_unlink = True
    owned = resources(recorder)
    owned.redis_claimed = True
    owned.redis_was_claimed = True
    owned.create_database("capability")
    with pytest.raises(smoke.SmokeError, match="Redis cleanup"):
        owned.cleanup()
    assert any("DROP DATABASE" in command[-1] for command in recorder.commands)
    assert owned.created_databases == []


def test_failed_redis_claim_never_cleans_an_unowned_prefix() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    with pytest.raises(smoke.SmokeError, match="claimed"):
        owned.claim_redis_prefix()
    owned.cleanup()
    assert not any("--scan" in command for command in recorder.commands)
    assert not any("UNLINK" in command for command in recorder.commands)


def test_owned_command_timeout_kills_the_process_group(tmp_path: Path) -> None:
    pid_file = tmp_path / "pid"
    source = (
        "import os,time; "
        f"open({str(pid_file)!r},'w').write(str(os.getpid())); "
        "time.sleep(120)"
    )
    with (tmp_path / "command.log").open("wb") as log:
        with pytest.raises(smoke.SmokeError, match="deadline"):
            smoke.run_owned_command(
                [sys.executable, "-c", source],
                cwd=tmp_path,
                env=dict(os.environ),
                log=log,
                timeout=0.2,
            )
    with pytest.raises(ProcessLookupError):
        os.killpg(int(pid_file.read_text()), 0)


def test_node_toolchain_requires_the_exact_frozen_version(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "node").touch()
    (tmp_path / "corepack").touch()
    monkeypatch.setattr(smoke, "command_output", lambda *_args, **_kwargs: "v22.99.0\n")
    with pytest.raises(smoke.SmokeError, match="v22.22.2"):
        smoke.node_environment(str(tmp_path), "v22.22.2")


def test_readiness_timeout_and_malformed_body_are_sanitized(monkeypatch) -> None:
    monkeypatch.setattr(
        smoke,
        "http_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(smoke.SmokeError("bad")),
    )
    process = SimpleNamespace(poll=lambda: None)
    with pytest.raises(smoke.SmokeError, match="ready"):
        smoke.wait_ready("http://127.0.0.1:1", process, timeout=0.03, poll=0.005)

    monkeypatch.setattr(
        smoke, "http_json", lambda *_args, **_kwargs: ({"bad": True}, {})
    )
    with pytest.raises(smoke.SmokeError, match="malformed"):
        smoke.wait_ready("http://127.0.0.1:1", process, timeout=0.03, poll=0.005)


def test_readiness_reports_child_early_exit(monkeypatch) -> None:
    monkeypatch.setattr(smoke, "http_json", lambda *_args, **_kwargs: ({}, {}))
    with pytest.raises(smoke.SmokeError, match="exited"):
        smoke.wait_ready(
            "http://127.0.0.1:1",
            SimpleNamespace(poll=lambda: 1),
            timeout=0.03,
            poll=0.005,
        )


def test_process_cleanup_handles_dead_leader_and_escalates(monkeypatch) -> None:
    states = iter([True, True, False])
    sent: list[int] = []
    monkeypatch.setattr(smoke, "process_group_exists", lambda _pid: next(states))
    monkeypatch.setattr(smoke.os, "killpg", lambda _pid, sig: sent.append(sig))
    monkeypatch.setattr(smoke.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(smoke.time, "monotonic", iter([0.0, 20.0, 20.0, 20.0]).__next__)
    smoke.stop_owned_process(SimpleNamespace(pid=123, poll=lambda: 0))
    assert sent == [signal.SIGTERM, signal.SIGKILL]


def test_process_cleanup_stops_child_after_leader_exits() -> None:
    leader = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import subprocess,sys; "
            "subprocess.Popen([sys.executable,'-c','import time; time.sleep(120)'], "
            "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)",
        ],
        start_new_session=True,
    )
    leader.wait(timeout=5)
    try:
        smoke.stop_owned_process(leader)
        with pytest.raises(ProcessLookupError):
            os.killpg(leader.pid, 0)
    finally:
        try:
            os.killpg(leader.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def test_run_smoke_cleans_all_registered_resources_after_midflight_failure(
    monkeypatch,
) -> None:
    events: list[str] = []

    class FakeResources(smoke.OwnedResources):
        def __init__(self, *_args: object) -> None:
            self.redis_key_present = False
            self.databases: set[str] = set()
            super().__init__(
                "postgresql://localhost/postgres",
                "redis://localhost",
                "a" * 24,
                command=self.record_command,
            )

        def record_command(self, args: list[str], **_kwargs: object) -> str:
            text = args[-1]
            if "PING" in args:
                return "PONG"
            if "SET" in args:
                self.redis_key_present = True
                events.append("claim-redis")
                return "OK"
            if "--scan" in args:
                return (
                    self.redis_prefix + "ownership\n" if self.redis_key_present else ""
                )
            if "UNLINK" in args:
                assert args[-1] == self.redis_prefix + "ownership"
                self.redis_key_present = False
                events.append("unlink-exact-redis")
                return ""
            if "CREATE DATABASE" in text:
                name = text.split('"')[1]
                self.databases.add(name)
                events.append(f"create-{name.rsplit('_', 1)[1]}")
                return ""
            if "DROP DATABASE" in text:
                name = text.split('"')[1]
                self.databases.remove(name)
                events.append(f"drop-{name.rsplit('_', 1)[1]}")
                return ""
            if "SELECT datname" in text:
                return next((name for name in self.databases if name in text), "")
            return ""

        def verify_clean(self) -> None:
            super().verify_clean()
            events.append("verify-clean")

    processes = [
        SimpleNamespace(pid=101, name="capability", poll=lambda: None),
        SimpleNamespace(pid=102, name="bff", poll=lambda: None),
    ]

    monkeypatch.setattr(smoke, "verify_release", lambda *_args: None)
    monkeypatch.setattr(
        smoke,
        "node_environment",
        lambda *_args: (Path("/fake/node"), {}),
    )
    monkeypatch.setattr(smoke, "OwnedResources", FakeResources)
    monkeypatch.setattr(smoke, "distinct_ports", lambda _count: [41001, 41002, 41003])
    monkeypatch.setattr(smoke, "install_schema", lambda *_args: None)
    monkeypatch.setattr(
        smoke,
        "start_process",
        lambda *_args: processes.pop(0),
    )
    monkeypatch.setattr(smoke, "wait_ready", lambda *_args: None)
    monkeypatch.setattr(
        smoke,
        "stop_owned_process",
        lambda process: events.append(f"stop-{process.name}"),
    )

    def fail(stage: str) -> None:
        assert stage == "after-processes-started"
        events.append("fault")
        raise smoke.SmokeError("injected failure")

    args = SimpleNamespace(
        postgres_admin_url="postgresql://localhost/postgres",
        redis_url="redis://localhost",
        bff_node_bin="/node22",
        capability_node_bin="/node24",
    )
    with pytest.raises(smoke.SmokeError, match="injected"):
        smoke.run_smoke(args, fault_injection=fail)

    assert events == [
        "claim-redis",
        "create-capability",
        "create-bff",
        "fault",
        "stop-bff",
        "stop-capability",
        "unlink-exact-redis",
        "drop-bff",
        "drop-capability",
        "verify-clean",
    ]


def test_failure_output_never_contains_credentials_tokens_or_payload() -> None:
    secrets = [
        "postgresql://user:password@localhost/postgres",
        "redis://:cache-secret@localhost:6379",
        "owner-token-value",
        '{"raw":"response-payload"}',
    ]
    output = smoke.failure_summary(RuntimeError(" ".join(secrets)), secrets)
    assert output == {"status": "FAIL", "error": "smoke execution failed"}
    assert not any(secret in json.dumps(output) for secret in secrets)


def test_eight_case_summary_is_an_invariant() -> None:
    cases = [f"case-{index}" for index in range(8)]
    assert smoke.success_summary(cases)["cases"] == 8
    with pytest.raises(smoke.SmokeError, match="eight"):
        smoke.success_summary(cases[:-1])


def test_legacy_q_rejection_does_not_advance_owner_log_count(tmp_path: Path) -> None:
    log = tmp_path / "capability.log"
    log.write_text(
        '{"event":"request.completed","trace_id":"query-forwarded",'
        '"operation":"GET /v1/skills"}\n',
        encoding="utf-8",
    )
    before = smoke.owner_request_count(log)
    assert before == 1
    assert smoke.owner_request_count(log) == before


def test_owner_log_evidence_requires_exact_operation_for_request_id(
    tmp_path: Path,
) -> None:
    log = tmp_path / "capability.log"
    log.write_text(
        '{"event":"request.completed","trace_id":"same-id",'
        '"operation":"GET /v1/mcp/servers"}\n',
        encoding="utf-8",
    )
    assert smoke.owner_request_count(log, "same-id", "GET /v1/mcp/servers") == 1
    assert smoke.owner_request_count(log, "same-id", "GET /v1/skills") == 0

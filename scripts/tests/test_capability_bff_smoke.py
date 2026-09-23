from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import socket
import threading
from threading import Thread
import time
from types import SimpleNamespace
import subprocess
import sys

import pytest

from scripts.e2e import run_capability_bff_smoke as smoke
from scripts.e2e import capability_bff_smoke_runtime as runtime


class Recorder:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.fail_create_for: str | None = None
        self.fail_queries = False
        self.fail_scan = False
        self.fail_unlink = False
        self.scan_output: str | None = None
        self.set_result = "OK"
        self.databases: set[str] = set()
        self.redis_values: dict[str, str] = {}

    def __call__(self, command: list[str], **_kwargs: object) -> str:
        self.commands.append(command)
        joined = " ".join(command)
        if self.fail_create_for and any(
            f'CREATE DATABASE "{self.fail_create_for}"' in value for value in command
        ):
            raise runtime.SmokeError("database creation failed")
        if "CREATE DATABASE" in joined:
            self.databases.add(joined.split('"')[1])
        elif "DROP DATABASE" in joined:
            self.databases.discard(joined.split('"')[1])
        elif "SELECT datname" in joined:
            if self.fail_queries:
                raise runtime.SmokeError("database inventory unavailable")
            return next((name for name in self.databases if name in joined), "")
        elif " SET " in f" {joined} ":
            if self.set_result == "OK":
                self.redis_values[command[-5]] = command[-4]
            return self.set_result
        elif " GET " in f" {joined} ":
            if self.fail_queries:
                raise runtime.SmokeError("redis inventory unavailable")
            return self.redis_values.get(command[-1], "")
        if "--scan" in command:
            if self.fail_scan:
                raise runtime.SmokeError("redis prefix inventory unavailable")
            if self.scan_output is not None:
                return self.scan_output
            prefix = command[-1][:-1]
            return "\n".join(key for key in self.redis_values if key.startswith(prefix))
        if "UNLINK" in command and self.fail_unlink:
            raise runtime.SmokeError("redis command failed")
        if "UNLINK" in command:
            for key in command[command.index("UNLINK") + 1 :]:
                self.redis_values.pop(key, None)
        return ""


class AcknowledgementLossRecorder(Recorder):
    def __init__(self, resource: str, *, fail_queries: bool = False) -> None:
        super().__init__()
        self.resource = resource
        self.fail_queries_after_loss = fail_queries
        self.ack_lost = False

    def __call__(self, command: list[str], **kwargs: object) -> str:
        joined = " ".join(command)
        if self.resource == "database" and "CREATE DATABASE" in joined:
            self.commands.append(command)
            self.databases.add(joined.split('"')[1])
            self.ack_lost = True
            raise runtime.SmokeError("database acknowledgement lost")
        if self.resource == "database" and "SELECT datname" in joined:
            if self.fail_queries_after_loss and self.ack_lost:
                raise runtime.SmokeError("database inventory unavailable")
        if self.resource == "redis" and " SET " in f" {joined} ":
            self.commands.append(command)
            self.redis_values[command[-5]] = command[-4]
            self.ack_lost = True
            raise runtime.SmokeError("redis acknowledgement lost")
        if self.resource == "redis" and " GET " in f" {joined} ":
            if self.fail_queries_after_loss and self.ack_lost:
                raise runtime.SmokeError("redis inventory unavailable")
        return super().__call__(command, **kwargs)


def resources(recorder: Recorder) -> runtime.OwnedResources:
    return runtime.OwnedResources(
        "postgresql://localhost/postgres?options=-csearch_path%3Dpublic",
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
    with pytest.raises(runtime.SmokeError, match="endpoint"):
        runtime.OwnedResources(postgres, redis, "a" * 24, command=Recorder())


@pytest.mark.parametrize("run_id", ["", "*", "../", "a" * 23, "A" * 24])
def test_rejects_unsafe_run_identity(run_id: str) -> None:
    recorder = Recorder()
    with pytest.raises(runtime.SmokeError, match="identity"):
        runtime.OwnedResources(
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
    assert "/w0b_cap_" + "a" * 24 + "_capability" in capability
    assert "/w0b_cap_" + "a" * 24 + "_bff" in bff
    assert "options=" not in capability
    assert owned.redis_prefix == "kokoro:w0b:capability:" + "a" * 24 + ":"
    assert "FLUSH" not in str(recorder.commands)


def test_redis_prefix_claim_is_exact_and_expiring() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    recorder_output = "OK"

    def command(args: list[str], **_kwargs: object) -> str:
        recorder.commands.append(args)
        if "--scan" in args:
            return ""
        if "GET" in args:
            return ""
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
    with pytest.raises(runtime.SmokeError):
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
    recorder.redis_values[owned.redis_prefix + "ownership"] = owned.run_id
    owned.redis_claimed = True
    owned.redis_was_claimed = True
    with pytest.raises(runtime.SmokeError, match="Redis cleanup"):
        owned.cleanup()
    assert not any("UNLINK" in command for command in recorder.commands)


def test_command_level_redis_failure_still_drops_owned_database() -> None:
    recorder = Recorder()
    recorder.redis_values["kokoro:w0b:capability:" + "a" * 24 + ":one"] = "value"
    recorder.fail_unlink = True
    owned = resources(recorder)
    recorder.redis_values[owned.redis_prefix + "ownership"] = owned.run_id
    owned.redis_claimed = True
    owned.redis_was_claimed = True
    owned.create_database("capability")
    with pytest.raises(runtime.SmokeError, match="Redis cleanup"):
        owned.cleanup()
    assert any("DROP DATABASE" in command[-1] for command in recorder.commands)
    assert owned.created_databases == []


def test_failed_redis_claim_never_cleans_an_unowned_prefix() -> None:
    recorder = Recorder()
    recorder.set_result = ""
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="claimed"):
        owned.claim_redis_prefix()
    owned.cleanup()
    assert sum("--scan" in command for command in recorder.commands) == 1
    assert not any("UNLINK" in command for command in recorder.commands)


def test_database_ack_loss_reconciles_exact_identity_and_cleans_it() -> None:
    recorder = AcknowledgementLossRecorder("database")
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="acknowledgement lost"):
        owned.create_database("capability")
    owned.cleanup()
    owned.verify_clean()
    assert recorder.databases == set()


def test_database_preexisting_identity_is_never_created_or_dropped() -> None:
    recorder = Recorder()
    name = "w0b_cap_" + "a" * 24 + "_capability"
    recorder.databases.add(name)
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="already exists"):
        owned.create_database("capability")
    owned.cleanup()
    assert recorder.databases == {name}
    assert not any(
        "CREATE DATABASE" in " ".join(command) for command in recorder.commands
    )
    assert not any(
        "DROP DATABASE" in " ".join(command) for command in recorder.commands
    )


def test_database_unknown_reconciliation_still_cleans_owned_redis() -> None:
    recorder = AcknowledgementLossRecorder("database", fail_queries=True)
    owned = resources(recorder)
    owned.claim_redis_prefix()
    with pytest.raises(runtime.SmokeError, match="acknowledgement lost"):
        owned.create_database("capability")
    with pytest.raises(runtime.SmokeError, match="PostgreSQL.*reconciliation"):
        owned.cleanup()
    assert recorder.redis_values == {}


def test_redis_ack_loss_reconciles_exact_ownership_and_cleans_it() -> None:
    recorder = AcknowledgementLossRecorder("redis")
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="acknowledgement lost"):
        owned.claim_redis_prefix()
    owned.cleanup()
    owned.verify_clean()
    assert recorder.redis_values == {}


def test_redis_preexisting_ownership_is_never_replaced_or_unlinked() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    ownership = owned.redis_prefix + "ownership"
    recorder.redis_values[ownership] = "someone-else"
    with pytest.raises(runtime.SmokeError, match="already exists"):
        owned.claim_redis_prefix()
    owned.cleanup()
    assert recorder.redis_values == {ownership: "someone-else"}
    assert not any("SET" in command for command in recorder.commands)
    assert not any("UNLINK" in command for command in recorder.commands)


def test_redis_markerless_preexisting_prefix_is_never_claimed_or_unlinked() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    foreign_key = owned.redis_prefix + "preexisting"
    recorder.redis_values[foreign_key] = "foreign-value"
    with pytest.raises(runtime.SmokeError, match="already exists"):
        owned.claim_redis_prefix()
    owned.cleanup()
    assert recorder.redis_values == {foreign_key: "foreign-value"}
    assert not any("SET" in command for command in recorder.commands)
    assert not any("UNLINK" in command for command in recorder.commands)


def test_redis_unknown_prefix_inventory_fails_closed_before_set() -> None:
    recorder = Recorder()
    recorder.fail_scan = True
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="inventory"):
        owned.claim_redis_prefix()
    owned.cleanup()
    assert not any("SET" in command for command in recorder.commands)
    assert not any("UNLINK" in command for command in recorder.commands)


def test_redis_unknown_reconciliation_still_drops_owned_database() -> None:
    recorder = AcknowledgementLossRecorder("redis", fail_queries=True)
    owned = resources(recorder)
    owned.create_database("bff")
    with pytest.raises(runtime.SmokeError, match="acknowledgement lost"):
        owned.claim_redis_prefix()
    with pytest.raises(runtime.SmokeError, match="Redis.*reconciliation"):
        owned.cleanup()
    assert recorder.databases == set()


def _request_threads_after(baseline: set[int]) -> list[Thread]:
    return [
        thread
        for thread in threading.enumerate()
        if thread.ident not in baseline and "process_request_thread" in thread.name
    ]


def test_readiness_fixture_drains_partial_header_without_stderr(
    capfd: pytest.CaptureFixture[str],
) -> None:
    baseline = {thread.ident for thread in threading.enumerate()}
    client: socket.socket | None = None
    try:
        with runtime.dependency_readiness_fixture() as base_url:
            port = int(base_url.rsplit(":", 1)[1])
            client = socket.create_connection(("127.0.0.1", port), timeout=2)
            client.sendall(b"GET /readyz HTTP/1.1\r\nHost: 127.0.0.1")
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline and not _request_threads_after(baseline):
                time.sleep(0.01)
            assert _request_threads_after(baseline)
        assert _request_threads_after(baseline) == []
        assert capfd.readouterr().err == ""
    finally:
        if client is not None:
            client.close()
        for thread in _request_threads_after(baseline):
            thread.join(timeout=2)


def test_readiness_fixture_keeps_unexpected_handler_errors_observable(
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    baseline = {thread.ident for thread in threading.enumerate()}

    def raise_unexpected(_handler: object) -> None:
        raise RuntimeError("unexpected readiness handler failure")

    monkeypatch.setattr(runtime._DependencyHandler, "do_GET", raise_unexpected)
    with runtime.dependency_readiness_fixture() as base_url:
        port = int(base_url.rsplit(":", 1)[1])
        with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
            client.sendall(b"GET /readyz HTTP/1.0\r\n\r\n")
            assert client.recv(1) == b""
    captured = capfd.readouterr()
    assert "unexpected readiness handler failure" in captured.err
    assert _request_threads_after(baseline) == []


def test_capability_release_pin_rejects_every_other_sha(
    tmp_path: Path, monkeypatch
) -> None:
    accepted = "9c88d0d934387b590bc74dae0179a587292e0253"
    assert smoke.CAPABILITY_RELEASE == accepted
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "main.js").touch()
    monkeypatch.setattr(runtime, "command_output", lambda *_args, **_kwargs: "0" * 40)
    with pytest.raises(runtime.SmokeError, match="frozen smoke input"):
        runtime.verify_release(tmp_path, accepted)


def test_capability_environment_overrides_inherited_wildcard_host() -> None:
    inherited = {"KOKORO_CAPABILITY_HOST": "0.0.0.0"}
    actual = smoke._capability_environment(
        inherited,
        "postgresql://localhost/owned",
        "redis://localhost/6",
        41001,
        "http://127.0.0.1:41002",
        "rpc-fixture",
        "owner-fixture",
    )
    assert actual["KOKORO_CAPABILITY_HOST"] == "127.0.0.1"
    assert inherited == {"KOKORO_CAPABILITY_HOST": "0.0.0.0"}


def test_bff_release_pin_rejects_every_other_sha(tmp_path: Path, monkeypatch) -> None:
    accepted = "804a5832c066ce60dde9f4592856ac40ce20f402"
    assert smoke.BFF_RELEASE == accepted
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "main.js").touch()
    monkeypatch.setattr(runtime, "command_output", lambda *_args, **_kwargs: "0" * 40)
    with pytest.raises(runtime.SmokeError, match="frozen smoke input"):
        runtime.verify_release(tmp_path, accepted)


def test_user_headers_use_bearer_without_self_asserted_identity() -> None:
    headers = smoke.bff_headers(
        "service-secret", "tenant-a", "user-a", "request-1", "session-token"
    )
    assert headers == {
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": "service-secret",
        "x-kokoro-request-id": "request-1",
        "authorization": "Bearer session-token",
    }


def test_owned_command_timeout_kills_the_process_group(tmp_path: Path) -> None:
    pid_file = tmp_path / "pid"
    source = (
        "import os,time; "
        f"open({str(pid_file)!r},'w').write(str(os.getpid())); "
        "time.sleep(120)"
    )
    with (tmp_path / "command.log").open("wb") as log:
        with pytest.raises(runtime.SmokeError, match="deadline"):
            runtime.run_owned_command(
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
    monkeypatch.setattr(
        runtime, "command_output", lambda *_args, **_kwargs: "v22.99.0\n"
    )
    with pytest.raises(runtime.SmokeError, match="v22.22.2"):
        runtime.node_environment(str(tmp_path), "v22.22.2")


def test_readiness_timeout_and_malformed_body_are_sanitized(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime,
        "http_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(runtime.SmokeError("bad")),
    )
    process = SimpleNamespace(poll=lambda: None)
    with pytest.raises(runtime.SmokeError, match="ready"):
        runtime.wait_ready("http://127.0.0.1:1", process, timeout=0.03, poll=0.005)

    monkeypatch.setattr(
        runtime, "http_json", lambda *_args, **_kwargs: ({"bad": True}, {})
    )
    with pytest.raises(runtime.SmokeError, match="malformed"):
        runtime.wait_ready("http://127.0.0.1:1", process, timeout=0.03, poll=0.005)


def test_readiness_reports_child_early_exit(monkeypatch) -> None:
    monkeypatch.setattr(runtime, "http_json", lambda *_args, **_kwargs: ({}, {}))
    with pytest.raises(runtime.SmokeError, match="exited"):
        runtime.wait_ready(
            "http://127.0.0.1:1",
            SimpleNamespace(poll=lambda: 1),
            timeout=0.03,
            poll=0.005,
        )


def test_process_cleanup_handles_dead_leader_and_escalates(monkeypatch) -> None:
    states = iter([True, True, False])
    sent: list[int] = []
    monkeypatch.setattr(runtime, "process_group_exists", lambda _pid: next(states))
    monkeypatch.setattr(runtime.os, "killpg", lambda _pid, sig: sent.append(sig))
    monkeypatch.setattr(runtime.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        runtime.time, "monotonic", iter([0.0, 20.0, 20.0, 20.0]).__next__
    )
    runtime.stop_owned_process(SimpleNamespace(pid=123, poll=lambda: 0))
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
        runtime.stop_owned_process(leader)
        with pytest.raises(ProcessLookupError):
            os.killpg(leader.pid, 0)
    finally:
        try:
            os.killpg(leader.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _midflight_resource_type(events: list[str]) -> type[runtime.OwnedResources]:
    class FakeResources(runtime.OwnedResources):
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
            if "GET" in args:
                return self.run_id if self.redis_key_present else ""
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

    return FakeResources


def test_run_smoke_cleans_all_registered_resources_after_midflight_failure(
    monkeypatch,
) -> None:
    events: list[str] = []

    processes = [
        SimpleNamespace(pid=101, name="capability", poll=lambda: None),
        SimpleNamespace(pid=102, name="bff", poll=lambda: None),
    ]

    monkeypatch.setattr(runtime, "verify_release", lambda *_args: None)
    monkeypatch.setattr(
        runtime,
        "node_environment",
        lambda *_args: (Path("/fake/node"), {}),
    )
    monkeypatch.setattr(runtime, "OwnedResources", _midflight_resource_type(events))
    monkeypatch.setattr(runtime, "distinct_ports", lambda _count: [41001, 41002, 41003])
    monkeypatch.setattr(runtime, "install_schema", lambda *_args: None)
    monkeypatch.setattr(
        runtime,
        "start_process",
        lambda *_args: processes.pop(0),
    )
    monkeypatch.setattr(runtime, "wait_ready", lambda *_args: None)
    monkeypatch.setattr(
        runtime,
        "stop_owned_process",
        lambda process: events.append(f"stop-{process.name}"),
    )

    def fail(stage: str) -> None:
        assert stage == "after-processes-started"
        events.append("fault")
        raise runtime.SmokeError("injected failure")

    args = SimpleNamespace(
        postgres_admin_url="postgresql://localhost/postgres",
        redis_url="redis://localhost",
        bff_node_bin="/node22",
        capability_node_bin="/node24",
    )
    with pytest.raises(runtime.SmokeError, match="injected"):
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
    with pytest.raises(runtime.SmokeError, match="eight"):
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

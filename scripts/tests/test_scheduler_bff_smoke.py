from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
import subprocess
import sys

import pytest

from scripts.e2e import run_scheduler_bff_smoke as smoke
from scripts.e2e import scheduler_bff_smoke_cases as case_owner
from scripts.e2e import scheduler_bff_smoke_http as http
from scripts.e2e import scheduler_bff_smoke_runtime as runtime

LOOPBACK_BINDING = ("fixture-host.local", "127.0.0.1", "127.0.0.1/32")


class Recorder:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.rows = ""
        self.redis_values: dict[str, str] = {}
        self.databases: set[str] = set()

    def __call__(self, command: list[str], **_kwargs: object) -> str:
        self.commands.append(command)
        joined = " ".join(command)
        if "CREATE DATABASE" in joined:
            self.databases.add(joined.split('"')[1])
        elif "DROP DATABASE" in joined:
            self.databases.discard(joined.split('"')[1])
        elif "SELECT datname" in joined:
            return next((name for name in self.databases if name in joined), "")
        elif "SELECT occurrence_id" in joined:
            return self.rows
        elif " SET " in f" {joined} ":
            self.redis_values[command[-5]] = command[-4]
            return "OK"
        elif "UNLINK" in command:
            for key in command[command.index("UNLINK") + 1 :]:
                self.redis_values.pop(key, None)
        elif "EXISTS" in command:
            return str(
                sum(
                    key in self.redis_values
                    for key in command[command.index("EXISTS") + 1 :]
                )
            )
        elif "GET" in command:
            return self.redis_values.get(command[-1], "")
        elif "--scan" in command:
            prefix = command[-1][:-1]
            return "\n".join(key for key in self.redis_values if key.startswith(prefix))
        elif "PING" in command:
            return "PONG"
        return ""


class AcknowledgementLossRecorder(Recorder):
    def __init__(self, resource: str, *, fail_queries: bool = False) -> None:
        super().__init__()
        self.resource = resource
        self.fail_queries = fail_queries
        self.ack_lost = False

    def __call__(self, command: list[str], **kwargs: object) -> str:
        joined = " ".join(command)
        if self.resource == "database" and "CREATE DATABASE" in joined:
            self.commands.append(command)
            self.databases.add(joined.split('"')[1])
            self.ack_lost = True
            raise runtime.SmokeError("database acknowledgement lost")
        if self.resource == "database" and "SELECT datname" in joined:
            if self.fail_queries and self.ack_lost:
                raise runtime.SmokeError("database inventory unavailable")
        if self.resource == "redis" and " SET " in f" {joined} ":
            self.commands.append(command)
            self.redis_values[command[-5]] = command[-4]
            self.ack_lost = True
            raise runtime.SmokeError("redis acknowledgement lost")
        if self.resource == "redis" and " GET " in f" {joined} ":
            if self.fail_queries and self.ack_lost:
                raise runtime.SmokeError("redis inventory unavailable")
            self.commands.append(command)
            return self.redis_values.get(command[-1], "")
        return super().__call__(command, **kwargs)


def resources(recorder: Recorder) -> runtime.OwnedResources:
    return runtime.OwnedResources(
        "postgresql://localhost/postgres?options=-csearch_path%3Dpublic",
        "redis://127.0.0.1:6379/7",
        "a" * 24,
        command=recorder,
    )


def test_parser_requires_all_four_explicit_flags() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/e2e/run_scheduler_bff_smoke.py"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    for flag in ("--postgres-admin-url", "--redis-url", "--bff-node-bin", "--go-bin"):
        assert flag in result.stderr


@pytest.mark.parametrize(
    ("postgres", "redis"),
    [
        ("http://localhost/postgres", "redis://localhost/7"),
        ("postgresql://localhost/postgres", "redis://localhost/8"),
        ("postgresql://localhost/postgres", "http://localhost/7"),
    ],
)
def test_requires_postgres_and_scheduler_redis_db_seven(
    postgres: str, redis: str
) -> None:
    with pytest.raises(runtime.SmokeError, match="endpoint|DB 7"):
        runtime.OwnedResources(postgres, redis, "a" * 24, command=Recorder())


@pytest.mark.parametrize("run_id", ["", "../", "*", "A" * 24, "a" * 23])
def test_rejects_unsafe_run_identity(run_id: str) -> None:
    with pytest.raises(runtime.SmokeError, match="identity"):
        runtime.OwnedResources(
            "postgresql://localhost/postgres",
            "redis://localhost/7",
            run_id,
            command=Recorder(),
        )


def test_database_names_redis_databases_and_harness_prefix_are_exact() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    scheduler = owned.create_database("scheduler")
    bff = owned.create_database("bff")
    assert "/w0b_sched_" + "a" * 24 + "_scheduler" in scheduler
    assert "/w0b_sched_" + "a" * 24 + "_bff" in bff
    assert "search_path%3Dpublic%2Cpg_catalog" in scheduler
    assert owned.scheduler_redis_url.endswith("/7")
    assert owned.bff_redis_url.endswith("/8")
    assert owned.redis_prefix == "kokoro:w0b:scheduler:" + "a" * 24 + ":"
    assert "FLUSH" not in str(recorder.commands)


def test_native_scheduler_keys_are_derived_only_from_private_tenant_rows() -> None:
    recorder = Recorder()
    recorder.rows = (
        "00000000-0000-0000-0000-000000000001\n00000000-0000-0000-0000-000000000002\n"
    )
    owned = resources(recorder)
    scheduler_url = owned.create_database("scheduler")
    owned.register_native_keys(scheduler_url, "tenant-a")
    expected = {
        runtime.native_dispatch_key("tenant-a", "00000000-0000-0000-0000-000000000001"),
        runtime.native_dispatch_key("tenant-a", "00000000-0000-0000-0000-000000000002"),
    }
    assert owned.native_redis_keys == expected
    query = next(
        command[-1]
        for command in recorder.commands
        if "SELECT occurrence_id" in command[-1]
    )
    assert "tenant_id = 'tenant-a'" in query
    assert not any(
        "kokoro:scheduler:dispatch:*" in value
        for command in recorder.commands
        for value in command
    )


def test_cleanup_unlinks_only_harness_and_registered_native_keys_then_drops_databases() -> (
    None
):
    recorder = Recorder()
    owned = resources(recorder)
    scheduler_url = owned.create_database("scheduler")
    owned.create_database("bff")
    owned.claim_harness_prefix()
    recorder.rows = "00000000-0000-0000-0000-000000000001\n"
    owned.register_native_keys(scheduler_url, "tenant-a")
    native = next(iter(owned.native_redis_keys))
    recorder.redis_values[native] = "lease"
    owned.cleanup()
    owned.verify_clean()
    unlinks = [command for command in recorder.commands if "UNLINK" in command]
    assert any(native in command for command in unlinks)
    assert any(owned.redis_prefix + "ownership" in command for command in unlinks)
    assert not any("kokoro:scheduler:dispatch:*" in command for command in unlinks)
    drops = [
        command[-1] for command in recorder.commands if "DROP DATABASE" in command[-1]
    ]
    assert drops[0].endswith('_bff" WITH (FORCE)')
    assert drops[1].endswith('_scheduler" WITH (FORCE)')


def test_database_ack_loss_reconciles_exact_identity_and_cleans_it() -> None:
    recorder = AcknowledgementLossRecorder("database")
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="acknowledgement lost"):
        owned.create_database("scheduler")
    owned.cleanup()
    owned.verify_clean()
    assert recorder.databases == set()


def test_database_preexisting_identity_is_never_created_or_dropped() -> None:
    recorder = Recorder()
    name = "w0b_sched_" + "a" * 24 + "_scheduler"
    recorder.databases.add(name)
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="already exists"):
        owned.create_database("scheduler")
    owned.cleanup()
    assert recorder.databases == {name}
    assert not any(
        "CREATE DATABASE" in " ".join(command) for command in recorder.commands
    )
    assert not any(
        "DROP DATABASE" in " ".join(command) for command in recorder.commands
    )


def test_database_ack_loss_with_unknown_inventory_fails_cleanup_closed() -> None:
    recorder = AcknowledgementLossRecorder("database", fail_queries=True)
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="acknowledgement lost"):
        owned.create_database("scheduler")
    with pytest.raises(runtime.SmokeError, match="PostgreSQL.*reconciliation"):
        owned.cleanup()


def test_redis_ack_loss_reconciles_random_ownership_value_and_cleans_it() -> None:
    recorder = AcknowledgementLossRecorder("redis")
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="acknowledgement lost"):
        owned.claim_harness_prefix()
    owned.cleanup()
    owned.verify_clean()
    assert recorder.redis_values == {}


def test_redis_preexisting_ownership_is_never_replaced_or_unlinked() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    ownership = owned.redis_prefix + "ownership"
    recorder.redis_values[ownership] = "someone-else"
    with pytest.raises(runtime.SmokeError, match="already exists"):
        owned.claim_harness_prefix()
    owned.cleanup()
    assert recorder.redis_values == {ownership: "someone-else"}
    assert not any("SET" in command for command in recorder.commands)
    assert not any("UNLINK" in command for command in recorder.commands)


def test_redis_ack_loss_with_unknown_inventory_fails_cleanup_closed() -> None:
    recorder = AcknowledgementLossRecorder("redis", fail_queries=True)
    owned = resources(recorder)
    with pytest.raises(runtime.SmokeError, match="acknowledgement lost"):
        owned.claim_harness_prefix()
    with pytest.raises(runtime.SmokeError, match="Redis.*reconciliation"):
        owned.cleanup()


def test_owned_command_timeout_kills_the_process_group(tmp_path: Path) -> None:
    pid_file = tmp_path / "pid"
    source = f"import os,time;open({str(pid_file)!r},'w').write(str(os.getpid()));time.sleep(120)"
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


def test_manual_replay_recomputes_content_length_for_changed_payload() -> None:
    with http.agent_receipt_stub() as target:
        call = http.ProxyCall(
            "/v1/runs",
            "POST",
            {"content-type": "application/json", "content-length": "999"},
            b"{}",
            202,
        )
        changed = json.dumps({"run_id": "run-replay"}).encode()
        result = case_owner.replay_proxy_call(
            target.base_url, call, changed, expected=202
        )
        assert result.status == 202


@pytest.mark.parametrize("duplicate_run", [False, True])
def test_agent_admission_rejects_same_or_different_run_second_call(
    duplicate_run: bool,
) -> None:
    tenant, task = "tenant-a", "scheduled-task-a"
    callback = http.ProxyCall(
        "/internal/bff/scheduled-tasks/dispatch",
        "POST",
        {
            "x-kokoro-scheduler-schedule": case_owner.schedule_name(task),
            "x-kokoro-scheduler-occurrence": "2026-09-22T12:00:00.123Z",
        },
        b"{}",
        202,
    )
    expected_run = case_owner.expected_agent_run_id(tenant, callback)
    first = http.AgentCall(
        expected_run,
        "request-a",
        {"run_id": expected_run, "session_id": f"scheduled:{task}"},
    )
    duplicate_id = expected_run if duplicate_run else "run_bff_different"
    second = http.AgentCall(
        duplicate_id,
        "request-b",
        {"run_id": duplicate_id, "session_id": f"scheduled:{task}"},
    )
    assert (
        case_owner.assert_single_agent_admission((), (first,), tenant, task, callback)
        == first
    )
    with pytest.raises(runtime.SmokeError, match="exactly one Agent admission"):
        case_owner.assert_single_agent_admission(
            (), (first, second), tenant, task, callback
        )


@pytest.mark.parametrize("duplicate_run", [False, True])
def test_agent_snapshot_detects_same_or_different_run_after_acceptance(
    duplicate_run: bool,
) -> None:
    first = http.AgentCall(
        "run-original",
        "request-a",
        {"run_id": "run-original", "session_id": "scheduled:task-a"},
    )
    duplicate_id = "run-original" if duplicate_run else "run-different"
    second = http.AgentCall(
        duplicate_id,
        "request-b",
        {"run_id": duplicate_id, "session_id": "scheduled:task-a"},
    )
    with pytest.raises(runtime.SmokeError, match="additional Agent admission"):
        case_owner.assert_agent_snapshot_unchanged((first,), (first, second))


def test_temporary_go_binary_is_removed_after_midflight_failure(
    monkeypatch, tmp_path: Path
) -> None:
    binary = tmp_path / "scheduler-smoke"
    binary.write_bytes(b"fixture")
    monkeypatch.setattr(smoke, "build_scheduler", lambda *_args, **_kwargs: binary)
    monkeypatch.setattr(smoke, "verify_inputs", lambda *_args, **_kwargs: ({}, {}))
    monkeypatch.setattr(smoke, "callback_binding", lambda: LOOPBACK_BINDING)
    monkeypatch.setattr(
        smoke,
        "OwnedResources",
        lambda *_args, **_kwargs: SimpleNamespace(
            cleanup=lambda: None, verify_clean=lambda: None
        ),
    )
    with pytest.raises(runtime.SmokeError, match="injected"):
        smoke.run_smoke(
            SimpleNamespace(
                postgres_admin_url="postgresql://localhost/postgres",
                redis_url="redis://localhost/7",
                bff_node_bin="/node",
                go_bin="/go",
            ),
            work_directory=tmp_path,
            fault_injection=lambda stage: (_ for _ in ()).throw(
                runtime.SmokeError(f"injected at {stage}")
            ),
        )
    assert not binary.exists()


def test_restart_sequence_stops_old_bff_before_starting_replacement(
    monkeypatch,
) -> None:
    events: list[str] = []
    old = SimpleNamespace(pid=10, poll=lambda: None, name="old")
    new = SimpleNamespace(pid=11, poll=lambda: None, name="new")
    monkeypatch.setattr(
        smoke,
        "stop_owned_process",
        lambda process: events.append(f"stop-{process.name}"),
    )
    monkeypatch.setattr(
        smoke,
        "start_process",
        lambda *_args, **_kwargs: events.append("start-new") or new,
    )
    restarted = smoke.restart_bff(old, Path("/node"), {}, Path("."), None)
    assert restarted is new
    assert events == ["stop-old", "start-new"]


def test_release_verification_is_fail_closed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(smoke, "command_output", lambda *_args, **_kwargs: "wrong\n")
    with pytest.raises(runtime.SmokeError, match="release"):
        smoke.verify_release(tmp_path, "expected")


def test_toolchain_check_resolves_pnpm_from_the_frozen_bff_checkout(
    tmp_path: Path, monkeypatch
) -> None:
    args = _toolchain_args(tmp_path)
    calls, output = _toolchain_output()
    monkeypatch.setattr(smoke, "command_output", output)
    smoke.verify_inputs(args, "release", "release")
    pnpm_call = next(call for call in calls if "pnpm" in call[0])
    assert pnpm_call[1] == smoke.BFF


def _toolchain_args(tmp_path: Path) -> SimpleNamespace:
    node_dir = tmp_path / "node-bin"
    node_dir.mkdir()
    for name in ("node", "corepack"):
        (node_dir / name).touch()
    go = tmp_path / "go"
    go.touch()
    return SimpleNamespace(bff_node_bin=str(node_dir), go_bin=str(go))


def _toolchain_output(
    *,
    node_version: str = "v22.22.2",
    pnpm_version: str = "11.25.0",
    go_version: str = "go version go1.26.8 darwin/arm64",
) -> tuple[list[tuple[list[str], Path]], Callable[..., str]]:
    calls: list[tuple[list[str], Path]] = []

    def output(command: list[str], **kwargs: object) -> str:
        calls.append((command, kwargs.get("cwd", runtime.ROOT)))
        if "rev-parse" in command:
            return "release\n"
        if "status" in command:
            return ""
        if command[-1] == "--version" and command[0].endswith("node"):
            return node_version + "\n"
        if "pnpm" in command:
            return pnpm_version + "\n"
        if command[-1] == "version":
            return go_version + "\n"
        return "auto\n"

    return calls, output


@pytest.mark.parametrize(
    "go_version",
    [
        "go version go1.26.80 darwin/arm64",
        "go version devel go1.26.8-buildfixture darwin/arm64",
        "go version go1.26.8rc1 darwin/arm64",
        "go version go1.26.8beta1 darwin/arm64",
    ],
)
def test_toolchain_rejects_non_exact_stable_go_token(
    tmp_path: Path, monkeypatch, go_version: str
) -> None:
    args = _toolchain_args(tmp_path)
    _, output = _toolchain_output(go_version=go_version)
    monkeypatch.setattr(smoke, "command_output", output)
    with pytest.raises(runtime.SmokeError, match="Go 1.26.8"):
        smoke.verify_inputs(args, "release", "release")


@pytest.mark.parametrize(
    ("node_version", "pnpm_version", "message"),
    [
        ("v22.22.20", "11.25.0", "Node v22.22.2"),
        ("v22.22.2", "11.25.00", "pnpm 11.25.0"),
    ],
)
def test_toolchain_rejects_non_exact_node_or_pnpm(
    tmp_path: Path,
    monkeypatch,
    node_version: str,
    pnpm_version: str,
    message: str,
) -> None:
    args = _toolchain_args(tmp_path)
    _, output = _toolchain_output(node_version=node_version, pnpm_version=pnpm_version)
    monkeypatch.setattr(smoke, "command_output", output)
    with pytest.raises(runtime.SmokeError, match=re.escape(message)):
        smoke.verify_inputs(args, "release", "release")


def test_readiness_accepts_scheduler_owner_envelope(monkeypatch) -> None:
    monkeypatch.setattr(
        smoke,
        "http_json",
        lambda *_args, **_kwargs: case_owner.HTTPResult(
            200,
            {
                "data": {"status": "ok", "service": "kokoro-scheduler"},
                "meta": {"request_id": "probe"},
            },
            {},
        ),
    )
    smoke.wait_ready(
        "http://127.0.0.1:1",
        SimpleNamespace(poll=lambda: None),
        timeout=0.02,
    )


@pytest.mark.parametrize(
    ("addresses", "expected"),
    [
        (["192.168.1.9"], None),
        (["10.0.0.9", "127.0.0.1"], LOOPBACK_BINDING),
    ],
)
def test_callback_binding_requires_and_prefers_loopback(
    monkeypatch, addresses: list[str], expected: tuple[str, str, str] | None
) -> None:
    monkeypatch.setattr(smoke.socket, "gethostname", lambda: "fixture-host.local")
    answers = [
        (smoke.socket.AF_INET, smoke.socket.SOCK_STREAM, 6, "", (address, 0))
        for address in addresses
    ]
    monkeypatch.setattr(smoke.socket, "getaddrinfo", lambda *_args, **_kwargs: answers)
    if expected is None:
        with pytest.raises(runtime.SmokeError, match="loopback"):
            smoke.callback_binding()
    else:
        assert smoke.callback_binding() == expected


def test_private_sql_suppresses_command_tags_for_returning_rows(monkeypatch) -> None:
    commands: list[list[str]] = []

    def output(command: list[str], **_kwargs: object) -> str:
        commands.append(command)
        return "row\n"

    monkeypatch.setattr(case_owner, "command_output", output)
    query = case_owner.sql(
        "postgresql://localhost/private", "UPDATE owned RETURNING id"
    )
    assert query == "row"
    assert "-q" in commands[0]


def test_eleven_case_summary_declares_agent_stub_limit() -> None:
    cases = [{"name": name, "status": "PASS"} for name in smoke.EXPECTED_CASES]
    releases = {"bff": "b", "scheduler": "s"}
    summary = smoke.success_summary(cases, releases, {"cleanup": "verified"})
    assert summary["status"] == "PASS"
    assert summary["cases"] == 11
    assert summary["agent_evidence"] == "deterministic receipt stub; not a real Agent"
    assert "known_risks" not in summary
    with pytest.raises(runtime.SmokeError, match="eleven"):
        smoke.success_summary(cases[:-1], {}, {})


def test_failure_output_is_sanitized() -> None:
    secrets = ["postgresql://u:p@h/d", "redis://:p@h/7", "token-value"]
    output = smoke.failure_summary(RuntimeError(" ".join(secrets)), secrets)
    assert output == {"status": "FAIL", "error": "smoke execution failed"}
    assert not any(secret in json.dumps(output) for secret in secrets)

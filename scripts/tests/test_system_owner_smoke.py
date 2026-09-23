from __future__ import annotations

import subprocess
import os
import signal
import sys
from types import SimpleNamespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from scripts.e2e.run_system_owner_smoke import (
    OwnedResources,
    SmokeError,
    http_json,
    seed_control_plane,
    stop_owned_process,
    run_owned_command,
    process_group_exists,
)


class Recorder:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.fail_create = False

    def __call__(self, command: list[str]) -> str:
        self.commands.append(command)
        if self.fail_create and any("CREATE DATABASE" in value for value in command):
            raise SmokeError("database creation failed")
        return ""


def fixture(recorder: Recorder) -> OwnedResources:
    return OwnedResources(
        "postgresql://localhost/postgres",
        "redis://localhost:6379/2",
        "a" * 24,
        command=recorder,
    )


def test_creates_unique_databases_without_resetting_shared_state() -> None:
    recorder = Recorder()
    resources = fixture(recorder)
    url = resources.create_database("system")
    assert url.endswith("/system_smoke_" + "a" * 24 + "_system")
    assert len(recorder.commands) == 1
    assert "CREATE DATABASE" in recorder.commands[0][-1]
    assert "DROP" not in str(recorder.commands)
    assert "FLUSH" not in str(recorder.commands)


def test_failed_create_is_never_registered_for_drop() -> None:
    recorder = Recorder()
    recorder.fail_create = True
    resources = fixture(recorder)
    with pytest.raises(SmokeError):
        resources.create_database("system")
    resources.cleanup()
    assert "DROP DATABASE" not in str(recorder.commands)


def test_cleanup_drops_only_successfully_created_databases() -> None:
    recorder = Recorder()
    resources = fixture(recorder)
    resources.create_database("bff")
    resources.cleanup()
    drops = [c[-1] for c in recorder.commands if "DROP DATABASE" in c[-1]]
    assert drops == ['DROP DATABASE "system_smoke_' + "a" * 24 + '_bff" WITH (FORCE)']
    assert resources.created_databases == []


def test_redis_cleanup_demands_command_level_failure_exit_status() -> None:
    recorded: list[list[str]] = []

    def command(args: list[str]) -> str:
        recorded.append(args)
        return (
            "kokoro:system-smoke:" + "a" * 24 + ":manifest\n"
            if "--scan" in args
            else ""
        )

    resources = OwnedResources(
        "postgresql://localhost/postgres",
        "redis://localhost/2",
        "a" * 24,
        command=command,
    )
    resources.cleanup()
    assert any("UNLINK" in args for args in recorded)
    assert all("-e" in args for args in recorded)


def test_process_cleanup_stops_children_after_leader_has_exited() -> None:
    # The child inherits the group but not stdout. Its leader exits immediately.
    leader = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time; time.sleep(120)'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)",
        ],
        start_new_session=True,
    )
    leader.wait(timeout=5)
    try:
        stop_owned_process(leader)
        with pytest.raises(ProcessLookupError):
            os.killpg(leader.pid, 0)
    finally:
        try:
            os.killpg(leader.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def test_schema_command_timeout_cleans_its_owned_process_group(tmp_path) -> None:
    pid_file = tmp_path / "pid"
    source = f"import os,time; open({str(pid_file)!r},'w').write(str(os.getpid())); time.sleep(120)"
    with (tmp_path / "log").open("wb") as log:
        with pytest.raises(SmokeError, match="deadline"):
            run_owned_command(
                [sys.executable, "-c", source],
                cwd=tmp_path,
                env=dict(os.environ),
                log=log,
                timeout=0.2,
            )
    with pytest.raises(ProcessLookupError):
        os.killpg(int(pid_file.read_text()), 0)


def test_cache_command_failure_still_cleans_owned_databases_and_fails() -> None:
    recorder = Recorder()

    def command(args: list[str]) -> str:
        recorder(args)
        if "--scan" in args:
            return "kokoro:system-smoke:" + "a" * 24 + ":manifest\n"
        if "UNLINK" in args:
            raise SmokeError("redis command failure")
        return ""

    resources = OwnedResources(
        "postgresql://localhost/postgres",
        "redis://localhost/2",
        "a" * 24,
        command=command,
    )
    resources.create_database("system")
    with pytest.raises(SmokeError, match="Redis cleanup failed"):
        resources.cleanup()
    assert any("DROP DATABASE" in args[-1] for args in recorder.commands)
    assert resources.created_databases == []


@pytest.mark.parametrize(
    "failure",
    [subprocess.CalledProcessError(1, "ps"), subprocess.TimeoutExpired("ps", 3)],
)
def test_process_inventory_failures_use_the_cleanup_error_boundary(
    monkeypatch, failure
) -> None:
    def fail(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr("scripts.e2e.run_system_owner_smoke.subprocess.run", fail)
    with pytest.raises(SmokeError, match="inventory"):
        process_group_exists(12345)


def test_process_inventory_failure_does_not_skip_registered_database_cleanup(
    monkeypatch,
) -> None:
    from scripts.e2e import run_system_owner_smoke as smoke

    recorder = Recorder()

    def command(args: list[str]) -> str:
        recorder(args)
        return "PONG" if "PING" in args else ""

    resources = OwnedResources(
        "postgresql://localhost/postgres",
        "redis://localhost/2",
        "a" * 24,
        command=command,
    )
    monkeypatch.setattr(smoke, "OwnedResources", lambda *_args: resources)
    monkeypatch.setattr(smoke, "verify_release_inputs", lambda: {})
    monkeypatch.setattr(smoke, "node_environment", lambda *_args: {})
    monkeypatch.setattr(smoke, "run_owned_command", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(
        smoke.subprocess,
        "Popen",
        lambda *_args, **_kwargs: SimpleNamespace(pid=12345, poll=lambda: None),
    )
    monkeypatch.setattr(smoke, "wait_ready", lambda *_args: None)

    def bad_seed(*_args):
        raise SmokeError("seed failed")

    def failed_inventory(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("ps", 3)

    monkeypatch.setattr(smoke, "seed_control_plane", bad_seed)
    monkeypatch.setattr(smoke.subprocess, "run", failed_inventory)
    with pytest.raises(SmokeError, match="process shutdown failed"):
        smoke.run_smoke(
            SimpleNamespace(
                node24_bin="",
                node22_bin="",
                postgres=resources.postgres,
                redis=resources.redis,
            )
        )
    assert resources.created_databases == []
    assert sum("DROP DATABASE" in args[-1] for args in recorder.commands) == 2


@pytest.mark.parametrize("identifier", ["", "*", "../", "a" * 23, "A" * 24])
def test_rejects_unsafe_run_identity_before_any_command(identifier: str) -> None:
    recorder = Recorder()
    with pytest.raises(SmokeError):
        OwnedResources(
            "postgresql://localhost/postgres",
            "redis://localhost/2",
            identifier,
            command=recorder,
        )
    assert recorder.commands == []


def test_rejects_arbitrary_database_owners() -> None:
    recorder = Recorder()
    with pytest.raises(SmokeError):
        fixture(recorder).create_database('system"; DROP DATABASE postgres; --')
    assert recorder.commands == []


def test_cache_cleanup_rejects_a_key_outside_the_owned_prefix() -> None:
    recorder = Recorder()

    def scan_other_key(command: list[str]) -> str:
        recorder(command)
        return "user:important\n" if "--scan" in command else ""

    resources = OwnedResources(
        "postgresql://localhost/postgres",
        "redis://localhost/2",
        "a" * 24,
        command=scan_other_key,
    )
    with pytest.raises(SmokeError):
        resources.cleanup()
    assert not any("UNLINK" in command for command in recorder.commands)


def test_entrypoint_help_does_not_touch_infrastructure() -> None:
    result = subprocess.run(
        ["python3", "scripts/e2e/run_system_owner_smoke.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "System" in result.stdout


def test_http_smoke_does_not_follow_owner_redirects() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/success")
                self.end_headers()
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"data":{}}')

        def log_message(self, *_: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with pytest.raises(SmokeError, match="returned 302"):
                http_json(f"http://127.0.0.1:{server.server_port}", "/redirect")
        finally:
            server.shutdown()
            thread.join()


def test_seed_uses_formal_http_and_scoped_preconditions(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []

    def http(_base: str, path: str, **kwargs) -> dict:
        calls.append((path, kwargs))
        return {"data": {"id": str(len(calls)), "version": "1"}}

    monkeypatch.setattr("scripts.e2e.run_system_owner_smoke.http_json", http)
    values = seed_control_plane("http://system.test", "tenant", "token", "a" * 24)
    assert values["feature_key"] == "chat." + "a" * 24
    assert values["release_id"]
    assert len(calls) == 22
    released = [
        kw["body"]
        for path, kw in calls
        if path.endswith("/config") and kw["body"]["release_id"]
    ]
    assert len(released) == 1
    # Presentation legitimately overrides theme; use references to prove release content.
    assert released[0]["module_key"] == "references"
    assert released[0]["config_key"] == "references"
    assert released[0]["value"][0]["resource_id"] == "published-" + "a" * 24
    for path, kwargs in calls:
        headers = kwargs["headers"]
        assert path.startswith("/v1/system/")
        assert headers["x-kokoro-service"] == "system-admin"
        assert headers["idempotency-key"]
        if kwargs["method"] == "PUT":
            assert headers["if-none-match"] == "*"
        if path.endswith(("/publish", "/validate")):
            assert headers["if-match"] == '"1"'
    assert "x-kokoro-tenant-id" not in calls[0][1]["headers"]
    assert calls[1][1]["headers"]["x-kokoro-tenant-id"] == "tenant"


def test_consumer_smoke_checks_manifest_and_catalog_tenant_isolation(
    monkeypatch,
) -> None:
    from scripts.e2e.run_system_owner_smoke import verify_read_consumers

    values = {
        "hostname": "site.localhost",
        "feature_key": "chat.smoke",
        "label_key": "opaque",
        "product_key": "smoke",
        "site_id": "site",
        "release_id": "release",
        "published_reference": "released",
    }
    manifest = {
        "tenant_id": "tenant",
        "site_id": "site",
        "release_id": "release",
        "references": [
            {"key": "artifact_store", "owner": "storage", "resource_id": "released"}
        ],
        "navigation": [{"key": "chat"}],
        "feature_flags": [{"key": "chat.smoke", "enabled": True}],
    }
    denied_manifests = set()
    seen_models: list[dict[str, str]] = []
    seen_manifest_headers: list[dict[str, str]] = []

    def http(base: str, path: str, **kwargs) -> dict:
        headers = kwargs["headers"]
        other = headers.get("x-kokoro-tenant-id") == "tenant-other"
        if "runtime-manifest" in path:
            if base == "http://bff.test":
                seen_manifest_headers.append(headers)
                return {"data": manifest}
            if other:
                assert kwargs["expected"] == 404
                denied_manifests.add(base)
                return {"error": {"code": "NOT_FOUND"}}
            return {"data": manifest}
        if path.endswith("/resolve"):
            assert other and kwargs["expected"] == 403
            return {"error": {"code": "FORBIDDEN"}}
        if path.startswith("/v1/models?"):
            seen_models.append(headers)
            return {
                "data": {
                    "models": []
                    if headers.get("authorization") == "Bearer token-b"
                    else [{"name": "opaque", "is_default": True}]
                }
            }
        return {"data": {"items": [] if other else [{"is_default": True}]}}

    monkeypatch.setattr("scripts.e2e.run_system_owner_smoke.http_json", http)
    verify_read_consumers(
        "http://system.test",
        "http://bff.test",
        "tenant",
        values,
        "bff-token",
        "web-token",
        "token-a",
        "token-b",
    )
    assert denied_manifests == {"http://system.test"}
    assert [headers["authorization"] for headers in seen_models] == [
        "Bearer token-a",
        "Bearer token-b",
    ]
    assert all(
        "x-kokoro-namespace" not in headers and "x-kokoro-principal-id" not in headers
        for headers in seen_models
    )
    assert len(seen_manifest_headers) == 2
    assert seen_manifest_headers[1]["x-kokoro-namespace"] == "tenant-other"
    assert seen_manifest_headers[1]["authorization"] == "Bearer token-b"


def test_runtime_evidence_distinguishes_commits_from_dirty_checkouts(
    monkeypatch,
) -> None:
    from scripts.e2e import run_system_owner_smoke as smoke

    def git(command: list[str]) -> str:
        assert "/apps/" in command[2]
        owner = command[2].rsplit("/", 1)[1]
        if command[3:] == ["rev-parse", "HEAD"]:
            return owner + "-sha\n"
        assert command[3:] == ["status", "--porcelain", "--untracked-files=normal"]
        return " M src/main.ts\n" if owner == "kokoro-system" else ""

    monkeypatch.setattr(smoke, "command_output", git)
    states = smoke.repository_evidence()
    assert states["kokoro-system"] == {
        "commit": "kokoro-system-sha",
        "working_tree_dirty": True,
    }
    assert states["kokoro-bff"] == {
        "commit": "kokoro-bff-sha",
        "working_tree_dirty": False,
    }
    assert states["kokoro-agent"] == {
        "commit": "kokoro-agent-sha",
        "working_tree_dirty": False,
    }


def test_release_inputs_require_exact_clean_head_and_index_gitlinks(
    monkeypatch, tmp_path
) -> None:
    from scripts.e2e import run_system_owner_smoke as smoke

    expected = smoke.EXPECTED_RELEASES
    assert expected["kokoro-bff"] == "a4dbc3339448c7ee8763b0f82d1c0ae4c213bf87"
    apps = tmp_path / "apps"
    apps.mkdir()
    for owner in expected:
        (apps / owner).mkdir()
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    calls: list[list[str]] = []
    changed_owner = "kokoro-bff"
    state = {
        "source_sha": expected[changed_owner],
        "source_dirty": False,
        "head_sha": expected[changed_owner],
        "head_mode": "160000",
        "index_sha": expected[changed_owner],
        "index_mode": "160000",
    }

    def git(command: list[str]) -> str:
        calls.append(command)
        if command[3:5] == ["ls-tree", "HEAD"]:
            owner = command[-1].rsplit("/", 1)[1]
            return f"{state['head_mode'] if owner == changed_owner else '160000'} commit {state['head_sha'] if owner == changed_owner else expected[owner]}\tapps/{owner}\n"
        if command[3:6] == ["ls-files", "--stage", "--"]:
            owner = command[-1].rsplit("/", 1)[1]
            return f"{state['index_mode'] if owner == changed_owner else '160000'} {state['index_sha'] if owner == changed_owner else expected[owner]} 0\tapps/{owner}\n"
        owner = command[2].rsplit("/", 1)[1]
        if command[3:] == ["rev-parse", "HEAD"]:
            return (
                state["source_sha"] if owner == changed_owner else expected[owner]
            ) + "\n"
        if command[3:] == ["status", "--porcelain", "--untracked-files=normal"]:
            return (
                " M src/main.ts\n"
                if owner == changed_owner and state["source_dirty"]
                else ""
            )
        raise AssertionError(command)

    monkeypatch.setattr(smoke, "command_output", git)
    assert smoke.verify_release_inputs() == {
        owner: {"commit": sha, "working_tree_dirty": False}
        for owner, sha in expected.items()
    }
    assert any("ls-tree" in command for command in calls)
    assert any("ls-files" in command for command in calls)

    for field, value in (
        ("source_sha", "0" * 40),
        ("source_dirty", True),
        ("head_sha", "0" * 40),
        ("head_mode", "100644"),
        ("index_sha", "0" * 40),
        ("index_mode", "120000"),
    ):
        original = state[field]
        state[field] = value
        with pytest.raises(SmokeError, match="release"):
            smoke.verify_release_inputs()
        state[field] = original

    (apps / changed_owner).rmdir()
    (apps / changed_owner).symlink_to(apps / "kokoro-system", target_is_directory=True)
    with pytest.raises(SmokeError, match="release"):
        smoke.verify_release_inputs()
    (apps / changed_owner).unlink()
    with pytest.raises(SmokeError, match="release"):
        smoke.verify_release_inputs()

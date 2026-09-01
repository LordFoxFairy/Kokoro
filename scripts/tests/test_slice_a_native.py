from __future__ import annotations

import hashlib
import errno
import json
import os
import stat
import subprocess
import sys
import signal
import socket
import time
from pathlib import Path

import pytest

import scripts.slice_a.guardian as guardian_module
import scripts.slice_a.native as native_module

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.slice_a.create_fixture_dir import create_fixture_directory
from scripts.slice_a.create_secrets import SECRET_FILES, create_secret_directory
from scripts.slice_a.native import (
    BACKEND_PROCESSES,
    DEFAULT_COMMITS,
    DEFAULT_TREES,
    ProcessSpec,
    _ensure_port_free,
    _free_ports,
    _grpc_health_probe,
    _minimal_environment,
    _owner_alive,
    _stop_process_inventory,
    _redact_text,
    _service_specs,
    _spawn,
    _stop_process,
    build_litellm_command,
    build_service_commands,
    find_postgres_18_bin,
    validate_candidate,
)
from scripts.slice_a.seed import (
    SITE_ID,
    bootstrap_model,
    build_model_manifest,
    build_site_contexts,
    select_site_context,
)


def _guardian_ports() -> dict[str, int]:
    return {
        "postgres": 55432,
        "redis": 56379,
        "model-fixture": 54001,
        "litellm": 4000,
        "iam": 7202,
        "model": 7203,
        "capability": 7204,
        "agent": 7206,
        "chat": 7205,
    }


def test_leaderless_owned_group_escalates_until_the_entire_group_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signals: list[signal.Signals] = []
    monkeypatch.setattr(guardian_module, "_process_facts", lambda _pid: None)
    monkeypatch.setattr(
        guardian_module,
        "group_alive",
        lambda _pgid: not signals or signals[-1] != signal.SIGKILL,
    )
    monkeypatch.setattr(
        os, "killpg", lambda _pgid, sent: signals.append(signal.Signals(sent))
    )

    guardian_module.stop_owned_group(
        pid=1234, pgid=1234, session_id=1234, identity="recorded", timeout=0
    )

    assert signals == [signal.SIGTERM, signal.SIGKILL]


def test_pid_reuse_and_unknown_identity_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    facts = guardian_module.ProcessFacts(1234, 1234, 1234, "live", "precise")
    monkeypatch.setattr(guardian_module, "_process_facts", lambda _pid: facts)
    with pytest.raises(RuntimeError, match="identity mismatch"):
        guardian_module.stop_owned_group(
            pid=1234, pgid=1234, session_id=1234, identity="stale"
        )
    monkeypatch.setattr(
        guardian_module,
        "_process_facts",
        lambda _pid: (_ for _ in ()).throw(RuntimeError("identity unknown")),
    )
    with pytest.raises(RuntimeError, match="identity unknown"):
        guardian_module.identity_matches(1234, "recorded")


def test_process_inventory_cleanup_attempts_every_owned_group_and_redacts_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempted: list[int] = []

    def stop(process: object) -> None:
        pid = int(getattr(process, "pid"))
        attempted.append(pid)
        if pid == 1:
            raise RuntimeError("SECRET cleanup failure")

    monkeypatch.setattr("scripts.slice_a.native._stop_process", stop)
    errors = _stop_process_inventory(
        {
            "first": type("Process", (), {"pid": 1})(),
            "second": type("Process", (), {"pid": 2})(),
        },
        frozenset({"SECRET"}),
    )
    assert attempted == [2, 1]
    assert errors == ["first: RuntimeError: [REDACTED] cleanup failure"]


def test_secret_manifest_has_only_independent_credentials_and_matching_rsa_keypair(
    tmp_path: Path,
) -> None:
    target = tmp_path / "secrets"
    create_secret_directory(target)

    assert set(SECRET_FILES) == {
        "web.workload-token",
        "chat.workload-token",
        "agent.workload-token",
        "iam.refresh-derivation-key",
        "web.session-key",
        "litellm.api-key",
        "iam.jwt-private.pem",
        "iam.jwt-public.pem",
    }
    assert {path.name for path in target.iterdir()} == set(SECRET_FILES) | {
        ".kokoro-slice-a-owner"
    }
    for name in SECRET_FILES:
        mode = stat.S_IMODE((target / name).stat().st_mode)
        assert mode == (0o644 if name == "iam.jwt-public.pem" else 0o600)
    hex_values = [
        (target / name).read_text()
        for name in SECRET_FILES
        if name.endswith("token") or name.endswith("key") or name == "litellm.api-key"
    ]
    assert len(hex_values) == len(set(hex_values)) == 6
    assert all(len(value) == 64 and value == value.lower() for value in hex_values)

    derived = subprocess.run(
        [
            "openssl",
            "pkey",
            "-in",
            str(target / "iam.jwt-private.pem"),
            "-pubout",
        ],
        check=True,
        capture_output=True,
    ).stdout
    assert derived == (target / "iam.jwt-public.pem").read_bytes()


def test_secret_creation_rejects_existing_or_symlink_target(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(RuntimeError, match="must not already exist"):
        create_secret_directory(existing)
    symlink = tmp_path / "link"
    symlink.symlink_to(existing, target_is_directory=True)
    with pytest.raises(RuntimeError, match="must not already exist"):
        create_secret_directory(symlink)


def test_fixture_directory_is_marked_private_and_initially_empty(
    tmp_path: Path,
) -> None:
    target = tmp_path / "fixtures"
    create_fixture_directory(target)
    assert stat.S_IMODE(target.stat().st_mode) == 0o700
    assert {path.name for path in target.iterdir()} == {
        ".kokoro-slice-a-owner",
        "magic-links",
    }
    magic_links = target / "magic-links"
    assert magic_links.is_dir()
    assert stat.S_IMODE(magic_links.stat().st_mode) == 0o700
    assert list(magic_links.iterdir()) == []


def test_backend_inventory_has_no_site_platform_session_or_web_process() -> None:
    assert BACKEND_PROCESSES == {
        "postgres",
        "redis",
        "model-fixture",
        "litellm",
        "iam",
        "model",
        "capability",
        "chat",
        "agent",
    }
    assert BACKEND_PROCESSES.isdisjoint({"site", "platform", "session", "user-web"})


def test_backend_candidates_are_pinned_to_the_reviewed_clean_cuts() -> None:
    assert DEFAULT_COMMITS == {
        "iam": "1ca2ced348832c81dd946ddb8b754640d77ced74",
        "chat": "3b5b0b5f8036d466c3fa4354f254b1444bcaf2aa",
        "agent": "5de3a2d7782e4c6eb68acf2c1aba1653794f3ed4",
        "model": "400b6ad39c6f03d8a9be93f24736cf27a95cbbcb",
        "capability": "ca0b3d4bdb0c8f06380d889508fa4773745db7c2",
    }
    assert DEFAULT_TREES == {
        "iam": "475d0ccfb345597c508dc02c3a2cc6382fe79b2f",
        "chat": "213b874868cbb8008c603ae8f50eecfd07c0c8c9",
        "agent": "7bc84f58319a653087ba895ca7a87e2e5c86a6ba",
        "model": "122f938d5617095cfa11463097cd4c9f822972c5",
        "capability": "49f5aa0e4f9b35735f2eee7bf37aef055350f218",
    }


def test_candidate_validation_requires_exact_commit_and_clean_tree(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "candidate"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "fixture@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Fixture"], check=True
    )
    (repo / "tracked").write_text("one\n")
    subprocess.run(["git", "-C", str(repo), "add", "tracked"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True)
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    validate_candidate(repo, commit, tree)
    with pytest.raises(RuntimeError, match="tree mismatch"):
        validate_candidate(repo, commit, "0" * 40)
    for mutable_ref in ("HEAD", commit[:12]):
        with pytest.raises(RuntimeError, match="full lowercase 40-hex"):
            validate_candidate(repo, mutable_ref, tree)
    with pytest.raises(RuntimeError, match="commit mismatch"):
        validate_candidate(repo, "0" * 40, tree)
    (repo / "tracked").write_text("dirty\n")
    with pytest.raises(RuntimeError, match="not clean"):
        validate_candidate(repo, commit, tree)


def test_runtime_state_never_serializes_secret_values(tmp_path: Path) -> None:
    from scripts.slice_a.native import write_runtime_state

    state = tmp_path / "state.json"
    write_runtime_state(
        state,
        processes={},
        public={"site_id": "11111111-1111-4111-8111-111111111111"},
        secret_values=frozenset({"ab" * 32}),
    )
    parsed = json.loads(state.read_text())
    assert parsed["public"]["site_id"] == "11111111-1111-4111-8111-111111111111"
    assert "ab" * 32 not in state.read_text()


def test_native_lifecycle_redacts_static_secrets_before_persisting_errors() -> None:
    secret = "static-workload-secret-value"
    assert _redact_text(f"startup failed: {secret}", frozenset({secret})) == (
        "startup failed: [REDACTED]"
    )


def test_supervisor_is_the_only_runtime_state_writer_after_process_spawn() -> None:
    import inspect

    from scripts.slice_a.native import _start, _supervise

    start_source = inspect.getsource(_start)
    supervise_source = inspect.getsource(_supervise)

    assert "write_runtime_state(" not in start_source
    assert supervise_source.index("_persist(") < supervise_source.index(
        "guardian = subprocess.Popen"
    )


def test_seed_artifacts_use_web_site_context_without_site_service() -> None:
    contexts = build_site_contexts()
    assert contexts == {
        "slice-a.localhost": {
            "site_id": SITE_ID,
            "brand_key": "kokoro",
            "locale": "en-US",
            "skin": "default",
        }
    }
    manifest = build_model_manifest()
    assert manifest["siteId"] == SITE_ID
    assert manifest["providerModelName"] == "slice-a-fixture"
    assert manifest["label"] == "default"
    assert (
        select_site_context(" SLICE-A.LOCALHOST. ", contexts)
        == contexts["slice-a.localhost"]
    )
    with pytest.raises(RuntimeError, match="unknown Site Host"):
        select_site_context("unknown.localhost", contexts)


def test_model_bootstrap_proves_exact_replay_and_manifest_drift(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest = tmp_path / "model.json"
    manifest.write_text(json.dumps(build_model_manifest()))
    calls: list[tuple[list[str], bool]] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((argv, bool(kwargs.get("check"))))
        if "model-drift" in Path(argv[-1]).name:
            return subprocess.CompletedProcess(argv, 1, "", "MODEL_BOOTSTRAP_DRIFT")
        return subprocess.CompletedProcess(argv, 0, "replayed=true", "")

    monkeypatch.setattr(subprocess, "run", run)
    evidence = bootstrap_model(tmp_path, "postgresql://fixture", manifest)

    assert len(calls) == 3
    assert evidence["exact_replay"] is True
    assert evidence["drift_rejected"] is True
    assert (
        evidence["manifest_sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    )


def test_service_commands_are_repository_native_development_entries(
    tmp_path: Path,
) -> None:
    roots = {
        "iam": tmp_path / "iam",
        "model": tmp_path / "model",
        "capability": tmp_path / "capability",
        "chat": tmp_path / "chat",
        "agent": tmp_path / "agent",
    }
    commands = build_service_commands(roots)
    assert commands == {
        "iam": ("pnpm", "dev"),
        "model": ("pnpm", "dev"),
        "capability": ("pnpm", "dev"),
        "chat": ("npm", "run", "dev"),
        "agent": ("uv", "run", "--frozen", "kokoro-agent-local", "--dev"),
    }


def test_all_native_services_bind_only_to_loopback(tmp_path: Path) -> None:
    roots = {
        name: tmp_path / name
        for name in ("iam", "model", "capability", "chat", "agent")
    }
    secret_dir = tmp_path / "secrets"
    secret_dir.mkdir()
    (secret_dir / "chat.workload-token").write_text("chat")
    (secret_dir / "web.workload-token").write_text("web")

    specs = _service_specs(
        roots,
        secret_dir,
        tmp_path / "fixtures",
        "postgresql://kokoro_app@127.0.0.1:5432/kokoro",
        6379,
    )

    assert specs["iam"].environment["KOKORO_IAM_BIND"] == "127.0.0.1:7202"
    assert specs["model"].environment["KOKORO_MODEL_HOST"] == "127.0.0.1"
    assert specs["capability"].environment["KOKORO_CAPABILITY_HOST"] == "127.0.0.1"
    assert specs["chat"].environment["KOKORO_CHAT_HOST"] == "127.0.0.1"
    assert specs["agent"].environment["KOKORO_SLICE_A_GRPC_BIND"] == "127.0.0.1:7206"


def test_native_processes_do_not_write_python_import_caches() -> None:
    assert _minimal_environment()["PYTHONDONTWRITEBYTECODE"] == "1"


def test_service_restart_preserves_the_pre_restart_log(tmp_path: Path) -> None:
    (tmp_path / "logs").mkdir()

    def run(message: str) -> None:
        spec = ProcessSpec(
            name="agent",
            argv=(sys.executable, "-c", f"print({message!r})"),
            cwd=tmp_path,
            environment=_minimal_environment(),
            port=7206,
            readiness="fixture",
        )
        process = _spawn(spec, tmp_path)
        assert process.wait(timeout=5) == 0

    run("before restart")
    run("after restart")

    assert (tmp_path / "logs" / "agent.log").read_text().splitlines() == [
        "before restart",
        "after restart",
    ]


def test_spawn_durably_records_ownership_before_child_executes(tmp_path: Path) -> None:
    (tmp_path / "logs").mkdir()
    effect = tmp_path / "effect"
    spec = ProcessSpec(
        name="agent",
        argv=(
            sys.executable,
            "-c",
            f"from pathlib import Path; Path({str(effect)!r}).write_text('ran')",
        ),
        cwd=tmp_path,
        environment=_minimal_environment(),
        port=7206,
        readiness="fixture",
    )
    recorded: list[int] = []

    def persist(process: subprocess.Popen[bytes]) -> None:
        assert not effect.exists()
        recorded.append(process.pid)

    process = _spawn(spec, tmp_path, persist)
    assert process.wait(timeout=5) == 0
    assert recorded == [process.pid]
    assert effect.read_text() == "ran"


def test_litellm_proxy_toolchain_is_versioned_including_python_and_fastapi(
    tmp_path: Path,
) -> None:
    command = build_litellm_command(tmp_path / "litellm.yaml")
    assert command[:9] == (
        "uvx",
        "--python",
        "3.11",
        "--from",
        "litellm[proxy]==1.80.11",
        "--with",
        "fastapi==0.121.3",
        "litellm",
        "--config",
    )


def test_grpc_readiness_normalizes_transient_transport_failure() -> None:
    port = _free_ports(1, set())[0]
    with pytest.raises(RuntimeError, match="gRPC health probe failed"):
        _grpc_health_probe(port, "kokoro.agent.v1.AgentRuntimeService")


def test_local_postgres_binary_is_version_18() -> None:
    bindir = find_postgres_18_bin()
    result = subprocess.run(
        [str(bindir / "postgres"), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PostgreSQL) 18." in result.stdout


def test_guardian_reaps_only_recorded_matching_process_groups(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.slice_a.guardian import process_identity, reap_orphans

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    monkeypatch.setattr(guardian_module, "_port_is_free", lambda _port: True)
    child = subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        identity = process_identity(child.pid)
        (state_dir / "runtime.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "processes": {
                        "chat": {
                            "pid": child.pid,
                            "pgid": child.pid,
                            "session_id": child.pid,
                            "start_identity": identity,
                            "port": _guardian_ports()["chat"],
                        }
                    },
                    "public": {"status": "ready", "ports": _guardian_ports()},
                }
            )
        )
        reap_orphans(
            state_dir, supervisor_pid=999_999_999, supervisor_identity="missing"
        )
        assert child.wait(timeout=5) < 0
        state = json.loads((state_dir / "runtime.json").read_text())
        assert state["public"]["status"] == "guardian_stopped"
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)


def test_guardian_fails_closed_for_malformed_owned_runtime_state(
    tmp_path: Path,
) -> None:
    from scripts.slice_a.guardian import reap_orphans

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "runtime.json").write_text(
        json.dumps(
            {
                "version": 1,
                "processes": [],
                "public": {"status": "ready", "ports": {}},
            }
        )
    )
    with pytest.raises(RuntimeError, match="guardian cleanup failed"):
        reap_orphans(
            state_dir, supervisor_pid=999_999_999, supervisor_identity="missing"
        )
    state = json.loads((state_dir / "runtime.json").read_text())
    assert state["public"]["status"] == "guardian_failed"


def test_guardian_fails_closed_when_a_recorded_port_survives_owner_crash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.slice_a.guardian import reap_orphans

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "runtime.json").write_text(
        json.dumps(
            {
                "version": 1,
                "processes": {},
                "public": {"status": "ready", "ports": _guardian_ports()},
            }
        )
    )
    monkeypatch.setattr(
        guardian_module, "_port_is_free", lambda _port: False, raising=False
    )
    with pytest.raises(RuntimeError, match="guardian cleanup failed"):
        reap_orphans(
            state_dir, supervisor_pid=999_999_999, supervisor_identity="missing"
        )
    state = json.loads((state_dir / "runtime.json").read_text())
    assert state["public"]["status"] == "guardian_failed"


def test_guardian_fails_closed_for_malformed_recorded_port_inventory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts.slice_a.guardian import reap_orphans

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    monkeypatch.setattr(guardian_module, "_port_is_free", lambda _port: True)
    (state_dir / "runtime.json").write_text(
        json.dumps(
            {
                "version": 1,
                "processes": {},
                "public": {
                    "status": "ready",
                    "ports": {**_guardian_ports(), "chat": "7205"},
                },
            }
        )
    )
    with pytest.raises(RuntimeError, match="guardian cleanup failed"):
        reap_orphans(
            state_dir, supervisor_pid=999_999_999, supervisor_identity="missing"
        )
    state = json.loads((state_dir / "runtime.json").read_text())
    assert state["public"]["status"] == "guardian_failed"
    assert state["public"]["guardian_errors"] == [
        "ports.inventory: RuntimeError",
        "port[8]: RuntimeError",
    ]


def test_guardian_port_proof_rejects_bound_not_listening_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BoundSocket:
        def __enter__(self) -> "BoundSocket":
            return self

        def __exit__(self, *_args: object) -> None:
            pass

        def settimeout(self, _timeout: float) -> None:
            pass

        def connect_ex(self, _address: tuple[str, int]) -> int:
            return errno.ECONNREFUSED

        def bind(self, _address: tuple[str, int]) -> None:
            raise OSError(errno.EADDRINUSE, "already bound")

    monkeypatch.setattr(guardian_module.socket, "socket", lambda *_args: BoundSocket())
    assert guardian_module._port_is_free(7205) is False


def test_outer_port_proof_rejects_bound_not_listening_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BoundSocket:
        def __enter__(self) -> "BoundSocket":
            return self

        def __exit__(self, *_args: object) -> None:
            pass

        def settimeout(self, _timeout: float) -> None:
            pass

        def connect_ex(self, _address: tuple[str, int]) -> int:
            return errno.ECONNREFUSED

        def bind(self, _address: tuple[str, int]) -> None:
            raise OSError(errno.EADDRINUSE, "already bound")

    monkeypatch.setattr(native_module.socket, "socket", lambda *_args: BoundSocket())
    with pytest.raises(RuntimeError, match="already occupied"):
        _ensure_port_free(7205)


def test_guardian_attempts_every_group_and_redacts_aggregated_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.slice_a.guardian import reap_orphans

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    records = {
        "iam": {
            "pid": 101,
            "pgid": 101,
            "session_id": 101,
            "start_identity": "a" * 64,
            "port": _guardian_ports()["iam"],
        },
        "chat": {
            "pid": 202,
            "pgid": 202,
            "session_id": 202,
            "start_identity": "b" * 64,
            "port": _guardian_ports()["chat"],
        },
    }
    (state_dir / "runtime.json").write_text(
        json.dumps(
            {
                "version": 1,
                "processes": records,
                "public": {"status": "ready", "ports": _guardian_ports()},
            }
        )
    )
    attempted: list[int] = []

    def stop(**record: object) -> None:
        pid = int(record["pid"])
        attempted.append(pid)
        if pid == 202:
            raise RuntimeError("Bearer synthetic-guardian-secret")

    monkeypatch.setattr(guardian_module, "stop_owned_group", stop)
    monkeypatch.setattr(guardian_module, "group_alive", lambda _pgid: False)
    monkeypatch.setattr(guardian_module, "_port_is_free", lambda _port: True)

    with pytest.raises(RuntimeError, match="guardian cleanup failed") as caught:
        reap_orphans(
            state_dir, supervisor_pid=999_999_999, supervisor_identity="missing"
        )

    assert attempted == [202, 101]
    assert "synthetic-guardian-secret" not in str(caught.value)
    state = json.loads((state_dir / "runtime.json").read_text())
    assert state["public"]["status"] == "guardian_failed"
    assert "synthetic-guardian-secret" not in json.dumps(state)
    assert state["public"]["guardian_errors"] == [
        "process[1]: RuntimeError",
    ]


def test_guardian_requires_complete_recorded_port_parity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.slice_a.guardian import reap_orphans

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "runtime.json").write_text(
        json.dumps(
            {
                "version": 1,
                "processes": {
                    "chat": {
                        "pid": 202,
                        "pgid": 202,
                        "session_id": 202,
                        "start_identity": "b" * 64,
                        "port": 7205,
                    }
                },
                "public": {"status": "ready", "ports": {}},
            }
        )
    )
    attempted: list[int] = []
    monkeypatch.setattr(
        guardian_module,
        "stop_owned_group",
        lambda **record: attempted.append(int(record["pid"])),
    )
    monkeypatch.setattr(guardian_module, "group_alive", lambda _pgid: False)

    with pytest.raises(RuntimeError, match="guardian cleanup failed"):
        reap_orphans(
            state_dir, supervisor_pid=999_999_999, supervisor_identity="missing"
        )
    state = json.loads((state_dir / "runtime.json").read_text())
    assert attempted == [202]
    assert state["public"]["status"] == "guardian_failed"


def test_guardian_never_persists_untrusted_inventory_keys_in_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.slice_a.guardian import reap_orphans

    secret = "guardian-secret-0123456789"
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "runtime.json").write_text(
        json.dumps(
            {
                "version": 1,
                "processes": {
                    f"Bearer {secret}": {
                        "pid": 202,
                        "pgid": 202,
                        "session_id": 202,
                        "start_identity": "b" * 64,
                        "port": 7205,
                    }
                },
                "public": {"status": "ready", "ports": {}},
            }
        )
    )
    monkeypatch.setattr(guardian_module, "stop_owned_group", lambda **_record: None)
    monkeypatch.setattr(guardian_module, "group_alive", lambda _pgid: False)

    with pytest.raises(RuntimeError, match="guardian cleanup failed") as caught:
        reap_orphans(
            state_dir, supervisor_pid=999_999_999, supervisor_identity="missing"
        )
    persisted = (state_dir / "runtime.json").read_text()
    assert secret not in persisted
    assert secret not in str(caught.value)


def test_guardian_sanitizes_a_malformed_process_inventory_before_persisting(
    tmp_path: Path,
) -> None:
    from scripts.slice_a.guardian import reap_orphans

    secret = "guardian-inventory-secret-0123456789"
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "runtime.json").write_text(
        json.dumps(
            {
                "version": 1,
                "processes": [secret],
                "public": {"status": "ready", "ports": _guardian_ports()},
            }
        )
    )
    with pytest.raises(RuntimeError, match="guardian cleanup failed"):
        reap_orphans(
            state_dir, supervisor_pid=999_999_999, supervisor_identity="missing"
        )
    assert secret not in (state_dir / "runtime.json").read_text()


def test_guardian_sanitizes_ports_even_when_process_inventory_is_malformed(
    tmp_path: Path,
) -> None:
    from scripts.slice_a.guardian import reap_orphans

    secret = "guardian-port-secret-0123456789"
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "runtime.json").write_text(
        json.dumps(
            {
                "version": 1,
                "processes": [],
                "public": {
                    "status": "ready",
                    "ports": {f"Bearer {secret}": secret},
                },
            }
        )
    )
    with pytest.raises(RuntimeError, match="guardian cleanup failed"):
        reap_orphans(
            state_dir, supervisor_pid=999_999_999, supervisor_identity="missing"
        )
    assert secret not in (state_dir / "runtime.json").read_text()


def test_guardian_reaps_recorded_process_after_supervisor_sigkill(
    tmp_path: Path,
) -> None:
    from scripts.slice_a.guardian import process_identity

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    owned = subprocess.Popen(["sleep", "60"], start_new_session=True)
    (state_dir / "runtime.json").write_text(
        json.dumps(
            {
                "version": 1,
                "processes": {
                    "chat": {
                        "pid": owned.pid,
                        "pgid": owned.pid,
                        "session_id": owned.pid,
                        "start_identity": process_identity(owned.pid),
                        "port": _guardian_ports()["chat"],
                    }
                },
                "public": {"status": "starting", "ports": _guardian_ports()},
            }
        )
    )
    controller_source = """
import subprocess, sys, time
from pathlib import Path
from scripts.slice_a.guardian import process_identity
state = Path(sys.argv[1])
guardian = subprocess.Popen(
    [sys.executable, 'scripts/slice_a/guardian.py', '--state-dir', str(state),
     '--supervisor-pid', str(__import__('os').getpid()), '--supervisor-identity', process_identity(__import__('os').getpid())],
    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    start_new_session=True,
)
(state / 'guardian.pid').write_text(str(guardian.pid))
while True: time.sleep(1)
"""
    controller = subprocess.Popen(
        [sys.executable, "-c", controller_source, str(state_dir)],
        cwd=ROOT,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 5
        while not (state_dir / "guardian.pid").exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert (state_dir / "guardian.pid").exists()
        os.killpg(controller.pid, signal.SIGKILL)
        controller.wait(timeout=5)
        deadline = time.monotonic() + 12
        while owned.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert owned.poll() is not None
        state = json.loads((state_dir / "runtime.json").read_text())
        assert state["public"]["status"] == "guardian_stopped"
    finally:
        if controller.poll() is None:
            os.killpg(controller.pid, signal.SIGKILL)
            controller.wait(timeout=5)
        if owned.poll() is None:
            os.killpg(owned.pid, signal.SIGKILL)
            owned.wait(timeout=5)


def test_wait_ready_rejects_incomplete_or_nonready_inventory() -> None:
    from scripts.slice_a.wait_ready import assert_ready_inventory

    records = {
        name: {"pid": 1, "start_identity": "id", "port": 1}
        for name in BACKEND_PROCESSES
    }
    assert_ready_inventory({"public": {"status": "ready"}, "processes": records})
    with pytest.raises(RuntimeError, match="inventory"):
        assert_ready_inventory({"public": {"status": "ready"}, "processes": {}})
    with pytest.raises(RuntimeError, match="not ready"):
        assert_ready_inventory({"public": {"status": "starting"}, "processes": records})


def test_dynamic_ports_are_unique_and_exclude_fixed_service_ports() -> None:
    excluded = {4000, 7202, 7203, 7204, 7205, 7206}
    ports = _free_ports(16, excluded)
    assert len(ports) == len(set(ports)) == 16
    assert excluded.isdisjoint(ports)


def test_occupied_port_is_rejected_before_any_process_launch() -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        with pytest.raises(RuntimeError, match="already occupied"):
            _ensure_port_free(listener.getsockname()[1])


@pytest.mark.parametrize("termination", [signal.SIGINT, signal.SIGTERM, signal.SIGKILL])
def test_owned_process_group_is_reaped_for_all_runner_termination_modes(
    termination: signal.Signals,
) -> None:
    child = subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        os.killpg(child.pid, termination)
        assert child.wait(timeout=5) < 0
    finally:
        _stop_process(child, timeout=0.1)


def test_owner_identity_fails_closed_after_owner_process_dies() -> None:
    from scripts.slice_a.guardian import process_identity

    owner = subprocess.Popen(["sleep", "60"])
    identity = process_identity(owner.pid)
    assert identity is not None
    assert _owner_alive({"owner_pid": owner.pid, "owner_identity": identity})
    owner.terminate()
    owner.wait(timeout=5)
    deadline = time.monotonic() + 2
    while (
        _owner_alive({"owner_pid": owner.pid, "owner_identity": identity})
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
    assert not _owner_alive({"owner_pid": owner.pid, "owner_identity": identity})


def test_stop_process_reaps_group_members_after_group_leader_exits(
    tmp_path: Path,
) -> None:
    child_pid_path = tmp_path / "child.pid"
    source = (
        "import pathlib, subprocess; "
        "child=subprocess.Popen(['sleep','60']); "
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid))"
    )
    leader = subprocess.Popen([sys.executable, "-c", source], start_new_session=True)
    leader.wait(timeout=5)
    child_pid = int(child_pid_path.read_text())
    _stop_process(leader, timeout=0.1)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        facts = guardian_module._process_facts(child_pid)
        if facts is None or facts.state == "zombie":
            break
        time.sleep(0.02)
    else:
        pytest.fail("group member survived after its recorded leader exited")


def test_app_database_url_has_no_search_path_override() -> None:
    from scripts.slice_a.native import _provision_postgres

    assert (
        "options=" not in _provision_postgres.__doc__
        if _provision_postgres.__doc__
        else True
    )
    source = Path(
        __import__("inspect").getsourcefile(_provision_postgres) or ""
    ).read_text()
    assert "?options=" not in source

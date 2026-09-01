from __future__ import annotations

import hashlib
import inspect
import json
import os
import signal
import shutil
import subprocess
import sys
import threading
import time
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.e2e.run_slice_a_native as runner_module

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.e2e.run_slice_a_native import (
    EXPECTED_CONTRACT_SOURCE,
    EXPECTED_GENERATED_COMMIT,
    NativeRuntime,
    REDIRECT_URI,
    RuntimePaths,
    RunInterrupted,
    _assert_no_secret_logs,
    _run_process,
    _read_stream_kinds,
    _validate_terminal_snapshot,
    _validate_retention_recovery,
    _wait_for,
    canonical_digest,
    compare_evidence,
    consume_digest,
    load_magic_link,
    logout_digest,
    main,
    refresh_digest,
    validate_release_evidence,
    validate_generated_client_provenance,
    validate_site_table_boundary,
)
from scripts.slice_a.seed import SITE_ID
from scripts.slice_a.guardian import process_identity


def test_documented_direct_pytest_entrypoint_collects_from_root() -> None:
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/pytest"),
            "scripts/tests/test_slice_a_backend_runner.py",
            "--collect-only",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "test_documented_direct_pytest_entrypoint_collects_from_root" in result.stdout
    )


def test_iam_canonical_request_digests_match_javascript_json_stringify() -> None:
    token = "fixture-token"
    nonce = "12" * 32
    auth_session_id = "22222222-2222-4222-8222-222222222222"
    token_digest = hashlib.sha256(token.encode()).hexdigest()

    assert (
        consume_digest(SITE_ID, token, nonce)
        == hashlib.sha256(
            (
                '{"nonce_digest":"'
                + nonce
                + '","site_id":"'
                + SITE_ID
                + '","token_digest":"'
                + token_digest
                + '"}'
            ).encode()
        ).hexdigest()
    )
    assert refresh_digest(SITE_ID, auth_session_id, token) == canonical_digest(
        {
            "auth_session_id": auth_session_id,
            "old_refresh_token_digest": token_digest,
            "site_id": SITE_ID,
        }
    )
    assert logout_digest(auth_session_id, token) == canonical_digest(
        {
            "auth_session_id": auth_session_id,
            "refresh_token_digest": token_digest,
        }
    )


def test_magic_link_redirect_uses_the_contract_fixed_callback_path() -> None:
    assert REDIRECT_URI == "https://slice-a.localhost/api/auth/callback"


def test_generated_clients_are_frozen_to_reviewed_root_contract_cut() -> None:
    validate_generated_client_provenance()
    assert EXPECTED_CONTRACT_SOURCE == "a5c07bc6cad3d0e18d87793e94d46ee465bd1263"
    assert EXPECTED_GENERATED_COMMIT == "2d7ad2c1f1e478724b584027ce4eea2ab0d6ef62"


def test_generated_validation_rejects_dirty_self_rehashed_or_extra_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = tmp_path / "root"
    generated = repo / "scripts/e2e/generated"
    (repo / "contract").mkdir(parents=True)
    (repo / "contract/authority").write_text("source\n")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "fixture@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Fixture"], check=True
    )
    subprocess.run(["git", "-C", str(repo), "add", "contract"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "source"], check=True)
    source_commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    source_tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    shutil.copytree(ROOT / "scripts/e2e/generated", generated)
    provenance_path = generated / "provenance.json"
    provenance = json.loads(provenance_path.read_text())
    provenance["sourceRootCommit"] = source_commit
    provenance["sourceRootTree"] = source_tree
    provenance_path.write_text(json.dumps(provenance, sort_keys=True, indent=2) + "\n")
    subprocess.run(["git", "-C", str(repo), "add", "scripts"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "generated"], check=True)
    output_commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    monkeypatch.setattr(runner_module, "ROOT", repo)
    monkeypatch.setattr(runner_module, "GENERATED", generated)
    monkeypatch.setattr(runner_module, "EXPECTED_CONTRACT_SOURCE", source_commit)
    monkeypatch.setattr(runner_module, "EXPECTED_CONTRACT_TREE", source_tree)
    monkeypatch.setattr(runner_module, "EXPECTED_GENERATED_COMMIT", output_commit)
    validate_generated_client_provenance()

    output = generated / next(iter(provenance["outputs"]))
    output.write_bytes(output.read_bytes() + b"# dirty\n")
    provenance["outputs"][output.relative_to(generated).as_posix()] = hashlib.sha256(
        output.read_bytes()
    ).hexdigest()
    provenance_path.write_text(json.dumps(provenance, sort_keys=True, indent=2) + "\n")
    with pytest.raises(RuntimeError, match="committed|dirty"):
        validate_generated_client_provenance()

    subprocess.run(["git", "-C", str(repo), "checkout", "--", "scripts"], check=True)
    (generated / "extra.py").write_text("# undeclared\n")
    with pytest.raises(RuntimeError, match="closure|dirty"):
        validate_generated_client_provenance()


def test_magic_link_sink_requires_private_regular_file_and_exact_delivery(
    tmp_path: Path,
) -> None:
    sink = tmp_path / "magic-links.jsonl"
    wanted = {
        "delivery_ref": "delivery-1",
        "site_id": SITE_ID,
        "email": "slice-a@example.com",
        "token": "TOKEN",
    }
    sink.write_text(json.dumps(wanted) + "\n")
    sink.chmod(0o600)

    assert (
        load_magic_link(
            sink,
            "delivery-1",
            expected_site_id=SITE_ID,
            expected_email="slice-a@example.com",
        )
        == wanted
    )
    assert not sink.exists()
    sink.write_text(json.dumps(wanted) + "\n")
    sink.chmod(0o600)
    with pytest.raises(RuntimeError, match="not found"):
        load_magic_link(
            sink,
            "delivery-missing",
            expected_site_id=SITE_ID,
            expected_email="slice-a@example.com",
            timeout=0.01,
        )

    sink.chmod(0o644)
    with pytest.raises(RuntimeError, match="0600"):
        load_magic_link(
            sink,
            "delivery-1",
            expected_site_id=SITE_ID,
            expected_email="slice-a@example.com",
        )


def test_dynamic_session_secrets_are_redacted_and_checked_without_static_files(
    tmp_path: Path,
) -> None:
    paths = RuntimePaths(
        owner=tmp_path,
        state=tmp_path / "state",
        secrets=tmp_path / "secrets",
        fixtures=tmp_path / "fixtures",
    )
    logs = paths.state / "logs"
    logs.mkdir(parents=True)
    dynamic_token = "dynamic-session-token-that-must-never-appear"
    (logs / "iam.log").write_text(f"request token={dynamic_token}\n")

    runtime = object.__new__(NativeRuntime)
    runtime.paths = paths
    runtime._sensitive_values = set()
    runtime.register_sensitive(dynamic_token)

    diagnostics = runtime.diagnostics()
    assert dynamic_token not in diagnostics
    assert "request token=[REDACTED]" in diagnostics
    with pytest.raises(RuntimeError, match="secret material appeared"):
        _assert_no_secret_logs(runtime, extra=())


def test_shutdown_secret_check_cleans_owned_state_and_remains_idempotent(
    tmp_path: Path,
) -> None:
    owner = tmp_path / "owner"
    state = owner / "state"
    logs = state / "logs"
    logs.mkdir(parents=True)
    (state / ".kokoro-slice-a-owner").write_text("kokoro-slice-a:state:v1\n")
    dynamic_token = "shutdown-session-token-that-must-never-appear"
    (logs / "iam.log").write_text(f"shutdown token={dynamic_token}\n")

    runtime = object.__new__(NativeRuntime)
    runtime.paths = RuntimePaths(
        owner=owner,
        state=state,
        secrets=owner / "secrets",
        fixtures=owner / "fixtures",
    )
    runtime.started = True
    runtime._sensitive_values = {dynamic_token}

    with pytest.raises(RuntimeError, match="secret material appeared"):
        runtime.stop()
    assert not owner.exists()
    assert runtime.started is False
    runtime.stop()


def test_canonical_digest_rejects_non_object_or_noncanonical_json_values() -> None:
    with pytest.raises(TypeError):
        canonical_digest(["not", "an", "object"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="finite"):
        canonical_digest({"bad": float("nan")})


def test_bounded_child_command_reaps_its_process_group_on_timeout(
    tmp_path: Path,
) -> None:
    pid_file = tmp_path / "pid"
    source = (
        "import os, pathlib, time; "
        f"pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid())); "
        "time.sleep(60)"
    )
    with pytest.raises(RuntimeError, match="timed out"):
        _run_process([sys.executable, "-c", source], timeout=0.1)
    pid = int(pid_file.read_text())
    with pytest.raises(ProcessLookupError):
        process_identity(pid)


def test_failed_child_output_is_redacted_before_entering_exception() -> None:
    secret = "dynamic-access-token-secret-value"
    with pytest.raises(RuntimeError) as captured:
        _run_process(
            [sys.executable, "-c", f"print({secret!r}); raise SystemExit(7)"],
            timeout=2,
            redact=lambda value: value.replace(secret, "[REDACTED]"),
        )
    assert secret not in str(captured.value)
    assert "[REDACTED]" in str(captured.value)


@pytest.mark.parametrize("termination", [signal.SIGINT, signal.SIGTERM])
def test_runner_signal_uses_the_same_finally_cleanup_path(
    monkeypatch: pytest.MonkeyPatch, termination: signal.Signals
) -> None:
    events: list[str] = []
    runtime_started = threading.Event()

    class RuntimeFixture:
        def __init__(self, _args: object) -> None:
            events.append("created")

        def start(self) -> None:
            events.append("starting")
            runtime_started.set()
            while True:
                time.sleep(0.01)

        def stop(self) -> None:
            events.append("stopped")

        def diagnostics(self) -> str:
            return ""

        def redact(self, value: str) -> str:
            return value

    monkeypatch.setattr("scripts.e2e.run_slice_a_native.NativeRuntime", RuntimeFixture)
    monkeypatch.setattr(sys, "argv", ["run_slice_a_native.py"])
    sender = threading.Thread(
        target=lambda: runtime_started.wait(5) and os.kill(os.getpid(), termination)
    )
    sender.start()
    with pytest.raises(RunInterrupted):
        main()
    sender.join(timeout=5)
    assert not sender.is_alive()
    assert events == ["created", "starting", "stopped"]


def test_runner_never_emits_pass_or_evidence_before_cleanup_succeeds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stops = 0

    class RuntimeFixture:
        def __init__(self, _args: object) -> None:
            pass

        def start(self) -> None:
            pass

        def stop(self) -> None:
            nonlocal stops
            stops += 1
            if stops == 1:
                raise RuntimeError("cleanup red")

        def diagnostics(self) -> str:
            return ""

        def redact(self, value: str) -> str:
            return value

    evidence = tmp_path / "evidence.json"
    monkeypatch.setattr("scripts.e2e.run_slice_a_native.NativeRuntime", RuntimeFixture)
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native._run_product_chain",
        lambda _runtime: {"chain": "complete"},
    )
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native.validate_generated_client_provenance",
        lambda: None,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_slice_a_native.py", "--evidence", str(evidence)],
    )

    with pytest.raises(RuntimeError, match="cleanup red"):
        main()

    assert stops == 2
    assert not evidence.exists()
    assert '"status": "PASS"' not in capsys.readouterr().out


def test_runner_revalidates_clean_candidates_after_successful_cleanup(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    events: list[str] = []

    class RuntimeFixture:
        def __init__(self, _args: object) -> None:
            events.append("created")

        def start(self) -> None:
            events.append("started")

        def stop(self) -> None:
            events.append("stopped")

        def diagnostics(self) -> str:
            return ""

        def redact(self, value: str) -> str:
            return value

    monkeypatch.setattr("scripts.e2e.run_slice_a_native.NativeRuntime", RuntimeFixture)
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native._run_product_chain",
        lambda _runtime: events.append("chain") or {"chain": "complete"},
    )
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native.validate_runtime_candidates",
        lambda _args: events.append("candidates-clean"),
    )
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native.validate_generated_client_provenance",
        lambda: events.append("provenance"),
    )
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native.validate_release_evidence", lambda _value: None
    )
    monkeypatch.setattr(sys, "argv", ["run_slice_a_native.py"])

    assert main() == 0
    assert events == [
        "provenance",
        "candidates-clean",
        "created",
        "started",
        "chain",
        "stopped",
        "candidates-clean",
        "provenance",
    ]
    assert json.loads(capsys.readouterr().out) == {
        "status": "PASS",
        "chain": "complete",
    }


def test_release_evidence_requires_every_reviewed_product_assertion() -> None:
    required = {
        "site_context",
        "site_owner_boundary",
        "site_suspend",
        "personal_authority",
        "model_capability_admission",
        "mutating_replay_drift",
        "retention_snapshot_required",
        "restart_no_duplicate_effect",
        "exact_snapshot_hitl",
        "catalog_50_plus_4",
        "terminal_exactly_once",
    }
    with pytest.raises(RuntimeError, match="missing release assertions"):
        validate_release_evidence({"assertions": {}})
    validate_release_evidence(
        {
            "assertions": {name: True for name in required},
            "catalog": {"owner": 50, "checkpointer": 4},
            "site_table_boundary": {"iam": 4},
            "retained_watermark": 41,
            "retention_tail_seq": 42,
            "retention_recovered_watermark": 42,
            "stream_kinds": [
                "tool.awaiting_approval",
                "interaction.resolved",
                "run.completed",
            ],
            "sql": {
                "event_kinds": [
                    "run.started",
                    "tool.awaiting_approval",
                    "run.control.receipt",
                    "run.completed",
                ],
                "tool_effects": 1,
            },
        }
    )

    evidence = {
        "assertions": {name: True for name in required},
        "catalog": {"owner": 50, "checkpointer": 4},
        "site_table_boundary": {"iam": 4},
        "retained_watermark": 41,
        "retention_tail_seq": 42,
        "retention_recovered_watermark": 42,
        "stream_kinds": [
            "tool.awaiting_approval",
            "interaction.resolved",
            "run.completed",
        ],
        "sql": {
            "event_kinds": [
                "run.started",
                "tool.awaiting_approval",
                "run.control.receipt",
                "run.completed",
            ],
            "tool_effects": 1,
            "catalog_tables": ["a"],
            "baseline_sha256": "1" * 64,
            "seed_digest": "2" * 64,
            "model_bootstrap": {
                "manifest_sha256": "3" * 64,
                "result_sha256": "4" * 64,
            },
        },
    }
    compare_evidence(evidence, json.loads(json.dumps(evidence)))
    drift = json.loads(json.dumps(evidence))
    drift["sql"]["seed_digest"] = "5" * 64
    with pytest.raises(RuntimeError, match="seed_digest"):
        compare_evidence(evidence, drift)
    broken_tail = json.loads(json.dumps(evidence))
    broken_tail["retention_tail_seq"] = 43
    with pytest.raises(RuntimeError, match="retention recovery"):
        validate_release_evidence(broken_tail)
    duplicate = json.loads(json.dumps(evidence))
    duplicate["sql"]["event_kinds"].append("tool.awaiting_approval")
    with pytest.raises(RuntimeError, match="event multiplicity"):
        validate_release_evidence(duplicate)
    reordered = json.loads(json.dumps(evidence))
    reordered["sql"]["event_kinds"] = list(reversed(reordered["sql"]["event_kinds"]))
    with pytest.raises(RuntimeError, match="event_kinds"):
        compare_evidence(evidence, reordered)


def test_generated_closure_drift_after_cleanup_blocks_evidence_and_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    checks = 0

    class RuntimeFixture:
        def __init__(self, _args: object) -> None:
            pass

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

        def diagnostics(self) -> str:
            return ""

        def redact(self, value: str) -> str:
            return value

    def provenance() -> None:
        nonlocal checks
        checks += 1
        if checks == 2:
            raise RuntimeError("generated closure drift")

    evidence_path = tmp_path / "evidence.json"
    monkeypatch.setattr("scripts.e2e.run_slice_a_native.NativeRuntime", RuntimeFixture)
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native.validate_generated_client_provenance",
        provenance,
    )
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native.validate_runtime_candidates", lambda _args: None
    )
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native._run_product_chain",
        lambda _runtime: {"chain": "complete"},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_slice_a_native.py", "--evidence", str(evidence_path)],
    )

    with pytest.raises(RuntimeError, match="generated closure drift"):
        main()
    assert checks == 2
    assert not evidence_path.exists()
    assert '"status": "PASS"' not in capsys.readouterr().out


def test_retention_recovery_requires_contiguous_new_tail_and_preserved_history() -> (
    None
):
    assert (
        _validate_retention_recovery(
            snapshot_watermark=41,
            tail_sequences=[42],
            snapshot_history=["user", "assistant"],
            recovered_history=["user", "assistant", "new-user", "new-assistant"],
        )
        == 42
    )
    for invalid in ([41], [43], [42, 42], [43, 42]):
        with pytest.raises(RuntimeError, match="tail"):
            _validate_retention_recovery(
                snapshot_watermark=41,
                tail_sequences=invalid,
                snapshot_history=["user", "assistant"],
                recovered_history=["user", "assistant", "new-user"],
            )
    with pytest.raises(RuntimeError, match="history"):
        _validate_retention_recovery(
            snapshot_watermark=41,
            tail_sequences=[42],
            snapshot_history=["user", "assistant"],
            recovered_history=["mutated", "assistant", "new-user"],
        )


def test_site_table_boundary_allows_only_iam_runtime_source(tmp_path: Path) -> None:
    roots: dict[str, Path] = {}
    for name in ("iam", "model", "capability", "chat", "agent"):
        repo = tmp_path / name
        (repo / "src").mkdir(parents=True)
        (repo / "src/runtime.txt").write_text(
            "SELECT * FROM kokoro.site_site\n" if name == "iam" else "runtime\n"
        )
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "src"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.com",
                "commit",
                "-qm",
                "fixture",
            ],
            check=True,
        )
        roots[name] = repo
    assert validate_site_table_boundary(roots) == {"iam": 1}

    capability_source = roots["capability"] / "src/runtime.txt"
    capability_source.write_text("SELECT * FROM kokoro.site_site\n")
    subprocess.run(
        ["git", "-C", str(roots["capability"]), "add", "src/runtime.txt"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(roots["capability"]),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.com",
            "commit",
            "-qm",
            "drift",
        ],
        check=True,
    )
    with pytest.raises(RuntimeError, match="Capability runtime source"):
        validate_site_table_boundary(roots)


def test_refresh_digest_drift_is_checked_before_logout_revokes_the_session() -> None:
    source = inspect.getsource(runner_module._run_product_chain)
    active_drift = source.index(
        'lambda: refresh_session("0" * 64), grpc.StatusCode.ABORTED'
    )
    logout = source.index("logout = logout_session()")
    revoked_retry = source.index(
        'lambda: refresh_session("0" * 64), grpc.StatusCode.UNAUTHENTICATED'
    )
    assert active_drift < logout < revoked_retry


def test_terminal_snapshot_rejects_extra_missing_or_wrong_kind_parts() -> None:
    pb = SimpleNamespace(
        MESSAGE_ROLE_USER=1,
        MESSAGE_ROLE_ASSISTANT=2,
        MESSAGE_STATUS_COMPLETED=3,
        MESSAGE_PART_KIND_TEXT=4,
        MESSAGE_PART_KIND_TOOL_CALL=5,
        MESSAGE_PART_KIND_TOOL_RESULT=6,
        MESSAGE_PART_STATUS_COMPLETE=7,
    )

    def part(ordinal: int, kind: int, payload: dict[str, object]) -> SimpleNamespace:
        return SimpleNamespace(
            part_id=f"part-{ordinal}",
            ordinal=ordinal,
            kind=kind,
            schema_version=1,
            payload_json=json.dumps(payload, separators=(",", ":")).encode(),
            status=pb.MESSAGE_PART_STATUS_COMPLETE,
        )

    user = SimpleNamespace(
        message_id="user-message",
        conversation_id="conversation",
        parent_message_id="",
        role=pb.MESSAGE_ROLE_USER,
        status=pb.MESSAGE_STATUS_COMPLETED,
        ordinal=1,
        generation=1,
        parts=[part(1, pb.MESSAGE_PART_KIND_TEXT, {"text": runner_module.CONTENT})],
        HasField=lambda name: False if name == "parent_message_id" else False,
    )
    assistant = SimpleNamespace(
        message_id="assistant-message",
        conversation_id="conversation",
        parent_message_id="user-message",
        role=pb.MESSAGE_ROLE_ASSISTANT,
        status=pb.MESSAGE_STATUS_COMPLETED,
        ordinal=2,
        generation=1,
        parts=[
            part(
                1,
                pb.MESSAGE_PART_KIND_TOOL_CALL,
                {
                    "segment_id": "segment",
                    "tool_id": runner_module.TOOL_ID,
                    "name": "ask_user_question",
                    "args": json.loads(runner_module.TOOL_ARGUMENTS),
                    "returned": True,
                    "awaitingApproval": True,
                },
            ),
            part(
                2,
                pb.MESSAGE_PART_KIND_TOOL_RESULT,
                {
                    "segment_id": "segment",
                    "tool_id": runner_module.TOOL_ID,
                    "name": "ask_user_question",
                    "result": "Approve",
                    "is_error": False,
                    "truncated": False,
                    "rejected": False,
                    "responded": False,
                },
            ),
            part(
                3,
                pb.MESSAGE_PART_KIND_TEXT,
                {
                    "segment_id": "segment-final",
                    "delta": "Slice A approved.",
                    "content": "Slice A approved.",
                },
            ),
        ],
        HasField=lambda name: True if name == "parent_message_id" else False,
    )
    terminal = SimpleNamespace(messages=[user, assistant])
    submitted = SimpleNamespace(
        user_message_id="user-message", assistant_message_id="assistant-message"
    )
    _validate_terminal_snapshot(pb, terminal, submitted, "conversation")

    for mutate in (
        lambda parts: parts.append(deepcopy(parts[-1])),
        lambda parts: parts.pop(),
        lambda parts: setattr(parts[-1], "kind", pb.MESSAGE_PART_KIND_TOOL_CALL),
    ):
        changed = deepcopy(terminal)
        mutate(changed.messages[1].parts)
        with pytest.raises(RuntimeError, match="terminal snapshot part shape"):
            _validate_terminal_snapshot(pb, changed, submitted, "conversation")


def test_stream_reader_rejects_a_duplicate_after_expected_kinds_first_appear() -> None:
    events = [
        SimpleNamespace(kind="tool.awaiting_approval", seq=1, event_id="event-1"),
        SimpleNamespace(kind="interaction.resolved", seq=2, event_id="event-2"),
        SimpleNamespace(kind="run.completed", seq=3, event_id="event-3"),
        SimpleNamespace(kind="run.completed", seq=4, event_id="event-4"),
    ]

    class Call:
        cancelled = False

        def __iter__(self):
            return iter(SimpleNamespace(event=event) for event in events)

        def cancel(self) -> None:
            self.cancelled = True

    call = Call()
    queries = SimpleNamespace(StreamConversationEvents=lambda *_args, **_kwargs: call)
    pb = SimpleNamespace(
        StreamConversationEventsRequest=lambda **kwargs: SimpleNamespace(**kwargs)
    )

    with pytest.raises(RuntimeError, match="duplicated a release event kind"):
        _read_stream_kinds(
            queries,
            pb,
            "conversation",
            "workload-token",
            "access-token",
            expected={
                "tool.awaiting_approval",
                "interaction.resolved",
                "run.completed",
            },
            through_seq=4,
        )
    assert call.cancelled


@pytest.mark.parametrize("sequences", ([1, 3], [1, 1], [1, 3, 2]))
def test_stream_reader_requires_the_exact_terminal_watermark_prefix(
    sequences: list[int],
) -> None:
    events = [
        SimpleNamespace(kind=f"kind-{index}", seq=seq, event_id=f"event-{index}")
        for index, seq in enumerate(sequences)
    ]

    class Call:
        def __iter__(self):
            return iter(SimpleNamespace(event=event) for event in events)

        def cancel(self) -> None:
            pass

    queries = SimpleNamespace(StreamConversationEvents=lambda *_args, **_kwargs: Call())
    pb = SimpleNamespace(
        StreamConversationEventsRequest=lambda **kwargs: SimpleNamespace(**kwargs)
    )
    with pytest.raises(RuntimeError, match="terminal watermark prefix"):
        _read_stream_kinds(
            queries,
            pb,
            "conversation",
            "workload-token",
            "access-token",
            expected=set(),
            through_seq=2,
        )


def test_wait_for_redacts_the_last_exception_before_raising() -> None:
    secret = "runtime-wait-secret"

    def fail() -> object:
        raise RuntimeError(secret)

    with pytest.raises(RuntimeError) as captured:
        _wait_for(
            fail,
            lambda _value: False,
            "redacted convergence",
            timeout=0.01,
            redact=lambda value: value.replace(secret, "[REDACTED]"),
        )
    assert secret not in str(captured.value)
    assert "[REDACTED]" in str(captured.value)


def test_main_redacts_product_exception_and_diagnostics_before_propagating(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    secret = "runtime-product-secret"

    class RuntimeFixture:
        def __init__(self, _args: object) -> None:
            pass

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

        def diagnostics(self) -> str:
            return f"diagnostic={secret}"

        def redact(self, value: str) -> str:
            return value.replace(secret, "[REDACTED]")

    monkeypatch.setattr("scripts.e2e.run_slice_a_native.NativeRuntime", RuntimeFixture)
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native.validate_generated_client_provenance",
        lambda: None,
    )
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native.validate_runtime_candidates", lambda _args: None
    )
    monkeypatch.setattr(
        "scripts.e2e.run_slice_a_native._run_product_chain",
        lambda _runtime: (_ for _ in ()).throw(RuntimeError(secret)),
    )
    monkeypatch.setattr(sys, "argv", ["run_slice_a_native.py"])

    with pytest.raises(RuntimeError) as captured:
        main()
    emitted = capsys.readouterr()
    assert secret not in str(captured.value)
    assert secret not in emitted.out + emitted.err
    assert "[REDACTED]" in str(captured.value)
    assert "diagnostic=[REDACTED]" in emitted.err

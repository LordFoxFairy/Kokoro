from __future__ import annotations

import argparse
import inspect
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
RUNNER = ROOT / "scripts/database/run_in_fresh_pg18.py"
FOUNDATION = ROOT / "database/schema/00-foundation.sql"

CHILD_SCRIPT = r"""
import json
import os
import sys
import time
import psycopg

marker = sys.argv[1]
with psycopg.connect(os.environ["DATABASE_URL_KOKORO_APP"]) as conn:
    conn.execute("CREATE TABLE isolation_marker (value text PRIMARY KEY)")
    conn.execute("INSERT INTO isolation_marker(value) VALUES (%s)", (marker,))
    rows = conn.execute("SELECT value FROM isolation_marker ORDER BY value").fetchall()
    schema = conn.execute("SELECT to_regnamespace('kokoro')::text").fetchone()[0]
    extension_schema = conn.execute(
        "SELECT n.nspname FROM pg_extension e "
        "JOIN pg_namespace n ON n.oid = e.extnamespace "
        "WHERE e.extname = 'pgcrypto'"
    ).fetchone()[0]
    search_path = conn.execute("SHOW search_path").fetchone()[0]
    marker_schema = conn.execute(
        "SELECT schemaname FROM pg_tables WHERE tablename = 'isolation_marker'"
    ).fetchone()[0]

assert os.environ["DATABASE_URL_KOKORO_APP"] == os.environ["KOKORO_TEST_DATABASE_URL"]
assert rows == [(marker,)]
assert schema == "kokoro"
assert extension_schema == "kokoro"
assert search_path == "kokoro, pg_catalog"
assert marker_schema == "kokoro"
time.sleep(0.5)
print(json.dumps({"marker": marker, "databaseUrl": os.environ["KOKORO_TEST_DATABASE_URL"]}))
"""


def _docker_names(kind: str, prefix: str) -> list[str]:
    if kind == "container":
        command = ["docker", "ps", "-a", "--format", "{{.Names}}"]
    else:
        command = ["docker", "volume", "ls", "--format", "{{.Name}}"]
    output = subprocess.run(command, check=True, text=True, capture_output=True).stdout
    return sorted(name for name in output.splitlines() if name.startswith(prefix))


def _runner_command(label: str, *child: str) -> list[str]:
    return [
        sys.executable,
        str(RUNNER),
        "--label",
        label,
        "--cwd",
        str(ROOT),
        "--baseline",
        str(FOUNDATION),
        "--",
        *child,
    ]


def test_two_fresh_pg18_runners_are_isolated_and_clean_up() -> None:
    token = uuid.uuid4().hex[:10]
    labels = [f"chat-{token}", f"agent-{token}"]
    prefix = "kokoro-pg18-"
    before_containers = _docker_names("container", prefix)
    before_volumes = _docker_names("volume", prefix)

    processes = [
        subprocess.Popen(
            _runner_command(label, sys.executable, "-c", CHILD_SCRIPT, label),
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for label in labels
    ]
    results = [process.communicate(timeout=90) for process in processes]

    for label, process, (stdout, stderr) in zip(labels, processes, results, strict=True):
        assert process.returncode == 0, stderr
        record = json.loads(stdout.strip().splitlines()[-1])
        assert record["marker"] == label
        assert "127.0.0.1:5432/" not in record["databaseUrl"]
    assert _docker_names("container", prefix) == before_containers
    assert _docker_names("volume", prefix) == before_volumes


def test_failed_child_exit_is_preserved_and_resources_are_removed() -> None:
    token = uuid.uuid4().hex[:10]
    label = f"failure-{token}"
    prefix = "kokoro-pg18-"
    before_containers = _docker_names("container", prefix)
    before_volumes = _docker_names("volume", prefix)

    result = subprocess.run(
        _runner_command(label, sys.executable, "-c", "raise SystemExit(7)"),
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
    )

    assert result.returncode == 7, result.stderr
    assert _docker_names("container", prefix) == before_containers
    assert _docker_names("volume", prefix) == before_volumes


@pytest.mark.parametrize(
    ("signum", "expected_exit"),
    [(signal.SIGINT, 130), (signal.SIGTERM, 143)],
)
def test_real_signal_removes_postgres_container_and_volume(
    tmp_path: Path, signum: signal.Signals, expected_exit: int
) -> None:
    token = uuid.uuid4().hex[:10]
    label = f"signal-{signum.name.lower()}-{token}"
    marker = tmp_path / "child-ready"
    child = (
        "from pathlib import Path; import sys, time; "
        "Path(sys.argv[1]).write_text('ready'); time.sleep(60)"
    )
    process = subprocess.Popen(
        _runner_command(label, sys.executable, "-c", child, str(marker)),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.monotonic() + 30
    while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    assert marker.exists(), process.communicate(timeout=5)[1]

    os.kill(process.pid, signum)
    _stdout, stderr = process.communicate(timeout=20)

    assert process.returncode == expected_exit, stderr
    assert not [
        name
        for name in _docker_names("container", "kokoro-pg18-")
        if token in name
    ]
    assert not [
        name for name in _docker_names("volume", "kokoro-pg18-") if token in name
    ]


@pytest.mark.parametrize("interrupt_during", ["volume", "container"])
def test_signal_between_docker_create_and_return_still_removes_owned_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interrupt_during: str
) -> None:
    from scripts.database import run_in_fresh_pg18 as runner

    baseline = tmp_path / "baseline.sql"
    baseline.write_text("SELECT 1;\n", encoding="utf-8")
    resources: dict[tuple[str, str], str] = {}
    removed: set[tuple[str, str]] = set()

    def completed(
        arguments: tuple[str, ...], returncode: int = 0, stdout: str = ""
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(["docker", *arguments], returncode, stdout, "")

    def fake_docker(
        *arguments: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        del check
        if arguments[:2] == ("volume", "create"):
            name = arguments[-1]
            owner = next(
                value.split("=", 1)[1]
                for index, value in enumerate(arguments)
                if arguments[index - 1 : index] == ("--label",)
                and value.startswith("kokoro.pg18.run=")
            )
            resources[("volume", name)] = owner
            if interrupt_during == "volume":
                raise runner.RunnerSignal(signal.SIGTERM)
            return completed(arguments, stdout=f"{name}\n")
        if arguments[0] == "run":
            name = arguments[arguments.index("--name") + 1]
            owner = next(
                value.split("=", 1)[1]
                for index, value in enumerate(arguments)
                if arguments[index - 1 : index] == ("--label",)
                and value.startswith("kokoro.pg18.run=")
            )
            resources[("container", name)] = owner
            if interrupt_during == "container":
                raise runner.RunnerSignal(signal.SIGTERM)
            return completed(arguments, stdout="container-id\n")
        if arguments[:2] in (("container", "inspect"), ("volume", "inspect")):
            resource = (arguments[0], arguments[-1])
            if resource not in resources:
                return completed(arguments, returncode=1)
            owner = resources[resource]
            inspection = (
                [{"Config": {"Labels": {"kokoro.pg18.run": owner}}}]
                if resource[0] == "container"
                else [{"Labels": {"kokoro.pg18.run": owner}}]
            )
            return completed(arguments, stdout=json.dumps(inspection))
        if arguments[:2] in (("rm", "--force"), ("volume", "rm")):
            kind = "container" if arguments[0] == "rm" else "volume"
            name = arguments[-1]
            removed.add((kind, name))
            resources.pop((kind, name), None)
            return completed(arguments)
        raise AssertionError(f"unexpected Docker call: {arguments}")

    monkeypatch.setattr(runner, "_run_docker", fake_docker)
    args = argparse.Namespace(
        label="signal-window",
        cwd=tmp_path,
        baseline=baseline,
        require_clean=False,
        command=["true"],
    )

    with pytest.raises(runner.RunnerSignal):
        runner.run(args)

    assert not resources
    assert {kind for kind, _name in removed} >= {interrupt_during}


def test_failed_create_does_not_remove_a_foreign_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.database import run_in_fresh_pg18 as runner

    baseline = tmp_path / "baseline.sql"
    baseline.write_text("SELECT 1;\n", encoding="utf-8")
    removed: list[tuple[str, ...]] = []
    foreign_volume: str | None = None

    def fake_docker(
        *arguments: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        nonlocal foreign_volume
        if arguments[:2] == ("volume", "create"):
            foreign_volume = arguments[-1]
            raise subprocess.CalledProcessError(1, ["docker", *arguments])
        if (
            arguments[:2] == ("volume", "inspect")
            and arguments[-1] == foreign_volume
        ):
            inspection = [{"Labels": {"kokoro.pg18.run": "another-run"}}]
            return subprocess.CompletedProcess(
                ["docker", *arguments], 0, json.dumps(inspection), ""
            )
        if "rm" in arguments:
            removed.append(arguments)
        return subprocess.CompletedProcess(["docker", *arguments], 1, "", "not owned")

    monkeypatch.setattr(runner, "_run_docker", fake_docker)
    args = argparse.Namespace(
        label="foreign-resource",
        cwd=tmp_path,
        baseline=baseline,
        require_clean=False,
        command=["true"],
    )

    with pytest.raises(subprocess.CalledProcessError):
        runner.run(args)

    assert removed == []


def test_unlabeled_foreign_resource_is_not_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.database import run_in_fresh_pg18 as runner

    removed: list[tuple[str, ...]] = []

    def fake_docker(
        *arguments: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        del check
        if arguments[:2] == ("container", "inspect"):
            inspection = [{"Config": {"Labels": None}}]
            return subprocess.CompletedProcess(
                ["docker", *arguments], 0, json.dumps(inspection), ""
            )
        if "rm" in arguments:
            removed.append(arguments)
        return subprocess.CompletedProcess(["docker", *arguments], 0, "", "")

    monkeypatch.setattr(runner, "_run_docker", fake_docker)
    resource = runner.OwnedDockerResource(
        "container", "foreign-container", "this-run"
    )

    runner._remove_if_owned(resource)

    assert removed == []


def _install_successful_runner_body(
    monkeypatch: pytest.MonkeyPatch, runner: object
) -> None:
    completed = subprocess.CompletedProcess(["docker"], 0, "", "")
    monkeypatch.setattr(runner, "_run_docker", lambda *args, **kwargs: completed)
    monkeypatch.setattr(runner, "_assert_owned", lambda resource: None)
    monkeypatch.setattr(runner, "_published_port", lambda name, pending: 54321)
    monkeypatch.setattr(
        runner, "_wait_for_postgres", lambda url, name, pending: True
    )
    monkeypatch.setattr(
        runner, "_initialize_database", lambda admin_url, app_url, baseline: None
    )
    monkeypatch.setattr(
        runner, "_run_child", lambda command, cwd, url, pending: 0
    )


def _track_signal_handlers(
    monkeypatch: pytest.MonkeyPatch, runner: object
) -> tuple[dict[signal.Signals, object], dict[signal.Signals, object]]:
    originals: dict[signal.Signals, object] = {
        signal.SIGINT: object(),
        signal.SIGTERM: object(),
    }
    active = originals.copy()

    def fake_getsignal(signum: signal.Signals) -> object:
        return active[signum]

    def fake_signal(signum: signal.Signals, handler: object) -> object:
        previous = active[signum]
        active[signum] = handler
        return previous

    monkeypatch.setattr(runner.signal, "getsignal", fake_getsignal)
    monkeypatch.setattr(runner.signal, "signal", fake_signal)
    return originals, active


def test_signal_during_cleanup_is_deferred_until_all_resources_and_handlers_finish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.database import run_in_fresh_pg18 as runner

    baseline = tmp_path / "baseline.sql"
    baseline.write_text("SELECT 1;\n", encoding="utf-8")
    _install_successful_runner_body(monkeypatch, runner)
    originals, active = _track_signal_handlers(monkeypatch, runner)
    cleanup_attempts: list[str] = []

    def fake_remove(resource: runner.OwnedDockerResource) -> None:
        cleanup_attempts.append(resource.kind)
        if resource.kind == "container":
            handler = active[signal.SIGTERM]
            assert callable(handler)
            handler(signal.SIGTERM, None)

    monkeypatch.setattr(runner, "_remove_if_owned", fake_remove)
    args = argparse.Namespace(
        label="cleanup-signal",
        cwd=tmp_path,
        baseline=baseline,
        require_clean=False,
        command=["true"],
    )

    with pytest.raises(runner.RunnerSignal) as raised:
        runner.run(args)

    assert raised.value.signum == signal.SIGTERM
    assert cleanup_attempts == ["container", "volume"]
    assert active == originals


def test_cleanup_errors_are_aggregated_after_all_resources_and_handler_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.database import run_in_fresh_pg18 as runner

    baseline = tmp_path / "baseline.sql"
    baseline.write_text("SELECT 1;\n", encoding="utf-8")
    _install_successful_runner_body(monkeypatch, runner)
    originals, active = _track_signal_handlers(monkeypatch, runner)
    cleanup_attempts: list[str] = []

    def fake_remove(resource: runner.OwnedDockerResource) -> None:
        cleanup_attempts.append(resource.kind)
        raise RuntimeError(f"{resource.kind} cleanup boom")

    monkeypatch.setattr(runner, "_remove_if_owned", fake_remove)
    args = argparse.Namespace(
        label="cleanup-errors",
        cwd=tmp_path,
        baseline=baseline,
        require_clean=False,
        command=["true"],
    )

    with pytest.raises(runner.CleanupError) as raised:
        runner.run(args)

    assert cleanup_attempts == ["container", "volume"]
    assert active == originals
    assert "container cleanup boom" in str(raised.value)
    assert "volume cleanup boom" in str(raised.value)


def test_signal_at_body_cleanup_handoff_cannot_skip_cleanup_or_handler_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.database import run_in_fresh_pg18 as runner

    baseline = tmp_path / "baseline.sql"
    baseline.write_text("SELECT 1;\n", encoding="utf-8")
    _install_successful_runner_body(monkeypatch, runner)
    originals, active = _track_signal_handlers(monkeypatch, runner)
    cleanup_attempts: list[str] = []
    monkeypatch.setattr(
        runner,
        "_remove_if_owned",
        lambda resource: cleanup_attempts.append(resource.kind),
    )
    source, first_line = inspect.getsourcelines(runner.run)
    handoff_line = first_line + next(
        index for index, line in enumerate(source) if "cleanup_started = True" in line
    )
    injected = False

    def inject_at_handoff(frame: object, event: str, argument: object) -> object:
        del argument
        nonlocal injected
        if (
            not injected
            and event == "line"
            and getattr(frame, "f_code") is runner.run.__code__
            and getattr(frame, "f_lineno") == handoff_line
        ):
            injected = True
            handler = active[signal.SIGTERM]
            assert callable(handler)
            handler(signal.SIGTERM, None)
        return inject_at_handoff

    args = argparse.Namespace(
        label="handoff-signal",
        cwd=tmp_path,
        baseline=baseline,
        require_clean=False,
        command=["true"],
    )
    sys.settrace(inject_at_handoff)
    try:
        with pytest.raises(runner.RunnerSignal) as raised:
            runner.run(args)
    finally:
        sys.settrace(None)

    assert injected
    assert raised.value.signum == signal.SIGTERM
    assert cleanup_attempts == ["container", "volume"]
    assert active == originals


def test_child_wait_polls_pending_signal_and_terminates_without_async_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.database import run_in_fresh_pg18 as runner

    class FakeChild:
        def __init__(self) -> None:
            self.terminated = False

        def poll(self) -> int | None:
            return -signal.SIGTERM if self.terminated else None

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, timeout: float | None = None) -> int:
            assert self.terminated
            return -signal.SIGTERM

        def kill(self) -> None:
            raise AssertionError("terminate should finish the fixture child")

    child = FakeChild()
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *args, **kwargs: child)

    result = runner._run_child(
        ["fixture-child"],
        tmp_path,
        "postgresql://fixture",
        lambda: signal.SIGINT,
    )

    assert child.terminated
    assert result == -signal.SIGTERM

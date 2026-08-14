from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import psycopg


POSTGRES_IMAGE = "postgres:18"
RESOURCE_PREFIX = "kokoro-pg18"
OWNERSHIP_LABEL = "kokoro.pg18.run"


class RunnerSignal(BaseException):
    def __init__(self, signum: int) -> None:
        self.signum = signum


class CleanupError(RuntimeError):
    def __init__(self, errors: list[BaseException]) -> None:
        self.errors = tuple(errors)
        details = "; ".join(f"{type(error).__name__}: {error}" for error in errors)
        super().__init__(f"Docker cleanup failed: {details}")


class OwnedDockerResource:
    def __init__(self, kind: str, name: str, ownership_token: str) -> None:
        self.kind = kind
        self.name = name
        self.ownership_token = ownership_token


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a command in an isolated PostgreSQL 18 database")
    parser.add_argument("--label", required=True)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--baseline", type=Path, default=Path("database/baseline/kokoro.sql"))
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a child command is required after --")
    return args


def _resource_name(label: str) -> str:
    sanitized = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "lane"
    sanitized = sanitized[:30].rstrip("-")
    return f"{RESOURCE_PREFIX}-{sanitized}-{os.getpid()}-{secrets.token_hex(4)}"


def _run_docker(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", *arguments],
        check=check,
        text=True,
        capture_output=True,
    )


def _assert_committed_baseline(baseline: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(baseline.parent), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError("--require-clean baseline is outside a Git worktree")
    root = Path(result.stdout.strip()).resolve()
    try:
        relative = baseline.relative_to(root)
    except ValueError as error:
        raise RuntimeError("--require-clean baseline is outside the Root worktree") from error
    committed = subprocess.run(
        ["git", "show", f"HEAD:{relative.as_posix()}"],
        cwd=root,
        capture_output=True,
    )
    if committed.returncode != 0:
        raise RuntimeError(f"baseline is uncommitted: {relative.as_posix()}")
    if committed.stdout != baseline.read_bytes():
        raise RuntimeError(f"baseline is dirty: {relative.as_posix()}")


def _published_port(
    container_name: str, pending_signal: Callable[[], int | None]
) -> int:
    deadline = time.monotonic() + 10
    result: subprocess.CompletedProcess[str] | None = None
    while time.monotonic() < deadline:
        if pending_signal() is not None:
            raise RunnerSignal(pending_signal() or signal.SIGTERM)
        result = _run_docker("port", container_name, "5432/tcp", check=False)
        for line in result.stdout.splitlines():
            match = re.fullmatch(r"127\.0\.0\.1:(\d+)", line.strip())
            if match:
                return int(match.group(1))
        time.sleep(0.1)
    detail = "" if result is None else f"{result.stdout}{result.stderr}"
    raise RuntimeError(f"Docker did not publish a loopback PostgreSQL port: {detail!r}")


def _wait_for_postgres(
    admin_url: str,
    container_name: str,
    pending_signal: Callable[[], int | None],
) -> bool:
    deadline = time.monotonic() + 60
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if pending_signal() is not None:
            return False
        try:
            with psycopg.connect(admin_url, connect_timeout=2):
                return True
        except psycopg.Error as error:
            last_error = error
            time.sleep(0.25)
    logs = _run_docker("logs", container_name, check=False).stdout
    raise RuntimeError(f"PostgreSQL 18 did not become ready: {last_error}\n{logs}")


def _initialize_database(admin_url: str, app_url: str, baseline: bytes) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute("CREATE ROLE kokoro_app LOGIN PASSWORD 'kokoro'")
        connection.execute("CREATE DATABASE kokoro OWNER kokoro_app")
    sql = baseline.decode("utf-8")
    with psycopg.connect(app_url) as connection:
        connection.execute(sql)


def _run_child(
    command: list[str],
    cwd: Path,
    database_url: str,
    pending_signal: Callable[[], int | None],
) -> int:
    environment = os.environ.copy()
    environment["DATABASE_URL_KOKORO_APP"] = database_url
    environment["KOKORO_TEST_DATABASE_URL"] = database_url
    child = subprocess.Popen(command, cwd=cwd, env=environment)
    try:
        while True:
            result = child.poll()
            if result is not None:
                return result
            if pending_signal() is not None:
                child.terminate()
                try:
                    return child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    return child.wait()
            time.sleep(0.05)
    except BaseException:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        raise


def _wait_until_removed(kind: str, name: str) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        result = _run_docker(kind, "inspect", name, check=False)
        if result.returncode != 0:
            return
        time.sleep(0.05)
    raise RuntimeError(f"Docker {kind} cleanup did not finish: {name}")


def _resource_labels(resource: OwnedDockerResource) -> dict[str, str] | None:
    result = _run_docker(resource.kind, "inspect", resource.name, check=False)
    if result.returncode != 0:
        return None
    try:
        inspection = json.loads(result.stdout)
        record = inspection[0]
        labels = (
            record["Config"]["Labels"]
            if resource.kind == "container"
            else record["Labels"]
        )
    except (json.JSONDecodeError, IndexError, KeyError, TypeError) as error:
        raise RuntimeError(
            f"cannot verify Docker {resource.kind} ownership: {resource.name}"
        ) from error
    if labels is None:
        return {}
    if not isinstance(labels, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in labels.items()
    ):
        raise RuntimeError(
            f"invalid Docker {resource.kind} labels: {resource.name}"
        )
    return labels


def _assert_owned(resource: OwnedDockerResource) -> None:
    labels = _resource_labels(resource)
    if labels is None or labels.get(OWNERSHIP_LABEL) != resource.ownership_token:
        raise RuntimeError(
            f"Docker {resource.kind} is not owned by this runner: {resource.name}"
        )


def _remove_if_owned(resource: OwnedDockerResource) -> None:
    labels = _resource_labels(resource)
    if labels is None or labels.get(OWNERSHIP_LABEL) != resource.ownership_token:
        return
    if resource.kind == "container":
        _run_docker("rm", "--force", resource.name, check=False)
    else:
        _run_docker("volume", "rm", "--force", resource.name, check=False)
    _wait_until_removed(resource.kind, resource.name)


def run(args: argparse.Namespace) -> int:
    cwd = args.cwd.resolve()
    if not cwd.is_dir():
        raise RuntimeError(f"child cwd is not a directory: {cwd}")
    baseline = args.baseline
    if not baseline.is_absolute():
        baseline = (Path.cwd() / baseline).resolve()
    if baseline.is_symlink():
        raise RuntimeError(f"baseline symlink is forbidden: {baseline}")
    baseline_bytes = baseline.read_bytes()
    if args.require_clean:
        _assert_committed_baseline(baseline)

    ownership_token = secrets.token_hex(16)
    container_name = _resource_name(args.label)
    volume_name = f"{container_name}-data"
    container = OwnedDockerResource("container", container_name, ownership_token)
    volume = OwnedDockerResource("volume", volume_name, ownership_token)
    previous_handlers: dict[signal.Signals, object] = {}
    pending_signal: int | None = None
    cleanup_started = False

    def handle_signal(signum: int, _frame: object) -> None:
        nonlocal pending_signal
        if pending_signal is None:
            pending_signal = signum
        if cleanup_started:
            return

    for sig in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[sig] = signal.getsignal(sig)
        signal.signal(sig, handle_signal)
    result_code: int | None = None
    body_error: BaseException | None = None
    cleanup_errors: list[BaseException] = []
    try:
        try:
            _run_docker(
                "volume",
                "create",
                "--label",
                "kokoro.pg18.runner=true",
                "--label",
                f"{OWNERSHIP_LABEL}={ownership_token}",
                volume_name,
            )
            if pending_signal is None:
                _assert_owned(volume)
            if pending_signal is None:
                _run_docker(
                    "run",
                    "--detach",
                    "--name",
                    container_name,
                    "--label",
                    "kokoro.pg18.runner=true",
                    "--label",
                    f"{OWNERSHIP_LABEL}={ownership_token}",
                    "--volume",
                    f"{volume_name}:/var/lib/postgresql",
                    "--env",
                    "POSTGRES_USER=postgres",
                    "--env",
                    "POSTGRES_PASSWORD=postgres",
                    "--publish",
                    "127.0.0.1::5432",
                    POSTGRES_IMAGE,
                )
            if pending_signal is None:
                _assert_owned(container)
            if pending_signal is None:
                port = _published_port(container_name, lambda: pending_signal)
                admin_url = (
                    f"postgresql://postgres:postgres@127.0.0.1:{port}/postgres"
                )
                app_url = (
                    f"postgresql://kokoro_app:kokoro@127.0.0.1:{port}/kokoro"
                )
                ready = _wait_for_postgres(
                    admin_url, container_name, lambda: pending_signal
                )
                if ready and pending_signal is None:
                    _initialize_database(admin_url, app_url, baseline_bytes)
                if pending_signal is None:
                    result_code = _run_child(
                        args.command, cwd, app_url, lambda: pending_signal
                    )
        except BaseException as error:
            body_error = error
    finally:
        cleanup_started = True
        for resource in (container, volume):
            try:
                _remove_if_owned(resource)
            except BaseException as error:
                cleanup_errors.append(error)
        for sig, previous in previous_handlers.items():
            try:
                signal.signal(sig, previous)
            except BaseException as error:
                cleanup_errors.append(error)

    signal_number = pending_signal
    if signal_number is None and isinstance(body_error, RunnerSignal):
        signal_number = body_error.signum
    if signal_number is not None:
        signal_error = RunnerSignal(signal_number)
        if cleanup_errors:
            signal_error.add_note(str(CleanupError(cleanup_errors)))
        raise signal_error
    if cleanup_errors:
        cleanup_error = CleanupError(cleanup_errors)
        if body_error is not None:
            raise cleanup_error from body_error
        raise cleanup_error
    if body_error is not None:
        raise body_error
    assert result_code is not None
    return result_code


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        return run(args)
    except RunnerSignal as error:
        return 128 + error.signum
    except (OSError, UnicodeError, psycopg.Error, RuntimeError, subprocess.SubprocessError) as error:
        print(f"fresh PG18 runner failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import signal
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeAlias
from urllib.request import urlopen

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.slice_a.create_fixture_dir import validate_fixture_directory
from scripts.slice_a.create_secrets import validate_secret_directory
from scripts.slice_a.guardian import identity_matches as _identity_matches
from scripts.slice_a.guardian import process_identity as _process_identity
from scripts.slice_a.guardian import group_alive as _group_alive
from scripts.slice_a.guardian import stop_owned_group as _stop_owned_group
from scripts.slice_a.seed import (
    SITE_HOST,
    SITE_ID,
    bootstrap_model,
    seed_site,
    write_seed_artifacts,
)

JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)
STATE_MARKER = ".kokoro-slice-a-owner"
STATE_MARKER_CONTENT = "kokoro-slice-a:state:v1\n"
STATE_FILE = "runtime.json"
CONTROL_FILE = "control.json"
LITELLM_VERSION = "1.80.11"
LITELLM_FASTAPI_VERSION = "0.121.3"
LITELLM_PYTHON = "3.11"
FIXED_PORTS = {
    "litellm": 4000,
    "iam": 7202,
    "model": 7203,
    "capability": 7204,
    "chat": 7205,
    "agent": 7206,
}
BACKEND_PROCESSES = {
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
DEFAULT_COMMITS = {
    "iam": "1ca2ced348832c81dd946ddb8b754640d77ced74",
    "chat": "3b5b0b5f8036d466c3fa4354f254b1444bcaf2aa",
    "agent": "5de3a2d7782e4c6eb68acf2c1aba1653794f3ed4",
    "model": "400b6ad39c6f03d8a9be93f24736cf27a95cbbcb",
    "capability": "ca0b3d4bdb0c8f06380d889508fa4773745db7c2",
}
DEFAULT_TREES = {
    "iam": "475d0ccfb345597c508dc02c3a2cc6382fe79b2f",
    "chat": "213b874868cbb8008c603ae8f50eecfd07c0c8c9",
    "agent": "7bc84f58319a653087ba895ca7a87e2e5c86a6ba",
    "model": "122f938d5617095cfa11463097cd4c9f822972c5",
    "capability": "49f5aa0e4f9b35735f2eee7bf37aef055350f218",
}


@dataclass(frozen=True, slots=True)
class ProcessSpec:
    name: str
    argv: tuple[str, ...]
    cwd: Path
    environment: dict[str, str]
    port: int
    readiness: str


def build_service_commands(_roots: dict[str, Path]) -> dict[str, tuple[str, ...]]:
    return {
        "iam": ("pnpm", "dev"),
        "model": ("pnpm", "dev"),
        "capability": ("pnpm", "dev"),
        "chat": ("npm", "run", "dev"),
        "agent": ("uv", "run", "--frozen", "kokoro-agent-local", "--dev"),
    }


def build_litellm_command(config_path: Path) -> tuple[str, ...]:
    return (
        "uvx",
        "--python",
        LITELLM_PYTHON,
        "--from",
        f"litellm[proxy]=={LITELLM_VERSION}",
        "--with",
        f"fastapi=={LITELLM_FASTAPI_VERSION}",
        "litellm",
        "--config",
        str(config_path),
        "--host",
        "127.0.0.1",
        "--port",
        "4000",
    )


def find_postgres_18_bin() -> Path:
    candidates: list[Path] = []
    if configured := os.environ.get("KOKORO_POSTGRES18_BIN"):
        candidates.append(Path(configured))
    try:
        result = subprocess.run(
            ["pg_config", "--bindir"], check=True, capture_output=True, text=True
        )
        candidates.append(Path(result.stdout.strip()))
    except (OSError, subprocess.SubprocessError):
        pass
    candidates.extend(
        (
            Path("/opt/homebrew/opt/postgresql@18/bin"),
            Path("/usr/local/opt/postgresql@18/bin"),
        )
    )
    for candidate in candidates:
        postgres, initdb = candidate / "postgres", candidate / "initdb"
        if (
            not postgres.is_file()
            or not os.access(postgres, os.X_OK)
            or not initdb.is_file()
        ):
            continue
        version = subprocess.run(
            [str(postgres), "--version"], check=True, capture_output=True, text=True
        ).stdout
        if "PostgreSQL) 18." in version:
            return candidate.resolve()
    raise RuntimeError("native PostgreSQL 18 binaries were not found")


def validate_candidate(path: Path, expected_commit: str, expected_tree: str) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", expected_commit) is None:
        raise RuntimeError("candidate commit must be a full lowercase 40-hex object ID")
    if re.fullmatch(r"[0-9a-f]{40}", expected_tree) is None:
        raise RuntimeError("candidate tree must be a full lowercase 40-hex object ID")
    path = path.absolute()
    if path.is_symlink() or not (path / ".git").exists():
        raise RuntimeError(f"candidate is not a Git worktree: {path}")
    commit = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    object_check = subprocess.run(
        ["git", "-C", str(path), "cat-file", "-t", expected_commit],
        check=False,
        capture_output=True,
        text=True,
    )
    if object_check.returncode != 0:
        raise RuntimeError(f"candidate commit mismatch: {path} lacks {expected_commit}")
    object_type = object_check.stdout.strip()
    if object_type != "commit":
        raise RuntimeError("candidate object is not a commit")
    if commit != expected_commit:
        raise RuntimeError(
            f"candidate commit mismatch: {path} expected {expected_commit}, got {commit}"
        )
    tree = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD^{tree}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if tree != expected_tree:
        raise RuntimeError(
            f"candidate tree mismatch: {path} expected {expected_tree}, got {tree}"
        )
    status = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain=v1", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if status:
        raise RuntimeError(f"candidate is not clean: {path}")


def write_runtime_state(
    path: Path,
    *,
    processes: dict[str, JsonValue],
    public: dict[str, JsonValue],
    secret_values: frozenset[str],
) -> None:
    payload: dict[str, JsonValue] = {
        "version": 1,
        "processes": processes,
        "public": public,
    }
    encoded = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if any(value and value in encoded for value in secret_values):
        raise RuntimeError("refusing to serialize a secret into runtime state")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _free_ports(count: int, excluded: set[int]) -> tuple[int, ...]:
    ports: list[int] = []
    while len(ports) < count:
        candidate = _free_port()
        if candidate not in excluded and candidate not in ports:
            ports.append(candidate)
    return tuple(ports)


def _ensure_port_free(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as error:
            if error.errno == errno.EADDRINUSE:
                raise RuntimeError(f"port {port} is already occupied") from None
            raise RuntimeError(f"cannot verify port {port} is free") from None


def _minimal_environment() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "en_US.UTF-8"),
        "NO_COLOR": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _redact_text(value: str, secrets: frozenset[str]) -> str:
    expanded = set(secrets)
    for secret in secrets:
        expanded.update(line for line in secret.splitlines() if len(line) >= 16)
    for secret in sorted(expanded, key=len, reverse=True):
        if secret:
            value = value.replace(secret, "[REDACTED]")
    return value


def _spawn(
    spec: ProcessSpec,
    state_dir: Path,
    before_exec: Callable[[subprocess.Popen[bytes]], None] | None = None,
) -> subprocess.Popen[bytes]:
    log_path = state_dir / "logs" / f"{spec.name}.log"
    descriptor = os.open(
        log_path,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    log = os.fdopen(descriptor, "wb", buffering=0)
    gate_read, gate_write = os.pipe()
    wrapper = (
        "import os,sys; fd=int(sys.argv[1]); gate=os.read(fd,1); os.close(fd); "
        "sys.exit(125) if gate != b'1' else None; "
        "os.execvpe(sys.argv[2],sys.argv[2:],os.environ)"
    )
    try:
        process = subprocess.Popen(
            (sys.executable, "-c", wrapper, str(gate_read), *spec.argv),
            cwd=spec.cwd,
            env=spec.environment,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            pass_fds=(gate_read,),
        )
        os.close(gate_read)
        gate_read = -1
        try:
            if before_exec is not None:
                before_exec(process)
            os.write(gate_write, b"1")
        except BaseException:
            os.close(gate_write)
            gate_write = -1
            process.wait(timeout=5)
            raise
        return process
    finally:
        if gate_read >= 0:
            os.close(gate_read)
        if gate_write >= 0:
            os.close(gate_write)
        log.close()


def _stop_process(process: subprocess.Popen[bytes], timeout: float = 15.0) -> None:
    try:
        identity = _process_identity(process.pid)
    except ProcessLookupError:
        identity = ""
    _stop_owned_group(
        pid=process.pid,
        pgid=process.pid,
        session_id=process.pid,
        identity=identity,
        timeout=timeout,
    )
    try:
        process.wait(timeout=0.2)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"owned process leader was not reaped: {process.pid}")


def _stop_process_inventory(
    processes: dict[str, subprocess.Popen[bytes]], secrets: frozenset[str]
) -> list[str]:
    errors: list[str] = []
    for name in reversed(tuple(processes)):
        try:
            _stop_process(processes[name])
        except BaseException as error:
            errors.append(
                _redact_text(f"{name}: {type(error).__name__}: {error}", secrets)
            )
    return errors


def _owner_alive(config: dict[str, object]) -> bool:
    pid, identity = config.get("owner_pid"), config.get("owner_identity")
    if pid is None and identity is None:
        return True
    if not isinstance(pid, int) or not isinstance(identity, str) or not identity:
        raise RuntimeError("owner PID and identity must be supplied together")
    return _identity_matches(pid, identity)


def _terminate_supervisor(
    supervisor: subprocess.Popen[bytes], *, timeout: float = 40.0
) -> None:
    try:
        identity = _process_identity(supervisor.pid)
    except ProcessLookupError:
        identity = ""
    _stop_owned_group(
        pid=supervisor.pid,
        pgid=supervisor.pid,
        session_id=supervisor.pid,
        identity=identity,
        timeout=timeout,
    )
    try:
        supervisor.wait(timeout=0.2)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Slice A supervisor leader was not reaped")


def _wait_until(
    name: str,
    process: subprocess.Popen[bytes],
    probe: Callable[[], None],
    log_path: Path,
    *,
    timeout: float = 90.0,
    secrets: frozenset[str] = frozenset(),
) -> None:
    deadline, last_error = time.monotonic() + timeout, "not probed"
    while time.monotonic() < deadline:
        if (code := process.poll()) is not None:
            output = (
                log_path.read_text(errors="replace")[-8000:]
                if log_path.exists()
                else ""
            )
            raise RuntimeError(
                _redact_text(
                    f"{name} exited before readiness ({code})\n{output}", secrets
                )
            )
        try:
            probe()
            return
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            last_error = _redact_text(str(error), secrets)
        time.sleep(0.15)
    output = log_path.read_text(errors="replace")[-8000:] if log_path.exists() else ""
    raise RuntimeError(
        _redact_text(f"{name} readiness timed out: {last_error}\n{output}", secrets)
    )


def _http_probe(url: str) -> None:
    with urlopen(url, timeout=1) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP readiness returned {response.status}")


def _http2_probe(url: str) -> None:
    subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "--http2-prior-knowledge",
            "--max-time",
            "2",
            url,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def _grpc_health_probe(port: int, service: str) -> None:
    import grpc

    name = service.encode()
    request = bytes((0x0A, len(name))) + name
    try:
        with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
            response = channel.unary_unary(
                "/grpc.health.v1.Health/Check",
                request_serializer=lambda value: value,
                response_deserializer=lambda value: value,
            )(request, timeout=1)
    except grpc.RpcError as error:
        raise RuntimeError(f"gRPC health probe failed: {error.code().name}") from error
    if response != b"\x08\x01":
        raise RuntimeError(f"gRPC health is not SERVING: {response!r}")


def _redis_probe(port: int) -> None:
    with socket.create_connection(("127.0.0.1", port), timeout=0.5) as connection:
        connection.sendall(b"*1\r\n$4\r\nPING\r\n")
        if connection.recv(64) != b"+PONG\r\n":
            raise RuntimeError("Redis PING did not return PONG")


def _run_checked(argv: list[str], *, environment: dict[str, str] | None = None) -> None:
    subprocess.run(argv, check=True, env=environment, stdout=subprocess.DEVNULL)


def _postgres_spec(bindir: Path, state_dir: Path, port: int) -> ProcessSpec:
    data = state_dir / "postgres-data"
    _run_checked(
        [str(bindir / "initdb"), "-D", str(data), "-A", "trust", "-U", "postgres"]
    )
    return ProcessSpec(
        "postgres",
        (str(bindir / "postgres"), "-D", str(data), "-p", str(port), "-h", "127.0.0.1"),
        state_dir,
        _minimal_environment(),
        port,
        "pg_isready",
    )


def _provision_postgres(bindir: Path, port: int, baseline: Path) -> tuple[str, str]:
    connection = ["-h", "127.0.0.1", "-p", str(port), "-U", "postgres"]
    _run_checked([str(bindir / "createuser"), *connection, "kokoro_app"])
    _run_checked([str(bindir / "createdb"), *connection, "-O", "postgres", "kokoro"])
    admin_url = f"postgresql://postgres@127.0.0.1:{port}/kokoro"
    _run_checked(
        [str(bindir / "psql"), admin_url, "-v", "ON_ERROR_STOP=1", "-f", str(baseline)]
    )
    grants = "REVOKE ALL ON DATABASE kokoro FROM PUBLIC; GRANT CONNECT ON DATABASE kokoro TO kokoro_app; REVOKE CREATE ON SCHEMA kokoro FROM PUBLIC, kokoro_app; GRANT USAGE ON SCHEMA kokoro TO kokoro_app; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA kokoro TO kokoro_app;"
    _run_checked(
        [str(bindir / "psql"), admin_url, "-v", "ON_ERROR_STOP=1", "-c", grants]
    )
    app_url = f"postgresql://kokoro_app@127.0.0.1:{port}/kokoro"
    smoke = subprocess.run(
        [
            str(bindir / "psql"),
            app_url,
            "-v",
            "ON_ERROR_STOP=1",
            "-Atc",
            "SELECT current_user || '|' || current_setting('search_path') || '|' || (SELECT count(*)::text FROM kokoro.site_site)",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not smoke.startswith('kokoro_app|"$user", public|'):
        raise RuntimeError(
            f"app-role qualified SQL smoke used an unexpected connection context: {smoke!r}"
        )
    return admin_url, app_url


def _assert_committed_baseline(path: Path) -> None:
    relative = path.resolve().relative_to(ROOT)
    committed = subprocess.run(
        ["git", "show", f"HEAD:{relative.as_posix()}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    if committed != path.read_bytes():
        raise RuntimeError("Root baseline must be committed and clean")


def _record(
    spec: ProcessSpec, process: subprocess.Popen[bytes], state_dir: Path
) -> dict[str, JsonValue]:
    pgid, session_id = os.getpgid(process.pid), os.getsid(process.pid)
    if pgid != process.pid or session_id != process.pid:
        raise RuntimeError(f"{spec.name} did not start in a dedicated process session")
    return {
        "pid": process.pid,
        "pgid": pgid,
        "session_id": session_id,
        "start_identity": _process_identity(process.pid),
        "argv": list(spec.argv),
        "cwd": str(spec.cwd),
        "port": spec.port,
        "readiness": spec.readiness,
        "log": str(state_dir / "logs" / f"{spec.name}.log"),
    }


def _secret_values(secret_dir: Path) -> frozenset[str]:
    names = (
        "web.workload-token",
        "chat.workload-token",
        "agent.workload-token",
        "iam.refresh-derivation-key",
        "web.session-key",
        "litellm.api-key",
    )
    return frozenset((secret_dir / name).read_text() for name in names)


def _service_specs(
    roots: dict[str, Path],
    secret_dir: Path,
    fixture_dir: Path,
    app_url: str,
    redis_port: int,
) -> dict[str, ProcessSpec]:
    base, commands = _minimal_environment(), build_service_commands(roots)
    chat_token, web_token = (
        (secret_dir / "chat.workload-token").read_text(),
        (secret_dir / "web.workload-token").read_text(),
    )
    return {
        "iam": ProcessSpec(
            "iam",
            commands["iam"],
            roots["iam"],
            {
                **base,
                "DATABASE_URL": app_url,
                "KOKORO_IAM_BIND": "127.0.0.1:7202",
                "KOKORO_WEB_WORKLOAD_TOKEN_FILE": str(
                    secret_dir / "web.workload-token"
                ),
                "KOKORO_CHAT_WORKLOAD_TOKEN_FILE": str(
                    secret_dir / "chat.workload-token"
                ),
                "KOKORO_IAM_REFRESH_DERIVATION_KEY_FILE": str(
                    secret_dir / "iam.refresh-derivation-key"
                ),
                "KOKORO_IAM_JWT_PRIVATE_KEY_FILE": str(
                    secret_dir / "iam.jwt-private.pem"
                ),
                "KOKORO_IAM_MAGIC_LINK_DELIVERY": "fixture-file",
                "KOKORO_IAM_MAGIC_LINK_FIXTURE_SINK_FILE": str(
                    fixture_dir / "magic-links" / "iam.magic-link-fixture.jsonl"
                ),
            },
            7202,
            "http://127.0.0.1:7202/readyz",
        ),
        "model": ProcessSpec(
            "model",
            commands["model"],
            roots["model"],
            {
                **base,
                "DATABASE_URL_KOKORO_APP": app_url,
                "KOKORO_AGENT_WORKLOAD_TOKEN_FILE": str(
                    secret_dir / "agent.workload-token"
                ),
                "KOKORO_MODEL_HOST": "127.0.0.1",
                "KOKORO_MODEL_PORT": "7203",
            },
            7203,
            "http://127.0.0.1:7203/readyz",
        ),
        "capability": ProcessSpec(
            "capability",
            commands["capability"],
            roots["capability"],
            {
                **base,
                "DATABASE_URL_KOKORO_APP": app_url,
                "KOKORO_AGENT_WORKLOAD_TOKEN_FILE": str(
                    secret_dir / "agent.workload-token"
                ),
                "KOKORO_CAPABILITY_HOST": "127.0.0.1",
                "KOKORO_CAPABILITY_PORT": "7204",
            },
            7204,
            "http://127.0.0.1:7204/readyz",
        ),
        "agent": ProcessSpec(
            "agent",
            commands["agent"],
            roots["agent"],
            {
                **base,
                "DATABASE_URL_KOKORO_APP": app_url,
                "KOKORO_SLICE_A_REDIS_URL": f"redis://127.0.0.1:{redis_port}/0",
                "KOKORO_SLICE_A_GRPC_BIND": "127.0.0.1:7206",
                "KOKORO_SLICE_A_CHAT_WORKLOAD_TOKEN_FILE": str(
                    secret_dir / "chat.workload-token"
                ),
                "KOKORO_SLICE_A_AGENT_WORKLOAD_TOKEN_FILE": str(
                    secret_dir / "agent.workload-token"
                ),
                "KOKORO_SLICE_A_LITELLM_ENDPOINT": "http://127.0.0.1:4000/v1",
                "KOKORO_SLICE_A_LITELLM_API_KEY_FILE": str(
                    secret_dir / "litellm.api-key"
                ),
                "KOKORO_SLICE_A_CAPABILITY_ENDPOINT": "127.0.0.1:7204",
                "KOKORO_SLICE_A_MODEL_ENDPOINT": "127.0.0.1:7203",
                "KOKORO_SLICE_A_WORKER_ID": "slice-a-native-agent",
                "KOKORO_SLICE_A_SCHEMA": "kokoro",
            },
            7206,
            "grpc.health.v1:kokoro.agent.v1.AgentRuntimeService",
        ),
        "chat": ProcessSpec(
            "chat",
            commands["chat"],
            roots["chat"],
            {
                **base,
                "DATABASE_URL_KOKORO_APP": app_url,
                "KOKORO_CHAT_HOST": "127.0.0.1",
                "KOKORO_CHAT_PORT": "7205",
                "KOKORO_IAM_URL": "http://127.0.0.1:7202",
                "KOKORO_IAM_JWKS_URL": "http://127.0.0.1:7202/.well-known/jwks.json",
                "KOKORO_AGENT_URL": "http://127.0.0.1:7206",
                "KOKORO_CHAT_WORKLOAD_TOKEN": chat_token,
                "KOKORO_WEB_WORKLOAD_TOKEN": web_token,
                "KOKORO_LAUNCH_POLL_MS": "50",
            },
            7205,
            "http://127.0.0.1:7205/readyz",
        ),
    }


def _probe_spec(spec: ProcessSpec) -> None:
    if spec.name in {"iam", "model", "capability", "chat"}:
        _http2_probe(spec.readiness)
    elif spec.name == "agent":
        _grpc_health_probe(spec.port, "kokoro.agent.v1.AgentRuntimeService")


def _persist(
    state_dir: Path,
    records: dict[str, dict[str, JsonValue]],
    public: dict[str, JsonValue],
    secrets: frozenset[str],
) -> None:
    write_runtime_state(
        state_dir / STATE_FILE,
        processes={name: record for name, record in records.items()},
        public=public,
        secret_values=secrets,
    )


def _supervise(config_path: Path) -> int:
    config = json.loads(config_path.read_text())
    if not isinstance(config, dict):
        raise RuntimeError("invalid supervisor configuration")
    state_dir, secret_dir, fixture_dir = (
        Path(str(config["state_dir"])),
        Path(str(config["secret_dir"])),
        Path(str(config["fixture_dir"])),
    )
    roots = {name: Path(str(path)) for name, path in dict(config["roots"]).items()}
    baseline, postgres_bin = (
        Path(str(config["baseline"])),
        Path(str(config["postgres_bin"])),
    )
    ports = {name: int(port) for name, port in dict(config["ports"]).items()}
    secrets = _secret_values(secret_dir)
    processes: dict[str, subprocess.Popen[bytes]] = {}
    specs: dict[str, ProcessSpec] = {}
    records: dict[str, dict[str, JsonValue]] = {}
    stopping, restart_requested = False, None
    guardian: subprocess.Popen[bytes] | None = None

    def stop_signal(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True

    def control_signal(_signum: int, _frame: object) -> None:
        nonlocal restart_requested, stopping
        control = json.loads((state_dir / CONTROL_FILE).read_text())
        if (
            not isinstance(control, dict)
            or control.get("command") != "restart"
            or control.get("name") not in {"agent", "chat"}
        ):
            stopping = True
            return
        restart_requested = str(control["name"])

    signal.signal(signal.SIGINT, stop_signal)
    signal.signal(signal.SIGTERM, stop_signal)
    signal.signal(signal.SIGUSR1, control_signal)
    public: dict[str, JsonValue] = {
        "status": "starting",
        "supervisor_pid": os.getpid(),
        "supervisor_pgid": os.getpgrp(),
        "supervisor_session_id": os.getsid(0),
        "supervisor_start_identity": _process_identity(os.getpid()),
        "site_id": SITE_ID,
        "site_host": SITE_HOST,
        "baseline": str(baseline),
        "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
        "secret_dir": str(secret_dir),
        "fixture_dir": str(fixture_dir),
        "candidates": {name: str(path) for name, path in roots.items()},
        "ports": ports,
    }
    _persist(state_dir, records, public, secrets)
    guardian_log_path = state_dir / "logs" / "guardian.log"
    guardian_log_descriptor = os.open(
        guardian_log_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600
    )
    guardian_log = os.fdopen(guardian_log_descriptor, "wb", buffering=0)
    try:
        guardian = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "scripts/slice_a/guardian.py"),
                "--state-dir",
                str(state_dir),
                "--supervisor-pid",
                str(os.getpid()),
                "--supervisor-identity",
                str(public["supervisor_start_identity"]),
            ],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=guardian_log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        guardian_log.close()
    guardian_pgid, guardian_session_id = (
        os.getpgid(guardian.pid),
        os.getsid(guardian.pid),
    )
    if guardian_pgid != guardian.pid or guardian_session_id != guardian.pid:
        raise RuntimeError("guardian did not start in a dedicated process session")
    public["guardian"] = {
        "pid": guardian.pid,
        "pgid": guardian_pgid,
        "session_id": guardian_session_id,
        "start_identity": _process_identity(guardian.pid),
    }
    _persist(state_dir, records, public, secrets)

    def start_one(
        spec: ProcessSpec, probe: Callable[[], None], timeout: float = 90.0
    ) -> None:
        _ensure_port_free(spec.port)

        def persist_before_exec(process: subprocess.Popen[bytes]) -> None:
            processes[spec.name], specs[spec.name], records[spec.name] = (
                process,
                spec,
                _record(spec, process, state_dir),
            )
            _persist(state_dir, records, public, secrets)

        process = _spawn(spec, state_dir, persist_before_exec)
        _wait_until(
            spec.name,
            process,
            probe,
            state_dir / "logs" / f"{spec.name}.log",
            timeout=timeout,
            secrets=secrets,
        )

    try:
        pg_spec = _postgres_spec(postgres_bin, state_dir, ports["postgres"])
        start_one(
            pg_spec,
            lambda: _run_checked(
                [
                    str(postgres_bin / "pg_isready"),
                    "-h",
                    "127.0.0.1",
                    "-p",
                    str(ports["postgres"]),
                    "-U",
                    "postgres",
                ]
            ),
        )
        admin_url, app_url = _provision_postgres(
            postgres_bin, ports["postgres"], baseline
        )
        public["database_url"], public["provisioning_database_url"] = app_url, admin_url
        redis_spec = ProcessSpec(
            "redis",
            (
                str(config["redis_server"]),
                "--bind",
                "127.0.0.1",
                "--port",
                str(ports["redis"]),
                "--save",
                "",
                "--appendonly",
                "no",
                "--dir",
                str(state_dir),
            ),
            state_dir,
            _minimal_environment(),
            ports["redis"],
            "RESP PING",
        )
        start_one(redis_spec, lambda: _redis_probe(ports["redis"]))
        fixture_spec = ProcessSpec(
            "model-fixture",
            (
                sys.executable,
                str(ROOT / "scripts/fixtures/openai_slice_a.py"),
                "--host",
                "127.0.0.1",
                "--port",
                str(ports["model-fixture"]),
            ),
            ROOT,
            _minimal_environment(),
            ports["model-fixture"],
            f"http://127.0.0.1:{ports['model-fixture']}/healthz",
        )
        start_one(fixture_spec, lambda: _http_probe(fixture_spec.readiness))
        litellm_config = state_dir / "litellm.yaml"
        litellm_config.write_text(
            "model_list:\n  - model_name: slice-a-fixture\n    litellm_params:\n      model: openai/slice-a-fixture\n"
            + f"      api_base: http://127.0.0.1:{ports['model-fixture']}/v1\n"
            + "      api_key: fixture-not-a-secret\nlitellm_settings:\n  drop_params: true\ngeneral_settings:\n  master_key: os.environ/LITELLM_MASTER_KEY\n"
        )
        os.chmod(litellm_config, 0o600)
        litellm_spec = ProcessSpec(
            "litellm",
            build_litellm_command(litellm_config),
            state_dir,
            {
                **_minimal_environment(),
                "LITELLM_MASTER_KEY": (secret_dir / "litellm.api-key").read_text(),
            },
            4000,
            "http://127.0.0.1:4000/health/liveliness",
        )
        start_one(
            litellm_spec, lambda: _http_probe(litellm_spec.readiness), timeout=180
        )
        site_contexts, model_manifest = write_seed_artifacts(fixture_dir)
        seed_site(admin_url)
        public["model_bootstrap"] = bootstrap_model(
            roots["model"], app_url, model_manifest
        )
        public["seed_digest"] = hashlib.sha256(
            site_contexts.read_bytes() + model_manifest.read_bytes()
        ).hexdigest()
        sink = fixture_dir / "magic-links" / "iam.magic-link-fixture.jsonl"
        os.close(os.open(sink, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
        service_specs = _service_specs(
            roots, secret_dir, fixture_dir, app_url, ports["redis"]
        )
        for name in ("iam", "model", "capability", "agent", "chat"):
            spec = service_specs[name]
            start_one(spec, lambda item=spec: _probe_spec(item), timeout=120)
        if set(records) != BACKEND_PROCESSES:
            raise RuntimeError(f"backend inventory mismatch: {sorted(records)}")
        public["status"] = "ready"
        _persist(state_dir, records, public, secrets)
        while not stopping:
            if not _owner_alive(config):
                stopping = True
                continue
            for name, process in processes.items():
                if (code := process.poll()) is not None:
                    raise RuntimeError(
                        f"owned process exited unexpectedly: {name} ({code})"
                    )
            if restart_requested is not None:
                name, restart_requested = restart_requested, None
                process, spec = processes[name], specs[name]
                _stop_process(process)
                _ensure_port_free(spec.port)

                def persist_replacement_before_exec(
                    replacement: subprocess.Popen[bytes],
                ) -> None:
                    processes[name], records[name] = (
                        replacement,
                        _record(spec, replacement, state_dir),
                    )
                    _persist(state_dir, records, public, secrets)

                replacement = _spawn(spec, state_dir, persist_replacement_before_exec)
                _wait_until(
                    name,
                    replacement,
                    lambda item=spec: _probe_spec(item),
                    state_dir / "logs" / f"{name}.log",
                    timeout=120,
                    secrets=secrets,
                )
                (state_dir / CONTROL_FILE).unlink(missing_ok=True)
                _persist(state_dir, records, public, secrets)
            time.sleep(0.1)
    except BaseException as error:
        public["status"], public["error"] = (
            "failed",
            _redact_text(f"{type(error).__name__}: {error}", secrets),
        )
        _persist(state_dir, records, public, secrets)
        raise
    finally:
        cleanup_errors = _stop_process_inventory(processes, secrets)
        public["status"] = "stopped" if not cleanup_errors else "cleanup_failed"
        if cleanup_errors:
            public["cleanup_errors"] = cleanup_errors
        _persist(state_dir, records, public, secrets)
        if guardian is not None:
            if guardian.stdin is not None:
                guardian.stdin.close()
            try:
                guardian_code = guardian.wait(timeout=10)
                if guardian_code != 0:
                    cleanup_errors.append(
                        f"guardian: exited with status {guardian_code}"
                    )
            except subprocess.TimeoutExpired:
                try:
                    _stop_process(guardian, timeout=2)
                except BaseException as error:
                    cleanup_errors.append(
                        _redact_text(
                            f"guardian: {type(error).__name__}: {error}", secrets
                        )
                    )
        if cleanup_errors:
            public["status"] = "cleanup_failed"
            public["cleanup_errors"] = cleanup_errors
            _persist(state_dir, records, public, secrets)
            raise RuntimeError(
                "owned process cleanup failed: " + "; ".join(cleanup_errors)
            )
    return 0


def _create_state_directory(state_dir: Path) -> None:
    if state_dir.exists() or state_dir.is_symlink():
        raise RuntimeError("state directory must not already exist")
    state_dir.mkdir(mode=0o700)
    os.chmod(state_dir, 0o700)
    (state_dir / STATE_MARKER).write_text(STATE_MARKER_CONTENT)
    os.chmod(state_dir / STATE_MARKER, 0o600)
    (state_dir / "logs").mkdir(mode=0o700)


def _load_state(state_dir: Path) -> dict[str, JsonValue]:
    marker = state_dir / STATE_MARKER
    if (
        state_dir.is_symlink()
        or marker.is_symlink()
        or marker.read_text() != STATE_MARKER_CONTENT
    ):
        raise RuntimeError("state directory is not owned by Slice A")
    raw = json.loads((state_dir / STATE_FILE).read_text())
    if not isinstance(raw, dict):
        raise RuntimeError("invalid runtime state")
    return raw


def _start(args: argparse.Namespace) -> int:
    if not args.fresh:
        raise RuntimeError("native start requires --fresh")
    state_dir, secret_dir, fixture_dir = (
        args.state_dir.absolute(),
        args.secret_dir.absolute(),
        args.fixture_dir.absolute(),
    )
    validate_secret_directory(secret_dir)
    secrets = _secret_values(secret_dir)
    validate_fixture_directory(fixture_dir, require_empty=True)
    roots = {
        name: getattr(args, name).absolute()
        for name in ("iam", "model", "capability", "chat", "agent")
    }
    for name, path in roots.items():
        validate_candidate(
            path,
            getattr(args, f"{name}_commit"),
            DEFAULT_TREES[name],
        )
    baseline = args.baseline.absolute()
    _assert_committed_baseline(baseline)
    postgres_bin = find_postgres_18_bin()
    redis_server = shutil.which("redis-server")
    if not redis_server:
        raise RuntimeError("native redis-server was not found")
    for port in FIXED_PORTS.values():
        _ensure_port_free(port)
    _create_state_directory(state_dir)
    postgres_port, redis_port, fixture_port = _free_ports(3, set(FIXED_PORTS.values()))
    ports = {
        "postgres": postgres_port,
        "redis": redis_port,
        "model-fixture": fixture_port,
        **FIXED_PORTS,
    }
    config: dict[str, JsonValue] = {
        "state_dir": str(state_dir),
        "secret_dir": str(secret_dir),
        "fixture_dir": str(fixture_dir),
        "roots": {name: str(path) for name, path in roots.items()},
        "baseline": str(baseline),
        "postgres_bin": str(postgres_bin),
        "redis_server": redis_server,
        "ports": ports,
    }
    if args.owner_pid is not None or args.owner_identity is not None:
        if args.owner_pid is None or args.owner_identity is None:
            raise RuntimeError(
                "--owner-pid and --owner-identity must be supplied together"
            )
        config["owner_pid"], config["owner_identity"] = (
            args.owner_pid,
            args.owner_identity,
        )
    config_path = state_dir / "supervisor.json"
    config_path.write_text(json.dumps(config, sort_keys=True) + "\n")
    os.chmod(config_path, 0o600)
    supervisor_log = state_dir / "logs" / "supervisor.log"
    descriptor = os.open(supervisor_log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "wb", buffering=0) as log:
        supervisor = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "_supervise",
                "--config",
                str(config_path),
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    try:
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            if (code := supervisor.poll()) is not None:
                raise RuntimeError(
                    _redact_text(
                        f"Slice A supervisor exited during start ({code})\n{supervisor_log.read_text(errors='replace')[-12000:]}",
                        secrets,
                    )
                )
            state_path = state_dir / STATE_FILE
            if state_path.exists():
                state = _load_state(state_dir)
                public = state.get("public")
                if isinstance(public, dict) and public.get("status") == "ready":
                    return 0
                if isinstance(public, dict) and public.get("status") == "failed":
                    raise RuntimeError(
                        _redact_text(
                            f"Slice A startup failed: {public.get('error')}", secrets
                        )
                    )
            time.sleep(0.2)
        raise RuntimeError("Slice A supervisor did not reach ready state")
    except BaseException:
        _terminate_supervisor(supervisor)
        raise


def _stop(state_dir: Path) -> int:
    state = _load_state(state_dir)
    public = state.get("public")
    if not isinstance(public, dict):
        raise RuntimeError("runtime state lacks public supervisor facts")
    pid, pgid, session_id, identity = (
        int(public["supervisor_pid"]),
        int(public["supervisor_pgid"]),
        int(public["supervisor_session_id"]),
        str(public["supervisor_start_identity"]),
    )
    _stop_owned_group(
        pid=pid, pgid=pgid, session_id=session_id, identity=identity, timeout=40
    )
    latest_state = _load_state(state_dir)
    latest, processes = latest_state.get("public"), latest_state.get("processes")
    if not isinstance(latest, dict) or latest.get("status") != "stopped":
        raise RuntimeError("supervisor did not persist stopped state")
    if not isinstance(processes, dict):
        raise RuntimeError("runtime process inventory is missing after stop")
    survivors = [
        name
        for name, record in processes.items()
        if isinstance(record, dict) and _group_alive(int(record["pgid"]))
    ]
    if survivors:
        raise RuntimeError(f"owned process groups survived stop: {sorted(survivors)}")
    ports = latest.get("ports")
    if not isinstance(ports, dict):
        raise RuntimeError("runtime port inventory is missing after stop")
    for port in ports.values():
        _ensure_port_free(int(port))
    return 0


def _restart(state_dir: Path, name: str) -> int:
    state = _load_state(state_dir)
    public, processes = state.get("public"), state.get("processes")
    if (
        not isinstance(public, dict)
        or not isinstance(processes, dict)
        or not isinstance(processes.get(name), dict)
    ):
        raise RuntimeError("invalid runtime state")
    old_pid, old_identity = (
        int(processes[name]["pid"]),
        str(processes[name]["start_identity"]),
    )
    control_path, temporary = (
        state_dir / CONTROL_FILE,
        state_dir / f"{CONTROL_FILE}.tmp",
    )
    temporary.write_text(json.dumps({"command": "restart", "name": name}) + "\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, control_path)
    pid, identity = (
        int(public["supervisor_pid"]),
        str(public["supervisor_start_identity"]),
    )
    if not _identity_matches(pid, identity):
        raise RuntimeError("supervisor process identity no longer matches")
    os.kill(pid, signal.SIGUSR1)
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        current = _load_state(state_dir).get("processes")
        if (
            isinstance(current, dict)
            and isinstance(current.get(name), dict)
            and (
                current[name].get("pid") != old_pid
                or current[name].get("start_identity") != old_identity
            )
            and not control_path.exists()
        ):
            return 0
        time.sleep(0.1)
    raise RuntimeError(f"{name} restart did not complete")


def _assert_no_process(state_dir: Path, name: str) -> int:
    processes = _load_state(state_dir).get("processes")
    if not isinstance(processes, dict):
        raise RuntimeError("invalid runtime process inventory")
    if name in processes:
        raise RuntimeError(f"unexpected process is present: {name}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Native Slice A lifecycle")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--fresh", action="store_true")
    start.add_argument("--state-dir", required=True, type=Path)
    start.add_argument("--secret-dir", required=True, type=Path)
    start.add_argument("--fixture-dir", required=True, type=Path)
    start.add_argument(
        "--baseline", type=Path, default=ROOT / "database/baseline/kokoro.sql"
    )
    start.add_argument("--owner-pid", type=int)
    start.add_argument("--owner-identity")
    for name in ("iam", "model", "capability", "chat", "agent"):
        start.add_argument(f"--{name}", required=True, type=Path)
        start.add_argument(f"--{name}-commit", default=DEFAULT_COMMITS[name])
    stop = commands.add_parser("stop")
    stop.add_argument("--state-dir", required=True, type=Path)
    restart = commands.add_parser("restart")
    restart.add_argument("--state-dir", required=True, type=Path)
    restart.add_argument("name", choices=("agent", "chat"))
    absent = commands.add_parser("assert-no-process")
    absent.add_argument("--state-dir", required=True, type=Path)
    absent.add_argument("--name", required=True)
    supervise = commands.add_parser("_supervise")
    supervise.add_argument("--config", required=True, type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "start":
        return _start(args)
    if args.command == "stop":
        return _stop(args.state_dir.absolute())
    if args.command == "restart":
        return _restart(args.state_dir.absolute(), args.name)
    if args.command == "assert-no-process":
        return _assert_no_process(args.state_dir.absolute(), args.name)
    if args.command == "_supervise":
        return _supervise(args.config.absolute())
    raise AssertionError("unreachable")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        print(f"native Slice A lifecycle failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

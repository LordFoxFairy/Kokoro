#!/usr/bin/env python3
"""Run the no-Docker Slice A backend product cut against fresh native infrastructure."""

from __future__ import annotations

import argparse
import atexit
import hashlib
import json
import math
import os
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import Any, Callable, TypeVar
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "scripts/e2e/generated"
sys.dont_write_bytecode = True
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(GENERATED) not in sys.path:
    sys.path.insert(0, str(GENERATED))

from scripts.slice_a.cleanup import remove_marked_directory
from scripts.slice_a.create_fixture_dir import create_fixture_directory
from scripts.slice_a.create_secrets import SECRET_FILES, create_secret_directory
from scripts.slice_a.guardian import group_alive, process_identity, stop_owned_group
from scripts.slice_a.native import (
    DEFAULT_COMMITS,
    DEFAULT_TREES,
    _ensure_port_free,
    validate_candidate,
)
from scripts.slice_a.seed import SITE_HOST, SITE_ID, select_site_context
from scripts.fixtures.openai_slice_a import TOOL_ARGUMENTS, TOOL_ID

T = TypeVar("T")
EMAIL = "slice-a-native@example.com"
NONCE_DIGEST = hashlib.sha256(b"slice-a-native-browser-nonce").hexdigest()
CONTENT = "slice-a-hitl: ask for approval and then confirm completion"
REDIRECT_URI = "https://slice-a.localhost/api/auth/callback"
PERMISSIONS = frozenset(
    {
        "chat.conversation.create",
        "chat.conversation.list",
        "chat.conversation.read",
        "chat.message.submit",
        "chat.interaction.decide",
    }
)
REQUIRED_PRODUCT_ASSERTIONS = frozenset(
    {
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
)
EXPECTED_CONTRACT_SOURCE = "a5c07bc6cad3d0e18d87793e94d46ee465bd1263"
EXPECTED_CONTRACT_TREE = "9234bba0923a5f066c75977937123ecda9eb89c1"
EXPECTED_MANIFEST_SHA256 = (
    "2f334317d6610935f7d3f9e7bd6decdd285e90b5a794abf4307dfb5c1a68da2c"
)
EXPECTED_GENERATOR_SHA256 = (
    "8778d9c9f3f1048ecaeb4fa382cc28b5837d1bbfb99859da955de926ae0b55ae"
)
EXPECTED_GENERATED_COMMIT = "2d7ad2c1f1e478724b584027ce4eea2ab0d6ef62"


class RunInterrupted(RuntimeError):
    """Raised from a handled process signal so the common cleanup path runs."""


def validate_release_evidence(evidence: dict[str, Any]) -> None:
    assertions = evidence.get("assertions")
    if not isinstance(assertions, dict):
        raise RuntimeError("release evidence is missing release assertions")
    passed = {name for name, value in assertions.items() if value is True}
    missing = REQUIRED_PRODUCT_ASSERTIONS - passed
    if missing:
        raise RuntimeError(f"missing release assertions: {sorted(missing)}")
    catalog = evidence.get("catalog")
    if not isinstance(catalog, dict) or (
        catalog.get("owner"),
        catalog.get("checkpointer"),
    ) != (50, 4):
        raise RuntimeError("release evidence lacks the exact 50+4 catalog")
    retention = tuple(
        evidence.get(name)
        for name in (
            "retained_watermark",
            "retention_tail_seq",
            "retention_recovered_watermark",
        )
    )
    if any(type(value) is not int for value in retention) or not (
        retention[1] == retention[0] + 1 and retention[2] >= retention[1]
    ):
        raise RuntimeError("release evidence lacks exact retention recovery facts")
    site_boundary = evidence.get("site_table_boundary")
    if (
        not isinstance(site_boundary, dict)
        or set(site_boundary) != {"iam"}
        or type(site_boundary.get("iam")) is not int
        or site_boundary["iam"] <= 0
    ):
        raise RuntimeError("release evidence lacks the IAM-only Site table boundary")
    stream_kinds = evidence.get("stream_kinds")
    sql = evidence.get("sql")
    event_kinds = sql.get("event_kinds") if isinstance(sql, dict) else None
    if not isinstance(stream_kinds, list) or not isinstance(event_kinds, list):
        raise RuntimeError("release evidence lacks exact event inventories")
    if any(
        stream_kinds.count(kind) != 1
        for kind in ("tool.awaiting_approval", "interaction.resolved", "run.completed")
    ) or any(
        event_kinds.count(kind) != 1
        for kind in ("tool.awaiting_approval", "run.control.receipt", "run.completed")
    ):
        raise RuntimeError("release evidence event multiplicity mismatch")
    if sql.get("tool_effects") != 1:
        raise RuntimeError("release evidence tool effect multiplicity mismatch")


def canonical_digest(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise TypeError("canonical digest payload must be an object")

    def reject_nonfinite(value: Any) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("canonical JSON numbers must be finite")
        if isinstance(value, dict):
            for child in value.values():
                reject_nonfinite(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                reject_nonfinite(child)

    reject_nonfinite(payload)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def consume_digest(site_id: str, token: str, nonce_digest: str) -> str:
    return canonical_digest(
        {
            "nonce_digest": nonce_digest,
            "site_id": site_id,
            "token_digest": hashlib.sha256(token.encode()).hexdigest(),
        }
    )


def refresh_digest(site_id: str, auth_session_id: str, refresh_token: str) -> str:
    return canonical_digest(
        {
            "auth_session_id": auth_session_id,
            "old_refresh_token_digest": hashlib.sha256(
                refresh_token.encode()
            ).hexdigest(),
            "site_id": site_id,
        }
    )


def logout_digest(auth_session_id: str, refresh_token: str) -> str:
    return canonical_digest(
        {
            "auth_session_id": auth_session_id,
            "refresh_token_digest": hashlib.sha256(refresh_token.encode()).hexdigest(),
        }
    )


def load_magic_link(
    path: Path,
    delivery_ref: str,
    *,
    expected_site_id: str,
    expected_email: str,
    timeout: float = 10.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() <= deadline:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) != 0o600
            ):
                raise RuntimeError("magic-link sink must be a regular 0600 file")
            chunks: list[bytes] = []
            while chunk := os.read(descriptor, 65536):
                chunks.append(chunk)
        finally:
            os.close(descriptor)
        for line in b"".join(chunks).decode().splitlines():
            record = json.loads(line)
            if not isinstance(record, dict):
                raise RuntimeError("magic-link sink record must be an object")
            if record.get("delivery_ref") == delivery_ref:
                if record.get("site_id") != expected_site_id:
                    raise RuntimeError("magic-link delivery Site mismatch")
                if record.get("email") != expected_email:
                    raise RuntimeError("magic-link delivery email mismatch")
                current = os.lstat(path)
                if (current.st_dev, current.st_ino) != (
                    metadata.st_dev,
                    metadata.st_ino,
                ):
                    raise RuntimeError("magic-link sink changed while being read")
                path.unlink()
                return record
        time.sleep(0.02)
    raise RuntimeError(f"magic-link delivery not found: {delivery_ref}")


def _request_id() -> str:
    return str(uuid4())


def validate_runtime_candidates(args: argparse.Namespace) -> None:
    roots: dict[str, Path] = {}
    for name in DEFAULT_COMMITS:
        root = Path(getattr(args, name))
        roots[name] = root
        validate_candidate(
            root,
            str(getattr(args, f"{name}_commit")),
            DEFAULT_TREES[name],
        )
    validate_site_table_boundary(roots)


def validate_site_table_boundary(roots: dict[str, Path]) -> dict[str, int]:
    observations: dict[str, int] = {}
    for name in ("iam", "model", "capability", "chat", "agent"):
        result = subprocess.run(
            [
                "git",
                "-C",
                str(roots[name]),
                "grep",
                "-I",
                "-n",
                "site_site",
                "HEAD",
                "--",
                "src",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"could not inspect {name.title()} runtime source")
        count = len(result.stdout.splitlines())
        if name == "iam":
            if count == 0:
                raise RuntimeError("IAM runtime source lacks the Site owner boundary")
            observations[name] = count
        elif count:
            raise RuntimeError(
                f"{name.title()} runtime source accesses IAM-owned site_site"
            )
    return observations


def validate_generated_client_provenance() -> None:
    provenance_path = GENERATED / "provenance.json"
    if provenance_path.is_symlink() or not provenance_path.is_file():
        raise RuntimeError("Root E2E generated provenance is not a regular file")
    provenance = json.loads(provenance_path.read_text())
    if provenance.get("sourceRootCommit") != EXPECTED_CONTRACT_SOURCE:
        raise RuntimeError(
            "Root E2E generated clients are not pinned to the reviewed contract source"
        )
    if provenance.get("sourceRootTree") != EXPECTED_CONTRACT_TREE:
        raise RuntimeError("Root E2E generated source tree is not the reviewed tree")
    if provenance.get("manifestSha256") != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("Root E2E generated manifest digest drift")
    if provenance.get("generatorSha256") != EXPECTED_GENERATOR_SHA256:
        raise RuntimeError("Root E2E generated generator digest drift")
    outputs = provenance.get("outputs")
    if not isinstance(outputs, dict):
        raise RuntimeError("Root E2E generated provenance lacks the output closure")
    required = {
        "kokoro/iam/v1/authentication_pb2.py",
        "kokoro/iam/v1/authentication_pb2_grpc.py",
        "kokoro/iam/v1/authorization_pb2.py",
        "kokoro/iam/v1/authorization_pb2_grpc.py",
        "kokoro/chat/v1/chat_pb2.py",
        "kokoro/chat/v1/chat_pb2_grpc.py",
    }
    if not required <= set(outputs):
        raise RuntimeError("Root E2E generated closure lacks required IAM/Chat clients")
    actual_files = {
        path.relative_to(GENERATED).as_posix()
        for path in GENERATED.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    declared_files = {"provenance.json", *outputs}
    if actual_files != declared_files:
        raise RuntimeError("Root E2E generated closure differs from provenance")
    for relative, digest in outputs.items():
        path = GENERATED / str(relative)
        if (
            path.is_symlink()
            or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != digest
        ):
            raise RuntimeError(f"Root E2E generated output drift: {relative}")
    tracked = {
        line.removeprefix("scripts/e2e/generated/")
        for line in subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD", "scripts/e2e/generated"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    }
    if tracked != declared_files:
        raise RuntimeError("Root E2E generated tracked closure drift")
    dirty = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            "scripts/e2e/generated",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if dirty:
        raise RuntimeError("Root E2E generated tree is dirty")
    for relative in declared_files:
        current = (GENERATED / relative).read_bytes()
        committed = subprocess.run(
            ["git", "show", f"HEAD:scripts/e2e/generated/{relative}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        if current != committed:
            raise RuntimeError(
                f"Root E2E generated file differs from committed bytes: {relative}"
            )
    contract_commit = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "contract"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if contract_commit != EXPECTED_CONTRACT_SOURCE:
        raise RuntimeError(
            "Root contract HEAD authority differs from generated provenance"
        )
    generated_commit = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "scripts/e2e/generated"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if generated_commit != EXPECTED_GENERATED_COMMIT:
        raise RuntimeError(f"unexpected Root E2E generated commit: {generated_commit}")


def _command(digest: str):
    from kokoro.common.v1 import common_pb2

    return common_pb2.CommandIdentity(command_id=str(uuid4()), request_digest=digest)


def _metadata(workload_token: str, request_id: str, access_token: str | None = None):
    metadata = [
        ("authorization", f"Bearer {workload_token}"),
        ("x-kokoro-request-id", request_id),
    ]
    if access_token is not None:
        metadata.append(("x-kokoro-user-authorization", f"Bearer {access_token}"))
    return tuple(metadata)


def _wait_for(
    read: Callable[[], T],
    accept: Callable[[T], bool],
    description: str,
    *,
    timeout: float = 45.0,
    redact: Callable[[str], str],
) -> T:
    deadline, last = time.monotonic() + timeout, "not observed"
    while time.monotonic() < deadline:
        try:
            observed = read()
            if accept(observed):
                return observed
            last = redact(repr(observed))
        except (
            Exception
        ) as error:  # readiness convergence deliberately retries transport races
            last = redact(f"{type(error).__name__}: {error}")
        time.sleep(0.1)
    raise RuntimeError(redact(f"timed out waiting for {description}; last={last}"))


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    owner: Path
    state: Path
    secrets: Path
    fixtures: Path


class NativeRuntime:
    def __init__(self, args: argparse.Namespace) -> None:
        private_temp_root = Path(tempfile.gettempdir()).resolve(strict=True)
        owner = Path(
            tempfile.mkdtemp(prefix="kokoro-slice-a-native-", dir=private_temp_root)
        )
        os.chmod(owner, 0o700)
        self.paths = RuntimePaths(
            owner, owner / "state", owner / "secrets", owner / "fixtures"
        )
        self.args = args
        self.started = False
        self._sensitive_values: set[str] = set()

    def register_sensitive(self, *values: str) -> None:
        for value in values:
            if value:
                self._sensitive_values.add(value)
                self._sensitive_values.update(
                    line for line in value.splitlines() if len(line) >= 16
                )

    def sensitive_values(self) -> frozenset[str]:
        return frozenset(self._sensitive_values)

    def redact(self, value: str) -> str:
        secrets = set(self.sensitive_values())
        if self.paths.secrets.is_dir():
            for name in SECRET_FILES:
                path = self.paths.secrets / name
                if path.is_file() and not path.is_symlink():
                    secret = path.read_text(errors="replace")
                    secrets.add(secret)
                    secrets.update(
                        line for line in secret.splitlines() if len(line) >= 16
                    )
        for secret in sorted(secrets, key=len, reverse=True):
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value

    def start(self) -> None:
        create_secret_directory(self.paths.secrets)
        create_fixture_directory(self.paths.fixtures)
        owner_identity = process_identity(os.getpid())
        if owner_identity is None:
            raise RuntimeError("could not establish E2E runner process identity")
        command = [
            sys.executable,
            str(ROOT / "scripts/slice_a/native.py"),
            "start",
            "--fresh",
            "--state-dir",
            str(self.paths.state),
            "--secret-dir",
            str(self.paths.secrets),
            "--fixture-dir",
            str(self.paths.fixtures),
            "--owner-pid",
            str(os.getpid()),
            "--owner-identity",
            owner_identity,
        ]
        for name in ("iam", "model", "capability", "chat", "agent"):
            command.extend(
                (
                    f"--{name}",
                    str(getattr(self.args, name)),
                    f"--{name}-commit",
                    str(getattr(self.args, f"{name}_commit")),
                )
            )
        _run_process(command, timeout=self.args.start_timeout, redact=self.redact)
        self.started = True

    def restart(self, name: str) -> None:
        _run_process(
            [
                sys.executable,
                str(ROOT / "scripts/slice_a/native.py"),
                "restart",
                "--state-dir",
                str(self.paths.state),
                name,
            ],
            timeout=180,
            redact=self.redact,
        )

    def state(self) -> dict[str, Any]:
        value = json.loads((self.paths.state / "runtime.json").read_text())
        if not isinstance(value, dict):
            raise RuntimeError("runtime state is not an object")
        return value

    def diagnostics(self) -> str:
        logs = self.paths.state / "logs"
        if not logs.is_dir():
            return ""
        sections: list[str] = []
        for path in sorted(logs.glob("*.log")):
            content = self.redact(path.read_text(errors="replace")[-3000:])
            sections.append(f"--- {path.name} ---\n{content}")
        return "\n".join(sections)

    def stop(self) -> None:
        if self.paths.state.exists() and (self.paths.state / "runtime.json").exists():
            try:
                _run_process(
                    [
                        sys.executable,
                        str(ROOT / "scripts/slice_a/native.py"),
                        "stop",
                        "--state-dir",
                        str(self.paths.state),
                    ],
                    timeout=60,
                    redact=self.redact,
                )
            except (OSError, RuntimeError, subprocess.SubprocessError):
                # The supervisor/guardian may already have completed owner-death cleanup.
                pass
            state = self.state()
            public, processes = state.get("public"), state.get("processes")
            if isinstance(public, dict):
                _force_stop_record(public)
                guardian = public.get("guardian")
                if isinstance(guardian, dict):
                    _force_stop_record(guardian)
            if isinstance(processes, dict):
                for record in reversed(tuple(processes.values())):
                    if isinstance(record, dict):
                        _force_stop_record(record)
                survivors = [
                    name
                    for name, record in processes.items()
                    if isinstance(record, dict) and _record_alive(record)
                ]
                if survivors:
                    raise RuntimeError(
                        f"owned processes survived cleanup: {sorted(survivors)}"
                    )
            config_path = self.paths.state / "supervisor.json"
            if config_path.is_file():
                config = json.loads(config_path.read_text())
                ports = config.get("ports") if isinstance(config, dict) else None
                if not isinstance(ports, dict):
                    raise RuntimeError("runtime cleanup lacks the owned port inventory")
                for port in ports.values():
                    _ensure_port_free(int(port))
        secret_error: RuntimeError | None = None
        try:
            _assert_no_secret_logs(self, extra=())
        except RuntimeError as error:
            secret_error = error
        for target in (self.paths.state, self.paths.fixtures, self.paths.secrets):
            if target.exists():
                remove_marked_directory(target)
        if self.paths.owner.exists():
            self.paths.owner.rmdir()
        self.started = False
        if secret_error is not None:
            raise secret_error


def _record_alive(record: dict[str, Any]) -> bool:
    pgid = record.get("pgid", record.get("supervisor_pgid"))
    if not isinstance(pgid, int):
        raise RuntimeError("owned process record lacks PGID")
    return group_alive(pgid)


def _force_stop_record(record: dict[str, Any]) -> None:
    pid = record.get("pid", record.get("supervisor_pid"))
    pgid = record.get("pgid", record.get("supervisor_pgid"))
    session_id = record.get("session_id", record.get("supervisor_session_id"))
    identity = record.get("start_identity", record.get("supervisor_start_identity"))
    if not all(
        (
            isinstance(pid, int),
            isinstance(pgid, int),
            isinstance(session_id, int),
            isinstance(identity, str),
        )
    ):
        raise RuntimeError("owned process record is incomplete")
    stop_owned_group(
        pid=pid,
        pgid=pgid,
        session_id=session_id,
        identity=identity,
        timeout=5,
    )


def _run_process(
    argv: list[str],
    *,
    timeout: float,
    redact: Callable[[str], str] = lambda value: value,
) -> None:
    try:
        process = subprocess.Popen(
            argv,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except BaseException as error:
        raise RuntimeError(
            redact(f"command launch failed: {argv!r}: {error}")
        ) from error
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            output, _ = process.communicate(timeout=5)
        raise RuntimeError(
            redact(f"command timed out: {argv!r}\n{output[-12000:]}")
        ) from error
    except BaseException:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
        raise
    if process.returncode != 0:
        raise RuntimeError(
            redact(
                f"command failed ({process.returncode}): {argv!r}\n{output[-12000:]}"
            )
        )


def _expect_rpc_error(call: Callable[[], Any], expected_status: Any) -> Any:
    import grpc

    try:
        call()
    except grpc.RpcError as error:
        if error.code() != expected_status:
            raise RuntimeError(
                f"RPC failed with {error.code().name}, expected {expected_status.name}"
            ) from error
        return error
    raise RuntimeError(f"RPC unexpectedly succeeded; expected {expected_status.name}")


def _psql(runtime: NativeRuntime, sql: str, *variables: tuple[str, str]) -> str:
    public = runtime.state().get("public")
    if not isinstance(public, dict):
        raise RuntimeError("runtime state lacks public database facts")
    config = json.loads((runtime.paths.state / "supervisor.json").read_text())
    postgres_bin = Path(str(config["postgres_bin"]))
    command = [
        str(postgres_bin / "psql"),
        str(public["provisioning_database_url"]),
        "-q",
        "-v",
        "ON_ERROR_STOP=1",
    ]
    for name, value in variables:
        command.extend(("-v", f"{name}={value}"))
    command.extend(("-Atc", sql))
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.strip()


def _set_site_status(runtime: NativeRuntime, status: str) -> None:
    if status not in {"active", "suspended"}:
        raise RuntimeError("invalid Site fixture status")
    changed = _psql(
        runtime,
        "UPDATE kokoro.site_site SET status=:'status' WHERE site_id=:'site_id'::uuid RETURNING status",
        ("status", status),
        ("site_id", SITE_ID),
    )
    if changed.splitlines()[-1:] != [status]:
        raise RuntimeError(f"Site fixture did not transition to {status}")


def _run_product_chain(runtime: NativeRuntime) -> dict[str, Any]:
    import grpc
    from kokoro.chat.v1 import chat_pb2, chat_pb2_grpc
    from kokoro.common.v1 import common_pb2
    from kokoro.iam.v1 import authentication_pb2, authentication_pb2_grpc

    contexts = json.loads((runtime.paths.fixtures / "site-contexts.json").read_text())
    if not isinstance(contexts, dict):
        raise RuntimeError("SiteContext fixture must be an object")
    try:
        select_site_context("unknown.slice-a.localhost", contexts)
    except RuntimeError as error:
        if "unknown Site Host" not in str(error):
            raise
    else:
        raise RuntimeError("unknown Site Host unexpectedly resolved")
    site_context = select_site_context(f" {SITE_HOST.upper()}. ", contexts)
    site_id = site_context.get("site_id")
    if site_id != SITE_ID:
        raise RuntimeError("selected SiteContext differs from the provisioned Site")

    web_token = (runtime.paths.secrets / "web.workload-token").read_text()
    chat_token = (runtime.paths.secrets / "chat.workload-token").read_text()
    iam_channel = grpc.insecure_channel("127.0.0.1:7202")
    chat_channel = grpc.insecure_channel("127.0.0.1:7205")
    iam = authentication_pb2_grpc.IamAuthenticationServiceStub(iam_channel)
    commands = chat_pb2_grpc.ChatCommandServiceStub(chat_channel)
    queries = chat_pb2_grpc.ChatQueryServiceStub(chat_channel)
    try:
        _set_site_status(runtime, "suspended")
        request_id = _request_id()
        suspended_command = _command(
            canonical_digest(
                {"email": EMAIL, "nonce_digest": NONCE_DIGEST, "site_id": site_id}
            )
        )
        _expect_rpc_error(
            lambda: iam.RequestMagicLink(
                authentication_pb2.RequestMagicLinkRequest(
                    request_id=request_id,
                    command=suspended_command,
                    site_id=site_id,
                    email=EMAIL,
                    redirect_uri=REDIRECT_URI,
                    nonce_digest=NONCE_DIGEST,
                ),
                metadata=_metadata(web_token, request_id),
                timeout=10,
            ),
            grpc.StatusCode.INVALID_ARGUMENT,
        )
        _set_site_status(runtime, "active")
        request_id = _request_id()
        request_command = _command(
            canonical_digest(
                {"email": EMAIL, "nonce_digest": NONCE_DIGEST, "site_id": site_id}
            )
        )

        def request_magic_link(digest: str | None = None):
            current_request_id = _request_id()
            return iam.RequestMagicLink(
                authentication_pb2.RequestMagicLinkRequest(
                    request_id=current_request_id,
                    command=(
                        request_command
                        if digest is None
                        else common_pb2.CommandIdentity(
                            command_id=request_command.command_id,
                            request_digest=digest,
                        )
                    ),
                    site_id=site_id,
                    email=EMAIL,
                    redirect_uri=REDIRECT_URI,
                    nonce_digest=NONCE_DIGEST,
                ),
                metadata=_metadata(web_token, current_request_id),
                timeout=10,
            )

        requested = request_magic_link()
        requested_replay = request_magic_link()
        if (
            requested_replay.magic_link_id != requested.magic_link_id
            or requested_replay.delivery_ref != requested.delivery_ref
            or not requested_replay.replayed
        ):
            raise RuntimeError("RequestMagicLink exact replay was not stable")
        _expect_rpc_error(lambda: request_magic_link("0" * 64), grpc.StatusCode.ABORTED)
        delivery = load_magic_link(
            runtime.paths.fixtures / "magic-links" / "iam.magic-link-fixture.jsonl",
            requested.delivery_ref,
            expected_site_id=site_id,
            expected_email=EMAIL,
        )
        token = str(delivery["token"])
        runtime.register_sensitive(token)
        consume_command = _command(consume_digest(site_id, token, NONCE_DIGEST))

        def consume_magic_link(digest: str | None = None):
            current_request_id = _request_id()
            return iam.ConsumeMagicLink(
                authentication_pb2.ConsumeMagicLinkRequest(
                    request_id=current_request_id,
                    command=(
                        consume_command
                        if digest is None
                        else common_pb2.CommandIdentity(
                            command_id=consume_command.command_id,
                            request_digest=digest,
                        )
                    ),
                    site_id=site_id,
                    token=token,
                    nonce_digest=NONCE_DIGEST,
                ),
                metadata=_metadata(web_token, current_request_id),
                timeout=10,
            )

        consumed = consume_magic_link()
        runtime.register_sensitive(consumed.access_token, consumed.refresh_token)
        consumed_replay = consume_magic_link()
        runtime.register_sensitive(
            consumed_replay.access_token, consumed_replay.refresh_token
        )
        if (
            consumed_replay.auth_session_id != consumed.auth_session_id
            or consumed_replay.refresh_token != consumed.refresh_token
            or consumed_replay.principal != consumed.principal
            or not consumed_replay.replayed
        ):
            raise RuntimeError("ConsumeMagicLink exact replay was not stable")
        _expect_rpc_error(lambda: consume_magic_link("0" * 64), grpc.StatusCode.ABORTED)
        principal = consumed.principal
        if principal.site_id != site_id or not principal.organization_id:
            raise RuntimeError(
                "IAM did not issue the personal Organization principal context"
            )
        if frozenset(principal.permission_keys) != PERMISSIONS:
            raise RuntimeError(
                f"IAM personal-owner permissions mismatch: {sorted(principal.permission_keys)}"
            )

        request_id = _request_id()
        session = iam.GetSession(
            authentication_pb2.GetSessionRequest(request_id=request_id),
            metadata=_metadata(web_token, request_id, consumed.access_token),
            timeout=10,
        )
        if (
            session.auth_session_id != consumed.auth_session_id
            or session.principal != principal
        ):
            raise RuntimeError("IAM GetSession did not round-trip the issued principal")
        _authorize(chat_token, consumed.access_token, principal.organization_id)

        create_command = _command(canonical_digest({"title": "Native Slice A"}))

        def create_conversation(*, title: str, digest: str):
            current_request_id = _request_id()
            return commands.CreateConversation(
                chat_pb2.CreateConversationRequest(
                    request_id=current_request_id,
                    command=common_pb2.CommandIdentity(
                        command_id=create_command.command_id, request_digest=digest
                    ),
                    title=title,
                ),
                metadata=_metadata(
                    web_token, current_request_id, consumed.access_token
                ),
                timeout=10,
            )

        created = create_conversation(
            title="Native Slice A", digest=create_command.request_digest
        )
        created_replay = create_conversation(
            title="Native Slice A", digest=create_command.request_digest
        )
        if (
            created_replay.conversation_id != created.conversation_id
            or not created_replay.replayed
        ):
            raise RuntimeError("CreateConversation exact replay was not stable")
        _expect_rpc_error(
            lambda: create_conversation(
                title="Native Slice A drift",
                digest=canonical_digest({"title": "Native Slice A drift"}),
            ),
            grpc.StatusCode.ABORTED,
        )
        submit_digest = canonical_digest(
            {"content": CONTENT, "conversation_id": created.conversation_id}
        )
        submit_command = _command(submit_digest)

        def submit_message(*, content: str, digest: str):
            current_request_id = _request_id()
            return commands.SubmitMessage(
                chat_pb2.SubmitMessageRequest(
                    request_id=current_request_id,
                    command=common_pb2.CommandIdentity(
                        command_id=submit_command.command_id, request_digest=digest
                    ),
                    conversation_id=created.conversation_id,
                    content=content,
                    requested_model_label="default",
                    requested_agent_key="general",
                ),
                metadata=_metadata(
                    web_token, current_request_id, consumed.access_token
                ),
                timeout=10,
            )

        submitted = submit_message(content=CONTENT, digest=submit_digest)
        submitted_replay = submit_message(content=CONTENT, digest=submit_digest)
        if (
            submitted_replay.launch_id != submitted.launch_id
            or submitted_replay.user_message_id != submitted.user_message_id
            or submitted_replay.assistant_message_id != submitted.assistant_message_id
            or not submitted_replay.replayed
        ):
            raise RuntimeError("SubmitMessage exact replay was not stable")
        changed_content = f"{CONTENT} drift"
        _expect_rpc_error(
            lambda: submit_message(
                content=changed_content,
                digest=canonical_digest(
                    {
                        "content": changed_content,
                        "conversation_id": created.conversation_id,
                    }
                ),
            ),
            grpc.StatusCode.ABORTED,
        )

        def snapshot():
            snapshot_request_id = _request_id()
            return queries.ReadConversationSnapshot(
                chat_pb2.ReadConversationSnapshotRequest(
                    request_id=snapshot_request_id,
                    conversation_id=created.conversation_id,
                ),
                metadata=_metadata(
                    web_token, snapshot_request_id, consumed.access_token
                ),
                timeout=5,
            )

        awaiting = _wait_for(
            snapshot,
            lambda item: (
                len(item.pending_interactions) == 1 and item.HasField("active_run")
            ),
            "ask_user HITL projection",
            redact=runtime.redact,
        )
        before_restart = _snapshot_fingerprint(awaiting)
        runtime.restart("agent")
        runtime.restart("chat")
        recovered = _wait_for(
            snapshot,
            lambda item: _snapshot_fingerprint(item) == before_restart,
            "Chat/Agent restart recovery",
            redact=runtime.redact,
        )
        interaction = recovered.pending_interactions[0]
        payload = json.loads(interaction.payload_json)
        pending_ids = payload.get("pending_tool_ids")
        allowed = payload.get("allowed_decisions")
        if (
            not isinstance(pending_ids, list)
            or pending_ids != [TOOL_ID]
            or allowed != ["respond"]
            or payload.get("name") != "ask_user_question"
            or payload.get("args") != json.loads(TOOL_ARGUMENTS)
        ):
            raise RuntimeError(f"unexpected ask_user projection payload: {payload!r}")
        decision_payload = {"response": "Approve"}
        decision = {
            "kind": common_pb2.DECISION_KIND_RESPOND,
            "target_id": str(pending_ids[0]),
            "payload": decision_payload,
        }
        decision_digest = canonical_digest(
            {
                "content": None,
                "control_kind": "CONTROL_KIND_DECIDE",
                "decisions": [decision],
                "message_id": None,
            }
        )
        decide_command = _command(decision_digest)

        def decide_interaction(*, response: str, digest: str):
            current_request_id = _request_id()
            return commands.DecideInteraction(
                chat_pb2.DecideInteractionRequest(
                    request_id=current_request_id,
                    command=common_pb2.CommandIdentity(
                        command_id=decide_command.command_id, request_digest=digest
                    ),
                    conversation_id=created.conversation_id,
                    interaction_id=interaction.interaction_id,
                    expected_generation=interaction.generation,
                    decisions=[
                        common_pb2.ControlDecision(
                            kind=common_pb2.DECISION_KIND_RESPOND,
                            target_id=str(pending_ids[0]),
                            payload_json=json.dumps(
                                {"response": response}, separators=(",", ":")
                            ).encode(),
                        )
                    ],
                ),
                metadata=_metadata(
                    web_token, current_request_id, consumed.access_token
                ),
                timeout=10,
            )

        decided = decide_interaction(response="Approve", digest=decision_digest)
        decided_replay = decide_interaction(response="Approve", digest=decision_digest)
        if (
            decided_replay.control_id != decided.control_id
            or not decided_replay.replayed
        ):
            raise RuntimeError("DecideInteraction exact replay was not stable")
        drift_payload = {"response": "Reject"}
        drift_decision = {
            "kind": common_pb2.DECISION_KIND_RESPOND,
            "target_id": str(pending_ids[0]),
            "payload": drift_payload,
        }
        _expect_rpc_error(
            lambda: decide_interaction(
                response="Reject",
                digest=canonical_digest(
                    {
                        "content": None,
                        "control_kind": "CONTROL_KIND_DECIDE",
                        "decisions": [drift_decision],
                        "message_id": None,
                    }
                ),
            ),
            grpc.StatusCode.ABORTED,
        )
        terminal = _wait_for(
            snapshot,
            lambda item: (
                not item.HasField("active_run") and not item.pending_interactions
            ),
            "terminal Chat projection",
            timeout=60,
            redact=runtime.redact,
        )
        _validate_terminal_snapshot(
            chat_pb2, terminal, submitted, created.conversation_id
        )
        event_kinds = _read_stream_kinds(
            queries,
            chat_pb2,
            created.conversation_id,
            web_token,
            consumed.access_token,
            expected={
                "tool.awaiting_approval",
                "interaction.resolved",
                "run.completed",
            },
            through_seq=terminal.watermark,
        )

        tail_content = "slice-a-retention-tail"
        tail_digest = canonical_digest(
            {"content": tail_content, "conversation_id": created.conversation_id}
        )
        tail_command = _command(tail_digest)

        def emit_retention_tail() -> None:
            def submit_tail(*, content: str, digest: str):
                current_request_id = _request_id()
                return commands.SubmitMessage(
                    chat_pb2.SubmitMessageRequest(
                        request_id=current_request_id,
                        command=common_pb2.CommandIdentity(
                            command_id=tail_command.command_id,
                            request_digest=digest,
                        ),
                        conversation_id=created.conversation_id,
                        content=content,
                        requested_model_label="default",
                        requested_agent_key="general",
                    ),
                    metadata=_metadata(
                        web_token, current_request_id, consumed.access_token
                    ),
                    timeout=10,
                )

            emitted = submit_tail(content=tail_content, digest=tail_digest)
            replayed = submit_tail(content=tail_content, digest=tail_digest)
            if (
                replayed.launch_id != emitted.launch_id
                or replayed.user_message_id != emitted.user_message_id
                or replayed.assistant_message_id != emitted.assistant_message_id
                or not replayed.replayed
            ):
                raise RuntimeError("retention tail SubmitMessage replay was not stable")
            drift_content = f"{tail_content}-drift"
            _expect_rpc_error(
                lambda: submit_tail(
                    content=drift_content,
                    digest=canonical_digest(
                        {
                            "content": drift_content,
                            "conversation_id": created.conversation_id,
                        }
                    ),
                ),
                grpc.StatusCode.ABORTED,
            )

        retention = _assert_retention_snapshot_required(
            runtime,
            queries,
            chat_pb2,
            created.conversation_id,
            web_token,
            consumed.access_token,
            terminal,
            emit_retention_tail,
        )

        refresh_command = _command(
            refresh_digest(site_id, consumed.auth_session_id, consumed.refresh_token)
        )

        def refresh_session(digest: str | None = None):
            current_request_id = _request_id()
            return iam.RefreshSession(
                authentication_pb2.RefreshSessionRequest(
                    request_id=current_request_id,
                    command=common_pb2.CommandIdentity(
                        command_id=refresh_command.command_id,
                        request_digest=digest or refresh_command.request_digest,
                    ),
                    refresh_token=consumed.refresh_token,
                ),
                metadata=_metadata(web_token, current_request_id),
                timeout=10,
            )

        refreshed = refresh_session()
        runtime.register_sensitive(refreshed.access_token, refreshed.refresh_token)
        refreshed_replay = refresh_session()
        runtime.register_sensitive(
            refreshed_replay.access_token, refreshed_replay.refresh_token
        )
        if (
            refreshed_replay.auth_session_id != refreshed.auth_session_id
            or refreshed_replay.refresh_token != refreshed.refresh_token
            or not refreshed_replay.replayed
        ):
            raise RuntimeError("RefreshSession exact replay was not stable")
        _expect_rpc_error(lambda: refresh_session("0" * 64), grpc.StatusCode.ABORTED)
        if (
            not refreshed.auth_session_id
            or refreshed.auth_session_id == consumed.auth_session_id
            or refreshed.principal != principal
        ):
            raise RuntimeError(
                "IAM RefreshSession did not preserve the issued authority context"
            )
        request_id = _request_id()
        try:
            iam.GetSession(
                authentication_pb2.GetSessionRequest(request_id=request_id),
                metadata=_metadata(web_token, request_id, consumed.access_token),
                timeout=10,
            )
        except grpc.RpcError as error:
            if error.code() != grpc.StatusCode.UNAUTHENTICATED:
                raise RuntimeError(
                    f"IAM rejected the rotated access session with {error.code().name}"
                ) from error
        else:
            raise RuntimeError("IAM kept the rotated access session active")
        _authorize(chat_token, refreshed.access_token, principal.organization_id)
        logout_command = _command(
            logout_digest(refreshed.auth_session_id, refreshed.refresh_token)
        )

        def logout_session(digest: str | None = None):
            current_request_id = _request_id()
            return iam.Logout(
                authentication_pb2.LogoutRequest(
                    request_id=current_request_id,
                    command=common_pb2.CommandIdentity(
                        command_id=logout_command.command_id,
                        request_digest=digest or logout_command.request_digest,
                    ),
                    refresh_token=refreshed.refresh_token,
                ),
                metadata=_metadata(web_token, current_request_id),
                timeout=10,
            )

        logout = logout_session()
        if not logout.revoked or logout.auth_session_id != refreshed.auth_session_id:
            raise RuntimeError("IAM logout did not revoke the refreshed session")
        logout_replay = logout_session()
        if (
            logout_replay.auth_session_id != logout.auth_session_id
            or not logout_replay.replayed
        ):
            raise RuntimeError("Logout exact replay was not stable")
        _expect_rpc_error(lambda: logout_session("0" * 64), grpc.StatusCode.ABORTED)
        _expect_rpc_error(
            lambda: refresh_session("0" * 64), grpc.StatusCode.UNAUTHENTICATED
        )
        request_id = _request_id()
        try:
            iam.GetSession(
                authentication_pb2.GetSessionRequest(request_id=request_id),
                metadata=_metadata(web_token, request_id, refreshed.access_token),
                timeout=10,
            )
        except grpc.RpcError as error:
            if error.code() != grpc.StatusCode.UNAUTHENTICATED:
                raise RuntimeError(
                    f"IAM rejected the logged-out session with {error.code().name}"
                ) from error
        else:
            raise RuntimeError("IAM kept the logged-out access session active")

        _assert_no_secret_logs(
            runtime,
            extra=(
                token,
                consumed.access_token,
                consumed.refresh_token,
                refreshed.access_token,
                refreshed.refresh_token,
            ),
        )

        evidence = _assert_sql_evidence(
            runtime,
            principal_id=principal.principal_id,
            organization_id=principal.organization_id,
            conversation_id=created.conversation_id,
            agent_namespace=created.agent_namespace,
            launch_id=submitted.launch_id,
            control_id=decided.control_id,
        )
        return {
            "site_id": SITE_ID,
            "organization_id": principal.organization_id,
            "conversation_id": created.conversation_id,
            "launch_id": submitted.launch_id,
            "control_id": decided.control_id,
            "terminal_watermark": terminal.watermark,
            "retained_watermark": retention["snapshot_watermark"],
            "retention_tail_seq": retention["tail_seq"],
            "retention_recovered_watermark": retention["recovered_watermark"],
            "stream_kinds": event_kinds,
            "sql": evidence,
            "catalog": evidence["catalog"],
            "site_table_boundary": evidence["site_table_boundary"],
            "assertions": {name: True for name in REQUIRED_PRODUCT_ASSERTIONS},
        }
    finally:
        iam_channel.close()
        chat_channel.close()


def _assert_no_secret_logs(runtime: NativeRuntime, *, extra: tuple[str, ...]) -> None:
    runtime.register_sensitive(*extra)
    values = set(runtime.sensitive_values())
    if runtime.paths.secrets.is_dir():
        for name in SECRET_FILES:
            path = runtime.paths.secrets / name
            if not path.is_file():
                continue
            value = path.read_text(errors="replace")
            values.add(value)
            values.update(line for line in value.splitlines() if len(line) >= 16)
    artifacts = [
        path
        for root in (runtime.paths.state, runtime.paths.fixtures)
        if root.is_dir()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    ]
    for artifact in artifacts:
        content = artifact.read_text(errors="replace")
        if any(value and value in content for value in values):
            raise RuntimeError(
                f"secret material appeared in owned artifact: {artifact.name}"
            )


def _snapshot_fingerprint(snapshot: Any) -> str:
    value = {
        "conversation_id": snapshot.conversation.conversation_id,
        "messages": [
            {
                "id": message.message_id,
                "status": message.status,
                "generation": message.generation,
                "parts": [
                    hashlib.sha256(part.payload_json).hexdigest()
                    for part in message.parts
                ],
            }
            for message in snapshot.messages
        ],
        "run": None
        if not snapshot.HasField("active_run")
        else {
            "id": snapshot.active_run.agent_run_id,
            "received": snapshot.active_run.received_seq,
            "projected": snapshot.active_run.projected_seq,
        },
        "interactions": [
            {
                "id": item.interaction_id,
                "generation": item.generation,
                "payload": hashlib.sha256(item.payload_json).hexdigest(),
            }
            for item in snapshot.pending_interactions
        ],
        "watermark": snapshot.watermark,
    }
    return canonical_digest(value)


def _validate_retention_recovery(
    *,
    snapshot_watermark: int,
    tail_sequences: list[int],
    snapshot_history: list[str],
    recovered_history: list[str],
) -> int:
    if not tail_sequences:
        raise RuntimeError("retention recovery produced no new tail")
    if tail_sequences != sorted(set(tail_sequences)):
        raise RuntimeError("retention recovery tail is duplicate or out of order")
    if tail_sequences[0] != snapshot_watermark + 1:
        raise RuntimeError("retention recovery tail looped or skipped the watermark")
    if recovered_history[: len(snapshot_history)] != snapshot_history:
        raise RuntimeError("retention recovery changed snapshot history")
    return tail_sequences[0]


def _snapshot_message_fingerprints(snapshot: Any) -> list[str]:
    return [
        canonical_digest(
            {
                "generation": message.generation,
                "id": message.message_id,
                "parts": [
                    hashlib.sha256(part.payload_json).hexdigest()
                    for part in message.parts
                ],
                "role": message.role,
                "status": message.status,
            }
        )
        for message in snapshot.messages
    ]


def _validate_terminal_snapshot(
    chat_pb2: Any, terminal: Any, submitted: Any, conversation_id: str
) -> None:
    messages = list(terminal.messages)
    if len(messages) != 2:
        raise RuntimeError("terminal snapshot message shape is not exact")
    user, assistant = messages
    if (
        user.message_id != submitted.user_message_id
        or assistant.message_id != submitted.assistant_message_id
        or user.conversation_id != conversation_id
        or assistant.conversation_id != conversation_id
        or user.role != chat_pb2.MESSAGE_ROLE_USER
        or assistant.role != chat_pb2.MESSAGE_ROLE_ASSISTANT
        or user.status != chat_pb2.MESSAGE_STATUS_COMPLETED
        or assistant.status != chat_pb2.MESSAGE_STATUS_COMPLETED
        or (user.ordinal, assistant.ordinal) != (1, 2)
        or (user.generation, assistant.generation) != (1, 1)
        or user.HasField("parent_message_id")
        or not assistant.HasField("parent_message_id")
        or assistant.parent_message_id != user.message_id
    ):
        raise RuntimeError("terminal snapshot message shape is not exact")
    expected_kinds = (
        (chat_pb2.MESSAGE_PART_KIND_TEXT,),
        (
            chat_pb2.MESSAGE_PART_KIND_TOOL_CALL,
            chat_pb2.MESSAGE_PART_KIND_TOOL_RESULT,
            chat_pb2.MESSAGE_PART_KIND_TEXT,
        ),
    )
    for message, kinds in zip(messages, expected_kinds, strict=True):
        parts = list(message.parts)
        if (
            tuple(part.kind for part in parts) != kinds
            or tuple(part.ordinal for part in parts) != tuple(range(1, len(kinds) + 1))
            or any(
                not part.part_id
                or part.schema_version != 1
                or part.status != chat_pb2.MESSAGE_PART_STATUS_COMPLETE
                for part in parts
            )
        ):
            raise RuntimeError("terminal snapshot part shape is not exact")

    payloads = [
        json.loads(part.payload_json) for message in messages for part in message.parts
    ]
    user_text, tool_call, tool_result, assistant_text = payloads
    expected_args = json.loads(TOOL_ARGUMENTS)
    if user_text != {"text": CONTENT}:
        raise RuntimeError("terminal snapshot user TEXT payload is not exact")
    if (
        set(tool_call)
        != {
            "segment_id",
            "tool_id",
            "name",
            "args",
            "returned",
            "awaitingApproval",
        }
        or not isinstance(tool_call["segment_id"], str)
        or not tool_call["segment_id"]
        or tool_call["tool_id"] != TOOL_ID
        or tool_call["name"] != "ask_user_question"
        or tool_call["args"] != expected_args
        or tool_call["returned"] is not True
        or tool_call["awaitingApproval"] is not True
    ):
        raise RuntimeError("terminal snapshot TOOL_CALL payload is not exact")
    if (
        set(tool_result)
        != {
            "segment_id",
            "tool_id",
            "name",
            "result",
            "is_error",
            "truncated",
            "rejected",
            "responded",
        }
        or not isinstance(tool_result["segment_id"], str)
        or not tool_result["segment_id"]
        or tool_result["tool_id"] != TOOL_ID
        or tool_result["name"] != "ask_user_question"
        or tool_result["result"] != "Approve"
        or any(
            tool_result[name] is not False
            for name in ("is_error", "truncated", "rejected", "responded")
        )
    ):
        raise RuntimeError("terminal snapshot TOOL_RESULT payload is not exact")
    if (
        set(assistant_text) != {"segment_id", "delta", "content"}
        or not isinstance(assistant_text["segment_id"], str)
        or not assistant_text["segment_id"]
        or assistant_text["delta"] != "Slice A approved."
        or assistant_text["content"] != "Slice A approved."
    ):
        raise RuntimeError("terminal snapshot assistant TEXT payload is not exact")


def _read_stream_kinds(
    queries: Any,
    chat_pb2: Any,
    conversation_id: str,
    workload_token: str,
    access_token: str,
    *,
    expected: set[str],
    through_seq: int | None = None,
) -> list[str]:
    request_id = _request_id()
    call = queries.StreamConversationEvents(
        chat_pb2.StreamConversationEventsRequest(
            request_id=request_id,
            conversation_id=conversation_id,
            after_seq=0,
        ),
        metadata=_metadata(workload_token, request_id, access_token),
        timeout=10,
    )
    kinds: list[str] = []
    sequences: list[int] = []
    event_ids: list[str] = []
    try:
        for response in call:
            if through_seq is not None and response.event.seq != len(sequences) + 1:
                raise RuntimeError("stream replay violates terminal watermark prefix")
            kinds.append(response.event.kind)
            sequences.append(response.event.seq)
            event_ids.append(response.event.event_id)
            if through_seq is not None and response.event.seq == through_seq:
                break
    finally:
        call.cancel()
    if through_seq is not None and sequences != list(range(1, through_seq + 1)):
        raise RuntimeError("stream replay violates terminal watermark prefix")
    if sequences != sorted(set(sequences)) or len(event_ids) != len(set(event_ids)):
        raise RuntimeError("stream replay contains duplicate/out-of-order events")
    if any(kinds.count(kind) > 1 for kind in expected):
        raise RuntimeError("stream replay duplicated a release event kind")
    missing = expected - set(kinds)
    if missing:
        raise RuntimeError(f"stream recovery lacks expected kinds: {sorted(missing)}")
    return kinds


def _assert_retention_snapshot_required(
    runtime: NativeRuntime,
    queries: Any,
    chat_pb2: Any,
    conversation_id: str,
    workload_token: str,
    access_token: str,
    expected_snapshot: Any,
    emit_tail: Callable[[], None],
) -> dict[str, int]:
    import grpc
    from kokoro.common.v1 import common_pb2

    changed = _psql(
        runtime,
        "UPDATE kokoro.chat_stream_event SET expires_at=now()-interval '1 day' WHERE conversation_id=:'conversation_id'::uuid RETURNING seq",
        ("conversation_id", conversation_id),
    )
    if not changed:
        raise RuntimeError("retention fixture found no stream rows to expire")
    runtime.restart("chat")

    def stale_stream() -> None:
        request_id = _request_id()
        call = queries.StreamConversationEvents(
            chat_pb2.StreamConversationEventsRequest(
                request_id=request_id,
                conversation_id=conversation_id,
                after_seq=0,
            ),
            metadata=_metadata(workload_token, request_id, access_token),
            timeout=5,
        )
        next(iter(call))

    deadline = time.monotonic() + 10
    error: grpc.RpcError | None = None
    while time.monotonic() < deadline:
        try:
            stale_stream()
        except grpc.RpcError as candidate:
            if candidate.code() == grpc.StatusCode.FAILED_PRECONDITION:
                error = candidate
                break
        time.sleep(0.1)
    if error is None:
        raise RuntimeError("expired stream cursor did not require a snapshot")
    detail_bytes: bytes | None = None
    for item in error.trailing_metadata() or ():
        if item.key == "kokoro-error-bin":
            detail_bytes = (
                item.value
                if isinstance(item.value, bytes)
                else __import__("base64").b64decode(item.value)
            )
            break
    if detail_bytes is None:
        raise RuntimeError("SNAPSHOT_REQUIRED lacks typed ErrorDetail")
    detail = common_pb2.ErrorDetail.FromString(detail_bytes)
    if detail.code != common_pb2.ERROR_CODE_SNAPSHOT_REQUIRED:
        raise RuntimeError("expired cursor returned the wrong typed error")
    request_id = _request_id()
    snapshot = queries.ReadConversationSnapshot(
        chat_pb2.ReadConversationSnapshotRequest(
            request_id=request_id, conversation_id=conversation_id
        ),
        metadata=_metadata(workload_token, request_id, access_token),
        timeout=10,
    )
    if _snapshot_fingerprint(snapshot) != _snapshot_fingerprint(expected_snapshot):
        raise RuntimeError("retention changed the complete owner snapshot")
    snapshot_watermark = int(snapshot.watermark)
    snapshot_history = _snapshot_message_fingerprints(snapshot)
    reconnect_request_id = _request_id()
    reconnected = queries.StreamConversationEvents(
        chat_pb2.StreamConversationEventsRequest(
            request_id=reconnect_request_id,
            conversation_id=conversation_id,
            after_seq=snapshot_watermark,
        ),
        metadata=_metadata(workload_token, reconnect_request_id, access_token),
        timeout=10,
    )
    try:
        emit_tail()
        tail = next(iter(reconnected)).event
    finally:
        reconnected.cancel()

    def recovered_snapshot() -> Any:
        current_request_id = _request_id()
        return queries.ReadConversationSnapshot(
            chat_pb2.ReadConversationSnapshotRequest(
                request_id=current_request_id,
                conversation_id=conversation_id,
            ),
            metadata=_metadata(workload_token, current_request_id, access_token),
            timeout=10,
        )

    recovered = _wait_for(
        recovered_snapshot,
        lambda candidate: int(candidate.watermark) >= int(tail.seq),
        "new stream tail after snapshot watermark",
        timeout=10,
        redact=runtime.redact,
    )
    tail_seq = _validate_retention_recovery(
        snapshot_watermark=snapshot_watermark,
        tail_sequences=[int(tail.seq)],
        snapshot_history=snapshot_history,
        recovered_history=_snapshot_message_fingerprints(recovered),
    )
    return {
        "snapshot_watermark": snapshot_watermark,
        "tail_seq": tail_seq,
        "recovered_watermark": int(recovered.watermark),
    }


def _authorize(workload_token: str, access_token: str, organization_id: str) -> None:
    """Exercise the committed Root-generated IAM Authorization client."""
    import grpc

    try:
        from kokoro.iam.v1 import authorization_pb2, authorization_pb2_grpc
    except ImportError as error:
        raise RuntimeError(
            "Root E2E generated closure does not yet contain IAM Authorization"
        ) from error
    channel = grpc.insecure_channel("127.0.0.1:7202")
    try:
        client = authorization_pb2_grpc.IamAuthorizationServiceStub(channel)
        for permission in sorted(PERMISSIONS):
            request_id = _request_id()
            response = client.Authorize(
                authorization_pb2.AuthorizeRequest(
                    request_id=request_id,
                    site_id=SITE_ID,
                    organization_id=organization_id,
                    permission_key=permission,
                ),
                metadata=_metadata(workload_token, request_id, access_token),
                timeout=10,
            )
            if not response.allowed or response.reason_code != "allowed":
                raise RuntimeError(f"IAM denied expected permission: {permission}")
    finally:
        channel.close()


def _assert_sql_evidence(
    runtime: NativeRuntime,
    *,
    principal_id: str,
    organization_id: str,
    conversation_id: str,
    agent_namespace: str,
    launch_id: str,
    control_id: str,
) -> dict[str, Any]:
    public = runtime.state().get("public")
    if not isinstance(public, dict):
        raise RuntimeError("runtime state lacks public database facts")
    database_url = str(public["provisioning_database_url"])
    config = json.loads((runtime.paths.state / "supervisor.json").read_text())
    postgres_bin = Path(str(config["postgres_bin"]))
    configured_roots = config.get("roots") if isinstance(config, dict) else None
    if not isinstance(configured_roots, dict):
        raise RuntimeError("runtime evidence lacks exact candidate roots")
    site_table_boundary = validate_site_table_boundary(
        {name: Path(str(configured_roots[name])) for name in DEFAULT_COMMITS}
    )
    query = """
    WITH selected_run AS (
      SELECT r.agent_run_id,r.state,a.projected_seq,a.rejected_seq,a.rejection_code,a.consumer_closed
      FROM kokoro.agent_run r
      JOIN kokoro.agent_projection_ack a ON a.agent_run_id=r.agent_run_id AND a.consumer='chat'
      WHERE r.launch_id=:'launch_id'::uuid
    )
    SELECT json_build_object(
      'org_kind',(SELECT kind FROM kokoro.iam_organization WHERE organization_id=:'organization_id'::uuid),
      'org_status',(SELECT status FROM kokoro.iam_organization WHERE organization_id=:'organization_id'::uuid),
      'org_owner',(SELECT personal_owner_principal_id::text FROM kokoro.iam_organization WHERE organization_id=:'organization_id'::uuid),
      'owner_membership',(SELECT count(*) FROM kokoro.iam_membership m JOIN kokoro.iam_membership_role mr USING(membership_id,organization_id) JOIN kokoro.iam_role r USING(role_id,organization_id) WHERE m.organization_id=:'organization_id'::uuid AND m.principal_id=:'principal_id'::uuid AND m.status='active' AND r.key='personal_owner' AND r.status='active'),
      'owner_permissions',(SELECT count(DISTINCT p.key) FROM kokoro.iam_membership m JOIN kokoro.iam_membership_role mr USING(membership_id,organization_id) JOIN kokoro.iam_role r USING(role_id,organization_id) JOIN kokoro.iam_role_permission rp USING(role_id) JOIN kokoro.iam_permission p USING(permission_id) WHERE m.organization_id=:'organization_id'::uuid AND m.principal_id=:'principal_id'::uuid AND m.status='active' AND r.key='personal_owner' AND r.status='active' AND p.status='active'),
      'iam_receipts',(SELECT count(*) FROM kokoro.iam_command_receipt WHERE status='completed'),
      'chat_receipts',(SELECT count(*) FROM kokoro.chat_command_receipt WHERE organization_id=:'organization_id'::uuid AND command_kind IN ('CreateConversation','SubmitMessage','DecideInteraction') AND status='completed'),
      'launch_accepted',(SELECT count(*) FROM kokoro.chat_launch_outbox WHERE launch_id=:'launch_id'::uuid AND accepted_at IS NOT NULL),
      'control_acked',(SELECT count(*) FROM kokoro.chat_control_outbox WHERE control_id=:'control_id'::uuid AND published_at IS NOT NULL AND acked_at IS NOT NULL),
      'projection_failed',(SELECT count(*) FROM kokoro.chat_projection_inbox i JOIN kokoro.chat_run_view v USING(agent_run_id) WHERE v.launch_id=:'launch_id'::uuid AND i.status='failed'),
      'projection_dlq',(SELECT count(*) FROM kokoro.chat_projection_dlq d JOIN kokoro.chat_projection_inbox i USING(inbox_id) JOIN kokoro.chat_run_view v USING(agent_run_id) WHERE v.launch_id=:'launch_id'::uuid),
      'agent_run_id',(SELECT agent_run_id::text FROM selected_run),
      'agent_state',(SELECT state FROM selected_run),
      'manifest_count',(SELECT count(*) FROM kokoro.agent_execution_manifest m WHERE m.agent_run_id=(SELECT agent_run_id FROM selected_run)),
      'manifest_exact',(SELECT count(*) FROM kokoro.agent_execution_manifest m JOIN kokoro.capability_runtime_snapshot c ON c.snapshot_id=m.capability_snapshot_id JOIN kokoro.model_revision mr ON mr.model_revision_id=m.model_revision_id JOIN kokoro.model_provider mp ON mp.provider_id=mr.provider_id WHERE m.agent_run_id=(SELECT agent_run_id FROM selected_run) AND m.namespace=:'agent_namespace' AND m.payload->>'requested_model_label'='default' AND m.payload->>'model_provider'='litellm' AND m.payload->>'provider_model_name'='slice-a-fixture' AND m.payload->'capability_selectors'='[]'::jsonb AND m.payload->'skills'='[]'::jsonb AND m.payload->'mcp_servers'='[]'::jsonb AND m.payload->>'capability_snapshot_id'=c.snapshot_id::text AND m.payload->>'capability_snapshot_digest'=encode(c.digest,'hex') AND m.payload->>'model_revision_id'=mr.model_revision_id::text AND mr.provider_model_name='slice-a-fixture' AND mp.key='slice-a-fixture'),
      'control_applied',(SELECT count(*) FROM kokoro.agent_control_inbox c WHERE c.agent_run_id=(SELECT agent_run_id FROM selected_run) AND c.status='applied'),
      'tool_effects',(SELECT count(*) FROM kokoro.agent_tool_effect e WHERE e.agent_run_id=(SELECT agent_run_id FROM selected_run)),
      'agent_event_kinds',(SELECT json_agg(e.kind ORDER BY e.seq) FROM kokoro.agent_event_outbox e WHERE e.agent_run_id=(SELECT agent_run_id FROM selected_run)),
      'terminal_events',(SELECT count(*) FROM kokoro.agent_event_outbox e WHERE e.agent_run_id=(SELECT agent_run_id FROM selected_run) AND e.kind='run.completed'),
      'terminal_projections',(SELECT count(*) FROM kokoro.chat_run_view v WHERE v.launch_id=:'launch_id'::uuid AND v.state='completed' AND v.terminal_kind='completed'),
      'acked_events',(SELECT count(*) FROM kokoro.agent_event_outbox e WHERE e.agent_run_id=(SELECT agent_run_id FROM selected_run) AND e.published_at IS NOT NULL AND e.acked_at IS NOT NULL),
      'all_events',(SELECT count(*) FROM kokoro.agent_event_outbox e WHERE e.agent_run_id=(SELECT agent_run_id FROM selected_run)),
      'projected_seq',(SELECT projected_seq FROM selected_run),
      'rejected_seq',(SELECT rejected_seq FROM selected_run),
      'rejection_code',(SELECT rejection_code FROM selected_run),
      'consumer_closed',(SELECT consumer_closed FROM selected_run)
      ,'catalog_tables',(SELECT json_agg(tablename ORDER BY tablename) FROM pg_catalog.pg_tables WHERE schemaname='kokoro')
    )::text
    """
    result = subprocess.run(
        [
            str(postgres_bin / "psql"),
            database_url,
            "-v",
            "ON_ERROR_STOP=1",
            "-v",
            f"principal_id={principal_id}",
            "-v",
            f"organization_id={organization_id}",
            "-v",
            f"conversation_id={conversation_id}",
            "-v",
            f"agent_namespace={agent_namespace}",
            "-v",
            f"launch_id={launch_id}",
            "-v",
            f"control_id={control_id}",
            "-Atc",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    facts = json.loads(result.stdout)
    if (facts["org_kind"], facts["org_status"], facts["org_owner"]) != (
        "personal",
        "active",
        principal_id,
    ):
        raise RuntimeError(f"personal Organization owner evidence mismatch: {facts!r}")
    if (facts["owner_membership"], facts["owner_permissions"]) != (1, 5):
        raise RuntimeError(
            f"personal owner membership/role evidence mismatch: {facts!r}"
        )
    if (
        facts["iam_receipts"] < 4
        or facts["chat_receipts"] != 4
        or tuple(
            facts[name]
            for name in (
                "launch_accepted",
                "control_acked",
                "projection_failed",
                "projection_dlq",
            )
        )
        != (1, 1, 0, 0)
    ):
        raise RuntimeError(f"Chat receipt/outbox/ACK/NACK evidence mismatch: {facts!r}")
    if (
        facts["agent_state"] != "completed"
        or facts["manifest_count"] != 1
        or facts["manifest_exact"] != 1
        or facts["control_applied"] != 1
    ):
        raise RuntimeError(
            f"Agent terminal/manifest/control evidence mismatch: {facts!r}"
        )
    if (
        facts["acked_events"] != facts["all_events"]
        or facts["projected_seq"] != facts["all_events"]
        or facts["rejected_seq"] is not None
        or facts["rejection_code"] is not None
        or facts["consumer_closed"] is not True
        or facts["terminal_events"] != 1
        or facts["terminal_projections"] != 1
    ):
        raise RuntimeError(f"Agent event ACK/NACK/close evidence mismatch: {facts!r}")
    event_kinds = facts["agent_event_kinds"]
    if not isinstance(event_kinds, list) or facts["tool_effects"] != 1:
        raise RuntimeError(f"Agent event inventory is invalid: {facts!r}")
    authority = json.loads((ROOT / "database/slices/slice-a.json").read_text())
    tables = authority.get("tables")
    if not isinstance(tables, dict):
        raise RuntimeError("Slice A table authority is invalid")
    expected_catalog = sorted(
        str(table) for owner_tables in tables.values() for table in owner_tables
    )
    if facts["catalog_tables"] != expected_catalog:
        raise RuntimeError("live PostgreSQL catalog differs from the 50+4 authority")
    checkpointer = set(tables.get("langgraph", []))
    owner_count = len(expected_catalog) - len(checkpointer)
    if (owner_count, len(checkpointer)) != (50, 4):
        raise RuntimeError("Slice A catalog authority is not exactly 50+4")
    baseline_manifest = json.loads(
        (ROOT / "database/baseline/manifest.json").read_text()
    )
    if public.get("baseline_sha256") != baseline_manifest.get("baselineSha256"):
        raise RuntimeError("runtime baseline digest differs from committed authority")
    model_bootstrap = public.get("model_bootstrap")
    if not isinstance(model_bootstrap, dict) or (
        model_bootstrap.get("exact_replay"),
        model_bootstrap.get("drift_rejected"),
    ) != (True, True):
        raise RuntimeError("Model bootstrap replay/drift evidence is incomplete")
    seed_digest = public.get("seed_digest")
    if not isinstance(seed_digest, str) or len(seed_digest) != 64:
        raise RuntimeError("runtime seed digest is missing")
    return {
        "iam_completed_receipts": int(facts["iam_receipts"]),
        "chat_completed_receipts": int(facts["chat_receipts"]),
        "agent_run_id": str(facts["agent_run_id"]),
        "agent_acked_events": int(facts["acked_events"]),
        "agent_nack_absent": True,
        "consumer_closed": True,
        "event_kinds": event_kinds,
        "tool_effects": int(facts["tool_effects"]),
        "baseline_sha256": str(public["baseline_sha256"]),
        "seed_digest": seed_digest,
        "model_bootstrap": model_bootstrap,
        "catalog_tables": expected_catalog,
        "catalog": {"owner": owner_count, "checkpointer": len(checkpointer)},
        "site_table_boundary": site_table_boundary,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the native no-Docker Slice A backend E2E"
    )
    parser.add_argument("--iam", type=Path, default=Path("/tmp/kokoro-iam-slice-a"))
    parser.add_argument("--model", type=Path, default=Path("/tmp/kokoro-model-slice-a"))
    parser.add_argument(
        "--capability", type=Path, default=Path("/tmp/kokoro-capability-slice-a")
    )
    parser.add_argument("--chat", type=Path, default=Path("/tmp/kokoro-bff-slice-a"))
    parser.add_argument("--agent", type=Path, default=Path("/tmp/kokoro-agent-slice-a"))
    for name, commit in DEFAULT_COMMITS.items():
        parser.add_argument(f"--{name}-commit", default=commit)
    parser.add_argument("--start-timeout", type=float, default=420.0)
    parser.add_argument("--total-timeout", type=float, default=720.0)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--compare-evidence", nargs=2, type=Path)
    return parser


def compare_evidence(first: dict[str, Any], second: dict[str, Any]) -> None:
    for label, evidence in (("first", first), ("second", second)):
        validate_release_evidence(evidence)
        sql = evidence.get("sql")
        if not isinstance(sql, dict):
            raise RuntimeError(f"{label} evidence lacks SQL parity facts")
    parity_paths = (
        ("catalog",),
        ("site_table_boundary",),
        ("retained_watermark",),
        ("retention_tail_seq",),
        ("retention_recovered_watermark",),
        ("stream_kinds",),
        ("sql", "event_kinds"),
        ("sql", "tool_effects"),
        ("sql", "catalog_tables"),
        ("sql", "baseline_sha256"),
        ("sql", "seed_digest"),
        ("sql", "model_bootstrap", "manifest_sha256"),
        ("sql", "model_bootstrap", "result_sha256"),
    )
    for path in parity_paths:
        left: Any = first
        right: Any = second
        for key in path:
            left, right = left[key], right[key]
        if left != right:
            raise RuntimeError(f"native evidence parity drift at {'.'.join(path)}")


def _redacted_runtime_error(
    runtime: NativeRuntime, error: BaseException
) -> RuntimeError:
    message = runtime.redact(f"{type(error).__name__}: {error}")
    if isinstance(error, RunInterrupted):
        return RunInterrupted(message)
    return RuntimeError(message)


def main() -> int:
    args = _parser().parse_args()
    if args.compare_evidence is not None:
        first, second = (json.loads(path.read_text()) for path in args.compare_evidence)
        if not isinstance(first, dict) or not isinstance(second, dict):
            raise RuntimeError("native evidence files must contain objects")
        compare_evidence(first, second)
        print(json.dumps({"status": "PASS", "evidenceParity": True}, sort_keys=True))
        return 0
    validate_generated_client_provenance()
    validate_runtime_candidates(args)
    runtime = NativeRuntime(args)
    cleaned = False

    def cleanup() -> None:
        nonlocal cleaned
        if cleaned:
            return
        runtime.stop()
        cleaned = True

    def interrupted(signum: int, _frame: FrameType | None) -> None:
        raise RunInterrupted(f"received signal {signal.Signals(signum).name}")

    atexit.register(cleanup)
    handled_signals = (signal.SIGINT, signal.SIGTERM, signal.SIGALRM)
    previous = {
        current: signal.signal(current, interrupted) for current in handled_signals
    }
    signal.setitimer(signal.ITIMER_REAL, args.total_timeout)
    try:
        runtime.start()
        evidence = _run_product_chain(runtime)
        encoded_evidence = json.dumps(evidence, sort_keys=True)
        if runtime.redact(encoded_evidence) != encoded_evidence:
            raise RuntimeError("secret material appeared in release evidence")
        cleanup()
        validate_runtime_candidates(args)
        validate_generated_client_provenance()
        validate_release_evidence(evidence)
        if args.evidence is not None:
            target = args.evidence.absolute()
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
            os.chmod(temporary, 0o600)
            os.replace(temporary, target)
        print(json.dumps({"status": "PASS", **evidence}, sort_keys=True))
        return 0
    except BaseException as error:
        try:
            diagnostics = runtime.diagnostics()
        except OSError:
            diagnostics = ""
        if diagnostics:
            print(runtime.redact(diagnostics), file=sys.stderr)
        raise _redacted_runtime_error(runtime, error) from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        for current, handler in previous.items():
            signal.signal(current, handler)
        try:
            cleanup()
        except BaseException as cleanup_error:
            raise _redacted_runtime_error(runtime, cleanup_error) from None
        finally:
            atexit.unregister(cleanup)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, RunInterrupted, subprocess.SubprocessError) as error:
        print(f"native Slice A E2E failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

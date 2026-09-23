#!/usr/bin/env python3
"""Run the isolated real-process Scheduler-to-BFF acceptance smoke."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass, field
import json
import os
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from typing import BinaryIO

if __package__:
    from . import scheduler_bff_smoke_runtime as _runtime
    from .bff_iam_admission_stub import AdmissionIdentity, iam_admission_stub
    from .scheduler_bff_smoke_cases import exercise_cases, http_json
    from .scheduler_bff_smoke_http import (
        AgentReceiptState,
        agent_receipt_stub,
        response_drop_proxy,
    )
else:
    import scheduler_bff_smoke_runtime as _runtime
    from bff_iam_admission_stub import AdmissionIdentity, iam_admission_stub
    from scheduler_bff_smoke_cases import exercise_cases, http_json
    from scheduler_bff_smoke_http import (
        AgentReceiptState,
        agent_receipt_stub,
        response_drop_proxy,
    )

BFF, SCHEDULER = _runtime.BFF, _runtime.SCHEDULER
OwnedResources, SmokeError = _runtime.OwnedResources, _runtime.SmokeError
ProcessLike = _runtime.ProcessLike
command_output, run_owned_command = (
    _runtime.command_output,
    _runtime.run_owned_command,
)
stop_owned_process = _runtime.stop_owned_process

BFF_RELEASE = "6238599667110fbfbc2d5ef3a9d53731f2623cfe"
SCHEDULER_RELEASE = "975dee59616a1e0eda609aa69283401344900d83"
EXPECTED_CASES = (
    "control_create",
    "control_replace",
    "control_delete",
    "delete_404_reconciled",
    "create_409_replaced",
    "replace_404_created",
    "fractional_rfc3339_callback",
    "duplicate_replay",
    "same_key_different_digest_409",
    "trusted_tenant_mismatch_400",
    "response_unknown_restart_retry",
)


def verify_release(repository: Path, expected: str) -> None:
    if command_output(["git", "rev-parse", "HEAD"], cwd=repository).strip() != expected:
        raise SmokeError(f"{repository.name} release mismatch")
    if command_output(["git", "status", "--porcelain"], cwd=repository).strip():
        raise SmokeError(f"{repository.name} release checkout is dirty")


def verify_inputs(
    args: argparse.Namespace, bff_release: str, scheduler_release: str
) -> tuple[dict[str, str], dict[str, str]]:
    verify_release(BFF, bff_release)
    verify_release(SCHEDULER, scheduler_release)
    node_dir = Path(args.bff_node_bin).expanduser().resolve()
    node, corepack = node_dir / "node", node_dir / "corepack"
    if not node.is_file() or not corepack.is_file():
        raise SmokeError("Node v22.22.2 toolchain is missing")
    node_env = dict(os.environ)
    node_env["PATH"] = os.pathsep.join(
        [str(node_dir), "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    )
    if command_output([str(node), "--version"], env=node_env).strip() != "v22.22.2":
        raise SmokeError("Node v22.22.2 required for BFF")
    if (
        command_output(
            [str(corepack), "pnpm", "--version"], cwd=BFF, env=node_env
        ).strip()
        != "11.25.0"
    ):
        raise SmokeError("pnpm 11.25.0 required for BFF")
    go = Path(args.go_bin).expanduser().resolve()
    if not go.is_file():
        raise SmokeError("Explicit Go toolchain is missing")
    go_env = dict(os.environ)
    go_version = command_output([str(go), "version"], cwd=SCHEDULER, env=go_env).split()
    if len(go_version) < 3 or go_version[:3] != ["go", "version", "go1.26.8"]:
        raise SmokeError("Go 1.26.8 required for Scheduler")
    if (
        command_output(
            [str(go), "env", "GOTOOLCHAIN"], cwd=SCHEDULER, env=go_env
        ).strip()
        != "auto"
    ):
        raise SmokeError("Scheduler Go toolchain must resolve through GOTOOLCHAIN=auto")
    return node_env, go_env


def build_scheduler(
    go: Path, go_env: dict[str, str], directory: Path, log: BinaryIO
) -> Path:
    binary = directory / "scheduler-smoke"
    if (
        run_owned_command(
            [str(go), "build", "-o", str(binary), "./cmd/scheduler"],
            cwd=SCHEDULER,
            env=go_env,
            log=log,
            timeout=180,
        )
        != 0
    ):
        raise SmokeError("Scheduler source build failed")
    return binary


def build_bff(node_env: dict[str, str], log: BinaryIO) -> None:
    corepack = str(Path(node_env["PATH"].split(os.pathsep)[0]) / "corepack")
    if (
        run_owned_command(
            [corepack, "pnpm", "build"], cwd=BFF, env=node_env, log=log, timeout=180
        )
        != 0
    ):
        raise SmokeError("BFF source build failed")


def apply_schemas(
    scheduler_url: str,
    bff_url: str,
    go: Path,
    go_env: dict[str, str],
    node_env: dict[str, str],
    log: BinaryIO,
) -> None:
    scheduler_env = {
        **go_env,
        "SCHEDULER_DATABASE_URL": scheduler_url,
        "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
    }
    if (
        run_owned_command(
            [str(go), "run", "./cmd/db-apply-schema"],
            cwd=SCHEDULER,
            env=scheduler_env,
            log=log,
            timeout=180,
        )
        != 0
    ):
        raise SmokeError("Scheduler schema installation failed")
    bff_env = {
        **node_env,
        "KOKORO_BFF_POSTGRES_URL": bff_url,
        "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
    }
    corepack = str(Path(node_env["PATH"].split(os.pathsep)[0]) / "corepack")
    if (
        run_owned_command(
            [corepack, "pnpm", "db:apply-schema"],
            cwd=BFF,
            env=bff_env,
            log=log,
            timeout=180,
        )
        != 0
    ):
        raise SmokeError("BFF schema installation failed")


def start_process(
    executable: Path, env: dict[str, str], cwd: Path, log: BinaryIO | None
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [str(executable)] if cwd == SCHEDULER else [str(executable), "dist/main.js"],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log or subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def wait_ready(base: str, process: ProcessLike, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise SmokeError("Owned process exited before readiness")
        try:
            result = http_json(base, "/readyz")
            data = result.body.get("data")
            if result.body.get("status") in {"ready", "ok"} or (
                isinstance(data, dict)
                and data.get("status") == "ok"
                and data.get("service") == "kokoro-scheduler"
            ):
                return
        except SmokeError:
            pass
        time.sleep(0.2)
    raise SmokeError("Owned process did not become ready in 30s")


def restart_bff(
    old: ProcessLike, node: Path, env: dict[str, str], cwd: Path, log: BinaryIO | None
) -> subprocess.Popen[bytes]:
    stop_owned_process(old)
    return start_process(node, env, cwd, log)


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


_PRIVATE_CALLBACK_NETWORKS = (
    IPv4Network("10.0.0.0/8"),
    IPv4Network("172.16.0.0/12"),
    IPv4Network("192.168.0.0/16"),
)


def _is_owned_address(address: str) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((address, 0))
        return True
    except OSError:
        return False


def callback_binding() -> tuple[str, str, str]:
    host = socket.gethostname().rstrip(".").lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
        raise SmokeError("Host does not provide a valid callback DNS name")
    addresses = sorted(
        {
            item[4][0]
            for item in socket.getaddrinfo(host, None, socket.AF_INET)
            if item[4]
        }
    )
    if len(addresses) != 1:
        raise SmokeError("Host callback address is ambiguous")
    address = addresses[0]
    try:
        parsed = IPv4Address(address)
    except ValueError:
        raise SmokeError("Host callback address is invalid") from None
    if address != "127.0.0.1" and not any(
        parsed in network for network in _PRIVATE_CALLBACK_NETWORKS
    ):
        raise SmokeError("Host callback address is not RFC1918 private")
    if not _is_owned_address(address):
        raise SmokeError("Host callback address is not locally owned")
    return host, address, address + "/32"


def success_summary(
    cases: list[dict[str, str]], releases: dict[str, str], cleanup: dict[str, str]
) -> dict[str, object]:
    names = tuple(case.get("name") for case in cases)
    if names != EXPECTED_CASES or any(case.get("status") != "PASS" for case in cases):
        raise SmokeError("Smoke must complete exactly eleven ordered cases")
    return {
        "status": "PASS",
        "cases": 11,
        "results": cases,
        "releases": releases,
        "toolchains": {"node": "v22.22.2", "pnpm": "11.25.0", "go": "go1.26.8"},
        "agent_evidence": "deterministic receipt stub; not a real Agent",
        "cleanup": cleanup,
    }


def failure_summary(_error: BaseException, _sensitive: list[str]) -> dict[str, str]:
    return {"status": "FAIL", "error": "smoke execution failed"}


@dataclass
class RunState:
    resources: OwnedResources
    tenant: str
    directory: Path
    directory_context: tempfile.TemporaryDirectory[str] | None
    processes: list[subprocess.Popen[bytes]] = field(default_factory=list)
    binary: Path | None = None
    scheduler_url: str | None = None


@dataclass(frozen=True)
class ServiceConfiguration:
    scheduler_base: str
    bff_base: str
    scheduler_env: dict[str, str]
    bff_env: dict[str, str]
    node: Path
    scheduler_token: str
    web_token: str
    session_token: str


def prepare_owned_dependencies(
    state: RunState,
    args: argparse.Namespace,
    node_env: dict[str, str],
    go_env: dict[str, str],
    log: BinaryIO,
    fault_injection: Callable[[str], None] | None,
) -> tuple[str, str]:
    state.binary = build_scheduler(
        Path(args.go_bin).expanduser().resolve(), go_env, state.directory, log
    )
    if fault_injection is not None:
        fault_injection("after-build")
    build_bff(node_env, log)
    command_output(
        [
            "psql",
            args.postgres_admin_url,
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-Atc",
            "SELECT 1",
        ]
    )
    if (
        command_output(["redis-cli", "-e", "-u", args.redis_url, "PING"]).strip()
        != "PONG"
    ):
        raise SmokeError("Shared Redis unavailable")
    state.resources.claim_harness_prefix()
    state.scheduler_url = state.resources.create_database("scheduler")
    bff_url = state.resources.create_database("bff")
    apply_schemas(
        state.scheduler_url,
        bff_url,
        Path(args.go_bin).expanduser().resolve(),
        go_env,
        node_env,
        log,
    )
    return state.scheduler_url, bff_url


def service_configuration(
    state: RunState,
    args: argparse.Namespace,
    node_env: dict[str, str],
    go_env: dict[str, str],
    scheduler_url: str,
    bff_url: str,
    agent_base: str,
    iam_base: str,
    session_token: str,
    proxy_base: str,
    callback_host: str,
    callback_cidr: str,
    scheduler_port: int,
    bff_port: int,
) -> ServiceConfiguration:
    scheduler_base = f"http://127.0.0.1:{scheduler_port}"
    bff_base = f"http://127.0.0.1:{bff_port}"
    proxy_port = proxy_base.rsplit(":", 1)[1]
    target_url = (
        f"http://{callback_host}:{proxy_port}/internal/bff/scheduled-tasks/dispatch"
    )
    scheduler_token, web_token, agent_token = (
        secrets.token_urlsafe(24) for _ in range(3)
    )
    scheduler_env = {
        **go_env,
        "SCHEDULER_DATABASE_URL": scheduler_url,
        "SCHEDULER_REDIS_URL": state.resources.scheduler_redis_url,
        "SCHEDULER_HTTP_ADDR": f"127.0.0.1:{scheduler_port}",
        "SCHEDULER_INTERNAL_SERVICE_TOKEN": scheduler_token,
        "SCHEDULER_TARGET_SERVICE_TOKEN": scheduler_token,
        "SCHEDULER_INTERNAL_TARGET_ALLOWLIST": json.dumps(
            [{"host": callback_host, "cidrs": [callback_cidr]}]
        ),
        "SCHEDULER_WAKEUP_INTERVAL": "100ms",
        "SCHEDULER_CLAIM_TTL": "10s",
        "SCHEDULER_DISPATCH_TIMEOUT": "5s",
        "SCHEDULER_WORKER_ID": "w0b-" + state.resources.run_id,
        "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
    }
    bff_env = {
        **node_env,
        "KOKORO_BFF_POSTGRES_URL": bff_url,
        "KOKORO_BFF_REDIS_URL": state.resources.bff_redis_url,
        "KOKORO_BFF_HOST": "127.0.0.1",
        "KOKORO_BFF_PORT": str(bff_port),
        "KOKORO_BFF_MODE": "live",
        "KOKORO_BFF_SHARED_SECRET": web_token,
        "KOKORO_IAM_BASE_URL": iam_base,
        "KOKORO_INTERNAL_SECRET_BFF": agent_token,
        "KOKORO_SCHEDULER_SERVICE_TOKEN": scheduler_token,
        "KOKORO_SCHEDULER_BASE_URL": scheduler_base,
        "KOKORO_SCHEDULER_TARGET_URL": target_url,
        "KOKORO_AGENT_ENABLED": "true",
        "KOKORO_AGENT_BASE_URL": agent_base,
        "KOKORO_TENANT_ID": state.tenant,
        "KOKORO_DOMAIN": state.resources.run_id + ".smoke.local",
        "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
    }
    node = Path(args.bff_node_bin).expanduser().resolve() / "node"
    return ServiceConfiguration(
        scheduler_base,
        bff_base,
        scheduler_env,
        bff_env,
        node,
        scheduler_token,
        web_token,
        session_token,
    )


def exercise_real_processes(
    state: RunState,
    args: argparse.Namespace,
    node_env: dict[str, str],
    go_env: dict[str, str],
    scheduler_url: str,
    bff_url: str,
    agent: AgentReceiptState,
    iam_base: str,
    session_token: str,
    log: BinaryIO,
    callback: tuple[str, str, str],
) -> list[dict[str, str]]:
    scheduler_port, bff_port = free_port(), free_port()
    bff_base = f"http://127.0.0.1:{bff_port}"
    callback_host, callback_address, callback_cidr = callback
    with response_drop_proxy(bff_base, bind_address=callback_address) as proxy:
        proxy.set_target_host(callback_host)
        config = service_configuration(
            state,
            args,
            node_env,
            go_env,
            scheduler_url,
            bff_url,
            agent.base_url,
            iam_base,
            session_token,
            proxy.base_url,
            callback_host,
            callback_cidr,
            scheduler_port,
            bff_port,
        )
        assert state.binary is not None
        scheduler_process = start_process(
            state.binary, config.scheduler_env, SCHEDULER, log
        )
        state.processes.append(scheduler_process)
        wait_ready(config.scheduler_base, scheduler_process)
        bff_process = start_process(config.node, config.bff_env, BFF, log)
        state.processes.append(bff_process)
        wait_ready(config.bff_base, bff_process)

        def restart() -> None:
            nonlocal bff_process
            bff_process = restart_bff(
                bff_process, config.node, config.bff_env, BFF, log
            )
            state.processes[-1] = bff_process
            wait_ready(config.bff_base, bff_process)

        return exercise_cases(
            config.bff_base,
            config.scheduler_base,
            bff_url,
            scheduler_url,
            config.web_token,
            config.session_token,
            config.scheduler_token,
            state.tenant,
            "subject-" + state.resources.run_id,
            proxy,
            agent,
            restart,
        )


def cleanup_run(state: RunState) -> None:
    failures: list[str] = []
    for process in reversed(state.processes):
        try:
            stop_owned_process(process)
        except (SmokeError, OSError):
            failures.append("owned process shutdown failed")
    if state.scheduler_url is not None:
        try:
            state.resources.register_native_keys(state.scheduler_url, state.tenant)
        except (SmokeError, subprocess.SubprocessError, OSError):
            failures.append("native Redis ownership registration failed")
    try:
        state.resources.cleanup()
    except SmokeError:
        failures.append("owned infrastructure cleanup failed")
    if not failures:
        try:
            state.resources.verify_clean()
        except SmokeError:
            failures.append("owned resource residue detected")
    if state.binary is not None:
        try:
            state.binary.unlink(missing_ok=True)
        except OSError:
            failures.append("temporary Scheduler binary cleanup failed")
    if state.directory_context is not None:
        state.directory_context.cleanup()
    if failures:
        raise SmokeError("; ".join(failures))


def run_smoke(
    args: argparse.Namespace,
    *,
    work_directory: Path | None = None,
    fault_injection: Callable[[str], None] | None = None,
) -> int:
    node_env, go_env = verify_inputs(args, BFF_RELEASE, SCHEDULER_RELEASE)
    callback = callback_binding()
    run_id = secrets.token_hex(12)
    directory_context = (
        tempfile.TemporaryDirectory(prefix="kokoro-w0b-scheduler-")
        if work_directory is None
        else None
    )
    directory = Path(directory_context.name) if directory_context else work_directory
    assert directory is not None
    directory.mkdir(parents=True, exist_ok=True)
    state = RunState(
        OwnedResources(args.postgres_admin_url, args.redis_url, run_id),
        "w0b-scheduler-" + run_id,
        directory,
        directory_context,
    )
    cases: list[dict[str, str]] = []
    session_token = secrets.token_urlsafe(32)
    try:
        with (
            (directory / "smoke.log").open("wb") as log,
            agent_receipt_stub() as agent,
            iam_admission_stub(
                {
                    session_token: AdmissionIdentity(
                        tenant_id=state.tenant,
                        user_id="subject-" + run_id,
                        session_id="session-" + run_id,
                        client_id="w0b-scheduler-smoke",
                    )
                }
            ) as iam_base,
        ):
            scheduler_url, bff_url = prepare_owned_dependencies(
                state, args, node_env, go_env, log, fault_injection
            )
            cases = exercise_real_processes(
                state,
                args,
                node_env,
                go_env,
                scheduler_url,
                bff_url,
                agent,
                iam_base,
                session_token,
                log,
                callback,
            )
    finally:
        cleanup_run(state)
    summary = success_summary(
        cases,
        {"bff": BFF_RELEASE, "scheduler": SCHEDULER_RELEASE},
        {
            "process_groups": "stopped",
            "databases": "dropped",
            "redis": "exact allow-list verified",
            "temporary_files": "removed",
        },
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--postgres-admin-url", required=True)
    result.add_argument("--redis-url", required=True)
    result.add_argument("--bff-node-bin", required=True)
    result.add_argument("--go-bin", required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return run_smoke(args)
    except Exception as error:
        print(
            json.dumps(
                failure_summary(error, [args.postgres_admin_url, args.redis_url])
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

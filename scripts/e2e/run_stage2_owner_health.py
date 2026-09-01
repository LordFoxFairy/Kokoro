#!/usr/bin/env python3
"""Run a disposable PostgreSQL + Redis health closure for the active owners.

This is intentionally an orchestration check, not a second service runtime. Each
owner is started from its own checkout and keeps its own config/database adapter;
the Root only supplies disposable infrastructure and records the observed health
responses.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
POSTGRES_NAME = "kokoro-stage2-owner-health-postgres"
REDIS_NAME = "kokoro-stage2-owner-health-redis"
POSTGRES_PORT = 55417
REDIS_PORT = 55418
DATABASE_URL = f"postgresql://kokoro:stage2_local@127.0.0.1:{POSTGRES_PORT}/kokoro_stage2"
REDIS_URL = f"redis://127.0.0.1:{REDIS_PORT}/15"
INTERNAL_SECRET = "stage2_owner_health_internal_secret"


class CheckError(RuntimeError):
    pass


def run(command: list[str], *, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode:
        detail = (result.stderr or result.stdout or "command failed").strip()
        raise CheckError(f"{' '.join(command)}: {detail[-1200:]}")
    return result


def wait_until(predicate: Any, timeout: float, label: str) -> None:
    deadline = time.monotonic() + timeout
    last_error = "not ready"
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
        except Exception as error:  # pragma: no cover - diagnostic retry boundary
            last_error = str(error)
        time.sleep(0.5)
    raise CheckError(f"timed out waiting for {label}: {last_error}")


def start_infra() -> None:
    for name in (POSTGRES_NAME, REDIS_NAME):
        run(["docker", "rm", "-f", name], check=False)
    run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            POSTGRES_NAME,
            "-e",
            "POSTGRES_DB=kokoro_stage2",
            "-e",
            "POSTGRES_USER=kokoro",
            "-e",
            "POSTGRES_PASSWORD=stage2_local",
            "-p",
            f"127.0.0.1:{POSTGRES_PORT}:5432",
            "postgres:16-alpine",
        ]
    )
    run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            REDIS_NAME,
            "-p",
            f"127.0.0.1:{REDIS_PORT}:6379",
            "redis:7-alpine",
        ]
    )
    wait_until(
        lambda: run(
            ["docker", "exec", POSTGRES_NAME, "pg_isready", "-U", "kokoro", "-d", "kokoro_stage2"],
            check=False,
        ).returncode
        == 0,
        30,
        "PostgreSQL",
    )
    wait_until(
        lambda: run(["docker", "exec", REDIS_NAME, "redis-cli", "ping"], check=False).returncode == 0,
        30,
        "Redis",
    )


def apply_schemas() -> None:
    commands = [
        (ROOT / "kokoro-system", ["pnpm", "db:apply"]),
        (ROOT / "kokoro-billing", ["pnpm", "db:migrate"]),
        (ROOT / "kokoro-capability", ["npm", "run", "db:apply-schema"]),
        (ROOT / "kokoro-storage", ["npm", "run", "db:apply-schema"]),
    ]
    env = {
        **os.environ,
        "DATABASE_URL": DATABASE_URL,
        "KOKORO_POSTGRES_URL": DATABASE_URL,
        "REDIS_URL": REDIS_URL,
        "KOKORO_REDIS_URL": REDIS_URL,
        "BILLING_AUTH_MODE": "header-fixture",
        "INTERNAL_SERVICE_SECRET": INTERNAL_SECRET,
        "BILLING_REDEEM_SECRET": "stage2_owner_health_redeem_secret_32",
        "BILLING_ENABLED_PROVIDERS": "mock",
        "PROVIDER_WEBHOOK_SECRETS_JSON": '{"mock":"stage2_owner_health"}',
    }
    for cwd, command in commands:
        result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
        if result.returncode:
            detail = (result.stderr or result.stdout or "schema command failed").strip()
            raise CheckError(f"schema {cwd.name}: {detail[-1600:]}")


def process_env(extra: dict[str, str]) -> dict[str, str]:
    return {
        **os.environ,
        "NODE_ENV": "development",
        "DATABASE_URL": DATABASE_URL,
        "KOKORO_POSTGRES_URL": DATABASE_URL,
        "KOKORO_REDIS_URL": REDIS_URL,
        "REDIS_URL": REDIS_URL,
        **extra,
    }


def start_processes(log_dir: Path) -> list[tuple[str, subprocess.Popen[str]]]:
    log_dir.mkdir(parents=True, exist_ok=True)
    specs: list[tuple[str, Path, list[str], dict[str, str]]] = [
        ("iam", ROOT / "kokoro-iam", ["pnpm", "dev"], {"KOKORO_IAM_HOST": "127.0.0.1", "KOKORO_IAM_PORT": "4211"}),
        ("system", ROOT / "kokoro-system", ["pnpm", "dev"], {"KOKORO_SYSTEM_HOST": "127.0.0.1", "KOKORO_SYSTEM_PORT": "4240", "KOKORO_IAM_BASE_URL": "http://127.0.0.1:4211", "KOKORO_IAM_BACKEND_TOKEN": INTERNAL_SECRET, "KOKORO_SYSTEM_REDIS_NAMESPACE": "kokoro:stage2:system"}),
        ("billing", ROOT / "kokoro-billing", ["pnpm", "dev"], {"BILLING_HOST": "127.0.0.1", "BILLING_PORT": "4245", "BILLING_AUTH_MODE": "header-fixture", "INTERNAL_SERVICE_SECRET": INTERNAL_SECRET, "BILLING_OPERATOR_PROXY_SECRET": INTERNAL_SECRET, "BILLING_REDEEM_SECRET": "stage2_owner_health_redeem_secret_32", "BILLING_ENABLED_PROVIDERS": "mock", "PROVIDER_WEBHOOK_SECRETS_JSON": '{"mock":"stage2_owner_health"}'}),
        ("storage", ROOT / "kokoro-storage", ["npm", "run", "dev"], {"KOKORO_STORAGE_PORT": "8085", "KOKORO_OBJECT_STORE_DRIVER": "local", "KOKORO_OBJECT_STORE_ROOT_DIR": str(log_dir / "objects")}),
        ("capability", ROOT / "kokoro-capability", ["npm", "run", "dev"], {"KOKORO_CAPABILITY_PORT": "8086", "KOKORO_STORAGE_URL": "http://127.0.0.1:8085"}),
        ("bff-live", ROOT / "kokoro-bff", ["pnpm", "start"], {"KOKORO_BFF_HOST": "127.0.0.1", "KOKORO_BFF_PORT": "4300", "KOKORO_BFF_MODE": "live", "KOKORO_DOMAIN": "dev.kokoro.localhost", "KOKORO_BFF_SHARED_SECRET": INTERNAL_SECRET, "KOKORO_INTERNAL_SECRET_BFF": INTERNAL_SECRET, "KOKORO_PROJECTS_BASE_URL": "http://127.0.0.1:4240", "KOKORO_HUB_BASE_URL": "http://127.0.0.1:8086", "KOKORO_SKILLS_BASE_URL": "http://127.0.0.1:8086", "KOKORO_SCHEDULED_BASE_URL": "http://127.0.0.1:4240", "KOKORO_AGENT_BASE_URL": "http://127.0.0.1:4240", "KOKORO_LIBRARY_BASE_URL": "http://127.0.0.1:4240", "KOKORO_BILLING_BASE_URL": "http://127.0.0.1:4245"}),
        ("web", ROOT / "kokoro", ["pnpm", "dev"], {"PORT": "3000", "KOKORO_DOMAIN": "dev.kokoro.localhost", "KOKORO_BFF_BASE_URL": "http://127.0.0.1:4300", "KOKORO_INTERNAL_SECRET_WEB_BFF": INTERNAL_SECRET, "NEXT_PUBLIC_SESSION_PREVIEW": "1", "NEXT_TELEMETRY_DISABLED": "1"}),
        ("agent", ROOT / "kokoro-agent", ["uv", "run", "kokoro-agent-worker"], {"KOKORO_AGENT_DATABASE_URL": DATABASE_URL, "KOKORO_AGENT_DATABASE_SCHEMA": "kokoro_agent_stage2", "KOKORO_DISABLE_STREAMING": "1"}),
        ("scheduler", ROOT / "kokoro-scheduler", ["go", "run", "./cmd/scheduler"], {"SCHEDULER_JOBS_JSON": "[]", "SCHEDULER_REDIS_URL": REDIS_URL}),
    ]
    processes: list[tuple[str, subprocess.Popen[str]]]=[]
    for name, cwd, command, extra in specs:
        log = (log_dir / f"{name}.log").open("w", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=process_env(extra),
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        processes.append((name, process))
    return processes


def stop_processes(processes: list[tuple[str, subprocess.Popen[str]]]) -> None:
    for _, process in processes:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    deadline = time.monotonic() + 10
    for _, process in processes:
        remaining = max(0.0, deadline - time.monotonic())
        try:
            process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def stop_infra() -> None:
    for name in (POSTGRES_NAME, REDIS_NAME):
        run(["docker", "rm", "-f", name], check=False)


def http_get(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"x-kokoro-tenant-id": "tenant_stage2", "x-kokoro-actor-id": "actor_stage2"})
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, response.read(400).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read(400).decode("utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=ROOT / "docs/reports/2026-09-01-stage2-owner-health.json")
    parser.add_argument("--keep-infra", action="store_true", help="leave disposable PostgreSQL/Redis containers running")
    args = parser.parse_args(argv)
    evidence: dict[str, Any] = {"mode": "disposable-owner-health", "checks": [], "processes": [], "status": "FAIL"}
    processes: list[tuple[str, subprocess.Popen[str]]] = []
    log_dir = Path("/tmp/kokoro-stage2-owner-health")
    try:
        start_infra()
        apply_schemas()
        processes = start_processes(log_dir)
        for name, process in processes:
            time.sleep(0.2)
            evidence["processes"].append({"name": name, "running": process.poll() is None, "exit_code": process.poll()})
        endpoints = {
            "iam_health": "http://127.0.0.1:4211/healthz",
            "iam_ready": "http://127.0.0.1:4211/readyz",
            "system_health": "http://127.0.0.1:4240/healthz",
            "system_ready": "http://127.0.0.1:4240/readyz",
            "billing_health": "http://127.0.0.1:4245/healthz",
            "billing_ready": "http://127.0.0.1:4245/readyz",
            "storage_health": "http://127.0.0.1:8085/healthz",
            "storage_ready": "http://127.0.0.1:8085/readyz",
            "capability_health": "http://127.0.0.1:8086/healthz",
            "capability_ready": "http://127.0.0.1:8086/readyz",
            "model_health": "http://127.0.0.1:4221/healthz",
            "model_ready": "http://127.0.0.1:4221/readyz",
            "bff_live_ready": "http://127.0.0.1:4300/readyz",
            "web_root": "http://127.0.0.1:3000/",
        }
        for name, url in endpoints.items():
            result: dict[str, Any] = {"name": name, "url": url}
            try:
                wait_until(lambda url=url: 200 <= http_get(url)[0] < 400, 45, name)
                result["status"], result["body"] = http_get(url)
                result["ok"] = True
            except CheckError as error:
                result["ok"] = False
                result["error"] = str(error)
            evidence["checks"].append(result)
        if all(item.get("ok") for item in evidence["checks"]) and all(item["running"] for item in evidence["processes"]):
            evidence["status"] = "PASS"
    except Exception as error:
        evidence["error"] = str(error)
    finally:
        stop_processes(processes)
        if not args.keep_infra:
            stop_infra()
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

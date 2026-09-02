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
WEB_NEXT_ENV = ROOT / "kokoro/next-env.d.ts"
POSTGRES_NAME = "kokoro-stage2-owner-health-postgres"
REDIS_NAME = "kokoro-stage2-owner-health-redis"
POSTGRES_PORT = 55417
REDIS_PORT = 55418
POSTGRES_HOST = f"127.0.0.1:{POSTGRES_PORT}"
OWNER_NAMES = ("bff", "system", "model", "billing", "capability", "storage", "agent")
DATABASE_URLS = {
    name: f"postgresql://kokoro:stage2_local@{POSTGRES_HOST}/kokoro_stage2_{name}"
    for name in OWNER_NAMES
}
REDIS_URLS = {
    name: f"redis://127.0.0.1:{REDIS_PORT}/{index}"
    for index, name in enumerate((*OWNER_NAMES, "scheduler"))
}
DATABASE_URL = DATABASE_URLS["bff"]
REDIS_URL = REDIS_URLS["bff"]
INTERNAL_SECRET = "stage2_owner_health_internal_secret"
TENANT_ID = "00000000-0000-0000-0000-000000000001"
ACTOR_ID = "00000000-0000-0000-0000-000000000002"


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
    for name in OWNER_NAMES:
        result = run(
            [
                "docker",
                "exec",
                POSTGRES_NAME,
                "psql",
                "-U",
                "kokoro",
                "-d",
                "kokoro_stage2",
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                f'CREATE DATABASE "kokoro_stage2_{name}"',
            ],
            check=False,
        )
        if result.returncode and "already exists" not in (result.stderr or ""):
            raise CheckError(f"create database {name}: {(result.stderr or result.stdout).strip()[-1200:]}")


def apply_schemas() -> None:
    commands = [
        (ROOT / "kokoro-bff", ["pnpm", "db:migrate"], {"KOKORO_BFF_POSTGRES_URL": DATABASE_URLS["bff"]}),
        (ROOT / "kokoro-system", ["pnpm", "db:apply"], {"DATABASE_URL": DATABASE_URLS["system"], "REDIS_URL": REDIS_URLS["system"]}),
        (ROOT / "kokoro-model", ["pnpm", "db:migrate"], {"DATABASE_URL_MODEL": DATABASE_URLS["model"]}),
        (ROOT / "kokoro-billing", ["pnpm", "db:migrate"], {"DATABASE_URL": DATABASE_URLS["billing"], "REDIS_URL": REDIS_URLS["billing"]}),
        (ROOT / "kokoro-capability", ["npm", "run", "db:apply-schema"], {"KOKORO_POSTGRES_URL": DATABASE_URLS["capability"], "KOKORO_REDIS_URL": REDIS_URLS["capability"]}),
        (ROOT / "kokoro-storage", ["npm", "run", "db:apply-schema"], {"KOKORO_POSTGRES_URL": DATABASE_URLS["storage"], "KOKORO_REDIS_URL": REDIS_URLS["storage"]}),
    ]
    env = {
        **os.environ,
        "DATABASE_URL": DATABASE_URL,
        "KOKORO_POSTGRES_URL": DATABASE_URL,
        "KOKORO_BFF_POSTGRES_URL": DATABASE_URL,
        "REDIS_URL": REDIS_URL,
        "KOKORO_REDIS_URL": REDIS_URL,
        "KOKORO_BFF_REDIS_URL": REDIS_URL,
        "DATABASE_URL_MODEL": DATABASE_URL,
        "BILLING_AUTH_MODE": "header-fixture",
        "INTERNAL_SERVICE_SECRET": INTERNAL_SECRET,
        "BILLING_REDEEM_SECRET": "stage2_owner_health_redeem_secret_32",
        "BILLING_ENABLED_PROVIDERS": "mock",
        "PROVIDER_WEBHOOK_SECRETS_JSON": '{"mock":"stage2_owner_health"}',
    }
    for cwd, command, overrides in commands:
        result = subprocess.run(command, cwd=cwd, env={**env, **overrides}, text=True, capture_output=True, check=False)
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
        ("iam", ROOT / "kokoro-iam", ["pnpm", "dev"], {
            "KOKORO_IAM_HOST": "127.0.0.1",
            "KOKORO_IAM_PORT": "4211",
            "KOKORO_IAM_SERVICE_TOKEN": INTERNAL_SECRET,
            "KOKORO_IAM_TENANT_BINDINGS": json.dumps([{
                "host": "dev.kokoro.localhost",
                "tenant_id": TENANT_ID,
                "status": "active",
                "binding_revision": "stage2",
            }]),
        }),
        ("system", ROOT / "kokoro-system", ["pnpm", "dev"], {"DATABASE_URL": DATABASE_URLS["system"], "REDIS_URL": REDIS_URLS["system"], "KOKORO_SYSTEM_HOST": "127.0.0.1", "KOKORO_SYSTEM_PORT": "4240", "KOKORO_IAM_BASE_URL": "http://127.0.0.1:4211", "KOKORO_IAM_BACKEND_TOKEN": INTERNAL_SECRET, "KOKORO_SYSTEM_BFF_SERVICE_TOKEN": INTERNAL_SECRET, "KOKORO_SYSTEM_REDIS_NAMESPACE": "kokoro:stage2:system"}),
        ("model", ROOT / "kokoro-model", ["pnpm", "dev"], {"DATABASE_URL_MODEL": DATABASE_URLS["model"], "KOKORO_MODEL_HTTP_PORT": "4221", "KOKORO_REDIS_URL": REDIS_URLS["model"]}),
        ("billing", ROOT / "kokoro-billing", ["pnpm", "dev"], {"DATABASE_URL": DATABASE_URLS["billing"], "REDIS_URL": REDIS_URLS["billing"], "BILLING_HOST": "127.0.0.1", "BILLING_PORT": "4245", "BILLING_AUTH_MODE": "header-fixture", "INTERNAL_SERVICE_SECRET": INTERNAL_SECRET, "BILLING_OPERATOR_PROXY_SECRET": INTERNAL_SECRET, "BILLING_REDEEM_SECRET": "stage2_owner_health_redeem_secret_32", "BILLING_ENABLED_PROVIDERS": "mock", "PROVIDER_WEBHOOK_SECRETS_JSON": '{"mock":"stage2_owner_health"}'}),
        ("storage", ROOT / "kokoro-storage", ["npm", "run", "dev"], {"KOKORO_POSTGRES_URL": DATABASE_URLS["storage"], "KOKORO_REDIS_URL": REDIS_URLS["storage"], "KOKORO_STORAGE_PORT": "8085", "KOKORO_STORAGE_BFF_SERVICE_TOKEN": INTERNAL_SECRET, "KOKORO_OBJECT_STORE_DRIVER": "local", "KOKORO_OBJECT_STORE_ROOT_DIR": str(log_dir / "objects")}),
        ("capability", ROOT / "kokoro-capability", ["npm", "run", "dev"], {"KOKORO_POSTGRES_URL": DATABASE_URLS["capability"], "KOKORO_REDIS_URL": REDIS_URLS["capability"], "KOKORO_CAPABILITY_PORT": "8086", "KOKORO_CAPABILITY_BFF_SERVICE_TOKEN": INTERNAL_SECRET, "KOKORO_STORAGE_URL": "http://127.0.0.1:8085"}),
        ("bff-live", ROOT / "kokoro-bff", ["pnpm", "start"], {"KOKORO_BFF_HOST": "127.0.0.1", "KOKORO_BFF_PORT": "4300", "KOKORO_BFF_MODE": "live", "KOKORO_DOMAIN": "dev.kokoro.localhost", "KOKORO_BFF_SHARED_SECRET": INTERNAL_SECRET, "KOKORO_INTERNAL_SECRET_BFF": INTERNAL_SECRET, "KOKORO_BFF_POSTGRES_URL": DATABASE_URLS["bff"], "KOKORO_BFF_REDIS_URL": REDIS_URLS["bff"], "KOKORO_IAM_BASE_URL": "http://127.0.0.1:4211", "KOKORO_IAM_SERVICE_TOKEN": INTERNAL_SECRET, "KOKORO_SYSTEM_BASE_URL": "http://127.0.0.1:4240", "KOKORO_MODEL_BASE_URL": "http://127.0.0.1:4221", "KOKORO_CAPABILITY_BASE_URL": "http://127.0.0.1:8086", "KOKORO_STORAGE_BASE_URL": "http://127.0.0.1:8085", "KOKORO_SCHEDULER_BASE_URL": "http://127.0.0.1:4252", "KOKORO_SCHEDULER_SERVICE_TOKEN": INTERNAL_SECRET, "KOKORO_SCHEDULER_TARGET_URL": "http://127.0.0.1:4300/internal/bff/scheduled-tasks/dispatch", "KOKORO_AGENT_BASE_URL": "http://127.0.0.1:4401", "KOKORO_BILLING_BASE_URL": "http://127.0.0.1:4245"}),
        ("web", ROOT / "kokoro", ["pnpm", "dev"], {"PORT": "3000", "KOKORO_DOMAIN": "dev.kokoro.localhost", "KOKORO_BFF_BASE_URL": "http://127.0.0.1:4300", "KOKORO_INTERNAL_SECRET_WEB_BFF": INTERNAL_SECRET, "NEXT_PUBLIC_SESSION_PREVIEW": "1", "NEXT_TELEMETRY_DISABLED": "1"}),
        ("agent", ROOT / "kokoro-agent", ["uv", "run", "kokoro-agent-worker"], {"KOKORO_AGENT_DATABASE_URL": DATABASE_URLS["agent"], "KOKORO_REDIS_URL": REDIS_URLS["agent"], "KOKORO_AGENT_DATABASE_SCHEMA": "kokoro_agent_stage2", "KOKORO_DISABLE_STREAMING": "1"}),
        ("agent-http", ROOT / "kokoro-agent", ["uv", "run", "kokoro-agent-http"], {"KOKORO_AGENT_DATABASE_URL": DATABASE_URLS["agent"], "KOKORO_REDIS_URL": REDIS_URLS["agent"], "KOKORO_AGENT_DATABASE_SCHEMA": "kokoro_agent_stage2", "KOKORO_AGENT_HTTP_HOST": "127.0.0.1", "KOKORO_AGENT_HTTP_PORT": "4401", "KOKORO_INTERNAL_SECRET_AGENT": INTERNAL_SECRET, "KOKORO_DISABLE_STREAMING": "1"}),
        ("scheduler", ROOT / "kokoro-scheduler", ["go", "run", "./cmd/scheduler"], {"SCHEDULER_JOBS_JSON": "[]", "SCHEDULER_REDIS_URL": REDIS_URLS["scheduler"], "SCHEDULER_HTTP_ADDR": "127.0.0.1:4252", "SCHEDULER_INTERNAL_SERVICE_TOKEN": INTERNAL_SECRET, "SCHEDULER_TARGET_SERVICE_TOKEN": INTERNAL_SECRET}),
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
        # The worker and HTTP ingress share the Agent-owned PostgreSQL schema.
        # Start the worker's schema bootstrap before the HTTP process so their
        # CREATE TYPE statements cannot race on a fresh disposable database.
        if name == "agent":
            time.sleep(3)
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


def snapshot_web_next_env() -> bytes | None:
    """Capture the tracked Next type shim before starting the dev server."""
    try:
        return WEB_NEXT_ENV.read_bytes()
    except OSError:
        return None


def restore_web_next_env(original: bytes | None) -> None:
    """Undo only the deterministic Next dev rewrite caused by this smoke run.

    Do not overwrite an unrelated user edit: restoration is limited to the
    exact `.next/types` -> `.next/dev/types` mutation emitted by Next.js.
    """
    if original is None:
        return
    generated = original.replace(
        b'import "./.next/types/routes.d.ts";',
        b'import "./.next/dev/types/routes.d.ts";',
    )
    try:
        if WEB_NEXT_ENV.read_bytes() == generated and generated != original:
            WEB_NEXT_ENV.write_bytes(original)
    except OSError:
        pass


def http_get(url: str) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        headers={
            "x-kokoro-tenant-id": TENANT_ID,
            "x-kokoro-actor-id": ACTOR_ID,
            "x-kokoro-service": "kokoro-bff",
            "x-kokoro-internal-secret": INTERNAL_SECRET,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, response.read(400).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read(400).decode("utf-8", errors="replace")


def http_json(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], Any]:
    request_headers = {
        "accept": "application/json",
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": INTERNAL_SECRET,
        "x-kokoro-namespace": TENANT_ID,
        "x-kokoro-principal-id": ACTOR_ID,
        "x-kokoro-request-id": f"stage2-live-{int(time.time() * 1000)}",
    }
    if headers:
        request_headers.update(headers)
    encoded = None
    if body is not None:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        request_headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=encoded, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return response.status, dict(response.headers.items()), json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            payload: Any = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        return error.code, dict(error.headers.items()), payload


def assert_live_case(
    cases: list[dict[str, Any]],
    case_id: str,
    status: int,
    expected_status: int,
    predicate: bool,
    detail: str,
) -> None:
    passed = status == expected_status and predicate
    cases.append({"id": case_id, "status": status, "expected_status": expected_status, "passed": passed, "detail": detail})
    if not passed:
        raise CheckError(f"{case_id} failed: status={status} expected={expected_status}; {detail}")


def envelope_data(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise CheckError(f"expected v1 data envelope, got {payload!r}")
    return payload["data"]


def run_live_business_flow() -> list[dict[str, Any]]:
    """Exercise the configured real owner processes through the live BFF."""
    base = "http://127.0.0.1:4300"
    cases: list[dict[str, Any]] = []
    status, _, payload = http_json(f"{base}/v1/system/runtime-manifest?product_id=kokoro&locale=en-US&surface_id=user-web", headers={
        "x-kokoro-namespace": "",
        "x-kokoro-principal-id": "",
        "x-kokoro-request-id": "stage2-live-system-iam",
    })
    data = envelope_data(payload) if isinstance(payload, dict) and isinstance(payload.get("data"), dict) else {}
    assert_live_case(cases, "LIVE-001", status, 200, data.get("productId", data.get("product_id")) == "kokoro", "System manifest is reached via BFF and IAM-derived tenant context")

    for case_id, path, field in (
        ("LIVE-002", "/v1/models", "models"),
        ("LIVE-003", "/v1/skills/catalog", "skills"),
        ("LIVE-004", "/v1/library", "items"),
        ("LIVE-005", "/v1/billing/plans", "plans"),
        ("LIVE-006", "/v1/projects", "projects"),
    ):
        status, _, payload = http_json(f"{base}{path}", headers={"x-kokoro-request-id": case_id.lower()})
        data = envelope_data(payload) if isinstance(payload, dict) and isinstance(payload.get("data"), dict) else {}
        assert_live_case(cases, case_id, status, 200, field in data, f"BFF owner adapter returned {field} from {path}")

    message_status, _, message = http_json(
        f"{base}/v1/sessions/live-session/messages",
        method="POST",
        body={"content": "Stage 2 live Agent admission"},
        headers={"idempotency-key": "stage2-live-message", "x-kokoro-request-id": "stage2-live-agent"},
    )
    message_data = envelope_data(message) if isinstance(message, dict) and isinstance(message.get("data"), dict) else {}
    assert_live_case(cases, "LIVE-007", message_status, 202, isinstance(message_data.get("run_id"), str), "BFF Chat adapter admitted a Run through Agent HTTP ingress")

    schedule_status, _, schedule = http_json(
        f"{base}/v1/scheduled-tasks",
        method="POST",
        body={"title": "Stage 2 live schedule", "prompt": "Run the live closure", "frequency": "daily", "time": "10:00", "timezone": "UTC", "auto_approve": False, "next_run_at": "2026-09-01T10:00:00.000Z"},
        headers={"idempotency-key": "stage2-live-schedule-create", "x-kokoro-request-id": "stage2-live-schedule-create"},
    )
    schedule_data = envelope_data(schedule) if isinstance(schedule, dict) and isinstance(schedule.get("data"), dict) else {}
    task = schedule_data.get("task") if isinstance(schedule_data.get("task"), dict) else {}
    task_id = task.get("id")
    assert_live_case(cases, "LIVE-008", schedule_status, 200, isinstance(task_id, str), "BFF persisted ScheduledTask and registered Scheduler ScheduleJob")

    job_name = f"kokoro.scheduled.{task_id}"
    occurrence = "20260901T120000Z"
    dispatch_status, _, dispatch = http_json(
        f"{base}/internal/bff/scheduled-tasks/dispatch",
        method="POST",
        body={"tenant_id": TENANT_ID, "task_id": task_id, "owner_id": ACTOR_ID, "prompt": task.get("prompt"), "auto_approve": task.get("auto_approve"), "timezone": task.get("timezone")},
        headers={
            "authorization": f"Bearer {INTERNAL_SECRET}",
            "x-kokoro-service": "scheduler",
            "x-kokoro-internal-secret": INTERNAL_SECRET,
            "x-kokoro-scheduler-job": job_name,
            "x-kokoro-scheduler-occurrence": occurrence,
            "x-request-id": "stage2-live-scheduler-dispatch",
            "idempotency-key": f"schedule:{job_name}:{occurrence}",
        },
    )
    dispatch_data = envelope_data(dispatch) if isinstance(dispatch, dict) and isinstance(dispatch.get("data"), dict) else {}
    assert_live_case(cases, "LIVE-009", dispatch_status, 202, isinstance(dispatch_data.get("run_id"), str), "Scheduler command was accepted by BFF and launched Agent")
    replay_status, _, replay = http_json(
        f"{base}/internal/bff/scheduled-tasks/dispatch",
        method="POST",
        body={"tenant_id": TENANT_ID, "task_id": task_id, "owner_id": ACTOR_ID, "prompt": task.get("prompt"), "auto_approve": task.get("auto_approve"), "timezone": task.get("timezone")},
        headers={
            "authorization": f"Bearer {INTERNAL_SECRET}",
            "x-kokoro-service": "scheduler",
            "x-kokoro-internal-secret": INTERNAL_SECRET,
            "x-kokoro-scheduler-job": job_name,
            "x-kokoro-scheduler-occurrence": occurrence,
            "x-request-id": "stage2-live-scheduler-replay",
            "idempotency-key": f"schedule:{job_name}:{occurrence}",
        },
    )
    assert_live_case(cases, "LIVE-010", replay_status, 202, replay == dispatch, "Scheduler occurrence replay returned the durable BFF receipt without a duplicate Agent run")

    delete_status, _, _ = http_json(
        f"{base}/v1/scheduled-tasks/{task_id}",
        method="DELETE",
        headers={"idempotency-key": "stage2-live-schedule-delete", "x-kokoro-request-id": "stage2-live-schedule-delete"},
    )
    assert_live_case(cases, "LIVE-011", delete_status, 200, True, "BFF removed the business fact after Scheduler unregister succeeded")
    return cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=ROOT / "docs/reports/2026-09-01-stage2-owner-health.json")
    parser.add_argument("--keep-infra", action="store_true", help="leave disposable PostgreSQL/Redis containers running")
    args = parser.parse_args(argv)
    evidence: dict[str, Any] = {"mode": "disposable-owner-health", "checks": [], "processes": [], "status": "FAIL"}
    processes: list[tuple[str, subprocess.Popen[str]]] = []
    log_dir = Path("/tmp/kokoro-stage2-owner-health")
    original_web_next_env = snapshot_web_next_env()
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
            "agent_http_health": "http://127.0.0.1:4401/healthz",
            "agent_http_ready": "http://127.0.0.1:4401/readyz",
            "scheduler_health": "http://127.0.0.1:4252/healthz",
            "scheduler_ready": "http://127.0.0.1:4252/readyz",
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
        if all(item.get("ok") for item in evidence["checks"]):
            evidence["live_business"] = run_live_business_flow()
        if all(item.get("ok") for item in evidence["checks"]) and all(item["running"] for item in evidence["processes"]):
            evidence["status"] = "PASS"
    except Exception as error:
        evidence["error"] = str(error)
    finally:
        stop_processes(processes)
        if not args.keep_infra:
            stop_infra()
        restore_web_next_env(original_web_next_env)
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

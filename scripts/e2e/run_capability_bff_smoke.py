#!/usr/bin/env python3
"""Run the isolated real-process Capability-to-BFF acceptance smoke."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import dataclass
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
from typing import BinaryIO
from urllib.parse import urlencode

if __package__:
    from . import capability_bff_smoke_runtime as runtime
    from .bff_iam_admission_stub import AdmissionIdentity, iam_admission_stub
else:
    import capability_bff_smoke_runtime as runtime
    from bff_iam_admission_stub import AdmissionIdentity, iam_admission_stub

ROOT = Path(__file__).resolve().parents[2]
BFF = ROOT / "apps" / "kokoro-bff"
CAPABILITY = ROOT / "apps" / "kokoro-capability"
BFF_RELEASE = "804a5832c066ce60dde9f4592856ac40ce20f402"
CAPABILITY_RELEASE = "9c88d0d934387b590bc74dae0179a587292e0253"


def owner_request_count(
    log_path: Path,
    request_id: str | None = None,
    operation: str | None = None,
) -> int:
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return 0
    total = 0
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("event") != "request.completed":
            continue
        event_operation = event.get("operation")
        if not isinstance(event_operation, str) or not event_operation.startswith(
            "GET /v1/"
        ):
            continue
        if request_id is not None and event.get("trace_id") != request_id:
            continue
        if operation is not None and event_operation != operation:
            continue
        total += 1
    return total


def wait_for_owner_request(log_path: Path, request_id: str, operation: str) -> None:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if owner_request_count(log_path, request_id, operation) == 1:
            return
        time.sleep(0.02)
    raise runtime.SmokeError("Capability owner request evidence was not observed")


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise runtime.SmokeError(detail)


def error_code(body: dict[str, object]) -> str | None:
    error = body.get("error")
    return error.get("code") if isinstance(error, dict) else None


def assert_success_envelope(body: dict[str, object]) -> None:
    require(set(body) == {"data", "meta"}, "BFF success envelope drift")
    require(isinstance(body.get("data"), dict), "BFF success data drift")
    require(isinstance(body.get("meta"), dict), "BFF success metadata drift")


def bff_headers(
    web_token: str, tenant: str, subject: str, request_id: str, session_token: str
) -> dict[str, str]:
    return {
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": web_token,
        "x-kokoro-request-id": request_id,
        "authorization": "Bearer " + session_token,
    }


def verify_good_bff_cases(
    bff_base: str,
    web_token: str,
    tenant: str,
    subject: str,
    session_token: str,
    run_id: str,
    capability_log: Path,
) -> list[str]:
    cases: list[str] = []
    query_marker = f"canonical-{run_id}"
    query_request_id = f"w0b-query-{run_id}"
    headers = bff_headers(web_token, tenant, subject, query_request_id, session_token)
    body, _ = runtime.http_json(
        bff_base,
        "/v1/skills?" + urlencode({"query": query_marker}),
        headers=headers,
    )
    assert_success_envelope(body)
    wait_for_owner_request(capability_log, query_request_id, "GET /v1/skills")
    cases.append("canonical_query_forwarded_to_owner")

    for name, path in (
        ("skill_pool", "/v1/skills/pool"),
        ("skill_catalog", "/v1/skills/catalog"),
        ("mcp_servers", "/v1/mcp/servers"),
    ):
        request_id = f"w0b-{name}-{run_id}"
        result, _ = runtime.http_json(
            bff_base,
            path,
            headers=bff_headers(web_token, tenant, subject, request_id, session_token),
        )
        assert_success_envelope(result)
        wait_for_owner_request(capability_log, request_id, f"GET {path}")
        cases.append(name)

    before = owner_request_count(capability_log)
    legacy, _ = runtime.http_json(
        bff_base,
        "/v1/skills?" + urlencode({"q": query_marker}),
        headers=bff_headers(
            web_token, tenant, subject, f"w0b-q-{run_id}", session_token
        ),
        expected=400,
    )
    require(error_code(legacy) == "invalid_query_parameter", "legacy q error drift")
    time.sleep(0.1)
    require(owner_request_count(capability_log) == before, "legacy q reached owner")
    cases.append("legacy_q_rejected_without_owner_io")

    missing_auth, _ = runtime.http_json(
        bff_base,
        "/v1/skills",
        headers={
            "x-kokoro-service": "web-bff",
            "authorization": "Bearer " + session_token,
        },
        expected=403,
    )
    require(error_code(missing_auth) == "service_auth_failed", "BFF auth error drift")
    cases.append("missing_bff_auth")

    invalid_cursor_id = f"w0b-invalid-cursor-{run_id}"
    invalid_cursor, _ = runtime.http_json(
        bff_base,
        "/v1/skills?" + urlencode({"cursor": "invalid"}),
        headers=bff_headers(
            web_token, tenant, subject, invalid_cursor_id, session_token
        ),
        expected=400,
    )
    require(
        error_code(invalid_cursor) == "invalid_query_parameter",
        "invalid cursor error drift",
    )
    wait_for_owner_request(capability_log, invalid_cursor_id, "GET /v1/skills")
    cases.append("invalid_cursor")
    return cases


def verify_bad_owner_token_case(
    bff_base: str,
    web_token: str,
    tenant: str,
    subject: str,
    session_token: str,
    run_id: str,
    capability_log: Path,
) -> str:
    request_id = f"w0b-bad-owner-token-{run_id}"
    body, _ = runtime.http_json(
        bff_base,
        "/v1/skills",
        headers=bff_headers(web_token, tenant, subject, request_id, session_token),
        expected=503,
    )
    require(error_code(body) == "capability_unavailable", "owner auth mapping drift")
    wait_for_owner_request(capability_log, request_id, "GET /v1/skills")
    return "bad_owner_token_mapped"


def success_summary(cases: list[str]) -> dict[str, object]:
    if len(cases) != 8 or len(set(cases)) != 8:
        raise runtime.SmokeError("Smoke must complete exactly eight distinct cases")
    return {
        "status": "PASS",
        "cases": 8,
        "case_names": cases,
        "bff_auth_missing_status": 403,
        "processes": "exact dist/main.js",
        "cleanup": {
            "postgres_databases": "removed",
            "redis_prefix": "empty",
            "process_groups": "absent",
            "temporary_logs": "removed",
        },
        "releases": {
            "kokoro-bff": BFF_RELEASE,
            "kokoro-capability": CAPABILITY_RELEASE,
        },
    }


def failure_summary(error: BaseException, sensitive: list[str]) -> dict[str, str]:
    if isinstance(error, runtime.SmokeError):
        detail = str(error)
        if detail and not any(secret and secret in detail for secret in sensitive):
            return {"status": "FAIL", "error": detail}
    return {"status": "FAIL", "error": "smoke execution failed"}


@dataclass(frozen=True)
class SmokeConfiguration:
    run_id: str
    tenant: str
    subject: str
    web_token: str
    session_token: str
    capability_base: str
    bff_base: str
    bad_bff_base: str
    capability_node: Path
    bff_node: Path
    capability_env: dict[str, str]
    good_bff_env: dict[str, str]
    bad_bff_env: dict[str, str]
    capability_log_path: Path
    capability_log: BinaryIO
    bff_log: BinaryIO
    bad_bff_log: BinaryIO


def _assert_dependencies(resources: runtime.OwnedResources) -> None:
    resources.command(
        [
            "psql",
            resources.postgres_admin_url,
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-Atc",
            "SELECT 1",
        ]
    )
    pong = resources.command(
        ["redis-cli", "-e", "-u", resources.redis_url, "PING"]
    ).strip()
    require(pong == "PONG", "Shared Redis unavailable")


def _capability_environment(
    base: dict[str, str],
    database_url: str,
    redis_url: str,
    port: int,
    dependency_base: str,
    rpc_token: str,
    owner_token: str,
) -> dict[str, str]:
    return {
        **base,
        "KOKORO_POSTGRES_URL": database_url,
        "KOKORO_REDIS_URL": redis_url,
        "KOKORO_CAPABILITY_HOST": "127.0.0.1",
        "KOKORO_CAPABILITY_PORT": str(port),
        "KOKORO_CAPABILITY_SERVICE_TOKEN": rpc_token,
        "KOKORO_CAPABILITY_BFF_SERVICE_TOKEN": owner_token,
        "KOKORO_CAPABILITY_SURFACES": "skill-catalog,skill-source,mcp-server",
        "KOKORO_STORAGE_URL": dependency_base,
        "KOKORO_IAM_ATTESTATION_VERIFIER_URL": (
            dependency_base + "/iam/attestation/verify"
        ),
        "KOKORO_MCP_CONNECTOR_PROVIDER_CATALOG_JSON": "[]",
        "KOKORO_CAPABILITY_READINESS_TIMEOUT_MS": "5000",
        "KOKORO_STORAGE_READINESS_TIMEOUT_MS": "5000",
        "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
    }


def _bff_environments(
    base: dict[str, str],
    database_url: str,
    redis_url: str,
    capability_base: str,
    run_id: str,
    tenant: str,
    web_token: str,
    iam_base: str,
    owner_token: str,
    wrong_owner_token: str,
    bff_port: int,
    bad_bff_port: int,
) -> tuple[dict[str, str], dict[str, str]]:
    common = {
        **base,
        "KOKORO_BFF_POSTGRES_URL": database_url,
        "KOKORO_BFF_REDIS_URL": redis_url,
        "KOKORO_BFF_HOST": "127.0.0.1",
        "KOKORO_BFF_MODE": "live",
        "KOKORO_BFF_SHARED_SECRET": web_token,
        "KOKORO_IAM_BASE_URL": iam_base,
        "KOKORO_CAPABILITY_BASE_URL": capability_base,
        "KOKORO_AGENT_ENABLED": "false",
        "KOKORO_TENANT_ID": tenant,
        "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
        "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
    }
    good = {
        **common,
        "KOKORO_BFF_PORT": str(bff_port),
        "KOKORO_INTERNAL_SECRET_BFF": owner_token,
    }
    bad = {
        **common,
        "KOKORO_BFF_PORT": str(bad_bff_port),
        "KOKORO_INTERNAL_SECRET_BFF": wrong_owner_token,
    }
    return good, bad


def _provision_configuration(
    args: argparse.Namespace,
    resources: runtime.OwnedResources,
    dependency_base: str,
    iam_base: str,
    session_token: str,
    temporary: str,
    files: ExitStack,
    bff_toolchain: tuple[Path, dict[str, str]],
    capability_toolchain: tuple[Path, dict[str, str]],
) -> SmokeConfiguration:
    _assert_dependencies(resources)
    resources.claim_redis_prefix()
    capability_database_url = resources.create_database("capability")
    bff_database_url = resources.create_database("bff")
    run_id = resources.run_id
    tenant = f"tenant-{run_id}"
    owner_token = secrets.token_hex(32)
    web_token = secrets.token_hex(32)
    capability_port, bff_port, bad_bff_port = runtime.distinct_ports(3)
    capability_base = f"http://127.0.0.1:{capability_port}"
    capability_node, capability_base_env = capability_toolchain
    bff_node, bff_base_env = bff_toolchain
    capability_env = _capability_environment(
        capability_base_env,
        capability_database_url,
        args.redis_url,
        capability_port,
        dependency_base,
        secrets.token_hex(32),
        owner_token,
    )
    good_bff_env, bad_bff_env = _bff_environments(
        bff_base_env,
        bff_database_url,
        args.redis_url,
        capability_base,
        run_id,
        tenant,
        web_token,
        iam_base,
        owner_token,
        secrets.token_hex(32),
        bff_port,
        bad_bff_port,
    )
    temporary_path = Path(temporary)
    capability_log_path = temporary_path / "kokoro-capability.log"
    return SmokeConfiguration(
        run_id=run_id,
        tenant=tenant,
        subject=f"subject-{run_id}",
        web_token=web_token,
        session_token=session_token,
        capability_base=capability_base,
        bff_base=f"http://127.0.0.1:{bff_port}",
        bad_bff_base=f"http://127.0.0.1:{bad_bff_port}",
        capability_node=capability_node,
        bff_node=bff_node,
        capability_env=capability_env,
        good_bff_env=good_bff_env,
        bad_bff_env=bad_bff_env,
        capability_log_path=capability_log_path,
        capability_log=files.enter_context(capability_log_path.open("wb")),
        bff_log=files.enter_context((temporary_path / "kokoro-bff.log").open("wb")),
        bad_bff_log=files.enter_context(
            (temporary_path / "kokoro-bff-bad-owner-token.log").open("wb")
        ),
    )


def _install_schemas(args: argparse.Namespace, config: SmokeConfiguration) -> None:
    runtime.install_schema(
        "kokoro-capability",
        CAPABILITY,
        args.capability_node_bin,
        config.capability_env,
        config.capability_log,
    )
    runtime.install_schema(
        "kokoro-bff",
        BFF,
        args.bff_node_bin,
        config.good_bff_env,
        config.bff_log,
    )


def _exercise_cases(
    config: SmokeConfiguration,
    processes: list[subprocess.Popen[bytes]],
    fault_injection: Callable[[str], None] | None,
) -> list[str]:
    capability_process = runtime.start_process(
        config.capability_node, CAPABILITY, config.capability_env, config.capability_log
    )
    processes.append(capability_process)
    runtime.wait_ready(config.capability_base, capability_process)
    bff_process = runtime.start_process(
        config.bff_node, BFF, config.good_bff_env, config.bff_log
    )
    processes.append(bff_process)
    runtime.wait_ready(config.bff_base, bff_process)
    if fault_injection is not None:
        fault_injection("after-processes-started")
    cases = verify_good_bff_cases(
        config.bff_base,
        config.web_token,
        config.tenant,
        config.subject,
        config.session_token,
        config.run_id,
        config.capability_log_path,
    )
    runtime.stop_owned_process(bff_process)
    processes.remove(bff_process)
    bad_bff_process = runtime.start_process(
        config.bff_node, BFF, config.bad_bff_env, config.bad_bff_log
    )
    processes.append(bad_bff_process)
    runtime.wait_ready(config.bad_bff_base, bad_bff_process)
    cases.append(
        verify_bad_owner_token_case(
            config.bad_bff_base,
            config.web_token,
            config.tenant,
            config.subject,
            config.session_token,
            config.run_id,
            config.capability_log_path,
        )
    )
    return cases


def _cleanup(
    resources: runtime.OwnedResources,
    processes: list[subprocess.Popen[bytes]],
) -> None:
    failures: list[str] = []
    for process in reversed(processes):
        try:
            runtime.stop_owned_process(process)
        except (runtime.SmokeError, OSError):
            failures.append("owned process shutdown failed")
    try:
        resources.cleanup()
    except runtime.SmokeError:
        failures.append("owned infrastructure cleanup failed")
    if not failures:
        try:
            resources.verify_clean()
        except runtime.SmokeError:
            failures.append("owned resource residue detected")
    if failures:
        raise runtime.SmokeError("; ".join(failures))


def _run_with_fixtures(
    args: argparse.Namespace,
    resources: runtime.OwnedResources,
    bff_toolchain: tuple[Path, dict[str, str]],
    capability_toolchain: tuple[Path, dict[str, str]],
    fault_injection: Callable[[str], None] | None,
) -> list[str]:
    processes: list[subprocess.Popen[bytes]] = []
    session_token = secrets.token_urlsafe(32)
    with (
        tempfile.TemporaryDirectory(prefix="kokoro-w0b-capability-") as temporary,
        ExitStack() as files,
        runtime.dependency_readiness_fixture() as dependency_base,
        iam_admission_stub(
            {
                session_token: AdmissionIdentity(
                    tenant_id=f"tenant-{resources.run_id}",
                    user_id=f"subject-{resources.run_id}",
                    session_id=f"session-{resources.run_id}",
                    client_id="w0b-capability-smoke",
                )
            }
        ) as iam_base,
    ):
        try:
            config = _provision_configuration(
                args,
                resources,
                dependency_base,
                iam_base,
                session_token,
                temporary,
                files,
                bff_toolchain,
                capability_toolchain,
            )
            _install_schemas(args, config)
            return _exercise_cases(config, processes, fault_injection)
        finally:
            _cleanup(resources, processes)


def run_smoke(
    args: argparse.Namespace,
    *,
    fault_injection: Callable[[str], None] | None = None,
) -> int:
    runtime.verify_release(BFF, BFF_RELEASE)
    runtime.verify_release(CAPABILITY, CAPABILITY_RELEASE)
    bff_toolchain = runtime.node_environment(args.bff_node_bin, "v22.22.2")
    capability_toolchain = runtime.node_environment(
        args.capability_node_bin, "v24.20.0"
    )
    run_id = secrets.token_hex(12)
    resources = runtime.OwnedResources(args.postgres_admin_url, args.redis_url, run_id)
    cases = _run_with_fixtures(
        args, resources, bff_toolchain, capability_toolchain, fault_injection
    )
    print(json.dumps(success_summary(cases), ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--postgres-admin-url", required=True)
    result.add_argument("--redis-url", required=True)
    result.add_argument("--bff-node-bin", required=True)
    result.add_argument("--capability-node-bin", required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    sensitive = [args.postgres_admin_url, args.redis_url]
    try:
        return run_smoke(args)
    except Exception as error:
        print(
            json.dumps(failure_summary(error, sensitive), ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

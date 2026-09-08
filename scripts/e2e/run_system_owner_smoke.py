#!/usr/bin/env python3
"""Run System HTTP and consumer smoke with exclusively owned temporary data."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import json
from hashlib import sha256
import os
from pathlib import Path
import re
import secrets
import signal
import socket
import subprocess
import tempfile
import time
from typing import BinaryIO
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]


class SmokeError(RuntimeError):
    """A sanitized, actionable smoke failure; never include credentials."""


def command_output(command: list[str]) -> str:
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=30, check=False
    )
    if result.returncode:
        raise SmokeError(
            f"{Path(command[0]).name} command failed (exit {result.returncode})"
        )
    return result.stdout


class OwnedResources:
    """Only register a database after CREATE succeeds; never reset shared data."""

    def __init__(
        self,
        postgres: str,
        redis: str,
        run_id: str,
        *,
        command: Callable[[list[str]], str] = command_output,
    ) -> None:
        if re.fullmatch(r"[a-f0-9]{24}", run_id) is None:
            raise SmokeError("Invalid smoke run identity")
        if urlsplit(postgres).scheme not in {"postgres", "postgresql"} or urlsplit(
            redis
        ).scheme not in {"redis", "rediss"}:
            raise SmokeError("Explicit PostgreSQL and Redis endpoints required")
        self.postgres = postgres
        self.redis = redis
        self.run_id = run_id
        self.namespace = f"kokoro:system-smoke:{run_id}"
        self.created_databases: list[str] = []
        self.command = command

    def create_database(self, owner: str) -> str:
        if owner not in {"system", "bff"}:
            raise SmokeError("Invalid smoke database owner")
        name = f"system_smoke_{self.run_id}_{owner}"
        if name in self.created_databases:
            raise SmokeError("Database already created by this run")
        self.command(
            [
                "psql",
                self.postgres,
                "-X",
                "-v",
                "ON_ERROR_STOP=1",
                "-Atc",
                f'CREATE DATABASE "{name}"',
            ]
        )
        self.created_databases.append(name)
        parts = urlsplit(self.postgres)
        return urlunsplit((parts.scheme, parts.netloc, f"/{name}", parts.query, ""))

    def cleanup(self) -> None:
        failures: list[str] = []
        try:
            prefix = f"{self.namespace}:"
            keys = self.command(
                [
                    "redis-cli",
                    "-e",
                    "-u",
                    self.redis,
                    "--scan",
                    "--pattern",
                    f"{prefix}*",
                ]
            ).splitlines()
            if any(not key.startswith(prefix) for key in keys):
                raise SmokeError("Redis scan returned a key outside this run")
            for start in range(0, len(keys), 100):
                self.command(
                    [
                        "redis-cli",
                        "-e",
                        "-u",
                        self.redis,
                        "UNLINK",
                        *keys[start : start + 100],
                    ]
                )
        except (SmokeError, subprocess.SubprocessError, OSError):
            failures.append("owned Redis cleanup failed")
        for name in reversed(self.created_databases.copy()):
            try:
                self.command(
                    [
                        "psql",
                        self.postgres,
                        "-X",
                        "-v",
                        "ON_ERROR_STOP=1",
                        "-Atc",
                        f'DROP DATABASE "{name}" WITH (FORCE)',
                    ]
                )
                self.created_databases.remove(name)
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("owned PostgreSQL cleanup failed")
        if failures:
            raise SmokeError("; ".join(failures))


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_: object) -> None:
        return None


def http_json(
    base: str,
    path: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: object = None,
    expected: int = 200,
) -> dict[str, object]:
    request = Request(
        base + path,
        method=method,
        headers={"content-type": "application/json", **(headers or {})},
        data=None if body is None else json.dumps(body).encode(),
    )
    try:
        response = build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=8)
    except HTTPError as error:
        response = error
    with response:
        if response.status != expected:
            raise SmokeError(
                f"{method} {path.split('?')[0]} returned {response.status}, expected {expected}"
            )
        raw = response.read(1_048_577)
    if len(raw) > 1_048_576:
        raise SmokeError("HTTP response exceeded smoke limit")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SmokeError("HTTP object response required")
    return value


def wait_ready(base: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise SmokeError("Owned source process exited before readiness")
        try:
            http_json(base, "/readyz")
            return
        except (SmokeError, URLError, TimeoutError):
            time.sleep(0.2)
    raise SmokeError("Owned source process did not become ready in 30s")


def process_group_exists(pgid: int) -> bool:
    # Confirm disappearance with an inventory; EPERM alone is not evidence of
    # termination, and signalling can race with the last child exiting.
    try:
        result = subprocess.run(
            ["ps", "-axo", "pgid="],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        raise SmokeError("Owned process inventory failed") from None
    return str(pgid) in result.stdout.split()


def stop_owned_process(process: subprocess.Popen[bytes]) -> None:
    # Pnpm/tsx leaders can exit before their children. Track the owned group,
    # not merely the original Popen handle, and reap the leader while waiting.
    for sig, seconds in [(signal.SIGTERM, 15), (signal.SIGKILL, 5)]:
        process.poll()
        if not process_group_exists(process.pid):
            return
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            process.poll()
            return
        except PermissionError:
            if not process_group_exists(process.pid):
                return
            raise SmokeError("Owned process group termination was denied") from None
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            process.poll()
            if not process_group_exists(process.pid):
                if sig == signal.SIGKILL:
                    raise SmokeError(
                        "Owned process exceeded graceful shutdown deadline"
                    )
                return
            time.sleep(0.05)
    raise SmokeError("Owned process group still exists after forced cleanup")


def run_owned_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    log: BinaryIO,
    timeout: float = 30,
) -> int:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SmokeError("Owned command exceeded its deadline") from None
    finally:
        stop_owned_process(process)


def node_environment(directory: str, major: int) -> dict[str, str]:
    env = dict(os.environ)
    if directory:
        env["PATH"] = directory + os.pathsep + env["PATH"]
    version = subprocess.run(
        ["node", "--version"], env=env, capture_output=True, text=True, check=True
    ).stdout.strip()
    if not version.startswith(f"v{major}."):
        raise SmokeError(f"Node {major} required for this owner; use --node{major}-bin")
    return env


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SmokeError(detail)


def data_of(envelope: dict[str, object]) -> dict[str, object]:
    data = envelope.get("data")
    if not isinstance(data, dict):
        raise SmokeError("Expected owner data object")
    return data


def seed_control_plane(
    base: str, tenant: str, token: str, run_id: str
) -> dict[str, str]:
    """Seed through the authoritative HTTP API, never through business table SQL."""

    def mutate(
        path: str,
        body: object = None,
        *,
        method: str = "POST",
        global_scope: bool = False,
        version: object = None,
        create: bool = False,
    ) -> dict[str, object]:
        headers = {
            "authorization": f"Bearer {token}",
            "x-kokoro-service": "system-admin",
            "x-kokoro-actor-id": "smoke-operator",
            "x-kokoro-iam-permissions": "system:read,system:write,system:publish",
            "idempotency-key": secrets.token_hex(16),
            "x-request-id": secrets.token_hex(16),
        }
        if not global_scope:
            headers["x-kokoro-tenant-id"] = tenant
        if version is not None:
            headers["if-match"] = f'"{version}"'
        if create:
            headers["if-none-match"] = "*"
        expected = (
            200
            if method in {"GET", "PUT"} or path.endswith(("/publish", "/validate"))
            else 201
        )
        result = http_json(
            base,
            "/v1/system/" + path,
            method=method,
            headers=headers,
            body=body,
            expected=expected,
        )
        require(set(result) == {"data"}, "System success envelope drift")
        return data_of(result)

    product_key = f"smoke-{run_id}"
    feature_key = f"chat.{run_id}"
    hostname = f"{run_id}.smoke.localhost"
    product = mutate(
        "products",
        {"product_key": product_key, "name": "Smoke product"},
        global_scope=True,
    )
    site = mutate(
        "sites",
        {"site_key": "smoke", "hostname": hostname, "display_name": "Smoke site"},
    )
    mutate(
        f"sites/{site['id']}/policy",
        {
            "default_locale": "en-US",
            "allowed_locales": ["en-US"],
            "allowed_products": [product_key],
            "public_manifest": True,
        },
        method="PUT",
        create=True,
    )
    feature = mutate(
        "features",
        {
            "global_feature_key": feature_key,
            "product_id": product["id"],
            "display_name": "Smoke chat",
            "result_contract": {
                "schema_version": 1,
                "outcome_kind": "message",
                "media_types": ["text/plain"],
                "required_fields": ["content"],
            },
        },
        global_scope=True,
    )
    application = mutate(
        "applications",
        {
            "site_id": site["id"],
            "product_id": product["id"],
            "app_key": "web",
            "display_name": "Smoke web",
        },
    )
    mutate(
        f"applications/{application['id']}/exposures/{feature['id']}",
        {"enabled": True, "display_order": 0},
        method="PUT",
        create=True,
    )
    mutate(
        f"applications/{application['id']}/presentation?locale=en-US&surface_id=user-web",
        {
            "schema_version": 1,
            "navigation": [
                {
                    "key": "chat",
                    "label": "Chat",
                    "href": "/chat",
                    "feature_key": feature_key,
                }
            ],
            "theme": {
                "mode": "system",
                "accent_color": "#3366FF",
                "logo_asset_id": None,
            },
            "locale_namespaces": [
                {"namespace": "common", "messages": {"title": "Smoke"}}
            ],
        },
        method="PUT",
        create=True,
    )
    for module, value in [
        ("feature_flags", [{"key": feature_key, "enabled": True}]),
        (
            "references",
            [
                {
                    "key": "artifact_store",
                    "owner": "storage",
                    "resource_id": f"smoke-{run_id}",
                }
            ],
        ),
    ]:
        mutate(
            "config",
            {
                "config_key": module,
                "scope_type": "product",
                "scope_id": product["id"],
                "product_id": product["id"],
                "site_id": None,
                "locale": None,
                "schema_version": 1,
                "release_id": None,
                "module_key": module,
                "value": value,
            },
        )
    # Draft digest is not release evidence. The owner validate operation below
    # computes the canonical content digest before publication is permitted.
    release = mutate(
        "releases",
        {
            "release_key": f"smoke-{run_id}",
            "digest": sha256(b"smoke draft").hexdigest(),
        },
    )
    mutate(
        "config",
        {
            "config_key": "references",
            "scope_type": "product",
            "scope_id": product["id"],
            "product_id": product["id"],
            "site_id": None,
            "locale": None,
            "schema_version": 1,
            "release_id": release["id"],
            "module_key": "references",
            "value": [
                {
                    "key": "artifact_store",
                    "owner": "storage",
                    "resource_id": f"published-{run_id}",
                }
            ],
        },
    )
    release_snapshot = mutate(f"releases/{release['id']}", method="GET")
    validated = mutate(
        f"releases/{release['id']}/validate", version=release_snapshot["version"]
    )
    mutate(f"releases/{release['id']}/publish", version=validated["version"])
    mutate(
        "release-bindings",
        {
            "scope_type": "product",
            "scope_id": product["id"],
            "site_id": None,
            "product_id": product["id"],
            "release_id": release["id"],
        },
    )
    provider = mutate(
        "model-catalog/providers",
        {
            "provider": "fixture",
            "provider_key": f"fixture-{run_id}",
            "display_name": "Smoke fixture provider",
            "secret_handle_ref": f"secret://smoke/{run_id}",
            "transport": "litellm",
            "priority": 0,
        },
        global_scope=True,
    )
    model = mutate(
        "model-catalog/definitions",
        {"model_key": f"fixture/{run_id}", "display_name": "Smoke model"},
        global_scope=True,
    )
    revision = mutate(
        "model-catalog/revisions",
        {
            "model_id": model["id"],
            "provider_id": provider["id"],
            "revision": 1,
            "provider_model_name": "smoke-model",
            "display_name": "Smoke model",
            "feature_key": feature_key,
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "transport": "litellm",
            "gateway_model_name": "smoke-model",
            "context_window": 8192,
            "priority": 0,
        },
        global_scope=True,
    )
    mutate(
        f"model-catalog/revisions/{revision['id']}/publish",
        global_scope=True,
        version=revision["version"],
    )
    label_key = f"default-{run_id}"
    label = mutate(
        "model-catalog/labels",
        {
            "label_key": label_key,
            "display_name": "Smoke default",
            "feature_key": feature_key,
            "default_revision_id": revision["id"],
        },
        global_scope=True,
    )
    mutate(
        f"model-catalog/providers/{provider['id']}/health",
        {
            "status": "healthy",
            "observed_at": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
        },
        method="PUT",
        global_scope=True,
        create=True,
    )
    mutate(
        f"model-catalog/routing-policies/{label['id']}",
        {
            "model_revision_id": revision["id"],
            "visible": True,
            "is_default": True,
            "priority": 0,
        },
        method="PUT",
        create=True,
    )
    return {
        "product_key": product_key,
        "site_id": str(site["id"]),
        "feature_key": feature_key,
        "revision_id": str(revision["id"]),
        "label_key": label_key,
        "hostname": hostname,
        "release_id": str(release["id"]),
        "published_reference": f"published-{run_id}",
    }


def verify_read_consumers(
    system: str,
    bff: str,
    tenant: str,
    values: dict[str, str],
    bff_token: str,
    web_token: str,
) -> None:
    owner_headers = {
        "authorization": f"Bearer {bff_token}",
        "x-kokoro-service": "web-bff",
        "x-kokoro-tenant-id": tenant,
        "forwarded": f"host={values['hostname']}",
    }
    catalog_query = urlencode({"feature_key": values["feature_key"], "limit": "20"})
    catalog = data_of(
        http_json(
            system,
            "/v1/system/model-catalog/catalog?" + catalog_query,
            headers=owner_headers,
        )
    )
    items = catalog.get("items")
    require(
        isinstance(items, list)
        and len(items) == 1
        and items[0].get("is_default") is True,
        "System catalog default missing",
    )
    web_headers = {
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": web_token,
        "x-kokoro-namespace": tenant,
        "x-kokoro-principal-id": "smoke-user",
    }
    models = data_of(http_json(bff, "/v1/models?" + catalog_query, headers=web_headers))
    public_models = models.get("models")
    require(
        isinstance(public_models, list)
        and len(public_models) == 1
        and public_models[0].get("name") == values["label_key"]
        and public_models[0].get("is_default") is True,
        "BFF model projection does not reflect System default",
    )
    query = urlencode(
        {
            "product_id": values["product_key"],
            "locale": "en-US",
            "surface_id": "user-web",
        }
    )
    manifest = data_of(
        http_json(system, "/v1/system/runtime-manifest?" + query, headers=owner_headers)
    )
    require(
        manifest.get("tenant_id") == tenant
        and manifest.get("site_id") == values["site_id"],
        "System manifest tenant/site mismatch",
    )
    require(
        manifest.get("release_id") == values["release_id"],
        "Published release binding was not selected",
    )
    require(
        manifest.get("references")
        == [
            {
                "key": "artifact_store",
                "owner": "storage",
                "resource_id": values["published_reference"],
            }
        ],
        "Published release configuration did not override ordinary configuration",
    )
    public_manifest = data_of(
        http_json(bff, "/v1/system/runtime-manifest?" + query, headers=web_headers)
    )
    for key in (
        "tenant_id",
        "product_id",
        "locale",
        "navigation",
        "theme",
        "locale_namespaces",
        "feature_flags",
        "references",
        "config_version",
        "release_id",
        "digest",
    ):
        require(
            public_manifest.get(key) == manifest.get(key),
            f"BFF manifest projection mismatch: {key}",
        )
    require(
        bool(manifest.get("navigation")) and bool(manifest.get("feature_flags")),
        "Manifest omitted seeded capabilities",
    )
    other = {**owner_headers, "x-kokoro-tenant-id": tenant + "-other"}
    for base, headers in (
        (system, other),
        (bff, {**web_headers, "x-kokoro-namespace": tenant + "-other"}),
    ):
        denied_manifest = http_json(
            base, "/v1/system/runtime-manifest?" + query, headers=headers, expected=404
        )
        require(
            data_of({"data": denied_manifest.get("error")}).get("code") == "NOT_FOUND",
            "Manifest crossed tenant boundary or returned an unexpected error",
        )
    empty = data_of(
        http_json(
            system, "/v1/system/model-catalog/catalog?" + catalog_query, headers=other
        )
    )
    require(empty.get("items") == [], "Catalog crossed tenant boundary")
    denied = http_json(
        system,
        "/v1/system/model-catalog/resolve",
        method="POST",
        headers=other,
        body={"feature_key": values["feature_key"]},
        expected=403,
    )
    require(
        data_of({"data": denied.get("error")}).get("code") == "FORBIDDEN",
        "BFF must not invoke Agent-only model resolution",
    )
    other_models = data_of(
        http_json(
            bff,
            "/v1/models?" + catalog_query,
            headers={**web_headers, "x-kokoro-namespace": tenant + "-other"},
        )
    )
    require(other_models.get("models") == [], "BFF models crossed tenant boundary")


AGENT_RESOLVE_CHECK = """
import asyncio, json, os
from pydantic import SecretStr
from kokoro_agent.clients.system import SystemModelClient, ModelResolutionError
from kokoro_agent.model.factory import model_from_route
async def main():
    async with SystemModelClient(os.environ["SMOKE_SYSTEM_URL"], SecretStr(os.environ["SMOKE_AGENT_TOKEN"])) as client:
        for label in (None, os.environ["SMOKE_LABEL"]):
            route = await client.resolve(tenant_id=os.environ["SMOKE_TENANT"], feature_key=os.environ["SMOKE_FEATURE"], label=label, request_id="smoke-agent-resolve")
            if route.revision_id != os.environ["SMOKE_REVISION"] or route.transport != "litellm":
                raise RuntimeError("System route mismatch")
            model = model_from_route(route, None)
            if model.provider != "litellm" or model.name != "smoke-model":
                raise RuntimeError("Agent model construction mapping mismatch")
        try:
            await client.resolve(tenant_id=os.environ["SMOKE_TENANT"] + "-other", feature_key=os.environ["SMOKE_FEATURE"], label=None, request_id=None)
        except ModelResolutionError as error:
            if error.code != "ROUTE_NOT_FOUND": raise
        else:
            raise RuntimeError("Agent resolution crossed tenant boundary")
    print(json.dumps({"agent_resolve": "PASS", "inference": "not-executed"}))
asyncio.run(main())
"""


def repository_evidence() -> dict[str, dict[str, str | bool]]:
    states: dict[str, dict[str, str | bool]] = {}
    for owner in ("kokoro-system", "kokoro-bff", "kokoro-agent"):
        command = ["git", "-C", str(ROOT / owner)]
        states[owner] = {
            "commit": command_output([*command, "rev-parse", "HEAD"]).strip(),
            "working_tree_dirty": bool(
                command_output(
                    [*command, "status", "--porcelain", "--untracked-files=normal"]
                ).strip()
            ),
        }
    return states


def run_smoke(args: argparse.Namespace) -> int:
    system_env = node_environment(args.node24_bin, 24)
    bff_env = node_environment(args.node22_bin, 22)
    resources = OwnedResources(args.postgres, args.redis, secrets.token_hex(12))
    processes: list[subprocess.Popen[bytes]] = []
    cleanup_errors: list[str] = []
    tenant = f"smoke-{resources.run_id}"
    system_port, bff_port = free_port(), free_port()
    while system_port == bff_port:
        bff_port = free_port()
    system, bff = f"http://127.0.0.1:{system_port}", f"http://127.0.0.1:{bff_port}"
    bff_token, agent_token, admin_token, web_token = (
        secrets.token_hex(24) for _ in range(4)
    )
    with (
        tempfile.TemporaryDirectory(prefix="kokoro-system-smoke-") as temporary,
        ExitStack() as files,
    ):
        try:
            resources.command(["psql", resources.postgres, "-X", "-Atc", "SELECT 1"])
            require(
                resources.command(
                    ["redis-cli", "-e", "-u", resources.redis, "PING"]
                ).strip()
                == "PONG",
                "Shared Redis unavailable",
            )
            system_env.update(
                {
                    "DATABASE_URL": resources.create_database("system"),
                    "REDIS_URL": args.redis,
                    "KOKORO_SYSTEM_REDIS_NAMESPACE": resources.namespace,
                    "KOKORO_SYSTEM_HOST": "127.0.0.1",
                    "KOKORO_SYSTEM_PORT": str(system_port),
                    "KOKORO_SYSTEM_BFF_SERVICE_TOKEN": bff_token,
                    "KOKORO_SYSTEM_AGENT_SERVICE_TOKEN": agent_token,
                    "KOKORO_SYSTEM_ADMIN_SERVICE_TOKEN": admin_token,
                    "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
                }
            )
            bff_env.update(
                {
                    "KOKORO_BFF_POSTGRES_URL": resources.create_database("bff"),
                    "KOKORO_BFF_REDIS_URL": args.redis,
                    "KOKORO_BFF_HOST": "127.0.0.1",
                    "KOKORO_BFF_PORT": str(bff_port),
                    "KOKORO_BFF_MODE": "live",
                    "KOKORO_BFF_SHARED_SECRET": web_token,
                    "KOKORO_INTERNAL_SECRET_BFF": bff_token,
                    "KOKORO_SYSTEM_BASE_URL": system,
                    "KOKORO_AGENT_ENABLED": "false",
                    "KOKORO_TENANT_ID": tenant,
                    "KOKORO_DOMAIN": f"{resources.run_id}.smoke.localhost",
                    "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
                }
            )
            for owner, env, base in [
                ("kokoro-system", system_env, system),
                ("kokoro-bff", bff_env, bff),
            ]:
                log = files.enter_context(open(Path(temporary) / f"{owner}.log", "wb"))
                installed = run_owned_command(
                    ["pnpm", "db:apply-schema"],
                    cwd=ROOT / owner,
                    env=env,
                    log=log,
                    timeout=30,
                )
                require(
                    installed == 0,
                    f"{owner} canonical schema installation failed",
                )
                process = subprocess.Popen(
                    ["pnpm", "dev"],
                    cwd=ROOT / owner,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                processes.append(process)
                wait_ready(base, process)
            values = seed_control_plane(system, tenant, admin_token, resources.run_id)
            verify_read_consumers(system, bff, tenant, values, bff_token, web_token)
            agent_env = {
                **os.environ,
                "SMOKE_SYSTEM_URL": system,
                "SMOKE_AGENT_TOKEN": agent_token,
                "SMOKE_TENANT": tenant,
                "SMOKE_FEATURE": values["feature_key"],
                "SMOKE_LABEL": values["label_key"],
                "SMOKE_REVISION": values["revision_id"],
            }
            checked = run_owned_command(
                [
                    "uv",
                    "run",
                    "--frozen",
                    "--no-sync",
                    "python",
                    "-c",
                    AGENT_RESOLVE_CHECK,
                ],
                cwd=ROOT / "kokoro-agent",
                env=agent_env,
                log=files.enter_context(open(Path(temporary) / "agent.log", "wb")),
                timeout=30,
            )
            require(
                checked == 0,
                "Agent live System resolver verification failed",
            )
        finally:
            for process in reversed(processes):
                try:
                    stop_owned_process(process)
                except (SmokeError, OSError):
                    cleanup_errors.append("owned process shutdown failed")
            try:
                resources.cleanup()
            except SmokeError:
                cleanup_errors.append("owned infrastructure cleanup failed")
            if cleanup_errors:
                raise SmokeError("; ".join(cleanup_errors))
    evidence = {
        "status": "PASS",
        "system": "source HTTP",
        "bff": "source HTTP manifest/catalog",
        "agent": "live HTTP resolve/default/explicit/tenant denial",
        "inference": "not-executed",
        "cleanup": "owned resources removed",
        "repositories": repository_evidence(),
    }
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--postgres",
        default=os.environ.get(
            "TEST_ADMIN_DATABASE_URL", "postgresql://localhost/postgres"
        ),
    )
    result.add_argument(
        "--redis", default=os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/2")
    )
    result.add_argument("--node24-bin", default="")
    result.add_argument("--node22-bin", default="")
    return result


def main() -> int:
    args = parser().parse_args()
    return run_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())

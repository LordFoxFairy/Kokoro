#!/usr/bin/env python3
"""Run-owned BFF Product → Agent claimed Run → Storage CLEAN Artifact smoke.

Requires pre-existing local PostgreSQL, Redis, S3-compatible object store and
ClamAV.  It does not start, reset, or clean shared infrastructure.  The model
provider is not involved: an owned pending Run is claimed and its production
delivery client/emitter are driven with deterministic bytes.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.parse import parse_qsl, quote, urlsplit, urlunsplit
from uuid import uuid4

if __package__:
    from scripts.e2e import run_agent_storage_artifact_smoke as agent_storage
    from scripts.e2e import run_bff_agent_worker_smoke as bff_agent
    from scripts.e2e.bff_iam_admission_stub import AdmissionIdentity, iam_admission_stub
    from scripts.e2e.bff_owner_schema import bff_owner_database_url
else:
    import run_agent_storage_artifact_smoke as agent_storage
    import run_bff_agent_worker_smoke as bff_agent
    from bff_iam_admission_stub import AdmissionIdentity, iam_admission_stub
    from bff_owner_schema import bff_owner_database_url


ROOT = Path(__file__).resolve().parents[2]
BFF = ROOT / "apps/kokoro-bff"
AGENT = ROOT / "apps/kokoro-agent"
STORAGE = ROOT / "apps/kokoro-storage"
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
REDIS_DBS = (6, 7, 8)


class SmokeError(RuntimeError):
    """Non-secret diagnostic emitted by this runner."""


def _safe_error(exc: BaseException | None) -> str | None:
    if isinstance(exc, SmokeError):
        return str(exc)
    return agent_storage._safe_error(exc)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _local_origin(value: str, label: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in LOCAL_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise SmokeError(f"{label} requires a local origin")
    try:
        port = parsed.port
    except ValueError:
        raise SmokeError(f"{label} port invalid") from None
    if port is None or port == 3310:
        raise SmokeError(f"{label} port 3310 is reserved or port missing")
    return f"{parsed.scheme}://{parsed.netloc}"


def redis_url(base: str, db: int) -> str:
    if db not in REDIS_DBS:
        raise SmokeError("Redis DB outside owned set")
    parsed = urlsplit(base)
    return urlunsplit((parsed.scheme, parsed.netloc, f"/{db}", "", ""))


def check_configuration(env: dict[str, str]) -> dict[str, str]:
    required = (
        "KOKORO_W2_POSTGRES_ADMIN_URL",
        "KOKORO_W2_REDIS_URL",
        "KOKORO_W2_BFF_NODE_BIN",
        "KOKORO_W2_STORAGE_NODE_BIN",
        "KOKORO_W2_TEST_BUCKET",
        "KOKORO_W2_EXCLUSIVE_BUCKET",
        "KOKORO_OBJECT_STORE_ENDPOINT",
        "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT",
        "KOKORO_OBJECT_STORE_REGION",
        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID",
        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY",
        "KOKORO_SCANNER_HOST",
        "KOKORO_SCANNER_PORT",
    )
    for name in required:
        if not env.get(name, "").strip():
            raise SmokeError(f"{name} is required")
    pg = urlsplit(env["KOKORO_W2_POSTGRES_ADMIN_URL"])
    if (
        pg.scheme not in {"postgres", "postgresql"}
        or pg.hostname not in LOCAL_HOSTS
        or not pg.username
        or pg.fragment
        or any(
            key.lower() in {"schema", "options", "search_path"}
            for key, _ in parse_qsl(pg.query)
        )
    ):
        raise SmokeError("local PostgreSQL admin URL without schema required")
    red = urlsplit(env["KOKORO_W2_REDIS_URL"])
    if (
        red.scheme not in {"redis", "rediss"}
        or red.hostname not in LOCAL_HOSTS
        or red.path != "/6"
        or red.query
        or red.fragment
    ):
        raise SmokeError("local Redis DB 6 URL without options required")
    bucket = env["KOKORO_W2_TEST_BUCKET"]
    if bucket != env["KOKORO_W2_EXCLUSIVE_BUCKET"]:
        raise SmokeError("exclusive bucket confirmation must match test bucket")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,62}", bucket):
        raise SmokeError("test bucket name invalid")
    _local_origin(env["KOKORO_OBJECT_STORE_ENDPOINT"], "object store")
    _local_origin(env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"], "public object store")
    if env.get("KOKORO_OBJECT_STORE_PROFILE") != "custom":
        raise SmokeError("custom S3 profile required")
    if env.get("KOKORO_OBJECT_STORE_FORCE_PATH_STYLE") != "true":
        raise SmokeError("path-style object store required")
    if env.get("AWS_SESSION_TOKEN") or env.get("KOKORO_OBJECT_STORE_SESSION_TOKEN"):
        raise SmokeError("session token not accepted for exclusive test bucket")
    if env["KOKORO_SCANNER_HOST"] not in LOCAL_HOSTS:
        raise SmokeError("local scanner required")
    try:
        scanner_port = int(env["KOKORO_SCANNER_PORT"])
    except ValueError:
        raise SmokeError("scanner port invalid") from None
    if scanner_port == 3310 or not 1 <= scanner_port <= 65535:
        raise SmokeError("scanner port 3310 reserved or invalid")
    for name in ("KOKORO_W2_BFF_NODE_BIN", "KOKORO_W2_STORAGE_NODE_BIN"):
        if not Path(env[name]).is_absolute():
            raise SmokeError(f"{name} must be absolute")
    return {
        "admin_url": env["KOKORO_W2_POSTGRES_ADMIN_URL"],
        "redis_url": env["KOKORO_W2_REDIS_URL"],
        "bucket": bucket,
    }


def owner_database_urls(admin_url: str, database: str) -> dict[str, str]:
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,62}", database):
        raise SmokeError("invalid owned database identifier")
    return {
        "bff": bff_owner_database_url(
            agent_storage.database_url(admin_url, database, "kokoro_bff")
        ),
        "agent": agent_storage.database_url(admin_url, database, "kokoro_agent"),
        "storage": agent_storage.storage_database_url(admin_url, database),
    }


def validate_owned_versions(items: list[dict[str, object]], prefix: str) -> None:
    try:
        agent_storage.validate_owned_versions(items, prefix)
    except agent_storage.SmokeError:
        raise SmokeError(
            "owned object identity is ambiguous; preserving resources"
        ) from None


def verify_artifact_bytes(
    metadata: dict[str, object], data: bytes, artifact_id: str, conversation_id: str
) -> None:
    if (
        metadata.get("artifact_id") != artifact_id
        or metadata.get("conversation_id") != conversation_id
        or metadata.get("content_sha256") != sha256(data)
        or str(metadata.get("size_bytes")) != str(len(data))
    ):
        raise SmokeError("Product artifact identity or original bytes differ")


def _frozen_sources() -> dict[str, str]:
    """Require committed, clean, root-pinned owner sources before side effects."""
    sources: dict[str, str] = {}
    for name, path in (("bff", BFF), ("agent", AGENT), ("storage", STORAGE)):
        sha = agent_storage._git_sha(path)
        line = bff_agent.command_output(
            ["git", "-C", str(ROOT), "ls-tree", "HEAD", f"apps/{path.name}"]
        )
        if not line.startswith(f"160000 commit {sha}\t"):
            raise SmokeError(f"{name} source is not pinned by Root HEAD")
        sources[name] = sha
    return sources


class ThreeRedisOwnership:
    """Claim only empty DB6/7/8 and delete only exact run-registered keys."""

    def __init__(self, base: str, run_token: str) -> None:
        self.urls = {db: redis_url(base, db) for db in REDIS_DBS}
        self.markers = {
            db: f"kokoro:root:artifact-combo:{run_token}:ownership" for db in REDIS_DBS
        }
        self.allowed = {db: {self.markers[db]} for db in REDIS_DBS}
        self.claimed: set[int] = set()
        self.token = run_token

    def _call(self, db: int, *args: str) -> str:
        return bff_agent.command_output(
            ["redis-cli", "-e", "-u", self.urls[db], *args]
        ).strip()

    def claim(self) -> None:
        try:
            for db in REDIS_DBS:
                reply = self._call(
                    db,
                    "EVAL",
                    bff_agent._REDIS_CLAIM_SCRIPT,
                    "1",
                    self.markers[db],
                    self.token,
                    "7200",
                )
                if reply != "OK":
                    raise SmokeError(f"Redis DB {db} is not empty or claim failed")
                self.claimed.add(db)
        except BaseException:
            self.cleanup()
            raise

    def register_agent_run(self, conversation: str, run: str) -> None:
        if not all(
            re.fullmatch(r"[A-Za-z0-9_.:-]+", value) for value in (conversation, run)
        ):
            raise SmokeError("invalid Agent Redis key identity")
        self.allowed[7].update(
            {
                "kokoro:runs:requests",
                f"kokoro:run:{run}:events",
                f"kokoro:run:{run}:control",
                f"kokoro:session:{conversation}:live",
                f"kokoro:agent:lease:{run}",
            }
        )

    def cleanup(self) -> None:
        failures = []
        for db in tuple(self.claimed):
            keys = [self.markers[db], *sorted(self.allowed[db] - {self.markers[db]})]
            reply = self._call(
                db,
                "EVAL",
                bff_agent._REDIS_CLEANUP_SCRIPT,
                str(len(keys)),
                *keys,
                self.token,
            )
            if reply == "OK":
                self.claimed.remove(db)
            else:
                failures.append(f"Redis DB {db} ownership/keys changed")
        if failures:
            raise SmokeError("; ".join(failures))


async def _pending_run(agent_url: str, run_id: str) -> object:
    from kokoro_agent.infrastructure.postgres_run_repository import (
        RunRepositorySettings,
        make_run_repository,
    )

    settings = RunRepositorySettings(
        database_url=agent_url, schema_name="kokoro_agent", lease_ttl_ms=90_000
    )
    deadline = time.monotonic() + 35
    async with make_run_repository(settings) as runs:
        while time.monotonic() < deadline:
            request = await runs.get_pending_dispatch(run_id)
            if request is not None:
                return request
            await asyncio.sleep(0.2)
    raise SmokeError("BFF dispatch did not create an Agent pending Run")


async def _deliver_pending(
    agent_url: str,
    agent_redis_url: str,
    storage_base: str,
    object_origin: str,
    agent_secret: str,
    run_request: object,
    content: bytes,
) -> object:
    from kokoro_agent.clients.storage import DeliveryRequest
    from kokoro_agent.clients.storage_delivery import StorageDeliveryClient
    from kokoro_agent.clients.storage_transport import StorageDeliveryTransport
    from kokoro_agent.infrastructure.postgres_run_repository import (
        RunRepositorySettings,
        make_run_repository,
    )
    from kokoro_agent.tools.deliver import DeliverResult

    settings = RunRepositorySettings(
        database_url=agent_url, schema_name="kokoro_agent", lease_ttl_ms=90_000
    )
    async with make_run_repository(settings) as runs:
        lease = await runs.claim_dispatch(run_request, "artifact-combo-smoke")
        if lease is None:
            raise SmokeError("Agent production Run lease was not claimed")
        tool_call_id = f"tool-{uuid4()}"
        filename = "delivered-work.txt"
        request = DeliveryRequest(
            request_id=f"delivery-{uuid4()}",
            run_id=run_request.run_id,
            namespace="",
            identity=run_request.execution_identity,
            path=f"/{filename}",
            title="Delivered work",
            note="Three-owner smoke artifact",
            mime_type="text/plain",
            content_sha256=sha256(content),
            content=content,
            lease=lease,
            tool_call_id=tool_call_id,
        )
        if not await runs.journal_tool_started(
            run_request.run_id, lease, tool_call_id, "deliver"
        ):
            raise SmokeError("Agent production tool journal did not start")
        async with StorageDeliveryTransport(
            storage_base, object_origin, agent_secret
        ) as transport:
            receipt = await StorageDeliveryClient(runs, transport).publish(request)
        result = DeliverResult.model_validate(
            agent_storage.deliver_result(
                receipt, request.path, request.title, request.note
            )
        )
        if not await runs.journal_tool_finished(
            run_request.run_id,
            lease,
            tool_call_id,
            result.model_dump_json(),
            False,
        ):
            raise SmokeError("Agent production delivery journal did not finish")
        await agent_storage._assert_agent_event_projection(
            runs,
            agent_url,
            agent_redis_url,
            run_request,
            lease,
            receipt.artifact_id,
            tool_call_id,
            receipt.artifact_kind,
        )
        return receipt


def _get_json(
    base: str, path: str, headers: dict[str, str], expected: int
) -> dict[str, object]:
    status, value, _ = bff_agent._request(base, path, headers=headers)
    return bff_agent._data(status, value, expected, path)


def _wait_public_artifact(
    bff_base: str, headers: dict[str, str], artifact_id: str, timeout: float
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        page = _get_json(bff_base, "/v1/library?kind=artifact&limit=1", headers, 200)
        items = page.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            if items[0].get("artifact_id") == artifact_id:
                return items[0]
        time.sleep(0.2)
    raise SmokeError("BFF projector did not associate delivered Artifact")


def _verify_product(
    bff_base: str,
    conversation: str,
    artifact_id: str,
    content: bytes,
    owner_headers: dict[str, str],
    other_headers: dict[str, str],
    outside_headers: dict[str, str],
) -> list[str]:
    import httpx

    listed = _wait_public_artifact(bff_base, owner_headers, artifact_id, 45)
    verify_artifact_bytes(listed, content, artifact_id, conversation)
    selector = f"/v1/library/artifacts/{quote(conversation)}/{quote(artifact_id)}"
    detail = _get_json(bff_base, selector, owner_headers, 200)
    verify_artifact_bytes(detail, content, artifact_id, conversation)
    other_page = _get_json(
        bff_base, "/v1/library?kind=artifact&limit=1", other_headers, 200
    )
    if other_page.get("items") != []:
        raise SmokeError("same-tenant other subject saw Artifact in Library")
    private_status, private_body, _ = bff_agent._request(
        bff_base, selector, headers=other_headers
    )
    bff_agent._error(
        private_status,
        private_body,
        404,
        "library_artifact_not_found",
        "private artifact detail",
    )
    with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
        response = client.get(f"{bff_base}{selector}/content", headers=owner_headers)
        if response.status_code != 200 or response.content != content:
            raise SmokeError("BFF Product content did not return original bytes")
        for header, expected in (
            ("cache-control", "no-store"),
            ("x-content-type-options", "nosniff"),
            ("referrer-policy", "no-referrer"),
        ):
            if response.headers.get(header) != expected:
                raise SmokeError("BFF Product download security header drift")
        if not response.headers.get("content-disposition", "").startswith(
            "attachment;"
        ):
            raise SmokeError("BFF Product content was not an attachment")
        hidden = client.get(f"{bff_base}{selector}/content", headers=other_headers)
        if hidden.status_code != 404:
            raise SmokeError("same-tenant other subject obtained Artifact")
        crossed = client.get(f"{bff_base}{selector}", headers=outside_headers)
        if crossed.status_code != 403:
            raise SmokeError("foreign tenant crossed Product admission")
    return [
        "product_first_message_dispatch",
        "agent_claimed_run_clean_delivery_event",
        "bff_projected_artifact_list_and_detail",
        "bff_original_bytes_and_secure_headers",
        "private_404_and_foreign_tenant_403",
    ]


def _verify_two_artifact_pagination(
    bff_base: str,
    owner_headers: dict[str, str],
    expected: dict[str, tuple[str, bytes]],
) -> None:
    first = _get_json(bff_base, "/v1/library?kind=artifact&limit=1", owner_headers, 200)
    first_items = first.get("items")
    cursor = first.get("next_cursor")
    if (
        not isinstance(first_items, list)
        or len(first_items) != 1
        or not isinstance(first_items[0], dict)
        or not isinstance(cursor, str)
        or not cursor
    ):
        raise SmokeError("two-Artifact first page or cursor missing")
    second = _get_json(
        bff_base,
        f"/v1/library?kind=artifact&limit=1&cursor={quote(cursor, safe='')}",
        owner_headers,
        200,
    )
    second_items = second.get("items")
    if (
        not isinstance(second_items, list)
        or len(second_items) != 1
        or not isinstance(second_items[0], dict)
        or second.get("next_cursor") is not None
    ):
        raise SmokeError("two-Artifact second page shape invalid")
    seen = set()
    for item in (first_items[0], second_items[0]):
        artifact_id = item.get("artifact_id")
        if not isinstance(artifact_id, str) or artifact_id not in expected:
            raise SmokeError("two-Artifact page contained an unexpected identity")
        conversation, content = expected[artifact_id]
        verify_artifact_bytes(item, content, artifact_id, conversation)
        seen.add(artifact_id)
    if seen != set(expected):
        raise SmokeError("two-Artifact pages duplicated or omitted an Artifact")


def run_smoke(env: dict[str, str], config: dict[str, str]) -> dict[str, object]:
    import psycopg

    sources = _frozen_sources()
    for name, expected in (
        ("KOKORO_W2_BFF_NODE_BIN", "v22."),
        ("KOKORO_W2_STORAGE_NODE_BIN", "v24."),
    ):
        version = subprocess.check_output(
            [env[name], "--version"], text=True, timeout=5
        ).strip()
        if not version.startswith(expected):
            raise SmokeError(f"{name} requires {expected} runtime")
    if env.get("NODE_ENV") == "production":
        raise SmokeError("local signed URL test requires development mode")
    for path in (
        BFF / "dist/main.js",
        STORAGE / "dist/main.js",
        STORAGE / "node_modules/tsx/dist/cli.mjs",
    ):
        if not path.is_file():
            raise SmokeError("frozen owner build/dependencies missing")
    run_token = secrets.token_hex(12)
    database = f"artifact_combo_{run_token}"
    tenant = f"tenant_{run_token}"
    owner = f"owner_{run_token}"
    other = f"other_{run_token}"
    prefix = f"{tenant}/"
    urls = owner_database_urls(config["admin_url"], database)
    redis = ThreeRedisOwnership(config["redis_url"], run_token)
    directory = Path(tempfile.mkdtemp(prefix="kokoro-artifact-combo-"))
    os.chmod(directory, 0o700)
    s3 = None
    admin = None
    database_created = False
    database_create_uncertain = False
    processes: list[subprocess.Popen[bytes]] = []
    failure: BaseException | None = None
    cleanup_error: BaseException | None = None
    cases: list[str] = []
    tokens = {
        label: secrets.token_urlsafe(24) for label in ("owner", "other", "outside")
    }
    web_secret, agent_secret, storage_secret = (secrets.token_hex(32) for _ in range(3))
    credentials = {
        config["admin_url"],
        *tokens.values(),
        web_secret,
        agent_secret,
        storage_secret,
    }
    try:
        s3 = agent_storage._s3(env)
        admin = psycopg.connect(config["admin_url"], autocommit=True, connect_timeout=5)
        agent_storage.preflight_bucket(s3, config["bucket"], prefix)
        redis.claim()
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
            if cur.fetchone() is not None:
                raise SmokeError("random database already exists; refusing adoption")
            try:
                cur.execute(f'CREATE DATABASE "{database}"')
            except BaseException:
                try:
                    cur.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s", (database,)
                    )
                    database_created = cur.fetchone() is not None
                except BaseException:
                    database_create_uncertain = True
                raise
            database_created = True
        base_env = {
            "PATH": env.get("PATH", ""),
            "HOME": env.get("HOME", ""),
            "NODE_ENV": "development",
            "TMPDIR": str(directory),
        }
        storage_port, bff_port, agent_port = (
            agent_storage._owned_port() for _ in range(3)
        )
        storage_base = f"http://127.0.0.1:{storage_port}"
        bff_base = f"http://127.0.0.1:{bff_port}"
        agent_base = f"http://127.0.0.1:{agent_port}"
        storage_env = agent_storage._storage_env(
            env, database, agent_secret, storage_secret, storage_port
        )
        storage_env["KOKORO_REDIS_URL"] = redis.urls[6]
        bff_env = {
            **base_env,
            "PATH": f"{Path(env['KOKORO_W2_BFF_NODE_BIN']).parent}:{base_env['PATH']}",
            "KOKORO_BFF_POSTGRES_URL": urls["bff"],
            "KOKORO_BFF_REDIS_URL": redis.urls[8],
            "KOKORO_BFF_HOST": "127.0.0.1",
            "KOKORO_BFF_PORT": str(bff_port),
            "KOKORO_BFF_MODE": "live",
            "KOKORO_BFF_SHARED_SECRET": web_secret,
            "KOKORO_TENANT_ID": tenant,
            "KOKORO_DOMAIN": f"{run_token}.smoke.localhost",
            "KOKORO_AGENT_ENABLED": "true",
            "KOKORO_AGENT_BASE_URL": agent_base,
            "KOKORO_INTERNAL_SECRET_BFF": agent_secret,
            "KOKORO_STORAGE_RPC_BASE_URL": storage_base,
            "KOKORO_STORAGE_OBJECT_ORIGIN": env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
            "KOKORO_BFF_STORAGE_SECRET": storage_secret,
        }
        agent_env = {
            **base_env,
            "PYTHON_DOTENV_DISABLED": "1",
            "KOKORO_AGENT_DATABASE_URL": urls["agent"],
            "KOKORO_AGENT_DATABASE_SCHEMA": "kokoro_agent",
            "KOKORO_REDIS_URL": redis.urls[7],
            "KOKORO_INTERNAL_SECRET_AGENT": agent_secret,
            "KOKORO_AGENT_HTTP_HOST": "127.0.0.1",
            "KOKORO_AGENT_HTTP_PORT": str(agent_port),
        }
        fixture = agent_storage._storage_schema_fixture(directory)
        with (directory / "owners.log").open("xb") as log:
            os.chmod(directory / "owners.log", 0o600)
            storage_schema_status = bff_agent.run_owned_command(
                [
                    env["KOKORO_W2_STORAGE_NODE_BIN"],
                    str(STORAGE / "node_modules/tsx/dist/cli.mjs"),
                    "scripts/apply-schema.ts",
                ],
                cwd=fixture,
                env=storage_env,
                log=log,
                timeout=90,
            )
            if storage_schema_status != 0:
                raise SmokeError("Storage schema installation failed")
            bff_schema_status = bff_agent.run_owned_command(
                [
                    str(Path(env["KOKORO_W2_BFF_NODE_BIN"]).parent / "corepack"),
                    "pnpm",
                    "db:apply-schema",
                ],
                cwd=BFF,
                env=bff_env,
                log=log,
                timeout=90,
            )
            if bff_schema_status != 0:
                raise SmokeError("BFF schema installation failed")
            asyncio.run(agent_storage._install_agent_schema(urls["agent"]))
            identities = {
                tokens["owner"]: AdmissionIdentity(
                    tenant, owner, f"session_{owner}", "web"
                ),
                tokens["other"]: AdmissionIdentity(
                    tenant, other, f"session_{other}", "web"
                ),
                tokens["outside"]: AdmissionIdentity(
                    f"outside_{tenant}", other, f"session_outside_{other}", "web"
                ),
            }
            with iam_admission_stub(identities) as iam_base:
                bff_env["KOKORO_IAM_BASE_URL"] = iam_base
                storage = bff_agent._start_process(
                    [env["KOKORO_W2_STORAGE_NODE_BIN"], str(STORAGE / "dist/main.js")],
                    cwd=STORAGE,
                    env=storage_env,
                    log=log,
                )
                processes.append(storage)
                agent_storage._wait_storage(storage_base, storage)
                agent_http = bff_agent._start_process(
                    [env.get("KOKORO_W2_UV_BIN", "uv"), "run", "kokoro-agent-http"],
                    cwd=AGENT,
                    env=agent_env,
                    log=log,
                )
                processes.append(agent_http)
                bff_agent._wait_ready(agent_base, agent_http, path="/healthz")
                bff = bff_agent._start_process(
                    [env["KOKORO_W2_BFF_NODE_BIN"], str(BFF / "dist/main.js")],
                    cwd=BFF,
                    env=bff_env,
                    log=log,
                )
                processes.append(bff)
                bff_agent._wait_ready(bff_base, bff)
                conversation = f"conv_{uuid4()}"
                owner_headers = bff_agent._bff_headers(
                    tokens["owner"], web_secret, f"artifact:{run_token}"
                )
                other_headers = bff_agent._bff_headers(tokens["other"], web_secret)
                outside_headers = bff_agent._bff_headers(tokens["outside"], web_secret)
                second_conversation = f"conv_{uuid4()}"
                status, payload, _ = bff_agent._request(
                    bff_base,
                    f"/v1/sessions/{conversation}/messages",
                    method="POST",
                    headers=owner_headers,
                    body={"content": "Create the smoke artifact."},
                )
                receipt = bff_agent._data(status, payload, 202, "Product first message")
                run_id = receipt.get("run_id")
                if not isinstance(run_id, str) or not run_id:
                    raise SmokeError("Product receipt missing run_id")
                redis.register_agent_run(conversation, run_id)
                pending = asyncio.run(_pending_run(urls["agent"], run_id))
                if pending.session_id != conversation:
                    raise SmokeError(
                        "Agent pending Run conversation differs from Product dispatch"
                    )
                if pending.execution_identity.tenant_ref != tenant:
                    raise SmokeError(
                        "Agent pending Run tenant differs from Product dispatch"
                    )
                content = f"Kokoro artifact {run_token}\n".encode()
                delivered = asyncio.run(
                    _deliver_pending(
                        urls["agent"],
                        redis.urls[7],
                        storage_base,
                        env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                        agent_secret,
                        pending,
                        content,
                    )
                )
                cases = _verify_product(
                    bff_base,
                    conversation,
                    delivered.artifact_id,
                    content,
                    owner_headers,
                    other_headers,
                    outside_headers,
                )
                status, payload, _ = bff_agent._request(
                    bff_base,
                    f"/v1/sessions/{second_conversation}/messages",
                    method="POST",
                    headers={
                        **owner_headers,
                        "idempotency-key": f"artifact-second:{run_token}",
                    },
                    body={"content": "Create one more independent smoke artifact."},
                )
                second_receipt = bff_agent._data(
                    status, payload, 202, "Product second message"
                )
                second_run_id = second_receipt.get("run_id")
                if not isinstance(second_run_id, str) or not second_run_id:
                    raise SmokeError("Product second receipt missing run_id")
                redis.register_agent_run(second_conversation, second_run_id)
                second_pending = asyncio.run(_pending_run(urls["agent"], second_run_id))
                if second_pending.session_id != second_conversation:
                    raise SmokeError(
                        "Agent second pending Run conversation differs from Product dispatch"
                    )
                if second_pending.execution_identity.tenant_ref != tenant:
                    raise SmokeError(
                        "Agent second pending Run tenant differs from Product dispatch"
                    )
                second_content = f"Kokoro second artifact {run_token}\n".encode()
                second_delivered = asyncio.run(
                    _deliver_pending(
                        urls["agent"],
                        redis.urls[7],
                        storage_base,
                        env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                        agent_secret,
                        second_pending,
                        second_content,
                    )
                )
                _wait_public_artifact(
                    bff_base, owner_headers, second_delivered.artifact_id, 45
                )
                _verify_two_artifact_pagination(
                    bff_base,
                    owner_headers,
                    {
                        delivered.artifact_id: (conversation, content),
                        second_delivered.artifact_id: (
                            second_conversation,
                            second_content,
                        ),
                    },
                )
                cases.append("two_artifact_cursor_pagination")
                log.flush()
                diagnostic = (directory / "owners.log").read_text(errors="replace")
                if any(secret in diagnostic for secret in credentials):
                    raise SmokeError("credential appeared in owned process log")
    except BaseException as exc:
        failure = exc
    try:
        stop_failures = []
        for process in reversed(processes):
            try:
                agent_storage._stop_owned(process)
            except BaseException:
                stop_failures.append(process.pid)
        if stop_failures:
            raise SmokeError("owned process shutdown uncertain; preserving resources")
        if redis.claimed:
            redis.cleanup()
        if (
            database_created
            and not database_create_uncertain
            and admin is not None
            and s3 is not None
        ):
            agent_storage.cleanup_objects(s3, config["bucket"], prefix)
            with admin.cursor() as cur:
                cur.execute(f'DROP DATABASE "{database}" WITH (FORCE)')
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
                if cur.fetchone() is not None:
                    raise SmokeError("owned database remained after drop")
            database_created = False
    except BaseException as exc:
        cleanup_error = exc
    finally:
        if admin is not None:
            admin.close()
        if s3 is not None:
            s3.close()
    if failure or cleanup_error:
        return {
            "result": "failed",
            "sources": sources,
            "error": _safe_error(failure),
            "cleanup_error": _safe_error(cleanup_error),
            "run_id": run_token,
            "database_candidate": database,
            "owned_database": database if database_created else None,
            "database_create_uncertain": database_create_uncertain,
            "bucket": config["bucket"],
            "owned_prefix": prefix,
            "evidence_dir": str(directory),
            "remaining_redis_claims": sorted(redis.claimed),
        }
    shutil.rmtree(directory)
    return {
        "result": "passed",
        "sources": sources,
        "cases": cases,
        "run_id": run_token,
        "owned_database_removed": True,
        "owned_redis_keys_removed": True,
        "owned_objects_removed": True,
        "model_boundary": "no model worker/provider invoked",
    }


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-config", action="store_true")
    args = parser.parse_args(argv)
    current_env = dict(os.environ) if env is None else env
    try:
        config = check_configuration(current_env)
        if args.check_config:
            print(
                "Three-owner artifact configuration shape valid; provider not contacted"
            )
            return 0
        report = run_smoke(current_env, config)
    except BaseException as exc:
        report = {"result": "failed", "error": _safe_error(exc)}
    print(
        json.dumps(report, sort_keys=True),
        file=sys.stdout if report["result"] == "passed" else sys.stderr,
    )
    return 0 if report["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Isolated real Agent claimed Run → Storage v2 → MinIO/ClamAV smoke.

Run with apps/kokoro-agent/.venv/bin/python. Shared infrastructure is reused,
not started or reset. The explicit test bucket must be exclusive to this run.
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
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "apps/kokoro-agent"
STORAGE = ROOT / "apps/kokoro-storage"
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


class SmokeError(RuntimeError):
    """Failure safe to print without URLs, credentials, or file content."""


def _local_origin(value: str, label: str) -> str:
    url = urlsplit(value)
    if (
        url.scheme not in {"http", "https"}
        or url.hostname not in LOCAL_HOSTS
        or url.username is not None
        or url.password is not None
        or url.query
        or url.fragment
        or url.path not in {"", "/"}
    ):
        raise SmokeError(f"{label} must be a local object store origin")
    try:
        port = url.port
    except ValueError:
        raise SmokeError(f"{label} port invalid") from None
    if port is None or port == 3310:
        raise SmokeError(f"{label} requires a non-preview port")
    return f"{url.scheme}://{url.netloc}"


def check_configuration(env: dict[str, str]) -> dict[str, str]:
    required = (
        "KOKORO_W2_POSTGRES_ADMIN_URL",
        "KOKORO_W2_REDIS_URL",
        "KOKORO_W2_TEST_BUCKET",
        "KOKORO_W2_EXCLUSIVE_BUCKET",
        "KOKORO_W2_STORAGE_NODE_BIN",
        "KOKORO_OBJECT_STORE_ENDPOINT",
        "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT",
        "KOKORO_OBJECT_STORE_REGION",
        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID",
        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY",
        "KOKORO_SCANNER_HOST",
        "KOKORO_SCANNER_PORT",
    )
    for key in required:
        if not env.get(key, "").strip():
            raise SmokeError(f"{key} is required")
    bucket = env["KOKORO_W2_TEST_BUCKET"]
    if env["KOKORO_W2_EXCLUSIVE_BUCKET"] != bucket:
        raise SmokeError("exclusive bucket confirmation must match test bucket")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,62}", bucket):
        raise SmokeError("test bucket name invalid")
    pg = urlsplit(env["KOKORO_W2_POSTGRES_ADMIN_URL"])
    if (
        pg.scheme not in {"postgres", "postgresql"}
        or pg.hostname not in LOCAL_HOSTS
        or not pg.username
        or pg.fragment
    ):
        raise SmokeError("local PostgreSQL admin URL required")
    if any(
        key.lower() in {"schema", "options", "search_path"}
        for key, _ in parse_qsl(pg.query)
    ):
        raise SmokeError("PostgreSQL admin URL must exclude search-path options")
    redis = urlsplit(env["KOKORO_W2_REDIS_URL"])
    if (
        redis.scheme not in {"redis", "rediss"}
        or redis.hostname not in LOCAL_HOSTS
        or redis.path != "/6"
        or redis.query
        or redis.fragment
    ):
        raise SmokeError("local Redis DB 6 URL without options required")
    _local_origin(env["KOKORO_OBJECT_STORE_ENDPOINT"], "internal object store origin")
    _local_origin(
        env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"], "public object store origin"
    )
    if env.get("KOKORO_OBJECT_STORE_PROFILE") != "custom":
        raise SmokeError("explicit custom S3 profile required")
    if env.get("KOKORO_OBJECT_STORE_FORCE_PATH_STYLE") != "true":
        raise SmokeError("path-style test bucket required")
    if env.get("AWS_SESSION_TOKEN") or env.get("KOKORO_OBJECT_STORE_SESSION_TOKEN"):
        raise SmokeError("explicit test credentials cannot use a session token")
    if env["KOKORO_SCANNER_HOST"] not in LOCAL_HOSTS:
        raise SmokeError("local scanner endpoint required")
    try:
        scanner_port = int(env["KOKORO_SCANNER_PORT"])
    except ValueError:
        raise SmokeError("scanner port invalid") from None
    if scanner_port == 3310 or not 1 <= scanner_port <= 65535:
        raise SmokeError("scanner port 3310 is reserved or invalid")
    if not Path(env["KOKORO_W2_STORAGE_NODE_BIN"]).is_absolute():
        raise SmokeError("Storage Node path must be absolute")
    return {"admin_url": env["KOKORO_W2_POSTGRES_ADMIN_URL"], "bucket": bucket}


def database_url(admin_url: str, database: str, schema: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,62}", database) or not re.fullmatch(
        r"[a-z][a-z0-9_]{2,62}", schema
    ):
        raise SmokeError("invalid owned database or schema identifier")
    parts = urlsplit(admin_url)
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            f"/{database}",
            urlencode({"options": f"-csearch_path={schema}"}),
            "",
        )
    )


def storage_database_url(admin_url: str, database: str) -> str:
    parts = urlsplit(admin_url)
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            f"/{database}",
            urlencode({"schema": "kokoro_storage"}),
            "",
        )
    )


def validate_owned_versions(
    items: list[dict[str, object]], prefix: str
) -> list[dict[str, object]]:
    for item in items:
        key, version, etag = item.get("Key"), item.get("VersionId"), item.get("ETag")
        if not (
            isinstance(key, str)
            and key.startswith(prefix)
            and re.fullmatch(
                re.escape(prefix) + r"(uploads|final)/[^/]+(?:/[^/]+)*", key
            )
            and isinstance(version, str)
            and version != "null"
            and version
            and isinstance(etag, str)
            and etag
        ):
            raise SmokeError("owned object identity is ambiguous; preserving resources")
    return items


def _list_versions(s3: object, bucket: str, prefix: str) -> list[dict[str, object]]:
    result = s3.list_object_versions(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
    if result.get("IsTruncated") or result.get("DeleteMarkers"):
        raise SmokeError("owned prefix inventory ambiguous; preserving resources")
    return validate_owned_versions(result.get("Versions", []), prefix)


def preflight_bucket(s3: object, bucket: str, prefix: str) -> None:
    s3.head_bucket(Bucket=bucket)
    versioning = s3.get_bucket_versioning(Bucket=bucket)
    lock = s3.get_object_lock_configuration(Bucket=bucket).get(
        "ObjectLockConfiguration", {}
    )
    if (
        versioning.get("Status") != "Enabled"
        or versioning.get("MFADelete") == "Enabled"
        or lock.get("ObjectLockEnabled") != "Enabled"
        or lock.get("Rule", {}).get("DefaultRetention")
    ):
        raise SmokeError(
            "exclusive test bucket requires Versioning/ObjectLock without retention"
        )
    if _list_versions(s3, bucket, prefix):
        raise SmokeError("random owned prefix was not empty before writes")


def cleanup_objects(s3: object, bucket: str, prefix: str) -> None:
    for item in _list_versions(s3, bucket, prefix):
        key, version, etag = item["Key"], item["VersionId"], item["ETag"]
        s3.delete_object(Bucket=bucket, Key=key, VersionId=version, IfMatch=etag)
        try:
            s3.head_object(Bucket=bucket, Key=key, VersionId=version)
        except Exception as exc:
            if (
                getattr(exc, "response", {})
                .get("ResponseMetadata", {})
                .get("HTTPStatusCode")
                != 404
            ):
                raise SmokeError("exact owned version deletion unconfirmed") from None
        else:
            raise SmokeError("exact owned version remained after deletion")
    if _list_versions(s3, bucket, prefix):
        raise SmokeError("owned versions remain after cleanup")


def _s3(env: dict[str, str]) -> object:
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=env["KOKORO_OBJECT_STORE_ENDPOINT"],
        region_name=env["KOKORO_OBJECT_STORE_REGION"],
        aws_access_key_id=env["KOKORO_OBJECT_STORE_ACCESS_KEY_ID"],
        aws_secret_access_key=env["KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY"],
        config=Config(
            s3={"addressing_style": "path"},
            retries={"max_attempts": 0},
            connect_timeout=3,
            read_timeout=10,
        ),
    )


def _owned_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _stop_owned(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait(timeout=5)
        return
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


def _storage_schema_fixture(directory: Path) -> Path:
    fixture = directory / "storage-schema"
    (fixture / "scripts").mkdir(parents=True)
    (fixture / "prisma").mkdir()
    for path in (
        "package.json",
        "prisma.config.ts",
        "prisma/schema.prisma",
        "scripts/apply-schema.ts",
    ):
        shutil.copyfile(STORAGE / path, fixture / path)
    (fixture / "node_modules").symlink_to(
        STORAGE / "node_modules", target_is_directory=True
    )
    return fixture


def _storage_env(
    env: dict[str, str], database: str, agent_secret: str, bff_secret: str, port: int
) -> dict[str, str]:
    node = Path(env["KOKORO_W2_STORAGE_NODE_BIN"])
    return {
        "PATH": f"{node.parent}:{env.get('PATH', '')}",
        "HOME": env.get("HOME", ""),
        "NODE_ENV": "development",
        "KOKORO_POSTGRES_URL": storage_database_url(
            env["KOKORO_W2_POSTGRES_ADMIN_URL"], database
        ),
        "KOKORO_REDIS_URL": env["KOKORO_W2_REDIS_URL"],
        "KOKORO_STORAGE_HOST": "127.0.0.1",
        "KOKORO_STORAGE_PORT": str(port),
        "KOKORO_STORAGE_SERVICE_CREDENTIALS": f"kokoro-agent={agent_secret},web-bff={bff_secret}",
        "KOKORO_OBJECT_STORE_DRIVER": "s3",
        "KOKORO_OBJECT_STORE_PROFILE": "custom",
        "KOKORO_OBJECT_STORE_BUCKET": env["KOKORO_W2_TEST_BUCKET"],
        "KOKORO_OBJECT_STORE_REGION": env["KOKORO_OBJECT_STORE_REGION"],
        "KOKORO_OBJECT_STORE_ENDPOINT": env["KOKORO_OBJECT_STORE_ENDPOINT"],
        "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": env[
            "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"
        ],
        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": env["KOKORO_OBJECT_STORE_ACCESS_KEY_ID"],
        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY": env[
            "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY"
        ],
        "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "true",
        "KOKORO_SCANNER_DRIVER": "clamav",
        "KOKORO_SCANNER_HOST": env["KOKORO_SCANNER_HOST"],
        "KOKORO_SCANNER_PORT": env["KOKORO_SCANNER_PORT"],
    }


def _wait_storage(base: str, process: subprocess.Popen[bytes]) -> None:
    import httpx

    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise SmokeError("owned Storage process exited before readiness")
        try:
            response = httpx.get(f"{base}/readyz", timeout=1.5, trust_env=False)
            if response.status_code == 200 and response.json() == {"status": "ready"}:
                return
        except (httpx.HTTPError, ValueError):
            pass
        time.sleep(0.2)
    raise SmokeError("owned Storage process did not become ready")


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def deliver_result(
    receipt: object, path: str, title: str, note: str
) -> dict[str, object]:
    """Construct the production DeliverResult shape before Agent journal commit."""
    return {
        "status": "delivered",
        "artifact_id": receipt.artifact_id,
        "asset_id": receipt.asset_id,
        "path": path,
        "title": title,
        "mime": receipt.mime_type,
        "size": receipt.size_bytes,
        "content_hash": receipt.content_sha256,
        "note": note,
    }


def verify_event_chain(
    outbox: list[dict[str, object]],
    chat: list[dict[str, object]],
    wire: list[dict[str, object]],
    artifact_id: str,
    tool_call_id: str,
) -> None:
    """Require one durable delivery before one terminal across all projections."""
    expected_kinds = ["run.started", "delivery.created", "run.completed"]
    if [frame.get("kind") for frame in outbox] != expected_kinds:
        raise SmokeError("delivery critical outbox order or cardinality drift")
    if [frame.get("durable_seq") for frame in outbox] != [1, 2, 3]:
        raise SmokeError("delivery critical outbox sequence drift")
    if [frame.get("index") for frame in outbox] != [0, 1, 2]:
        raise SmokeError("delivery critical outbox index drift")
    ids = [frame.get("event_id") for frame in outbox]
    if len(set(ids)) != 3 or not all(isinstance(item, str) and item for item in ids):
        raise SmokeError("delivery critical outbox duplicate event ID")
    payload = json.loads(str(outbox[1].get("payload_json", "")))
    if (
        payload.get("artifact_id") != artifact_id
        or payload.get("tool_call_id") != tool_call_id
    ):
        raise SmokeError("delivery critical outbox payload drift")
    if [record.get("event_type") for record in chat] != [
        "run.started",
        "delivery",
        "run.completed",
    ]:
        raise SmokeError("delivery Chat projection order or cardinality drift")
    if [record.get("source_index") for record in chat] != [0, 1, 2]:
        raise SmokeError("delivery Chat projection source index drift")
    chat_payload = json.loads(str(chat[1].get("payload_json", "")))
    if (
        chat_payload.get("artifact_id") != artifact_id
        or chat_payload.get("tool_call_id") != tool_call_id
    ):
        raise SmokeError("delivery Chat projection payload drift")
    if [event.get("kind") for event in wire] != expected_kinds:
        raise SmokeError("delivery live stream order or duplicate frame")
    if [event.get("event_id") for event in wire] != ids:
        raise SmokeError("delivery live stream duplicate or drifted event ID")
    if [event.get("durable_seq") for event in wire] != [1, 2, 3]:
        raise SmokeError("delivery live stream sequence drift")
    wire_payload = wire[1].get("payload")
    if (
        not isinstance(wire_payload, dict)
        or wire_payload.get("artifact_id") != artifact_id
        or wire_payload.get("tool_call_id") != tool_call_id
    ):
        raise SmokeError("delivery live stream payload drift")


def _storage_read(
    base: str, secret: str, tenant: str, subject: str, scope: str, artifact: str
) -> tuple[int, dict[str, object]]:
    import httpx

    body = {
        "command": {
            "commandId": str(uuid4()),
            "requestDigest": _hash(artifact.encode()),
        },
        "artifactId": artifact,
    }
    headers = {
        "content-type": "application/json",
        "connect-protocol-version": "1",
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": secret,
        "x-kokoro-tenant-id": tenant,
        "x-kokoro-subject-id": subject,
        "x-kokoro-request-id": str(uuid4()),
        "x-kokoro-scope-kind": "conversation",
        "x-kokoro-scope-id": scope,
    }
    with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
        response = client.post(
            f"{base}/kokoro.storage.v2.StorageService/GetFinalArtifactDownloadReference",
            json=body,
            headers=headers,
        )
        try:
            payload = response.json()
        except ValueError:
            raise SmokeError("Storage read response is not JSON") from None
    if not isinstance(payload, dict):
        raise SmokeError("Storage read response is not an object")
    return response.status_code, payload


async def _assert_agent_event_projection(
    runs: object,
    database_url_value: str,
    redis_url: str,
    run: object,
    lease: object,
    artifact_id: str,
    tool_call_id: str,
) -> None:
    """Use the production emitter, outbox, Redis bus, and Chat repository."""
    from datetime import UTC, datetime

    from kokoro_agent.domain.run.scope import RunScope
    from kokoro_agent.execution.events import RunEmitter
    from kokoro_agent.infrastructure.postgres_chat_repository import (
        PostgresChatRepositorySettings,
        make_chat_repository,
    )
    from kokoro_agent.protocol import (
        RunCompletedPayload,
        RunStartedPayload,
        run_events_stream,
    )
    from kokoro_agent.streams.factory import StreamSettings, make_stream

    scope = RunScope.of(run)
    stream = run_events_stream(run.run_id)
    bus = make_stream(StreamSettings(redis_url=redis_url))
    owned_stream = False
    try:
        if await bus.read_all(stream):
            raise SmokeError(
                "random Agent Redis stream already exists; refusing adoption"
            )
        owned_stream = True
        async with make_chat_repository(
            PostgresChatRepositorySettings(
                database_url=database_url_value, schema_name="kokoro_agent"
            )
        ) as chat:
            await chat.ensure_session(
                run.execution_identity.tenant_ref,
                scope.namespace,
                run.session_id,
                project_ref=None,
                title="W2 artifact smoke",
                updated_at=datetime.now(UTC),
            )
            emitter = await RunEmitter.attach(
                bus,
                run.run_id,
                outbox=runs,
                lease=lease,
                tenant_id=run.execution_identity.tenant_ref,
                namespace=scope.namespace,
                session_id=run.session_id,
                chat_repository=chat,
            )
            await emitter.emit(RunStartedPayload())
            await emitter.ensure_delivery_events()
            first = await bus.read_all(stream)
            if [item.event.get("kind") for item in first] != [
                "run.started",
                "delivery.created",
            ]:
                raise SmokeError("Agent did not publish one durable delivery")
            await emitter.ensure_delivery_events()
            if len(await bus.read_all(stream)) != len(first):
                raise SmokeError("delivery replay double-published")
            if not await runs.try_mark_terminal(run.run_id, lease):
                raise SmokeError("Agent Run terminal CAS failed")
            await emitter.emit(
                RunCompletedPayload(status="completed", token_usage=None)
            )
            await emitter.ensure_delivery_events()
            wire = [item.event for item in await bus.read_all(stream)]
            reconcile = await runs.reconcile_receipts(run.run_id, republish_grace_ms=0)
            outbox = [frame.model_dump() for frame in reconcile.republish]
            chat_events = [
                record.model_dump()
                for record in await chat.replay(
                    run.execution_identity.tenant_ref,
                    scope.namespace,
                    run.session_id,
                )
            ]
            verify_event_chain(outbox, chat_events, wire, artifact_id, tool_call_id)
            if any(
                frame.run_id == run.run_id
                for frame in await runs.list_unpublished_outbox()
            ):
                raise SmokeError("Agent retained unpublished critical outbox")
    finally:
        try:
            if owned_stream:
                await bus.delete(stream)
        finally:
            await bus.aclose()


async def _agent_cases(
    database_url_value: str,
    redis_url: str,
    base: str,
    object_origin: str,
    agent_secret: str,
    bff_secret: str,
    tenant: str,
    run_token: str,
) -> list[str]:
    import httpx
    from kokoro_agent.clients.storage import DeliveryRequest, StorageClientError
    from kokoro_agent.clients.storage_delivery import StorageDeliveryClient
    from kokoro_agent.clients.storage_transport import StorageDeliveryTransport
    from kokoro_agent.infrastructure.postgres_run_repository import (
        RunRepositorySettings,
        make_run_repository,
    )
    from kokoro_agent.tools.deliver import DeliverResult
    from kokoro_agent.protocol import (
        ExecutionIdentity,
        IdentityRef,
        RunInput,
        RunRequest,
    )

    owner = f"owner-{run_token}"
    scope = f"conversation-{run_token}"
    identity = ExecutionIdentity(
        tenant_ref=tenant,
        actor=IdentityRef(kind="user", opaque_ref=owner),
        subject=IdentityRef(kind="user", opaque_ref=owner),
        identity_assertion_ref=f"assertion-{run_token}",
    )
    bytes_value = f"Kokoro owned artifact {run_token}\n".encode()
    settings = RunRepositorySettings(
        database_url=database_url_value, schema_name="kokoro_agent", lease_ttl_ms=90_000
    )
    async with make_run_repository(settings) as runs:
        async with StorageDeliveryTransport(
            base, object_origin, agent_secret
        ) as transport:

            class CountingTransport:
                def __init__(self) -> None:
                    self.operations: list[str] = []

                async def call(
                    self, method: str, request: object, headers: dict[str, str]
                ) -> object:
                    self.operations.append(method)
                    return await transport.call(method, request, headers)

                async def put(self, reference: object, content: bytes) -> None:
                    self.operations.append("signed_put")
                    await transport.put(reference, content)

            counted = CountingTransport()
            delivery = StorageDeliveryClient(runs, counted)

            async def claimed_publish(
                suffix: str, content: bytes, ttl_repo: object = runs
            ) -> tuple[object, object, object]:
                run = RunRequest(
                    kind="run.request",
                    run_id=f"run-{suffix}-{run_token}",
                    session_id=scope,
                    feature_key="general",
                    execution_identity=identity,
                    input=RunInput(
                        message_id=f"message-{suffix}-{run_token}",
                        content="Publish artifact",
                    ),
                )
                lease = await ttl_repo.try_claim(run, f"smoke-worker-{run_token}")
                if lease is None:
                    raise SmokeError("Agent Run claim was not acquired")
                request = DeliveryRequest(
                    request_id=f"request-{suffix}-{run_token}",
                    run_id=run.run_id,
                    namespace="",
                    identity=identity,
                    path=f"/{suffix}.txt",
                    title=f"{suffix} artifact",
                    note="W2 vertical smoke",
                    mime_type="text/plain",
                    content_sha256=_hash(content),
                    content=content,
                    lease=lease,
                    tool_call_id=f"tool-{suffix}-{run_token}",
                )
                if not await ttl_repo.journal_tool_started(
                    run.run_id, lease, request.tool_call_id, "deliver"
                ):
                    raise SmokeError("Agent tool journal did not start")
                return run, lease, request

            _run, _lease, clean_request = await claimed_publish("clean", bytes_value)
            receipt = await delivery.publish(clean_request)
            if (
                not receipt.artifact_id
                or not receipt.asset_id
                or receipt.content_sha256 != _hash(bytes_value)
            ):
                raise SmokeError("Agent did not receive a final artifact receipt")
            if not await runs.journal_tool_finished(
                clean_request.run_id,
                clean_request.lease,
                clean_request.tool_call_id,
                DeliverResult.model_validate(
                    deliver_result(
                        receipt,
                        clean_request.path,
                        clean_request.title,
                        clean_request.note,
                    )
                ).model_dump_json(),
                False,
            ):
                raise SmokeError("Agent did not finalize its tool journal")
            journal = await runs.get_tool_journal(
                clean_request.run_id, clean_request.tool_call_id
            )
            if (
                journal is None
                or journal.status != "succeeded"
                or receipt.artifact_id not in journal.result
            ):
                raise SmokeError("Agent journal did not retain final artifact receipt")
            await _assert_agent_event_projection(
                runs,
                database_url_value,
                redis_url,
                _run,
                _lease,
                receipt.artifact_id,
                clean_request.tool_call_id,
            )
            status, own = _storage_read(
                base, bff_secret, tenant, owner, scope, receipt.artifact_id
            )
            reference = own.get("downloadReference")
            if (
                status != 200
                or not isinstance(reference, dict)
                or reference.get("method") != "GET"
            ):
                raise SmokeError("owner final artifact read was not granted")
            url = reference.get("url")
            if (
                not isinstance(url, str)
                or urlsplit(url).netloc != urlsplit(object_origin).netloc
            ):
                raise SmokeError("owner download origin drift")
            with httpx.Client(
                timeout=15, follow_redirects=False, trust_env=False
            ) as client:
                downloaded = client.get(
                    url, headers=reference.get("requiredHeaders", {})
                )
            if downloaded.status_code != 200 or downloaded.content != bytes_value:
                raise SmokeError("owner signed GET bytes differ from published bytes")
            cases = [
                "claimed_run_clean_final",
                "agent_tool_journal_succeeded",
                "delivery_critical_chat_terminal_order",
                "delivery_repeat_no_double_publish",
                "owner_signed_get_original_bytes",
            ]
            stale_settings = RunRepositorySettings(
                database_url=database_url_value,
                schema_name="kokoro_agent",
                lease_ttl_ms=25,
            )
            async with make_run_repository(stale_settings) as stale_runs:
                _run, _lease, stale_request = await claimed_publish(
                    "stale", b"stale", stale_runs
                )
                await asyncio.sleep(0.15)
                outbound_before_stale = len(counted.operations)
                try:
                    await delivery.publish(stale_request)
                except StorageClientError as exc:
                    if exc.code != "DELIVERY_LEASE_STALE":
                        raise SmokeError(
                            "expired lease rejected with unexpected code"
                        ) from None
                else:
                    raise SmokeError("expired lease was accepted")
                if len(counted.operations) != outbound_before_stale:
                    raise SmokeError("expired lease caused owner outbound I/O")
            cases.append("expired_lease_rejected_before_rpc")

            _run, _lease, infected_request = await claimed_publish("eicar", EICAR)
            finalizations_before_eicar = counted.operations.count("finalize_artifact")
            try:
                await delivery.publish(infected_request)
            except StorageClientError as exc:
                if exc.code != "DELIVERY_SCAN_REJECTED":
                    raise SmokeError(
                        "EICAR was rejected with unexpected code"
                    ) from None
            else:
                raise SmokeError("EICAR produced a final artifact")
            if (
                counted.operations.count("finalize_artifact")
                != finalizations_before_eicar
            ):
                raise SmokeError("EICAR reached artifact finalization RPC")
            cases.append("eicar_cannot_finalize")
            for label, candidate_tenant, candidate_subject, candidate_scope in (
                ("other_scope_denied", tenant, owner, f"other-{scope}"),
                ("other_tenant_denied", f"other-{tenant}", owner, scope),
            ):
                denied_status, denied = _storage_read(
                    base,
                    bff_secret,
                    candidate_tenant,
                    candidate_subject,
                    candidate_scope,
                    receipt.artifact_id,
                )
                if denied_status not in {403, 404} or "downloadReference" in denied:
                    raise SmokeError(
                        f"{label} unexpectedly obtained a final artifact reference"
                    )
                cases.append(label)
            return cases


async def _install_agent_schema(database_url_value: str) -> None:
    from kokoro_agent.infrastructure.postgres import connect_pg
    from kokoro_agent.infrastructure.schema import apply_agent_schema

    async with connect_pg(database_url_value) as conn:
        await apply_agent_schema(conn, "kokoro_agent", require_blank=True)


def _run(env: dict[str, str], config: dict[str, str]) -> dict[str, object]:
    import psycopg

    run_token = secrets.token_hex(12)
    tenant = f"w2-agent-{run_token}"
    prefix = f"{tenant}/"
    database = f"w2_agent_storage_{run_token}"
    sources = {"agent": _git_sha(AGENT), "storage": _git_sha(STORAGE)}
    directory = Path(tempfile.mkdtemp(prefix="kokoro-w2-agent-storage-"))
    os.chmod(directory, 0o700)
    result: dict[str, object] = {
        "result": "failed",
        "sources": sources,
        "run_id": run_token,
        "database_candidate": database,
        "bucket": config["bucket"],
        "owned_prefix": prefix,
        "evidence_dir": str(directory),
    }
    database_created = False
    database_uncertain = False
    objects_clean = False
    storage: subprocess.Popen[bytes] | None = None
    failure: BaseException | None = None
    cleanup_failure: BaseException | None = None
    cases: list[str] = []
    s3 = None
    admin = None
    try:
        s3 = _s3(env)
        admin = psycopg.connect(config["admin_url"], autocommit=True, connect_timeout=5)
        preflight_bucket(s3, config["bucket"], prefix)
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
            if cur.fetchone() is not None:
                raise SmokeError("random database already exists; refusing adoption")
            try:
                cur.execute(f'CREATE DATABASE "{database}"')
                database_created = True
            except BaseException:
                database_uncertain = True
                try:
                    cur.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s", (database,)
                    )
                    database_created = cur.fetchone() is not None
                    database_uncertain = False
                except Exception:
                    pass
                raise
        agent_url = database_url(config["admin_url"], database, "kokoro_agent")
        asyncio.run(_install_agent_schema(agent_url))
        fixture = _storage_schema_fixture(directory)
        port = _owned_port()
        base = f"http://127.0.0.1:{port}"
        agent_secret = secrets.token_hex(32)
        bff_secret = secrets.token_hex(32)
        storage_env = _storage_env(env, database, agent_secret, bff_secret, port)
        node = env["KOKORO_W2_STORAGE_NODE_BIN"]
        with (directory / "owners.log").open("xb") as log:
            os.chmod(directory / "owners.log", 0o600)
            subprocess.run(
                [
                    node,
                    str(STORAGE / "node_modules/tsx/dist/cli.mjs"),
                    "scripts/apply-schema.ts",
                ],
                cwd=fixture,
                env=storage_env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                timeout=90,
                check=True,
            )
            storage = subprocess.Popen(
                [node, str(STORAGE / "dist/main.js")],
                cwd=STORAGE,
                env=storage_env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            _wait_storage(base, storage)
            redis_parts = urlsplit(env["KOKORO_W2_REDIS_URL"])
            agent_redis_url = urlunsplit(
                (redis_parts.scheme, redis_parts.netloc, "/7", "", "")
            )
            cases = asyncio.run(
                _agent_cases(
                    agent_url,
                    agent_redis_url,
                    base,
                    env["KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"],
                    agent_secret,
                    bff_secret,
                    tenant,
                    run_token,
                )
            )
    except BaseException as exc:
        failure = exc
    try:
        _stop_owned(storage)
        if (
            database_created
            and not database_uncertain
            and s3 is not None
            and admin is not None
        ):
            cleanup_objects(s3, config["bucket"], prefix)
            objects_clean = True
            with admin.cursor() as cur:
                cur.execute(f'DROP DATABASE "{database}" WITH (FORCE)')
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
                if cur.fetchone() is not None:
                    raise SmokeError("owned database remains after drop")
            database_created = False
    except BaseException as exc:
        cleanup_failure = exc
    finally:
        if admin is not None:
            admin.close()
        if s3 is not None:
            s3.close()
    if failure or cleanup_failure:
        result.update(
            error=_safe_error(failure),
            cleanup_error=_safe_error(cleanup_failure),
            owned_database=database if database_created or database_uncertain else None,
            database_create_uncertain=database_uncertain,
            objects_clean=objects_clean,
            processes_stopped=storage is None or storage.poll() is not None,
        )
        return result
    shutil.rmtree(directory)
    return {
        "result": "passed",
        "sources": sources,
        "cases": cases,
        "run_id": run_token,
        "owned_database_removed": True,
        "owned_objects_removed": True,
    }


def _git_sha(path: Path) -> str:
    sha = subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True, timeout=5
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"],
        text=True,
        timeout=5,
    )
    if dirty:
        raise SmokeError(f"{path.name} worktree is not frozen")
    return sha


def _safe_error(exc: BaseException | None) -> str | None:
    if exc is None:
        return None
    if isinstance(exc, SmokeError):
        return str(exc)
    return type(exc).__name__


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="validate shape only; do not contact providers",
    )
    args = parser.parse_args()
    try:
        config = check_configuration(dict(os.environ))
        if args.check_config:
            print("Agent Storage configuration shape valid; provider not contacted")
            return 0
        if (
            not (STORAGE / "dist/main.js").is_file()
            or not (STORAGE / "node_modules/tsx/dist/cli.mjs").is_file()
        ):
            raise SmokeError("Storage compiled runtime/dependencies missing")
        node_version = subprocess.check_output(
            [os.environ["KOKORO_W2_STORAGE_NODE_BIN"], "--version"],
            text=True,
            timeout=5,
        ).strip()
        if not node_version.startswith("v24."):
            raise SmokeError("Storage smoke requires Node 24")
        report = _run(dict(os.environ), config)
    except Exception as exc:
        report = {"result": "failed", "error": _safe_error(exc)}
    print(
        json.dumps(report, sort_keys=True),
        file=sys.stdout if report["result"] == "passed" else sys.stderr,
    )
    return 0 if report["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compose real IAM, Web, BFF and Agent worker for one Product Chat turn."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass, field
from http.server import ThreadingHTTPServer
from io import BytesIO
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from threading import Thread
import time
from typing import BinaryIO
from urllib.parse import unquote, urlsplit
from uuid import uuid4

E2E = Path(__file__).resolve().parent
if str(E2E) not in sys.path:
    sys.path.insert(0, str(E2E))

if __package__:
    from . import run_bff_agent_worker_smoke as worker
    from . import run_web_bff_iam_product_session_smoke as product
else:
    import run_bff_agent_worker_smoke as worker
    import run_web_bff_iam_product_session_smoke as product


SmokeError = worker.SmokeError
ROOT = worker.ROOT
WEB = product.WEB
BFF = worker.BFF
IAM = product.IAM
AGENT = worker.AGENT
EXPECTED_RELEASES = {
    "kokoro-app": "210ddfdd77f24143a0ed0617e2ecf1089bcf513c",
    "kokoro-bff": "84a560abeac5b7a63f32d7064abdde849ab33cf9",
    "kokoro-iam": "b35a9a5301219654ea344c03407fd355f58c481e",
    "kokoro-agent": "520ec181a101298b4f336aad273ce003b2735955",
}


def _read_bounded_chunked(
    stream: BinaryIO, *, max_bytes: int = product.old.MAX_BODY
) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        line = stream.readline(130)
        if (
            not line.endswith(b"\r\n")
            or len(line) > 128
            or re.fullmatch(rb"[0-9A-Fa-f]{1,8}\r\n", line) is None
        ):
            raise SmokeError("chunked proxy body was malformed")
        size = int(line[:-2], 16)
        if size == 0:
            if stream.readline(3) != b"\r\n":
                raise SmokeError("chunked proxy trailers are not allowed")
            return b"".join(chunks)
        total += size
        if total > max_bytes:
            raise SmokeError("chunked proxy body exceeded its limit")
        chunk = stream.read(size)
        if len(chunk) != size or stream.read(2) != b"\r\n":
            raise SmokeError("chunked proxy body was truncated")
        chunks.append(chunk)


class BoundedProxyHandler(product.old.ProxyHandler):
    def forward(self) -> None:
        content_lengths = self.headers.get_all("content-length") or []
        if len(content_lengths) > 1 or (
            content_lengths
            and (
                re.fullmatch(r"[0-9]+", content_lengths[0]) is None
                or len(content_lengths[0]) > len(str(product.old.MAX_BODY))
                or int(content_lengths[0]) > product.old.MAX_BODY
            )
        ):
            self.send_error(413)
            return
        transfer_encoding = self.headers.get_all("transfer-encoding") or []
        if not transfer_encoding:
            super().forward()
            return
        if (
            len(transfer_encoding) != 1
            or transfer_encoding[0].strip().lower() != "chunked"
            or self.headers.get("content-length") is not None
        ):
            self.send_error(413)
            return
        try:
            body = _read_bounded_chunked(self.rfile)
        except SmokeError:
            self.send_error(413)
            return
        del self.headers["transfer-encoding"]
        self.headers["content-length"] = str(len(body))
        self.rfile = BytesIO(body)
        super().forward()


class BoundedObservingProxy(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        upstream_port: int,
        *,
        credentials: product.previous.CredentialRegistry,
    ) -> None:
        super().__init__(("127.0.0.1", 0), BoundedProxyHandler)
        self.upstream_port = upstream_port
        self.web_host = None
        self.tls_web = False
        self.observed: list[tuple[str, str]] = []
        self.credentials = credentials
        self.thread = Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.shutdown()
        self.server_close()
        self.thread.join(timeout=5)


def _web_json(
    response: product.BrowserResponse, expected_status: int, case: str
) -> dict[str, object]:
    if response.status != expected_status:
        raise SmokeError(
            f"{case} HTTP {response.status}, code {product.safe_error_code(response)}"
        )
    return product._product_chat_response_body(response, expected_status)


def _web_error(
    response: product.BrowserResponse, expected_status: int, code: str, case: str
) -> None:
    body = product._product_chat_response_body(response, expected_status)
    worker._error(response.status, body, expected_status, code, case)


def _parse_web_sse(response: product.BrowserResponse) -> list[dict[str, object]]:
    if response.status != 200 or not response.headers.get(
        "content-type", ""
    ).startswith("text/event-stream"):
        raise SmokeError("Web AG-UI replay response drift")
    cache = {
        directive.strip().lower()
        for directive in response.headers.get("cache-control", "").split(",")
    }
    if not {"private", "no-store"}.issubset(cache) or "public" in cache:
        raise SmokeError("Web AG-UI replay cache policy invalid")
    try:
        text = response.body.decode()
    except UnicodeDecodeError:
        raise SmokeError("Web AG-UI replay was not UTF-8") from None
    frames: list[dict[str, object]] = []
    for block in text.split("\n\n"):
        values: dict[str, str] = {}
        for line in block.splitlines():
            name, separator, value = line.partition(":")
            if separator and name in {"id", "data"}:
                values[name] = value.lstrip()
        if "id" not in values or "data" not in values:
            continue
        try:
            event = json.loads(values["data"])
        except json.JSONDecodeError:
            raise SmokeError("Web AG-UI frame JSON was invalid") from None
        if not isinstance(event, dict):
            raise SmokeError("Web AG-UI event object required")
        frames.append({"id": values["id"], "event": event})
    if not frames or len({frame["id"] for frame in frames}) != len(frames):
        raise SmokeError("Web AG-UI replay cursor evidence was incomplete")
    return frames


@dataclass(slots=True)
class AuthenticatedChatAction:
    resources: worker.OwnedResources
    start_worker: Callable[[], None]
    database_url: str
    web_origin: str
    conversation_id: str
    idempotency_key: str
    content: str
    changed_content: str
    expected_reply: str
    timeout: float
    result: dict[str, object] = field(default_factory=dict, init=False)

    def __call__(self, request: product.AuthenticatedRequest) -> str:
        path = f"/api/session/sessions/{self.conversation_id}/messages"

        def create(content: str) -> product.BrowserResponse:
            return request(
                path,
                method="POST",
                json_body={"content": content},
                origin=self.web_origin,
                idempotency_key=self.idempotency_key,
                accept="application/json",
            )

        receipt = _web_json(create(self.content), 202, "Web first message")
        run_id = receipt.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise SmokeError("Web first-message receipt identity missing")
        self.resources.register_agent_keys(self.conversation_id, run_id)
        initial = worker._first_turn_facts(
            self.resources, self.database_url, self.conversation_id
        )
        if (
            initial.get("conversation_count") != 1
            or initial.get("message_count") != 2
            or initial.get("assistant_status") != "pending"
            or initial.get("outbox_count") != 1
            or initial.get("outbox_status") not in {"pending", "retryable"}
            or initial.get("expected_run") != run_id
        ):
            raise SmokeError("Web first-turn durable transaction evidence drift")
        replay = _web_json(create(self.content), 202, "Web idempotent replay")
        if replay != receipt:
            raise SmokeError("Web same-key replay changed the receipt")
        _web_error(
            create(self.changed_content),
            409,
            "idempotency_conflict",
            "Web changed replay",
        )
        self.start_worker()

        snapshot_path = f"/api/session/sessions/{self.conversation_id}"
        deadline = time.monotonic() + self.timeout
        snapshot: dict[str, object] | None = None
        while time.monotonic() < deadline:
            candidate = _web_json(
                request(snapshot_path, accept="application/json"),
                200,
                "Web terminal snapshot",
            )
            messages = candidate.get("messages")
            assistants = (
                [
                    message
                    for message in messages
                    if isinstance(message, dict) and message.get("role") == "assistant"
                ]
                if isinstance(messages, list)
                else []
            )
            if (
                len(assistants) == 1
                and assistants[0].get("status") == "completed"
                and assistants[0].get("content") == self.expected_reply
                and isinstance(candidate.get("event_watermark"), str)
            ):
                snapshot = candidate
                break
            time.sleep(0.25)
        if snapshot is None:
            raise SmokeError("Web terminal snapshot did not converge")
        messages = snapshot.get("messages")
        if not isinstance(messages, list) or len(messages) != 2:
            raise SmokeError("Web snapshot did not contain exactly one turn")
        reloaded = _web_json(
            request(snapshot_path, accept="application/json"),
            200,
            "Web reloaded snapshot",
        )
        if reloaded.get("messages") != messages or reloaded.get(
            "event_watermark"
        ) != snapshot.get("event_watermark"):
            raise SmokeError("Web reload duplicated or lost durable facts")
        frames = _parse_web_sse(
            request(
                f"{snapshot_path}/events",
                accept="text/event-stream",
            )
        )
        frame_types = [
            frame["event"].get("type")
            for frame in frames
            if isinstance(frame.get("event"), dict)
        ]
        if (
            "RUN_STARTED" not in frame_types
            or "RUN_FINISHED" not in frame_types
            or frames[-1]["id"] != snapshot.get("event_watermark")
        ):
            raise SmokeError("Web durable AG-UI replay evidence drift")
        sql_evidence = worker._final_sql_evidence(
            self.resources, self.database_url, self.conversation_id, run_id
        )
        if (
            sql_evidence.get("bff_outbox_status") != "succeeded"
            or sql_evidence.get("bff_assistant_status") != "completed"
            or sql_evidence.get("agent_terminal") is not True
            or sql_evidence.get("agent_dispatch_status") != "claimed"
            or sql_evidence.get("agent_completed_assistants") != 1
        ):
            raise SmokeError("Web worker durable SQL evidence drift")
        self.result = {
            "conversation_id": self.conversation_id,
            "run_id": run_id,
            "event_watermark": snapshot["event_watermark"],
            "agui_frame_types": frame_types,
            "sql_evidence": sql_evidence,
        }
        return self.conversation_id


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-admin-url", required=True)
    parser.add_argument("--web-iam-redis-url", required=True)
    parser.add_argument("--bff-redis-url", required=True)
    parser.add_argument("--agent-redis-url", required=True)
    parser.add_argument("--iam-node-bin", required=True)
    parser.add_argument("--node22-bin", required=True)
    parser.add_argument("--uv-bin", default="uv")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    if urlsplit(args.postgres_admin_url).scheme not in {"postgres", "postgresql"}:
        parser.error("explicit PostgreSQL admin URL required")
    redis_urls = (
        args.web_iam_redis_url,
        args.bff_redis_url,
        args.agent_redis_url,
    )
    try:
        redis_databases = [worker.redis_database_number(url) for url in redis_urls]
    except SmokeError as error:
        parser.error(str(error))
    if len(set(redis_databases)) != len(redis_databases):
        parser.error("Web/IAM, BFF and Agent Redis databases must be distinct")
    for name in ("iam_node_bin", "node22_bin"):
        value = Path(getattr(args, name)).expanduser().resolve()
        if not value.is_file() or not os.access(value, os.X_OK):
            parser.error(f"{name} must be an executable Node binary")
        setattr(args, name, value)
    uv_value = (
        str(Path(args.uv_bin).expanduser().resolve())
        if os.path.sep in args.uv_bin
        else shutil.which(args.uv_bin)
    )
    uv = Path(uv_value) if uv_value is not None else Path("")
    if not uv.is_file() or not os.access(uv, os.X_OK):
        parser.error("uv-bin must resolve to an executable")
    if args.timeout < 20 or args.timeout > 600:
        parser.error("timeout must be between 20 and 600 seconds")
    args.uv_bin = uv
    return args


def verify_release_inputs() -> dict[str, dict[str, object]]:
    sources: dict[str, dict[str, object]] = {}
    for name, repo, gitlink in (
        ("kokoro-app", WEB, "apps/kokoro-app"),
        ("kokoro-bff", BFF, "apps/kokoro-bff"),
        ("kokoro-iam", IAM, "apps/kokoro-iam"),
        ("kokoro-agent", AGENT, "apps/kokoro-agent"),
    ):
        sources[name] = product.session.verify_source(
            repo, EXPECTED_RELEASES[name], gitlink
        )
    return sources


def _cleanup_web_redis(
    redis_url: str,
    web_origin: str,
    resources: product.runtime.OwnedResources,
    before: set[str],
) -> None:
    extras = product.web_redis_keys(redis_url, web_origin, resources) - before
    if extras:
        resources.command(
            ["redis-cli", "-e", "-u", redis_url, "UNLINK", *sorted(extras)]
        )
    if product.web_redis_keys(redis_url, web_origin, resources) != before:
        raise SmokeError("Web Redis cleanup incomplete")


def _stop_processes_then_cleanup_data(
    processes: list[subprocess.Popen[bytes]],
    data_cleanups: list[tuple[str, Callable[[], None]]],
) -> list[str]:
    process_stop_failed = False
    for process in reversed(processes):
        try:
            worker.runtime.stop_owned_process(process)
        except Exception:
            process_stop_failed = True
    if process_stop_failed:
        return [
            "owned process cleanup failed; all owned data cleanup deferred; "
            "ownership retained"
        ]
    failures: list[str] = []
    for label, cleanup in data_cleanups:
        try:
            cleanup()
        except Exception:
            failures.append(label)
    return failures


def _cleanup_bff_agent_resources(resources: worker.OwnedResources) -> None:
    resources.cleanup()
    resources.verify_clean()


def run_smoke(args: argparse.Namespace) -> dict[str, object]:
    sources = verify_release_inputs()
    run_id = secrets.token_hex(12)
    web_origin = f"https://web-{run_id}.example.test"
    host_name = urlsplit(web_origin).hostname
    if host_name is None:
        raise SmokeError("Web origin host missing")
    resources = worker.OwnedResources(
        args.postgres_admin_url,
        args.bff_redis_url,
        args.agent_redis_url,
        run_id,
    )
    infra = product.runtime.OwnedResources(
        args.postgres_admin_url,
        args.web_iam_redis_url,
        run_id,
    )
    iam_resource_id = str(uuid4())
    iam_identity = product.named_iam_identity(iam_resource_id)
    iam_owner_token = secrets.token_hex(16)
    bff_secret = secrets.token_urlsafe(32)
    agent_secret = secrets.token_urlsafe(32)
    model_secret = secrets.token_urlsafe(32)
    reply = f"Durable Web worker reply {run_id}."
    credentials = product.previous.CredentialRegistry(
        args.postgres_admin_url,
        args.web_iam_redis_url,
        args.bff_redis_url,
        args.agent_redis_url,
    )
    credentials.add(iam_owner_token, bff_secret, agent_secret, model_secret)
    for raw in (
        args.postgres_admin_url,
        args.web_iam_redis_url,
        args.bff_redis_url,
        args.agent_redis_url,
    ):
        password = unquote(urlsplit(raw).password or "")
        if len(password) >= 12:
            credentials.add(password)
    iam_env = product.session.node_environment(
        args.iam_node_bin, "v24.20.0", args.node22_bin.parent
    )
    node_env = worker._node_environment(args.node22_bin)
    web_env = product.session.node_environment(
        args.node22_bin, "v22.22.2", args.node22_bin.parent
    )
    agent_env = worker._agent_environment([args.uv_bin.parent])
    processes: list[subprocess.Popen[bytes]] = []
    proxies: list[product.Proxy | BoundedObservingProxy] = []
    reader: product.session.ProtocolReader | None = None
    before_web: set[str] | None = None
    iam_attempted = False
    stage = "preflight"
    observation: worker.FixtureObservation | None = None
    chat_result: dict[str, object] = {}
    cleanup_failures: list[str] = []
    primary_error: BaseException | None = None

    with tempfile.TemporaryDirectory(
        prefix="kokoro-web-chat-worker-", dir=ROOT.parent
    ) as temporary:
        temporary_path = Path(temporary)
        log_path = temporary_path / "process.log"
        workspace = temporary_path / "workspace"
        workspace.mkdir()
        with log_path.open("w+b") as log:
            try:
                stage = "dependency preflight"
                worker.command_output(
                    ["psql", args.postgres_admin_url, "-X", "-Atc", "SELECT 1"]
                )
                if (
                    infra.command(
                        [
                            "redis-cli",
                            "-e",
                            "-u",
                            args.web_iam_redis_url,
                            "PING",
                        ]
                    ).strip()
                    != "PONG"
                ):
                    raise SmokeError("Web/IAM Redis unavailable")
                resources.claim_redis()
                database_url = resources.create_database()

                stage = "BFF exact-source build"
                if (
                    worker.run_owned_command(
                        [str(args.node22_bin.parent / "corepack"), "pnpm", "build"],
                        cwd=BFF,
                        env=node_env,
                        log=log,
                        timeout=120,
                    )
                    != 0
                ):
                    raise SmokeError("BFF current-source build failed")
                bff_env = {
                    **node_env,
                    "KOKORO_BFF_POSTGRES_URL": worker.bff_owner_database_url(
                        database_url
                    ),
                    "KOKORO_BFF_REDIS_URL": args.bff_redis_url,
                }
                stage = "BFF schema install"
                if (
                    worker.run_owned_command(
                        [
                            str(args.node22_bin.parent / "corepack"),
                            "pnpm",
                            "db:apply-schema",
                        ],
                        cwd=BFF,
                        env=bff_env,
                        log=log,
                        timeout=90,
                    )
                    != 0
                ):
                    raise SmokeError("BFF schema installation failed")
                common_agent_env = {
                    **agent_env,
                    "KOKORO_REDIS_URL": args.agent_redis_url,
                    "KOKORO_AGENT_DATABASE_URL": database_url,
                    "KOKORO_AGENT_DATABASE_SCHEMA": "kokoro_agent",
                    "KOKORO_INTERNAL_SECRET_AGENT": agent_secret,
                }
                stage = "Agent schema install"
                if (
                    worker.run_owned_command(
                        [str(args.uv_bin), "run", "kokoro-agent-db-apply-schema"],
                        cwd=AGENT,
                        env=common_agent_env,
                        log=log,
                        timeout=90,
                    )
                    != 0
                ):
                    raise SmokeError("Agent schema installation failed")

                stage = "IAM host"
                if product.iam_owned_inventory(infra, iam_identity) != (set(), set()):
                    raise SmokeError("IAM named resources already exist")
                iam_env.update(
                    {
                        "IAM_TEST_ADMIN_URL": args.postgres_admin_url,
                        "IAM_TEST_REDIS_URL": args.web_iam_redis_url,
                        "IAM_TEST_WEB_ORIGIN": web_origin,
                        "IAM_TEST_RESOURCE_ID": iam_resource_id,
                        "IAM_TEST_RESOURCE_OWNER_TOKEN": iam_owner_token,
                        "NODE_ENV": "test",
                    }
                )
                iam_attempted = True
                iam = subprocess.Popen(
                    [str(args.iam_node_bin), "--import", "tsx", str(product.HOST)],
                    cwd=IAM,
                    env=iam_env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=log,
                    start_new_session=True,
                    bufsize=0,
                )
                processes.append(iam)
                if iam.stdout is None:
                    raise SmokeError("IAM host protocol absent")
                reader = product.session.ProtocolReader(iam.stdout.fileno())
                ready = product.validate_ready(reader.record(), web_origin)
                if (ready.database_name, ready.redis_prefix) != (
                    iam_identity.database_name,
                    iam_identity.redis_prefix,
                ):
                    raise SmokeError("IAM ready identity differs from runner ownership")
                if (
                    ready.database_name
                    not in product.iam_owned_inventory(infra, ready)[0]
                ):
                    raise SmokeError("IAM owned database absent after host ready")
                credentials.add(ready.client_secret, ready.password)
                before_web = product.web_redis_keys(
                    args.web_iam_redis_url, web_origin, infra
                )

                fixture_identity = worker.FixtureIdentity(
                    ready.tenant_id,
                    agent_secret,
                    model_secret,
                    reply,
                )
                with worker.system_model_fixtures(fixture_identity) as fixtures:
                    observation = fixtures.observation
                    agent_port = product.runtime.free_port()
                    bff_port = product.runtime.free_port()
                    agent_base = f"http://127.0.0.1:{agent_port}"
                    bff_base = f"http://127.0.0.1:{bff_port}"
                    agent_http_env = {
                        **common_agent_env,
                        "KOKORO_AGENT_HTTP_HOST": "127.0.0.1",
                        "KOKORO_AGENT_HTTP_PORT": str(agent_port),
                    }
                    worker_env = {
                        **common_agent_env,
                        "KOKORO_SYSTEM_BASE_URL": fixtures.system_url,
                        "KOKORO_LITELLM_ENABLED": "1",
                        "KOKORO_LITELLM_BASE_URL": fixtures.model_url + "/v1",
                        "KOKORO_LITELLM_API_KEY": model_secret,
                        "KOKORO_DISABLE_STREAMING": "1",
                        "KOKORO_AGENT_LOCAL_SHELL_ROOT": str(workspace),
                        "KOKORO_MCP_EGRESS_MODE": "deny",
                    }
                    stage = "BFF startup"
                    bff_env.update(
                        {
                            "KOKORO_BFF_HOST": "127.0.0.1",
                            "KOKORO_BFF_PORT": str(bff_port),
                            "KOKORO_BFF_MODE": "live",
                            "KOKORO_BFF_SHARED_SECRET": bff_secret,
                            "KOKORO_IAM_BASE_URL": ready.base_url,
                            "KOKORO_IAM_ISSUER_URL": ready.issuer_url,
                            "KOKORO_IAM_WEB_ORIGIN": web_origin,
                            "KOKORO_IAM_WEB_CALLBACK_URI": ready.redirect_uri,
                            "KOKORO_IAM_WEB_POST_LOGOUT_URI": ready.post_logout_redirect_uri,
                            "KOKORO_AGENT_ENABLED": "true",
                            "KOKORO_AGENT_BASE_URL": agent_base,
                            "KOKORO_INTERNAL_SECRET_BFF": agent_secret,
                            "KOKORO_TENANT_ID": ready.tenant_id,
                            "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
                            "KOKORO_UPSTREAM_TIMEOUT_MS": "5000",
                        }
                    )
                    bff_process = worker._start_process(
                        [str(args.node22_bin), str(BFF / "dist" / "main.js")],
                        cwd=BFF,
                        env=bff_env,
                        log=log,
                    )
                    processes.append(bff_process)
                    worker._wait_ready(bff_base, bff_process)
                    bff_proxy = BoundedObservingProxy(bff_port, credentials=credentials)
                    proxies.append(bff_proxy)

                    stage = "Web HTTPS startup"
                    next_root = product.isolated_next(temporary_path)
                    next_port = product.runtime.free_port()
                    web_env.update(
                        {
                            "KOKORO_WEB_ORIGIN": web_origin,
                            "KOKORO_DOMAIN": host_name,
                            "KOKORO_BFF_BASE_URL": f"http://127.0.0.1:{bff_proxy.server_port}",
                            "KOKORO_INTERNAL_SECRET_WEB_BFF": bff_secret,
                            "KOKORO_WEB_REDIS_URL": args.web_iam_redis_url,
                            "KOKORO_OIDC_CLIENT_ID": ready.client_id,
                            "KOKORO_OIDC_CLIENT_SECRET": ready.client_secret,
                            "KOKORO_WEB_AUTH_SECRET": secrets.token_hex(32),
                            "NEXTAUTH_URL": web_origin + "/api/auth",
                        }
                    )
                    credentials.add(web_env["KOKORO_WEB_AUTH_SECRET"])
                    next_process = subprocess.Popen(
                        [
                            str(args.node22_bin),
                            str(next_root / "server.cjs"),
                            str(next_port),
                            host_name,
                        ],
                        cwd=next_root,
                        env=web_env,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=log,
                        start_new_session=True,
                    )
                    processes.append(next_process)
                    web_proxy = product.Proxy(
                        next_port,
                        host_name,
                        product.certificate(temporary_path, host_name),
                    )
                    proxies.append(web_proxy)
                    stage = "Web HTTPS origin preflight"
                    deadline = time.monotonic() + 30
                    while True:
                        try:
                            fixture = product.https_browser(
                                web_proxy.server_port,
                                "/api/fixture-origin",
                                web_origin,
                            )
                            if fixture.status == 200:
                                break
                        except product.SmokeError:
                            pass
                        if (
                            time.monotonic() >= deadline
                            or next_process.poll() is not None
                        ):
                            raise SmokeError("Next origin fixture not ready")
                        time.sleep(0.1)
                    try:
                        origin_readback = json.loads(fixture.body)
                    except (ValueError, UnicodeError):
                        raise SmokeError("Next origin fixture malformed") from None
                    if origin_readback != {
                        "origin": web_origin,
                        "host": host_name,
                        "proto": "https",
                    }:
                        raise SmokeError("Next origin fixture rejected")

                    def start_agent_worker() -> None:
                        agent_http = worker._start_process(
                            [str(args.uv_bin), "run", "kokoro-agent-http"],
                            cwd=AGENT,
                            env=agent_http_env,
                            log=log,
                        )
                        processes.append(agent_http)
                        worker._wait_ready(agent_base, agent_http, path="/healthz")
                        agent_worker = worker._start_process(
                            [str(args.uv_bin), "run", "kokoro-agent-worker"],
                            cwd=AGENT,
                            env=worker_env,
                            log=log,
                        )
                        processes.append(agent_worker)

                    action = AuthenticatedChatAction(
                        resources=resources,
                        start_worker=start_agent_worker,
                        database_url=database_url,
                        web_origin=web_origin,
                        conversation_id=f"conv_{uuid4()}",
                        idempotency_key=f"web-worker:{run_id}",
                        content="Run the deterministic Web worker smoke.",
                        changed_content="Changed content must conflict.",
                        expected_reply=reply,
                        timeout=args.timeout,
                    )
                    stage = "real IAM Product Session and Web worker turn"
                    product.run_browser(
                        web_proxy.server_port,
                        web_origin,
                        ready,
                        bff_proxy.observed,
                        credentials,
                        authenticated_action=action,
                    )
                    chat_result = action.result
                    if not chat_result:
                        raise SmokeError("authenticated Web chat action did not run")
                    if (
                        observation.system_requests < 1
                        or observation.model_requests < 1
                        or observation.real_provider
                    ):
                        raise SmokeError("strict System/model fixture evidence drift")
                    log.flush()
                    product.previous.assert_log_clean(log_path, credentials.values())
            except BaseException as error:
                log.flush()
                excerpt = worker.safe_log_excerpt(log_path, set(credentials.values()))
                if isinstance(
                    error,
                    (
                        SmokeError,
                        product.SmokeError,
                        product.runtime.SmokeError,
                        product.previous.SmokeError,
                        product.session.SmokeError,
                    ),
                ):
                    primary_error = SmokeError(
                        f"{stage}: {error}\nowned log tail:\n{excerpt}"
                    )
                else:
                    primary_error = error
            finally:
                for proxy in reversed(proxies):
                    try:
                        proxy.close()
                    except Exception:
                        cleanup_failures.append("owned proxy cleanup")
                data_cleanups: list[tuple[str, Callable[[], None]]] = []
                if before_web is not None:
                    data_cleanups.append(
                        (
                            "Web Redis cleanup",
                            lambda: _cleanup_web_redis(
                                args.web_iam_redis_url,
                                web_origin,
                                infra,
                                before_web,
                            ),
                        )
                    )
                if iam_attempted:
                    data_cleanups.append(
                        (
                            "IAM resource cleanup",
                            lambda: product.reconcile_iam_identity(
                                infra, iam_identity, iam_owner_token
                            ),
                        )
                    )
                data_cleanups.append(
                    (
                        "BFF/Agent resource cleanup",
                        lambda: _cleanup_bff_agent_resources(resources),
                    )
                )
                cleanup_failures.extend(
                    _stop_processes_then_cleanup_data(processes, data_cleanups)
                )
                if reader is not None:
                    try:
                        reader.close()
                    except Exception:
                        cleanup_failures.append("IAM protocol cleanup")
                try:
                    log.flush()
                    product.previous.assert_log_clean(log_path, credentials.values())
                except Exception:
                    cleanup_failures.append("credential log scan")
    if primary_error is not None:
        if cleanup_failures:
            raise SmokeError(
                f"{primary_error}; cleanup: "
                + "; ".join(dict.fromkeys(cleanup_failures))
            ) from None
        raise primary_error
    if cleanup_failures:
        raise SmokeError("; ".join(dict.fromkeys(cleanup_failures)))
    if observation is None:
        raise SmokeError("fixture observation was unavailable")
    return {
        "status": "PASS",
        "flow": "real IAM Product Session -> Web adapter -> BFF -> real Agent worker",
        "browser_boundary": "Python CookieJar HTTPS client; not Chromium",
        "agent_worker": "real independent CLI process",
        "system_model_boundary": "strict deterministic fixtures; not a real provider",
        "sources": sources,
        "system_requests": observation.system_requests,
        "model_requests": observation.model_requests,
        "chat": chat_result,
        "owned_postgres_databases_remaining": 0,
        "owned_redis_keys_remaining": 0,
        "owned_processes_remaining": 0,
    }


def main(argv: list[str] | None = None) -> int:
    result = run_smoke(parse_args(argv))
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (
        SmokeError,
        product.SmokeError,
        product.runtime.SmokeError,
        product.previous.SmokeError,
        product.session.SmokeError,
        subprocess.SubprocessError,
        OSError,
    ) as error:
        print(f"Web Chat worker smoke failed: {error}", file=sys.stderr)
        sys.exit(1)

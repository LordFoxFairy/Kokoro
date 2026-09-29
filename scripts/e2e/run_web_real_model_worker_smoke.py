#!/usr/bin/env python3
"""One real Product Run through System, local Ollama and worker-owned delivery.

No infrastructure or model is downloaded. Existing W2 ownership owns all child
processes, PostgreSQL schemas, Redis keys and S3 cleanup, including on failure.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
from threading import Thread
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_system_owner_smoke as system
import run_web_project_resource_chromium_smoke as stack

SmokeError = stack.SmokeError
SYSTEM = stack.ROOT / "apps/kokoro-system"
DRIVER = Path(__file__).with_name("web_real_model_worker_chromium.mjs")


@dataclass(frozen=True)
class RealModelConfig:
    endpoint: str
    model: str
    system_sha: str

    def __post_init__(self) -> None:
        p = urlsplit(self.endpoint)
        if (
            p.scheme != "http"
            or p.hostname != "127.0.0.1"
            or p.port != 11434
            or p.path
            or p.query
            or p.fragment
            or p.username
            or p.password
        ):
            raise SmokeError("only existing loopback Ollama 11434 origin is admitted")
        if (
            self.model != "qwen3:8b"
            or re.fullmatch(r"[a-f0-9]{40}", self.system_sha) is None
        ):
            raise SmokeError("explicit real model and exact System source required")


def provider_preflight(config: RealModelConfig) -> dict[str, str]:
    """Read inventory only; never start Ollama or pull a model."""
    try:
        with build_opener(ProxyHandler({})).open(
            Request(config.endpoint + "/api/tags"), timeout=5
        ) as response:
            raw = response.read(1_048_577)
            if response.status != 200 or len(raw) > 1_048_576:
                raise SmokeError("Ollama inventory rejected")
        values = json.loads(raw)["models"]
        selected = [item for item in values if item.get("name") == config.model]
        if (
            len(selected) != 1
            or re.fullmatch(r"[a-f0-9]{64}", selected[0].get("digest", "")) is None
        ):
            raise SmokeError("existing exact Ollama model absent")
        return {
            "endpoint": config.endpoint,
            "model": config.model,
            "digest": selected[0]["digest"],
        }
    except (OSError, ValueError, KeyError, TypeError):
        raise SmokeError("existing Ollama inventory unavailable") from None


def validate_browser_evidence(value: dict[str, object], digest: str) -> None:
    if (
        value.get("browser") != "chromium"
        or value.get("message_post_status") != 202
        or value.get("agui_status") != 200
        or value.get("text_marker_visible") is not True
        or value.get("live_delivery") is not True
        or value.get("reload_card_count") != 1
        or value.get("download_sha256") != digest
        or value.get("member_statuses") != [404, 404, 404]
        or any(
            not isinstance(value.get(key), str) or not value[key]
            for key in ("conversation_id", "run_id", "artifact_id", "asset_id")
        )
    ):
        raise SmokeError("real model browser stages incomplete")


class ObservingProxy(ThreadingHTTPServer):
    """Bounded byte-preserving HTTP observer; never produces successful replies."""

    daemon_threads = True

    def __init__(
        self,
        upstream: str,
        *,
        kind: str,
        token: str,
        tenant: str,
        model: str,
        revision: str,
        timeout: float,
    ):
        super().__init__(("127.0.0.1", 0), _ProxyHandler)
        self.upstream = urlsplit(upstream)
        self.kind, self.token, self.tenant = kind, token, tenant
        self.model, self.revision, self.timeout = model, revision, timeout
        self.requests = self.successes = self.response_bytes = 0
        self.errors: list[str] = []
        self.thread = Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.server_port}"

    def close(self) -> None:
        self.shutdown()
        self.server_close()
        self.thread.join(timeout=5)


class _ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        pass

    def do_POST(self) -> None:
        owner = self.server
        assert isinstance(owner, ObservingProxy)
        upstream = None
        try:
            length = int(self.headers.get("content-length", "0"))
            if not 0 < length <= 1_048_576:
                raise ValueError("request size")
            raw = self.rfile.read(length)
            body = json.loads(raw)
            if self.headers.get("authorization") != f"Bearer {owner.token}":
                raise ValueError("credential")
            if owner.kind == "system":
                if (
                    self.path != "/v1/system/model-catalog/resolve"
                    or body != {"feature_key": "chat"}
                    or self.headers.get("x-kokoro-tenant-id") != owner.tenant
                    or self.headers.get("x-kokoro-service") != "kokoro-agent"
                ):
                    raise ValueError("route identity")
            elif (
                self.path != "/v1/chat/completions"
                or body.get("model") != owner.model
                or body.get("stream") is not True
            ):
                raise ValueError("model stream")
            owner.requests += 1
            upstream = http.client.HTTPConnection(
                owner.upstream.hostname, owner.upstream.port, timeout=owner.timeout
            )
            headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower() not in {"host", "connection", "transfer-encoding"}
            }
            upstream.request("POST", self.path, raw, headers)
            response = upstream.getresponse()
            self.send_response(response.status)
            self.send_header(
                "content-type",
                response.getheader("content-type", "application/octet-stream"),
            )
            self.send_header("connection", "close")
            self.end_headers()
            total = 0
            captured = bytearray()
            while chunk := response.read1(8192):
                total += len(chunk)
                if total > 8_388_608:
                    raise ValueError("response size")
                if owner.kind == "system":
                    captured.extend(chunk)
                self.wfile.write(chunk)
                self.wfile.flush()
            owner.response_bytes += total
            if response.status != 200:
                raise ValueError("upstream status")
            if owner.kind == "system":
                route = json.loads(captured)["data"]
                if (
                    route["revision_id"] != owner.revision
                    or route["gateway_model_name"] != owner.model
                    or route["feature_key"] != "chat"
                ):
                    raise ValueError("route source")
            owner.successes += 1
        except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException):
            owner.errors.append("upstream_observation_failed")
        finally:
            self.close_connection = True
            if upstream is not None:
                upstream.close()


def _query(infra, database_url: str, query: str) -> object:
    return json.loads(
        infra.command(
            ["psql", database_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", query]
        ).strip()
    )


def register_owned_worker_runs(infra, database_url: str, ownership) -> None:
    """Allow cleanup of the one real run even when Chromium reports a failure."""
    rows = _query(
        infra,
        database_url,
        """SELECT coalesce(json_agg(json_build_object(
          'run',run_id,'session',request_json::jsonb->>'session_id')),
          '[]'::json) FROM kokoro_agent.kokoro_agent_run""",
    )
    if not isinstance(rows, list) or len(rows) > 1:
        raise SmokeError("real model owned Run inventory drift")
    for row in rows:
        if not isinstance(row, dict):
            raise SmokeError("real model owned Run identity drift")
        ownership.register_run(row.get("session"), row.get("run"))


def worker_owns_lease(owner: object, process_group: int) -> bool:
    if not isinstance(owner, str):
        return False
    prefix = socket.gethostname() + "-"
    if not owner.startswith(prefix) or not owner[len(prefix) :].isdigit():
        return False
    try:
        return os.getpgid(int(owner[len(prefix) :])) == process_group
    except OSError:
        return False


def durable_evidence(
    infra,
    database_url: str,
    browser: dict[str, object],
    tenant: str,
    worker_pid: int,
    digest: str,
) -> dict[str, object]:
    run, conversation, artifact, asset = (
        str(browser[key])
        for key in ("run_id", "conversation_id", "artifact_id", "asset_id")
    )
    if any(
        re.fullmatch(r"[A-Za-z0-9_:-]{1,191}", v) is None
        for v in (run, conversation, artifact, asset, tenant)
    ):
        raise SmokeError("SQL evidence identity rejected")
    # Each query stays in one owner schema. These are read-only test assertions.
    agent = _query(
        infra,
        database_url,
        f"""SELECT json_build_object(
      'terminal',terminal,'generation',lease_generation,'owner',owner,
      'file_writes',(SELECT count(*) FROM kokoro_agent.kokoro_agent_tool_journal w
        WHERE w.run_id=r.run_id AND name='write_file' AND status='succeeded' AND NOT is_error),
      'deliveries',(SELECT count(*) FROM kokoro_agent.kokoro_agent_tool_journal j
        WHERE j.run_id=r.run_id AND name='deliver' AND status='succeeded' AND NOT is_error
        AND result::jsonb->>'artifact_id'='{artifact}' AND result::jsonb->>'asset_id'='{asset}'
        AND result::jsonb->>'content_hash'='{digest}'),
      'events',(SELECT json_agg(kind ORDER BY durable_seq) FROM kokoro_agent.kokoro_agent_run_outbox e
        WHERE e.run_id=r.run_id AND status='published'))
      FROM kokoro_agent.kokoro_agent_run r WHERE run_id='{run}' AND tenant_id='{tenant}'""",
    )
    events = agent.get("events", []) if isinstance(agent, dict) else []
    if (
        not isinstance(agent, dict)
        or agent.get("terminal") is not True
        or agent.get("generation", 0) < 1
        or not worker_owns_lease(agent.get("owner"), worker_pid)
        or agent.get("deliveries") != 1
        or agent.get("file_writes", 0) < 1
        or events.count("delivery.created") != 1
        or events.count("run.completed") != 1
        or "run.failed" in events
        or events.index("delivery.created") > events.index("run.completed")
    ):
        raise SmokeError("standard worker lease/journal/terminal evidence drift")
    storage = _query(
        infra,
        database_url,
        f"""SELECT json_build_object('count',count(*))
      FROM kokoro_storage.storage_artifact a JOIN kokoro_storage.storage_asset s
      ON s.tenant_id=a.tenant_id AND s.asset_id=a.asset_id AND s.scope_id=a.scope_id
      WHERE a.tenant_id='{tenant}' AND a.scope_id='{conversation}' AND a.artifact_id='{artifact}'
      AND a.asset_id='{asset}' AND a.source_run_id='{run}' AND a.state='final'
      AND a.finalized_sha256='{digest}' AND s.scan_state='clean'""",
    )
    if storage != {"count": 1}:
        raise SmokeError("real worker Storage FINAL CLEAN digest drift")
    return {"agent": agent, "storage": storage}


def real_scenario(config: RealModelConfig, **context) -> dict[str, object]:
    c = context
    source = stack._verify_source(SYSTEM, config.system_sha, "apps/kokoro-system")
    provider = provider_preflight(config)
    directory, log, infra = c["directory"], c["log"], c["infra"]
    node = c["node24"]
    system_root = stack._isolated_owner(SYSTEM, directory, "system")
    # System's current canonical installer owns public; all other owners in this
    # same test-owned database use independent explicit schemas.
    system_db = c["owner_db_url"]
    token = secrets.token_urlsafe(32)
    model_key = secrets.token_urlsafe(32)
    c["credentials"].add(token, model_key)
    port = stack.product.runtime.free_port()
    system_base = f"http://127.0.0.1:{port}"
    env = stack.product.session.node_environment(node, "v24.20.0", c["node"].parent)
    env.update(
        DATABASE_URL=system_db,
        REDIS_URL=c["system_redis_url"],
        KOKORO_SYSTEM_REDIS_NAMESPACE=infra.redis_prefix + "system",
        KOKORO_SYSTEM_HOST="127.0.0.1",
        KOKORO_SYSTEM_PORT=str(port),
        KOKORO_SYSTEM_BFF_SERVICE_TOKEN=token,
        KOKORO_SYSTEM_AGENT_SERVICE_TOKEN=c["agent_secret"],
        KOKORO_SYSTEM_ADMIN_SERVICE_TOKEN=token,
        KOKORO_SYSTEM_MODEL_HEALTH_MAX_AGE_MS="300000",
        PGOPTIONS="-c search_path=public,pg_catalog -c timezone=UTC",
    )
    for command in (
        [
            str(node),
            str(system_root / "node_modules/tsx/dist/cli.mjs"),
            "scripts/apply-schema.ts",
        ],
        [
            str(node),
            str(system_root / "node_modules/typescript/bin/tsc"),
            "-p",
            "tsconfig.build.json",
        ],
    ):
        stack._run_owner_command(
            command, cwd=system_root, env=env, log=log, timeout=120
        )
    system_process = stack.product.runtime.start_process(node, system_root, env, log)
    c["processes"].append(system_process)
    system.wait_ready(system_base, system_process)
    route = system.seed_control_plane(
        system_base,
        c["ready"].tenant_id,
        token,
        c["run_id"],
        feature_key="chat",
        provider="ollama",
        model_name=config.model,
    )
    system_proxy = ObservingProxy(
        system_base,
        kind="system",
        token=c["agent_secret"],
        tenant=c["ready"].tenant_id,
        model=config.model,
        revision=route["revision_id"],
        timeout=c["timeout"],
    )
    c["proxies"].append(system_proxy)
    model_proxy = ObservingProxy(
        config.endpoint,
        kind="model",
        token=model_key,
        tenant=c["ready"].tenant_id,
        model=config.model,
        revision=route["revision_id"],
        timeout=c["timeout"],
    )
    c["proxies"].append(model_proxy)
    worker_env = {
        **c["agent_env"],
        "KOKORO_SYSTEM_BASE_URL": system_proxy.origin,
        "KOKORO_LITELLM_ENABLED": "1",
        "KOKORO_LITELLM_BASE_URL": model_proxy.origin + "/v1",
        "KOKORO_LITELLM_API_KEY": model_key,
        "KOKORO_DISABLE_STREAMING": "0",
        "KOKORO_STORAGE_BASE_URL": c["storage_base"],
        "KOKORO_STORAGE_OBJECT_ORIGIN": c["object_origin"],
        "KOKORO_STORAGE_SERVICE_SECRET": c["agent_secret"],
        "KOKORO_MCP_EGRESS_MODE": "deny",
    }
    process = subprocess.Popen(
        [
            os.environ.get("KOKORO_W2_UV_BIN", "uv"),
            "run",
            "--frozen",
            "--no-sync",
            "kokoro-agent-worker",
        ],
        cwd=stack.AGENT,
        env=worker_env,
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    c["processes"].append(process)
    content = f"KOKORO_REAL_MODEL_{c['run_id']}"
    digest = hashlib.sha256(content.encode()).hexdigest()
    payload = {
        "web_origin": c["origin"],
        "web_root": str(stack.WEB),
        "screenshot": str(c["screenshot"]),
        "web_certificate": str(c["certificate"]),
        "owner_email": c["ready"].email,
        "owner_password": c["ready"].password,
        "member_email": c["member"].email,
        "member_password": c["member"].password,
        "marker": content,
        "content_sha256": digest,
        "timeout_ms": int(c["timeout"] * 1000),
    }
    browser_process = subprocess.Popen(
        [str(c["node"]), str(DRIVER)],
        cwd=stack.ROOT,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    c["processes"].append(browser_process)
    try:
        output, errors = browser_process.communicate(
            json.dumps(payload), timeout=c["timeout"] + 60
        )
    except subprocess.TimeoutExpired:
        raise SmokeError("real model Chromium deadline") from None
    finally:
        register_owned_worker_runs(infra, c["agent_db_url"], c["agent_redis"])
    if browser_process.returncode != 0:
        # Driver emits only stage names, not provider payloads or credentials.
        phase = errors.strip()
        if re.fullmatch(r"REAL_MODEL_FAILURE:[a-z0-9-]+", phase) is None:
            phase = "REAL_MODEL_FAILURE:driver"
        raise SmokeError(phase)
    try:
        browser = json.loads(output)
    except ValueError:
        raise SmokeError("real model browser evidence malformed") from None
    validate_browser_evidence(browser, digest)
    durable = durable_evidence(
        infra, c["agent_db_url"], browser, c["ready"].tenant_id, process.pid, digest
    )
    if (
        system_proxy.errors
        or model_proxy.errors
        or system_proxy.successes != 1
        or model_proxy.successes < 2
        or model_proxy.response_bytes == 0
    ):
        raise SmokeError("actual route/model observations incomplete")
    return {
        **browser,
        "system_source": source,
        "provider": provider,
        "system_route": route,
        "system_requests": system_proxy.requests,
        "model_requests": model_proxy.requests,
        "model_successes": model_proxy.successes,
        "durable": durable,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ollama-origin", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--expected-system-sha", required=True)
    model_args, rest = parser.parse_known_args(argv)
    config = RealModelConfig(
        model_args.ollama_origin, model_args.model, model_args.expected_system_sha
    )
    args = stack.parse_args(rest)
    env = stack.check_configuration(dict(os.environ))
    if args.check_config:
        print("real model shape valid; no provider contacted")
        return 0
    stack._verify_source(SYSTEM, config.system_sha, "apps/kokoro-system")
    result = stack._run_smoke(
        args, env, real_model_scenario=lambda **kwargs: real_scenario(config, **kwargs)
    )
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeError as error:
        print(f"Real model smoke failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None

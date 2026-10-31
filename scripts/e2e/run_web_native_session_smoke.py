#!/usr/bin/env python3
"""Exercise the real Web native-session path through BFF and IAM."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit

import capability_bff_smoke_runtime as runtime
from bff_owner_schema import bff_owner_database_url
import run_bff_iam_session_smoke as session
import run_web_bff_iam_oidc_smoke as web

ROOT = Path(__file__).resolve().parents[2]
IAM = ROOT / "apps/kokoro-iam"
BFF = ROOT / "apps/kokoro-bff"
APP = ROOT / "apps/kokoro-app"
IAM_HOST = IAM / "test/fixtures/bff-session-admission-host.ts"


class SmokeError(RuntimeError):
    pass


@dataclass(frozen=True)
class NativeReceipt:
    cookie: str
    credential_file: str
    iam_web_origin: str


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("postgres-admin-url", "redis-url", "iam-node-bin", "bff-node-bin", "web-node-bin"):
        parser.add_argument("--" + name, required=True)
    for name in ("expected-iam-sha", "expected-bff-sha", "expected-app-sha"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--allow-unpublished-iam-gitlink", action="store_true")
    args = parser.parse_args(argv)
    if urlsplit(args.postgres_admin_url).scheme != "postgresql" or urlsplit(args.redis_url).scheme not in {"redis", "rediss"}:
        parser.error("explicit PostgreSQL and Redis URLs required")
    for name in ("iam_node_bin", "bff_node_bin", "web_node_bin"):
        node = Path(getattr(args, name)).expanduser().resolve()
        if not node.is_file() or not os.access(node, os.X_OK): parser.error(f"{name} must be executable")
        setattr(args, name, node)
    for name in ("expected_iam_sha", "expected_bff_sha", "expected_app_sha"):
        if not re.fullmatch(r"[a-f0-9]{40}", getattr(args, name)): parser.error("expected source SHA must be full commit")
    return args


def verify_source(repo: Path, expected: str, gitlink: str, allow_unpublished: bool = False) -> dict[str, object]:
    actual = runtime.command_output(["git", "-C", str(repo), "rev-parse", "HEAD"]).strip()
    clean = runtime.command_output(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"]).strip() == ""
    tree = runtime.command_output(["git", "-C", str(ROOT), "ls-tree", "HEAD", gitlink]).strip().split()
    published = len(tree) >= 3 and tree[2] == actual
    if actual != expected or not clean or (not published and not allow_unpublished):
        raise SmokeError(f"{repo.name} source identity, cleanliness, or Root gitlink mismatch")
    return {"sha": actual, "clean": clean, "root_gitlink_matches": published}


def native_command(process: subprocess.Popen[bytes], reader: session.ProtocolReader) -> NativeReceipt:
    if process.stdin is None: raise SmokeError("IAM host stdin unavailable")
    process.stdin.write(b'{"command":"native"}\n')
    process.stdin.flush()
    record = reader.record()
    if set(record) != {"kind", "cookie", "credential_file", "web_origin"} or record.get("kind") != "native":
        raise SmokeError("native receipt protocol drift")
    cookie = record.get("cookie")
    credential_file = record.get("credential_file")
    web_origin = record.get("web_origin")
    if not isinstance(cookie, str) or not re.search(r"(?:^|; )kokoro-issuer\.session_token=[^;]+", cookie):
        raise SmokeError("native cookie missing")
    if not isinstance(credential_file, str) or not credential_file or not Path(credential_file).is_file():
        raise SmokeError("native credential file missing")
    if not isinstance(web_origin, str) or urlsplit(web_origin).scheme not in {"http", "https"}:
        raise SmokeError("IAM Web origin invalid")
    return NativeReceipt(cookie, credential_file, web_origin)


def stop_processes(processes: list[subprocess.Popen[bytes]]) -> None:
    for process in reversed(processes):
        try: runtime.stop_owned_process(process)
        except Exception: pass


def require_json(response: web.BrowserResponse, status: int, label: str) -> dict:
    if response.status != status: raise SmokeError(f"{label}: HTTP {response.status}, expected {status}")
    try: body = json.loads(response.body)
    except (ValueError, UnicodeError): raise SmokeError(f"{label}: JSON response invalid") from None
    if not isinstance(body, dict): raise SmokeError(f"{label}: JSON object required")
    return body


def main(argv=None) -> int:
    args = parse_args(argv)
    sources = {
        "iam": verify_source(IAM, args.expected_iam_sha, "apps/kokoro-iam", args.allow_unpublished_iam_gitlink),
        "bff": verify_source(BFF, args.expected_bff_sha, "apps/kokoro-bff"),
        "app": verify_source(APP, args.expected_app_sha, "apps/kokoro-app"),
    }
    print(json.dumps(sources), flush=True)
    iam_env = session.node_environment(args.iam_node_bin, "v24.20.0", args.bff_node_bin.parent)
    bff_env = session.node_environment(args.bff_node_bin, "v22.22.2", args.bff_node_bin.parent)
    web_env = session.node_environment(args.web_node_bin, "v22.22.2", args.web_node_bin.parent)
    run_id = secrets.token_hex(12)
    web_origin = f"https://web-native-{run_id}.example.test"
    host_name = urlsplit(web_origin).hostname
    resources = runtime.OwnedResources(args.postgres_admin_url, args.redis_url, run_id)
    processes: list[subprocess.Popen[bytes]] = []
    proxies: list[web.Proxy] = []
    reader = None
    cases = 0
    stage = "preflight"
    with tempfile.TemporaryDirectory(prefix="kokoro-web-native-", dir=ROOT.parent) as temporary:
        directory = Path(temporary)
        log_path = directory / "process.log"
        with log_path.open("w+b") as log:
            try:
                stage = "BFF build"
                if runtime.run_owned_command([str(args.bff_node_bin.parent / "corepack"), "pnpm", "build"], cwd=BFF, env=bff_env, log=log, timeout=90) != 0:
                    raise SmokeError("BFF build failed")
                resources.command(["psql", args.postgres_admin_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", "SELECT 1"])
                if resources.command(["redis-cli", "-e", "-u", args.redis_url, "PING"]).strip() != "PONG": raise SmokeError("Redis unavailable")
                db_url = bff_owner_database_url(resources.create_database("bff"))
                bff_env.update({"KOKORO_BFF_POSTGRES_URL": db_url, "KOKORO_BFF_REDIS_URL": args.redis_url})
                runtime.install_schema("bff", BFF, str(args.bff_node_bin.parent), bff_env, log)
                stage = "IAM host"
                iam_env.update({"IAM_TEST_ADMIN_URL": args.postgres_admin_url, "IAM_TEST_REDIS_URL": args.redis_url, "IAM_TEST_WEB_ORIGIN": web_origin, "NODE_ENV": "test"})
                iam = subprocess.Popen([str(args.iam_node_bin), "--import", "tsx", str(IAM_HOST)], cwd=IAM, env=iam_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, start_new_session=True, bufsize=0)
                processes.append(iam)
                if iam.stdout is None: raise SmokeError("IAM host protocol absent")
                reader = session.ProtocolReader(iam.stdout.fileno())
                ready = session.validate_ready(reader.record())
                receipt = native_command(iam, reader)
                if receipt.iam_web_origin != web_origin:
                    raise SmokeError("IAM and Web origins diverged")
                secret = secrets.token_urlsafe(32)
                bff_port = runtime.free_port()
                bff_env.update({
                    "KOKORO_BFF_HOST": "127.0.0.1", "KOKORO_BFF_PORT": str(bff_port), "KOKORO_BFF_MODE": "live",
                    "KOKORO_BFF_SHARED_SECRET": secret, "KOKORO_IAM_BASE_URL": ready.base_url,
                    "KOKORO_IAM_WEB_ORIGIN": web_origin,
                    "KOKORO_IAM_ISSUER_URL": web_origin + "/iam",
                    "KOKORO_IAM_WEB_CALLBACK_URI": web_origin + "/api/auth/callback/kokoro-iam",
                    "KOKORO_IAM_WEB_POST_LOGOUT_URI": web_origin + "/auth/sign-in",
                    "KOKORO_BFF_IAM_SESSION_ADMISSION_CREDENTIAL_FILE": receipt.credential_file,
                    "KOKORO_AGENT_ENABLED": "false", "KOKORO_TENANT_ID": ready.tenant_id,
                    "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
                })
                stage = "BFF startup"
                bff = runtime.start_process(args.bff_node_bin, BFF, bff_env, log)
                processes.append(bff)
                runtime.wait_ready(f"http://127.0.0.1:{bff_port}", bff)
                bff_proxy = web.Proxy(bff_port)
                proxies.append(bff_proxy)
                stage = "Web startup"
                next_root = web.isolated_next(directory)
                next_port = runtime.free_port()
                web_env.update({
                    "KOKORO_WEB_ORIGIN": web_origin, "KOKORO_DOMAIN": host_name,
                    "KOKORO_BFF_BASE_URL": f"http://127.0.0.1:{bff_proxy.server_port}",
                    "KOKORO_INTERNAL_SECRET_WEB_BFF": secret, "KOKORO_WEB_REDIS_URL": args.redis_url,
                    "KOKORO_OIDC_CLIENT_ID": "native-fixture-client", "KOKORO_OIDC_CLIENT_SECRET": secrets.token_urlsafe(32),
                    "KOKORO_TENANT_ID": ready.tenant_id, "KOKORO_WEB_AUTH_SECRET": secrets.token_hex(32),
                    "NEXTAUTH_URL": web_origin + "/api/auth",
                })
                next_process = subprocess.Popen([str(args.web_node_bin), str(next_root / "server.cjs"), str(next_port), host_name], cwd=next_root, env=web_env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=log, start_new_session=True)
                processes.append(next_process)
                web_proxy = web.Proxy(next_port, host_name, web.certificate(directory, host_name))
                proxies.append(web_proxy)
                stage = "Web HTTPS preflight"
                deadline = time.monotonic() + 30
                while True:
                    try:
                        fixture = web.https_browser(web_proxy.server_port, "/api/fixture-origin", web_origin)
                        if fixture.status == 200: break
                    except SmokeError: pass
                    if time.monotonic() >= deadline or next_process.poll() is not None: raise SmokeError("Next origin fixture not ready")
                    time.sleep(0.1)
                stage = "native session"
                session_response = web.https_browser(web_proxy.server_port, "/api/auth/session", web_origin, cookie=receipt.cookie)
                body = require_json(session_response, 200, "native Web session")
                if body.get("authenticated") is not True or body.get("mode") != "native" or body.get("subject") != ready.user_id or not isinstance(body.get("expires_at"), int):
                    raise SmokeError("native Web session response drift")
                cases += 1
                projects = web.https_browser(web_proxy.server_port, "/api/session/projects", web_origin, cookie=receipt.cookie)
                project_body = require_json(projects, 200, "native Web BFF projects")
                if project_body != {"projects": []}:
                    raise SmokeError("native Web BFF project response drift")
                cases += 1
                if iam.stdin is None: raise SmokeError("IAM host stdin unavailable")
                iam.stdin.write(b'{"command":"signout"}\n'); iam.stdin.flush()
                result = reader.record()
                if result != {"kind": "result", "command": "signout", "status": "ok"}: raise SmokeError("IAM signout receipt drift")
                signed_out = web.https_browser(web_proxy.server_port, "/api/auth/session", web_origin, cookie=receipt.cookie)
                out_body = require_json(signed_out, 401, "native Web signed-out session")
                if out_body.get("error", {}).get("code") != "native_session_required": raise SmokeError("native logout was not enforced")
                cases += 1
                iam.stdin.write(b'{"command":"stop"}\n'); iam.stdin.flush()
                if reader.record() != {"kind": "result", "command": "stop", "status": "ok"}: raise SmokeError("IAM stop receipt drift")
                log.flush()
                diagnostic = log_path.read_bytes()
                for value in (secret, receipt.cookie):
                    if value.encode() in diagnostic: raise SmokeError("native credential appeared in process log")
                cases += 1
            finally:
                for proxy in reversed(proxies):
                    try: proxy.close()
                    except Exception: pass
                stop_processes(processes)
                resources.cleanup()
                resources.verify_clean()
                if reader is not None: reader.close()
    print(json.dumps({"status": "passed", "cases": cases, "web_origin": web_origin, "iam_web_origin": receipt.iam_web_origin}), flush=True)
    return 0


if __name__ == "__main__":
    try: sys.exit(main())
    except (SmokeError, runtime.SmokeError, subprocess.SubprocessError, OSError) as error:
        print(f"smoke failed: {error}", file=sys.stderr)
        sys.exit(1)

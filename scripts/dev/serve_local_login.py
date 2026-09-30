#!/usr/bin/env python3
"""Serve real local Web → BFF → IAM login at http://127.0.0.1:3310.

This is an interactive, foreground development fixture. Ctrl-C stops only the
processes and isolated PostgreSQL/Redis resources created by this invocation.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.parse import unquote, urlsplit
from uuid import uuid4

E2E = Path(__file__).resolve().parents[1] / "e2e"
sys.path.insert(0, str(E2E))

import capability_bff_smoke_runtime as runtime  # noqa: E402
from bff_owner_schema import bff_owner_database_url  # noqa: E402
import run_bff_iam_oidc_smoke as previous  # noqa: E402
import run_bff_iam_session_smoke as session  # noqa: E402
import run_web_bff_iam_oidc_smoke as web_smoke  # noqa: E402
import run_web_bff_iam_first_login_smoke as first_login  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_chat_runtime as chat_runtime  # noqa: E402
import model_provider  # noqa: E402

WEB_PORT = 3310
NODE_PARENT_GUARD = """\
const expectedParent = process.ppid
let orphanedAt = 0
const watcher = setInterval(() => {
  if (expectedParent > 1 && process.ppid === expectedParent) return
  const now = Date.now()
  if (orphanedAt === 0) {
    orphanedAt = now
    process.kill(process.pid, "SIGTERM")
    return
  }
  if (now - orphanedAt >= 5000) process.kill(process.pid, "SIGKILL")
}, 100)
watcher.unref()
"""


def web_origin(_run_id: str) -> str:
    return f"http://127.0.0.1:{WEB_PORT}"


class LaunchError(RuntimeError):
    """A sanitized launcher failure, without credential-bearing data."""


def failure_category(error: Exception) -> str:
    """Classify only by trusted types; never render an exception or its class name."""
    for types, category in (
        ((LaunchError,), "launcher"),
        ((chat_runtime.ChatError,), "chat"),
        ((model_provider.ProviderError,), "provider"),
        ((OSError,), "io"),
        ((subprocess.SubprocessError,), "subprocess"),
        (
            (
                runtime.SmokeError,
                session.SmokeError,
                web_smoke.SmokeError,
                previous.SmokeError,
                first_login.FirstLoginError,
            ),
            "owner_smoke",
        ),
    ):
        if isinstance(error, types):
            return category
    return "unexpected"


def require_free_web_port() -> None:
    """Fail before creating resources when another process owns the entrance."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", WEB_PORT))
    except OSError:
        raise LaunchError("local login port 3310 is occupied") from None


def local_next_server(source: str) -> str:
    marker = "port: 443"
    if source.count(marker) != 1:
        raise LaunchError("isolated Next server template changed")
    return source.replace(marker, f"port: {WEB_PORT}")


def install_node_parent_guard(directory: Path, *environments: dict[str, str]) -> Path:
    """Make each Node process exit when its own direct parent disappears."""
    guard = directory / "node-parent-guard.mjs"
    guard.write_text(NODE_PARENT_GUARD, encoding="utf-8")
    option = f"--import={guard.as_uri()}"
    for environment in environments:
        existing = environment.get("NODE_OPTIONS", "").strip()
        environment["NODE_OPTIONS"] = f"{existing} {option}".strip()
    return guard


def require_owned_stack_alive(processes: list[subprocess.Popen[bytes]]) -> None:
    if any(process.poll() is not None for process in processes):
        raise LaunchError("owned service exited")


def http_browser(
    port: int, path: str, origin: str, *, cookie: str = ""
) -> web_smoke.BrowserResponse:
    """Read only the local, same-origin HTTP surface with bounded response size."""
    if origin != f"http://127.0.0.1:{port}":
        raise LaunchError("local browser origin mismatch")
    target = web_smoke.browser_target(path, origin)
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=12)
    try:
        headers = {
            "Host": urlsplit(origin).netloc,
            "Accept": "text/html,application/json",
        }
        if cookie:
            headers["Cookie"] = cookie
        connection.request("GET", target, headers=headers)
        response = connection.getresponse()
        body = response.read(web_smoke.MAX_BODY + 1)
        if len(body) > web_smoke.MAX_BODY:
            raise LaunchError("local browser response oversized")
        return web_smoke.BrowserResponse(
            response.status,
            {
                name.lower(): value
                for name, value in response.getheaders()
                if name.lower() != "set-cookie"
            },
            [
                value
                for name, value in response.getheaders()
                if name.lower() == "set-cookie"
            ],
            body,
        )
    except (OSError, http.client.HTTPException):
        raise web_smoke.SmokeError("local HTTP browser request failed") from None
    finally:
        connection.close()


def fixture_origin_matches(observed: object, origin: str) -> bool:
    """Next normalizes request.nextUrl to localhost; Host remains browser authority."""
    return observed == {
        "origin": f"http://localhost:{WEB_PORT}",
        "host": urlsplit(origin).netloc,
        "proto": "http",
    }


def wait_for_web(process: subprocess.Popen[bytes], origin: str) -> None:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline and process.poll() is None:
        try:
            response = http_browser(WEB_PORT, "/api/fixture-origin", origin)
            if response.status == 200:
                try:
                    observed = json.loads(response.body)
                except (ValueError, UnicodeError):
                    raise LaunchError("Next origin fixture malformed") from None
                if not fixture_origin_matches(observed, origin):
                    raise LaunchError("Next origin fixture mismatch")
                return
        except web_smoke.SmokeError:
            pass
        time.sleep(0.2)
    raise LaunchError("local Web login page did not become ready")


def write_private_credentials(directory: Path, email: str, password: str) -> Path:
    """Create one exclusive private credential file; never emit its contents."""
    path = directory / "login-credentials.json"
    with open(
        path,
        "x",
        encoding="utf-8",
        opener=lambda name, flags: os.open(name, flags, 0o600),
    ) as credential_file:
        json.dump({"email": email, "password": password}, credential_file)
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iam-node-bin", type=Path, required=True)
    parser.add_argument("--bff-node-bin", type=Path, required=True)
    parser.add_argument("--web-node-bin", type=Path, required=True)
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Enable real System/provider/Agent Chat; never falls back to login-only",
    )
    parser.add_argument("--agent-redis-url", default="")
    parser.add_argument("--uv-bin", type=Path)
    parser.add_argument("--model-origin")
    parser.add_argument("--model")
    parser.add_argument("--external-model-credential-file", type=Path)
    args = parser.parse_args(argv)
    args.postgres_admin_url = os.environ.get("KOKORO_LOCAL_POSTGRES_URL", "")
    args.redis_url = os.environ.get("KOKORO_LOCAL_REDIS_URL", "")
    args.external_model = None
    if args.external_model_credential_file is not None:
        if not args.chat or args.model_origin is not None or args.model is not None:
            parser.error(
                "external provider requires --chat and is exclusive with Ollama options"
            )
        try:
            args.external_model = model_provider.load_external(
                args.external_model_credential_file
            )
        except model_provider.ProviderError:
            parser.error("external provider requires a valid private credential file")
    args.model_origin = args.model_origin or "http://127.0.0.1:11434"
    args.model = (
        args.external_model.model
        if args.external_model is not None
        else args.model or "qwen3:8b"
    )
    if urlsplit(args.postgres_admin_url).scheme != "postgresql" or urlsplit(
        args.redis_url
    ).scheme not in {"redis", "rediss"}:
        parser.error("set KOKORO_LOCAL_POSTGRES_URL and KOKORO_LOCAL_REDIS_URL")
    if urlsplit(args.postgres_admin_url).password or urlsplit(args.redis_url).password:
        parser.error("use local passwordless endpoints for this foreground fixture")
    for name in ("iam_node_bin", "bff_node_bin", "web_node_bin"):
        node = getattr(args, name).expanduser().resolve()
        if not node.is_file() or not os.access(node, os.X_OK):
            parser.error(f"{name} must be executable")
        setattr(args, name, node)
    if args.chat:
        try:
            chat_runtime.validate_options(
                args.redis_url,
                args.agent_redis_url,
                args.model_origin,
                args.model,
                args.external_model,
            )
        except chat_runtime.ChatError:
            parser.error(
                "chat requires a distinct explicit Agent Redis DB and a valid selected provider"
            )
        if (
            args.uv_bin is None
            or not args.uv_bin.is_file()
            or not os.access(args.uv_bin, os.X_OK)
        ):
            parser.error("chat requires executable --uv-bin")
        args.uv_bin = args.uv_bin.absolute()
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    require_free_web_port()
    run_id = secrets.token_hex(12)
    origin = web_origin(run_id)
    host_name = "127.0.0.1"
    iam_resource_id = str(uuid4())
    iam_identity = web_smoke.named_iam_identity(iam_resource_id)
    iam_owner_token = secrets.token_hex(16)
    resources = runtime.OwnedResources(args.postgres_admin_url, args.redis_url, run_id)
    iam_env = session.node_environment(
        args.iam_node_bin, "v24.20.0", args.bff_node_bin.parent
    )
    bff_env = session.node_environment(
        args.bff_node_bin, "v22.22.2", args.bff_node_bin.parent
    )
    web_env = session.node_environment(
        args.web_node_bin, "v22.22.2", args.web_node_bin.parent
    )
    credentials = previous.CredentialRegistry(
        args.postgres_admin_url, args.redis_url, iam_owner_token
    )
    for raw in (args.postgres_admin_url, args.redis_url):
        password = unquote(urlsplit(raw).password or "")
        if len(password) >= 12:
            credentials.add(password)
    processes: list[subprocess.Popen[bytes]] = []
    reader: session.ProtocolReader | None = None
    before_web: set[str] | None = None
    iam_attempted = False
    stage = "preflight"
    failures: list[str] = []
    chat = None
    chat_config = None
    with tempfile.TemporaryDirectory(
        prefix="kokoro-local-login-", dir=web_smoke.ROOT.parent, delete=False
    ) as temp:
        directory = Path(temp)
        install_node_parent_guard(directory, iam_env, bff_env, web_env)
        log_path = directory / "process.log"
        log_path.touch(mode=0o600)
        with log_path.open("w+b") as log:
            try:
                if args.chat:
                    stage = "real Chat preflight"
                    chat_config = chat_runtime.preflight(
                        args.uv_bin,
                        args.model_origin,
                        args.model,
                        log,
                        getattr(args, "external_model", None),
                    )
                stage = "BFF build"
                if (
                    runtime.run_owned_command(
                        [str(args.bff_node_bin.parent / "corepack"), "pnpm", "build"],
                        cwd=web_smoke.BFF,
                        env=bff_env,
                        log=log,
                        timeout=90,
                    )
                    != 0
                ):
                    raise LaunchError("BFF build failed")
                stage = "infrastructure preflight"
                resources.command(
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
                    resources.command(
                        ["redis-cli", "-e", "-u", args.redis_url, "PING"]
                    ).strip()
                    != "PONG"
                ):
                    raise LaunchError("Redis unavailable")
                before_web = web_smoke.web_redis_keys(args.redis_url, origin, resources)
                stage = "BFF database"
                application_db_url = resources.create_database("bff")
                db_url = bff_owner_database_url(application_db_url)
                bff_env.update(
                    {
                        "KOKORO_BFF_POSTGRES_URL": db_url,
                        "KOKORO_BFF_REDIS_URL": args.redis_url,
                    }
                )
                runtime.install_schema(
                    "bff", web_smoke.BFF, str(args.bff_node_bin.parent), bff_env, log
                )
                stage = "IAM host"
                if web_smoke.iam_owned_inventory(resources, iam_identity) != (
                    set(),
                    set(),
                ):
                    raise LaunchError("IAM named resources already exist")
                iam_env.update(
                    {
                        "IAM_TEST_ADMIN_URL": args.postgres_admin_url,
                        "IAM_TEST_REDIS_URL": args.redis_url,
                        "IAM_TEST_WEB_ORIGIN": origin,
                        "IAM_TEST_ALLOW_HTTP_LOOPBACK": "1",
                        "IAM_TEST_RESOURCE_ID": iam_resource_id,
                        "IAM_TEST_RESOURCE_OWNER_TOKEN": iam_owner_token,
                        "NODE_ENV": "test",
                    }
                )
                iam_attempted = True
                iam = subprocess.Popen(
                    [str(args.iam_node_bin), "--import", "tsx", str(web_smoke.HOST)],
                    cwd=web_smoke.IAM,
                    env=iam_env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=log,
                    start_new_session=True,
                    bufsize=0,
                )
                processes.append(iam)
                if iam.stdout is None:
                    raise LaunchError("IAM host protocol absent")
                reader = session.ProtocolReader(iam.stdout.fileno())
                ready = web_smoke.validate_ready(reader.record(), origin)
                if (ready.database_name, ready.redis_prefix) != (
                    iam_identity.database_name,
                    iam_identity.redis_prefix,
                ):
                    raise LaunchError(
                        "IAM ready identity differs from runner ownership"
                    )
                if (
                    ready.database_name
                    not in web_smoke.iam_owned_inventory(resources, ready)[0]
                ):
                    raise LaunchError("IAM owned database absent after host ready")
                credentials.add(ready.client_secret, ready.password)
                stage = "BFF startup"
                secret = secrets.token_urlsafe(32)
                credentials.add(secret)
                bff_port = runtime.free_port()
                bff_env.update(
                    {
                        "KOKORO_BFF_HOST": "127.0.0.1",
                        "KOKORO_BFF_PORT": str(bff_port),
                        "KOKORO_BFF_MODE": "live",
                        "KOKORO_BFF_SHARED_SECRET": secret,
                        "KOKORO_IAM_BASE_URL": ready.base_url,
                        "KOKORO_IAM_ISSUER_URL": ready.issuer_url,
                        "KOKORO_IAM_WEB_ORIGIN": origin,
                        "KOKORO_IAM_WEB_CALLBACK_URI": ready.redirect_uri,
                        "KOKORO_IAM_WEB_POST_LOGOUT_URI": ready.post_logout_redirect_uri,
                        "KOKORO_AGENT_ENABLED": "false",
                        "KOKORO_TENANT_ID": ready.tenant_id,
                        "KOKORO_DOMAIN": host_name,
                    }
                )
                if args.chat:
                    stage = "real Chat startup"
                    chat = chat_runtime.LocalChatRuntime(
                        config=chat_config,
                        uv=args.uv_bin,
                        node=args.iam_node_bin,
                        node_env=iam_env,
                        directory=directory,
                        resources=resources,
                        credentials=credentials,
                        log=log,
                        tenant=ready.tenant_id,
                        agent_redis_url=args.agent_redis_url,
                    )
                    bff_env.update(chat.start(application_db_url))
                stage = "BFF startup"
                bff = runtime.start_process(
                    args.bff_node_bin, web_smoke.BFF, bff_env, log
                )
                processes.append(bff)
                runtime.wait_ready(f"http://127.0.0.1:{bff_port}", bff)
                stage = "Web startup"
                next_root = web_smoke.isolated_next(directory)
                server_path = next_root / "server.cjs"
                server_path.write_text(local_next_server(server_path.read_text()))
                web_env.update(
                    {
                        "KOKORO_WEB_ORIGIN": origin,
                        "KOKORO_DOMAIN": host_name,
                        "KOKORO_BFF_BASE_URL": f"http://127.0.0.1:{bff_port}",
                        "KOKORO_INTERNAL_SECRET_WEB_BFF": secret,
                        "KOKORO_WEB_REDIS_URL": args.redis_url,
                        "KOKORO_TENANT_ID": ready.tenant_id,
                        "KOKORO_OIDC_CLIENT_ID": ready.client_id,
                        "KOKORO_OIDC_CLIENT_SECRET": ready.client_secret,
                        "KOKORO_WEB_AUTH_SECRET": secrets.token_hex(32),
                        "NEXTAUTH_URL": origin + "/api/auth",
                    }
                )
                credentials.add(web_env["KOKORO_WEB_AUTH_SECRET"])
                next_process = subprocess.Popen(
                    [
                        str(args.web_node_bin),
                        str(server_path),
                        str(WEB_PORT),
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
                wait_for_web(next_process, origin)
                stage = "formal login navigation"
                first_login.probe_formal_login_entry(
                    WEB_PORT, origin, credentials, browser_request=http_browser
                )
                stage = "private credential setup"
                credential_path = write_private_credentials(
                    directory, ready.email, ready.password
                )
                print(f"Local login: {origin}/login", flush=True)
                print(f"Private login credentials: {credential_path}", flush=True)
                print(
                    "Mode: real Chat (empty Skills; Storage not configured)"
                    if args.chat
                    else "Mode: login only",
                    flush=True,
                )
                print(
                    "Press Ctrl-C to stop and remove this run's resources.", flush=True
                )
                while True:
                    stage = "serving stack guard"
                    require_owned_stack_alive(processes)
                    if chat is not None:
                        stage = "serving chat tick"
                        chat.tick()
                    stage = "serving wait"
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass
            except (
                LaunchError,
                web_smoke.SmokeError,
                runtime.SmokeError,
                session.SmokeError,
                OSError,
                subprocess.SubprocessError,
            ) as error:
                failures.append(f"{stage} ({failure_category(error)})")
            except Exception as error:
                failures.append(f"{stage} ({failure_category(error)})")
            finally:
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                signal.signal(signal.SIGHUP, signal.SIG_IGN)
                owned_processes_stopped = True
                for process in reversed(processes[1:]):
                    try:
                        runtime.stop_owned_process(process)
                    except Exception:
                        owned_processes_stopped = False
                        failures.append("owned process cleanup")
                chat_failures = []
                if chat is not None:
                    if owned_processes_stopped:
                        chat_failures = chat.close()
                    else:
                        chat_failures = [
                            "Chat dependencies preserved for active frontend"
                        ]
                failures.extend(chat_failures)
                if chat is not None and not chat.quiescent:
                    owned_processes_stopped = False
                if owned_processes_stopped and processes:
                    try:
                        runtime.stop_owned_process(processes[0])
                    except Exception:
                        owned_processes_stopped = False
                        failures.append("IAM process cleanup")
                if reader is not None:
                    try:
                        reader.close()
                    except Exception:
                        failures.append("IAM protocol cleanup")
                if before_web is not None and owned_processes_stopped:
                    try:
                        extras = (
                            web_smoke.web_redis_keys(args.redis_url, origin, resources)
                            - before_web
                        )
                        if extras:
                            resources.command(
                                [
                                    "redis-cli",
                                    "-e",
                                    "-u",
                                    args.redis_url,
                                    "UNLINK",
                                    *sorted(extras),
                                ]
                            )
                        if (
                            web_smoke.web_redis_keys(args.redis_url, origin, resources)
                            != before_web
                        ):
                            failures.append("Web Redis cleanup")
                    except Exception:
                        failures.append("Web Redis cleanup")
                elif before_web is not None:
                    failures.append("Web Redis cleanup deferred; owned services active")
                try:
                    if owned_processes_stopped and not chat_failures:
                        resources.cleanup()
                        resources.verify_clean()
                    else:
                        failures.append("application resources preserved")
                except Exception:
                    failures.append("BFF database cleanup")
                if iam_attempted and owned_processes_stopped:
                    try:
                        web_smoke.reconcile_iam_identity(
                            resources, iam_identity, iam_owner_token
                        )
                    except Exception:
                        failures.append("IAM resource cleanup")
                elif iam_attempted:
                    failures.append("IAM resource cleanup deferred")
                try:
                    log.flush()
                    previous.assert_log_clean(log_path, credentials.values())
                except Exception:
                    failures.append("credential log scan")
    if failures:
        print(f"Local evidence preserved: {directory}", file=sys.stderr)
        raise LaunchError("; ".join(sorted(set(failures))) + " failed")
    shutil.rmtree(directory)
    print("Local login stopped; owned resources removed.", flush=True)
    return 0


if __name__ == "__main__":

    def stop_owned_stack(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop_owned_stack)
    signal.signal(signal.SIGHUP, stop_owned_stack)
    try:
        sys.exit(main())
    except LaunchError as error:
        print(f"Local login failed: {error}", file=sys.stderr)
        sys.exit(1)

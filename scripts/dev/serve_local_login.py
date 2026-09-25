#!/usr/bin/env python3
"""Serve real local Web → BFF → IAM login on a temporary HTTPS origin at port 3310.

This is an interactive, foreground development fixture. Ctrl-C stops only the
processes and isolated PostgreSQL/Redis resources created by this invocation.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
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

WEB_PORT = 3310


def web_origin(run_id: str) -> str:
    return f"https://web-{run_id}.example.test:{WEB_PORT}"


class LaunchError(RuntimeError):
    """A sanitized launcher failure, without credential-bearing data."""


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


class LocalWebProxy(web_smoke.Proxy):
    """Reuse the tested TLS proxy handler on the interactive local port."""

    def server_bind(self) -> None:
        self.server_address = ("127.0.0.1", WEB_PORT)
        super().server_bind()

    def __init__(self, upstream_port: int, host: str, certificate: tuple[Path, Path]):
        super().__init__(
            upstream_port, web_host=f"{host}:{WEB_PORT}", certificate=certificate
        )
        self.web_port = WEB_PORT


def wait_for_web(
    proxy: LocalWebProxy, process: subprocess.Popen[bytes], origin: str
) -> None:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline and process.poll() is None:
        try:
            response = web_smoke.https_browser(
                proxy.server_port, "/api/fixture-origin", origin
            )
            if response.status == 200:
                try:
                    observed = json.loads(response.body)
                except (ValueError, UnicodeError):
                    raise LaunchError("Next origin fixture malformed") from None
                if observed != {
                    "origin": origin,
                    "host": urlsplit(origin).netloc,
                    "proto": "https",
                }:
                    raise LaunchError("Next origin fixture mismatch")
                return
        except web_smoke.SmokeError:
            pass
        time.sleep(0.2)
    raise LaunchError("local Web login page did not become ready")


def chromium_command(
    chromium: Path, profile: Path, host: str, origin: str, certificate_spki: str
) -> list[str]:
    if not re.fullmatch(r"web-[a-f0-9]{24}\.example\.test", host):
        raise LaunchError("unexpected local Web host")
    if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", certificate_spki):
        raise LaunchError("invalid local certificate fingerprint")
    return [
        str(chromium),
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-proxy-server",
        "--new-window",
        f"--host-resolver-rules=MAP {host} 127.0.0.1",
        f"--ignore-certificate-errors-spki-list={certificate_spki}",
        origin + "/login",
    ]


def certificate_spki_sha256(certificate: Path) -> str:
    try:
        public_key = subprocess.run(
            ["openssl", "x509", "-in", str(certificate), "-pubkey", "-noout"],
            capture_output=True,
            check=True,
            timeout=5,
        ).stdout
        der = subprocess.run(
            ["openssl", "pkey", "-pubin", "-outform", "DER"],
            input=public_key,
            capture_output=True,
            check=True,
            timeout=5,
        ).stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise LaunchError("local certificate fingerprint unavailable") from None
    return base64.b64encode(hashlib.sha256(der).digest()).decode("ascii")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iam-node-bin", type=Path, required=True)
    parser.add_argument("--bff-node-bin", type=Path, required=True)
    parser.add_argument("--web-node-bin", type=Path, required=True)
    parser.add_argument(
        "--chromium-bin",
        type=Path,
        default=Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    )
    args = parser.parse_args(argv)
    args.postgres_admin_url = os.environ.get("KOKORO_LOCAL_POSTGRES_URL", "")
    args.redis_url = os.environ.get("KOKORO_LOCAL_REDIS_URL", "")
    if urlsplit(args.postgres_admin_url).scheme != "postgresql" or urlsplit(
        args.redis_url
    ).scheme not in {"redis", "rediss"}:
        parser.error("set KOKORO_LOCAL_POSTGRES_URL and KOKORO_LOCAL_REDIS_URL")
    if urlsplit(args.postgres_admin_url).password or urlsplit(args.redis_url).password:
        parser.error("use local passwordless endpoints for this foreground fixture")
    for name in ("iam_node_bin", "bff_node_bin", "web_node_bin", "chromium_bin"):
        node = getattr(args, name).expanduser().resolve()
        if not node.is_file() or not os.access(node, os.X_OK):
            parser.error(f"{name} must be executable")
        setattr(args, name, node)
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    require_free_web_port()
    run_id = secrets.token_hex(12)
    origin = web_origin(run_id)
    host_name = urlsplit(origin).hostname
    if host_name is None:
        raise LaunchError("Web host absent")
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
    proxies: list[web_smoke.Proxy] = []
    reader: session.ProtocolReader | None = None
    before_web: set[str] | None = None
    iam_attempted = False
    stage = "preflight"
    failures: list[str] = []
    with tempfile.TemporaryDirectory(
        prefix="kokoro-local-login-", dir=web_smoke.ROOT.parent
    ) as temp:
        directory = Path(temp)
        log_path = directory / "process.log"
        with log_path.open("w+b") as log:
            try:
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
                db_url = bff_owner_database_url(resources.create_database("bff"))
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
                bff = runtime.start_process(
                    args.bff_node_bin, web_smoke.BFF, bff_env, log
                )
                processes.append(bff)
                runtime.wait_ready(f"http://127.0.0.1:{bff_port}", bff)
                bff_proxy = web_smoke.Proxy(bff_port, credentials=credentials)
                proxies.append(bff_proxy)
                stage = "Web startup"
                next_root = web_smoke.isolated_next(directory)
                server_path = next_root / "server.cjs"
                server_path.write_text(local_next_server(server_path.read_text()))
                next_port = runtime.free_port()
                web_env.update(
                    {
                        "KOKORO_WEB_ORIGIN": origin,
                        "KOKORO_DOMAIN": host_name,
                        "KOKORO_BFF_BASE_URL": f"http://127.0.0.1:{bff_proxy.server_port}",
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
                certificate = web_smoke.certificate(directory, host_name)
                web_proxy = LocalWebProxy(next_port, host_name, certificate)
                proxies.append(web_proxy)
                wait_for_web(web_proxy, next_process, origin)
                stage = "formal login navigation"
                first_login.probe_formal_login_entry(
                    web_proxy.server_port, origin, credentials
                )
                stage = "Chromium startup"
                chrome = subprocess.Popen(
                    chromium_command(
                        args.chromium_bin,
                        directory / "chromium-profile",
                        host_name,
                        origin,
                        certificate_spki_sha256(certificate[0]),
                    ),
                    cwd=directory,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                processes.append(chrome)
                time.sleep(0.5)
                if chrome.poll() is not None:
                    raise LaunchError("Chromium exited before local login became ready")
                print(f"Local login: {origin}/login", flush=True)
                print(f"Temporary email: {ready.email}", flush=True)
                print(f"Temporary password: {ready.password}", flush=True)
                print(
                    "Press Ctrl-C to stop and remove this run's resources.", flush=True
                )
                stage = "serving"
                while True:
                    if any(process.poll() is not None for process in processes):
                        raise LaunchError("owned service exited")
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
            ):
                failures.append(stage)
            except Exception:
                failures.append(stage)
            finally:
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                signal.signal(signal.SIGHUP, signal.SIG_IGN)
                for proxy in reversed(proxies):
                    try:
                        proxy.close()
                    except Exception:
                        failures.append("owned proxy cleanup")
                owned_processes_stopped = True
                for process in reversed(processes):
                    try:
                        runtime.stop_owned_process(process)
                    except Exception:
                        owned_processes_stopped = False
                        failures.append("owned process cleanup")
                if reader is not None:
                    try:
                        reader.close()
                    except Exception:
                        failures.append("IAM protocol cleanup")
                if before_web is not None:
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
                try:
                    resources.cleanup()
                    resources.verify_clean()
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
        raise LaunchError("; ".join(sorted(set(failures))) + " failed")
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

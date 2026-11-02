#!/usr/bin/env python3
"""Exercise the real Web native-session path through BFF and IAM."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote, quote_plus, unquote, urlsplit
from uuid import uuid4

import capability_bff_smoke_runtime as runtime
from bff_owner_schema import bff_owner_database_url
import run_bff_iam_session_smoke as session
import run_web_bff_iam_oidc_smoke as web

ROOT = Path(__file__).resolve().parents[2]
IAM = ROOT / "apps/kokoro-iam"
BFF = ROOT / "apps/kokoro-bff"
APP = ROOT / "apps/kokoro-app"
IAM_HOST = IAM / "test/fixtures/bff-session-admission-host.ts"
EVIDENCE_ROOT = ROOT / "var/dev/web-native-session-smoke"
REQUIRED_NODE_VERSIONS = {"iam": "24.20.0", "bff": "24.20.0", "app": "22.23.4"}


class SmokeError(RuntimeError):
    pass


@dataclass(frozen=True)
class NativeReceipt:
    cookie: str
    credential_file: str
    iam_web_origin: str


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "postgres-admin-url",
        "redis-url",
        "iam-node-bin",
        "bff-node-bin",
        "web-node-bin",
    ):
        parser.add_argument("--" + name, required=True)
    for name in ("expected-iam-sha", "expected-bff-sha", "expected-app-sha"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--allow-unpublished-iam-gitlink", action="store_true")
    parser.add_argument("--browser-journeys", action="store_true")
    args = parser.parse_args(argv)
    if urlsplit(args.postgres_admin_url).scheme != "postgresql" or urlsplit(
        args.redis_url
    ).scheme not in {"redis", "rediss"}:
        parser.error("explicit PostgreSQL and Redis URLs required")
    for name in ("iam_node_bin", "bff_node_bin", "web_node_bin"):
        node = Path(getattr(args, name)).expanduser().resolve()
        if not node.is_file() or not os.access(node, os.X_OK):
            parser.error(f"{name} must be executable")
        setattr(args, name, node)
    for name in ("expected_iam_sha", "expected_bff_sha", "expected_app_sha"):
        if not re.fullmatch(r"[a-f0-9]{40}", getattr(args, name)):
            parser.error("expected source SHA must be full commit")
    return args


def verify_source(
    repo: Path, expected: str, gitlink: str, allow_unpublished: bool = False
) -> dict[str, object]:
    actual = runtime.command_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"]
    ).strip()
    clean = (
        runtime.command_output(
            ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"]
        ).strip()
        == ""
    )
    tree = (
        runtime.command_output(["git", "-C", str(ROOT), "ls-tree", "HEAD", gitlink])
        .strip()
        .split()
    )
    published = len(tree) >= 3 and tree[2] == actual
    if actual != expected or not clean or (not published and not allow_unpublished):
        raise SmokeError(
            f"{repo.name} source identity, cleanliness, or Root gitlink mismatch"
        )
    return {"sha": actual, "clean": clean, "root_gitlink_matches": published}


def native_command(
    process: subprocess.Popen[bytes], reader: session.ProtocolReader
) -> NativeReceipt:
    if process.stdin is None:
        raise SmokeError("IAM host stdin unavailable")
    process.stdin.write(b'{"command":"native"}\n')
    process.stdin.flush()
    record = reader.record()
    if (
        set(record) != {"kind", "cookie", "credential_file", "web_origin"}
        or record.get("kind") != "native"
    ):
        raise SmokeError("native receipt protocol drift")
    cookie = record.get("cookie")
    credential_file = record.get("credential_file")
    web_origin = record.get("web_origin")
    if not isinstance(cookie, str) or not re.search(
        r"(?:^|; )kokoro-issuer\.session_token=[^;]+", cookie
    ):
        raise SmokeError("native cookie missing")
    if (
        not isinstance(credential_file, str)
        or not credential_file
        or not Path(credential_file).is_file()
    ):
        raise SmokeError("native credential file missing")
    if not isinstance(web_origin, str) or urlsplit(web_origin).scheme not in {
        "http",
        "https",
    }:
        raise SmokeError("IAM Web origin invalid")
    return NativeReceipt(cookie, credential_file, web_origin)


BROWSER_JOURNEYS = {
    "cold_login": {
        "initial_issuer_cookies": 0,
        "sign_in_status": 303,
        "session_status": 200,
        "authenticated": True,
        "projects_status": 200,
        "profile_status": 200,
        "profile_visible": True,
        "owner": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "fixed",
        },
    },
    "tenant_rejection_recovery": {
        "foreign_owner": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "other",
        },
        "pre_mutation_profile_visible": True,
        "session_status": 401,
        "projects_status": 401,
        "private_ui_retired": True,
        "relogin_status": 303,
        "recovered_session_status": 200,
        "recovered_projects_status": 200,
        "recovered_profile_status": 200,
        "recovered_profile_visible": True,
        "recovered_owner": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "fixed",
        },
    },
    "ui_logout": {
        "clicked": True,
        "sign_out_status": 200,
        "owner": {
            "exists": True,
            "unexpired": False,
            "member": True,
            "active_tenant": "fixed",
        },
        "issuer_cookies": 0,
        "session_status": 200,
        "authenticated": False,
        "projects_status": 401,
        "old_cookie_status": 401,
    },
    "independent_revocation": {
        "a_owner": {
            "exists": False,
            "unexpired": False,
            "member": True,
            "active_tenant": "none",
        },
        "a_session_status": 401,
        "a_projects_status": 401,
        "a_private_ui_retired": True,
        "b_session_status_before_membership": 200,
        "b_owner_before_membership": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "fixed",
        },
        "b_owner_after_membership": {
            "exists": True,
            "unexpired": True,
            "member": False,
            "active_tenant": "fixed",
        },
        "b_session_status": 401,
        "b_projects_status": 401,
        "private_ui_retired": True,
    },
}


def exact_browser_fact(value, expected) -> bool:
    """Reject unknown fields and Python bool/int equivalence at the boundary."""
    if type(value) is not type(expected):
        return False
    if isinstance(expected, dict):
        return value.keys() == expected.keys() and all(
            exact_browser_fact(value[key], expected[key]) for key in expected
        )
    return value == expected


def validate_browser_receipt(record: dict) -> dict:
    if not isinstance(record, dict) or set(record) != {"kind", "journeys", "race"}:
        raise SmokeError("browser receipt shape invalid")
    if record["kind"] != "browser_result" or not exact_browser_fact(
        record["journeys"], BROWSER_JOURNEYS
    ):
        raise SmokeError("browser journey facts incomplete or failed")
    race = record["race"]
    if not isinstance(race, dict) or race.get("observation") not in (
        "cancelled",
        "delivered_and_retired",
    ):
        raise SmokeError("browser race observation missing")
    if not exact_browser_fact(
        race,
        {
            "upstream_profile_status": 200,
            "observation": race["observation"],
            "private_ui_retired": True,
            "cross_tab_focus": True,
        },
    ):
        raise SmokeError("browser race facts incomplete or failed")
    return record


def private_json_write(stream, record: dict, timeout: float) -> None:
    """Bounded nonblocking private-pipe write, never a log or command argument."""
    payload = (json.dumps(record, separators=(",", ":")) + "\n").encode()
    if len(payload) > 16_384 or timeout <= 0 or stream is None:
        raise SmokeError("private protocol write invalid")
    fd = stream.fileno()
    was_blocking = os.get_blocking(fd)
    deadline = time.monotonic() + timeout
    try:
        os.set_blocking(fd, False)
        while payload:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([], [fd], [], remaining)[1]:
                raise SmokeError("private protocol write deadline exceeded")
            try:
                count = os.write(fd, payload)
            except BlockingIOError:
                continue
            if count <= 0:
                raise SmokeError("private protocol write closed")
            payload = payload[count:]
    except (OSError, ValueError):
        raise SmokeError("private protocol write failed") from None
    finally:
        os.set_blocking(fd, was_blocking)


class BrowserBroker:
    """The six fixed IAM fixture operations; no arbitrary owner command relay."""

    def __init__(self, process, reader, *, credentials, timeout=10):
        self.process = process
        self.reader = reader
        self.credentials = credentials
        self.timeout = timeout

    def dispatch(self, request: dict, *, timeout=None) -> dict:
        if not isinstance(request, dict):
            raise SmokeError("browser command invalid")
        command = request.get("command")
        fields = {
            "browser_fixture": {"command"},
            "bind_browser_session": {"command", "slot", "cookie"},
            "activate_browser_tenant": {"command", "slot", "tenant"},
            "inspect_browser_session": {"command", "slot"},
            "revoke_browser_session": {"command", "slot"},
            "revoke_browser_membership": {"command"},
        }
        if (
            not isinstance(command, str)
            or command not in fields
            or set(request) != fields[command]
        ):
            raise SmokeError("browser command invalid")
        if "slot" in request and request["slot"] not in ("primary", "secondary"):
            raise SmokeError("browser slot invalid")
        if command == "activate_browser_tenant" and request["tenant"] not in (
            "fixed",
            "other",
        ):
            raise SmokeError("browser tenant invalid")
        if command == "bind_browser_session":
            cookie = request["cookie"]
            if not isinstance(cookie, str) or not re.fullmatch(
                r"(?:__Secure-)?kokoro-issuer\.session_token=[^;\s\x00-\x1f\x7f]{1,4096}",
                cookie,
            ):
                raise SmokeError("browser cookie invalid")
            self.credentials.add(cookie, cookie.partition("=")[2])
        budget = min(self.timeout, self.timeout if timeout is None else timeout)
        deadline = time.monotonic() + budget
        private_json_write(self.process.stdin, request, budget)
        try:
            record = self.reader.record(timeout=max(0, deadline - time.monotonic()))
        except Exception:
            raise SmokeError("browser owner protocol failed") from None
        if not isinstance(record, dict):
            raise SmokeError("browser owner response invalid")
        if command == "browser_fixture":
            fields = {
                "kind",
                "email",
                "password",
                "tenant_id",
                "credential_file",
                "web_origin",
            }
            if set(record) != fields or record.get("kind") != "browser_fixture":
                raise SmokeError("browser fixture response invalid")
            if any(
                not isinstance(record[key], str)
                or not record[key]
                or len(record[key]) > 4096
                for key in fields - {"kind"}
            ):
                raise SmokeError("browser fixture value invalid")
            if (
                not Path(record["credential_file"]).is_file()
                or urlsplit(record["web_origin"]).scheme != "https"
            ):
                raise SmokeError("browser fixture configuration invalid")
            self.credentials.add(record["password"], record["email"])
            return record
        if command == "inspect_browser_session":
            if (
                set(record)
                != {"kind", "slot", "exists", "unexpired", "member", "active_tenant"}
                or record.get("kind") != "browser_session"
                or record.get("slot") != request["slot"]
                or type(record.get("exists")) is not bool
                or type(record.get("unexpired")) is not bool
                or type(record.get("member")) is not bool
                or record.get("active_tenant") not in ("fixed", "other", "none")
            ):
                raise SmokeError("browser session observation invalid")
            return record
        if record != {"kind": "result", "command": command, "status": "ok"}:
            raise SmokeError("browser owner mutation rejected")
        return record


def validate_browser_failure(record) -> dict:
    fields = {"kind", "stage", "error_type", "driver_line", "driver_column"}
    stages = (
        "config",
        "cold_login",
        "tenant_rejection_recovery",
        "ui_logout",
        "independent_revocation",
        "browser_close",
    )
    if (
        not isinstance(record, dict)
        or set(record) != fields
        or record.get("kind") != "browser_failure"
        or record.get("stage") not in stages
        or record.get("error_type") not in ("Error", "TimeoutError")
    ):
        raise SmokeError("browser failure diagnostic invalid")
    line, column = record["driver_line"], record["driver_column"]
    if not (
        (line is None and column is None)
        or (
            type(line) is int
            and type(column) is int
            and 1 <= line <= 100_000
            and 1 <= column <= 100_000
        )
    ):
        raise SmokeError("browser failure frame invalid")
    return record


class BrowserJourneyError(SmokeError):
    def __init__(self, record):
        self.diagnostic = dict(validate_browser_failure(record))
        self.stage = self.diagnostic["stage"]
        super().__init__("browser " + self.stage + " failed")


def run_browser_journeys(
    *,
    node,
    env,
    broker,
    web_origin,
    proxy_port,
    processes,
    browser_processes,
    log,
    work_dir,
    timeout=180,
) -> dict:
    deadline = time.monotonic() + timeout
    reader = None
    # Do not inherit inspector/debug flags that could log private protocol input.
    driver_env = {
        key: value
        for key, value in env.items()
        if key in {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ"}
    }
    process = subprocess.Popen(
        [str(node), str(Path(__file__).with_name("web_native_session_chromium.mjs"))],
        cwd=ROOT,
        env=driver_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=log,
        start_new_session=True,
        bufsize=0,
    )
    processes.append(process)
    browser_processes.append(process)
    try:
        if process.stdout is None:
            raise SmokeError("browser protocol unavailable")
        reader = session.ProtocolReader(process.stdout.fileno())
        private_json_write(
            process.stdin,
            {
                "kind": "config",
                "app": str(APP),
                "origin": web_origin,
                "port": proxy_port,
                "work_dir": str(work_dir),
            },
            deadline - time.monotonic(),
        )
        for _ in range(64):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SmokeError("browser deadline exceeded")
            message = reader.record(timeout=remaining)
            if not isinstance(message, dict):
                raise SmokeError("browser protocol invalid")
            if (
                set(message) == {"kind", "request"}
                and message["kind"] == "owner_command"
            ):
                response = broker.dispatch(
                    message["request"], timeout=deadline - time.monotonic()
                )
                private_json_write(process.stdin, response, deadline - time.monotonic())
            elif message.get("kind") == "browser_failure":
                raise BrowserJourneyError(message)
            elif message.get("kind") == "browser_result":
                result = validate_browser_receipt(message)
                if process.wait(timeout=max(0.001, deadline - time.monotonic())) != 0:
                    raise SmokeError("browser driver failed")
                return result
            else:
                raise SmokeError("browser protocol invalid")
        raise SmokeError("browser command limit exceeded")
    except BrowserJourneyError:
        raise
    except Exception:
        raise SmokeError("browser journeys failed") from None
    finally:
        if reader is not None:
            reader.close()


class NativeCleanupError(SmokeError):
    def __init__(self, failures: list[str], quiescent: bool):
        self.failures = failures
        self.quiescent = quiescent
        super().__init__("; ".join(failures))


def native_web_redis_keys(resources: runtime.OwnedResources, origin: str) -> set[str]:
    """The current App owns login-flow and CSRF keys, scoped by public origin."""
    digest = hashlib.sha256(origin.encode()).hexdigest()
    keys: set[str] = set()
    for name in ("iam-signin-flow", "iam-csrf"):
        prefix = f"kokoro:web:{name}:{digest}:"
        found = set(
            resources.command(
                [
                    "redis-cli",
                    "-e",
                    "-u",
                    resources.redis_url,
                    "--scan",
                    "--pattern",
                    prefix + "*",
                ]
            ).splitlines()
        )
        if any(not key.startswith(prefix) for key in found):
            raise SmokeError("Web Redis inventory outside run namespace")
        keys.update(found)
    return keys


def cleanup_web_redis(
    resources: runtime.OwnedResources, origin: str, before: set[str]
) -> None:
    if before:
        raise SmokeError("Web Redis namespace was preexisting")
    keys = sorted(native_web_redis_keys(resources, origin))
    for start in range(0, len(keys), 100):
        resources.command(
            [
                "redis-cli",
                "-e",
                "-u",
                resources.redis_url,
                "UNLINK",
                *keys[start : start + 100],
            ]
        )
    if native_web_redis_keys(resources, origin):
        raise SmokeError("Web Redis namespace remains")


def close_native_resources(
    processes,
    proxies,
    reader,
    resources,
    *,
    iam_process=None,
    browser_process=None,
    iam_identity=None,
    iam_before=None,
    iam_owner_token=None,
    web_origin=None,
    web_before=None,
) -> None:
    """Close independent resources; retain dependencies when producers may live.

    The IAM host's graceful shutdown removes its DB and credentials. Avoid that
    path while a Web/BFF consumer may still be using those resources.
    Error text is deliberately allowlisted, never copied from an exception.
    """
    failures: list[str] = []
    quiescent = True
    if browser_process is not None:
        try:
            runtime.stop_owned_process(browser_process)
            browser_process.wait(timeout=5)
            if runtime.process_group_exists(browser_process.pid):
                raise SmokeError("browser process group remains")
        except Exception:
            failures.append("browser process cleanup failed")
            quiescent = False
    for proxy in reversed(proxies):
        try:
            proxy.close()
            thread = getattr(proxy, "thread", None)
            if thread is not None and thread.is_alive():
                raise SmokeError("proxy thread remains")
        except Exception:
            failures.append("owned proxy cleanup failed")
            quiescent = False
    for process in reversed(processes):
        if process is browser_process:
            continue
        if process is iam_process and not quiescent:
            # Leaving stdin open only delays EOF until this runner exits. Kill
            # this owned group without invoking IAM's DB/credential teardown.
            try:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
                if runtime.process_group_exists(process.pid):
                    raise SmokeError("IAM process group remains")
            except Exception:
                failures.append("IAM forced process cleanup failed")
            failures.append("IAM resource cleanup deferred: consumers not quiescent")
            continue
        try:
            runtime.stop_owned_process(process)
        except Exception:
            failures.append("owned process cleanup failed")
            quiescent = False
    if reader is not None:
        try:
            reader.close()
        except Exception:
            failures.append("IAM protocol cleanup failed")
    if quiescent:
        for process in reversed(processes):
            for name in ("stdin", "stdout", "stderr"):
                stream = getattr(process, name, None)
                if stream is not None:
                    try:
                        stream.close()
                    except Exception:
                        failures.append("owned pipe cleanup failed")
    if not quiescent:
        failures.append("dependency cleanup deferred: runtime not quiescent")
    else:
        if resources is not None:
            if web_before is not None:
                try:
                    cleanup_web_redis(resources, web_origin, web_before)
                except Exception:
                    failures.append("Web Redis cleanup failed")
            for label, action in (
                ("owned database cleanup", resources.cleanup),
                ("owned resource cleanup verification", resources.verify_clean),
            ):
                try:
                    action()
                except Exception:
                    failures.append(label + " failed")
            if iam_before is not None:
                try:
                    if iam_before != (set(), set()):
                        raise SmokeError("IAM namespace was preexisting")
                    after = web.iam_owned_inventory(resources, iam_identity)
                    if after != iam_before and iam_owner_token is not None:
                        web.reconcile_iam_identity(
                            resources, iam_identity, iam_owner_token
                        )
                        after = web.iam_owned_inventory(resources, iam_identity)
                    if after != iam_before:
                        raise SmokeError("IAM resources remain")
                except Exception:
                    failures.append("IAM resource cleanup failed")
    if failures:
        raise NativeCleanupError(failures, quiescent)


def run_native_command(command, *, cwd, env, log, processes) -> None:
    """Track build/install children as well as service children for failed stops."""
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    processes.append(process)
    try:
        if process.wait(timeout=90) != 0:
            raise SmokeError("owned command failed")
    except subprocess.TimeoutExpired:
        raise SmokeError("owned command deadline exceeded") from None
    # Keep the handle registered even if termination fails. The final cleanup
    # retries and refuses to drop data while this process group still exists.
    runtime.stop_owned_process(process)
    processes.remove(process)


def observe_node_version(node: Path) -> str:
    result = subprocess.run(
        [str(node), "--version"], capture_output=True, text=True, timeout=5, check=True
    ).stdout.strip()
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", result):
        raise SmokeError("Node version response invalid")
    return result.removeprefix("v")


def require_json(response: web.BrowserResponse, status: int, label: str) -> dict:
    if response.status != status:
        raise SmokeError(f"{label}: HTTP {response.status}, expected {status}")
    try:
        body = json.loads(response.body)
    except (ValueError, UnicodeError):
        raise SmokeError(f"{label}: JSON response invalid") from None
    if not isinstance(body, dict):
        raise SmokeError(f"{label}: JSON object required")
    return body


def main(argv=None) -> int:
    args = parse_args(argv)
    run_id = secrets.token_hex(12)
    web_origin = f"https://web-native-{run_id}.example.test"
    host_name = urlsplit(web_origin).hostname
    iam_resource_id = str(uuid4())
    iam_identity = web.IamOwnedIdentity(
        "iam_web_oidc_" + iam_resource_id.replace("-", ""),
        f"iam:test:bff-session-admission-host:{iam_resource_id}:",
    )
    iam_owner_token = secrets.token_hex(16)
    evidence = EVIDENCE_ROOT / run_id
    evidence.mkdir(parents=True, mode=0o700)
    evidence.chmod(0o700)
    directory = Path(tempfile.mkdtemp(prefix="work-", dir=evidence))
    resources = None
    processes: list[subprocess.Popen[bytes]] = []
    proxies: list[web.Proxy] = []
    reader = iam = None
    browser_processes = []
    browser_receipt = None
    browser_failure = None
    credential_log_check = "not_run"
    browser_mode = args.browser_journeys
    iam_before = web_before = None
    recovery_path = directory / "iam-recovery.json"
    node_versions: dict[str, str | None] = dict.fromkeys(REQUIRED_NODE_VERSIONS)
    cases = 0
    stage = "source preflight"
    expected_sources = {
        "iam": args.expected_iam_sha,
        "bff": args.expected_bff_sha,
        "app": args.expected_app_sha,
    }
    sources: dict[str, object] = {}
    failures: list[str] = []
    cleanup_failures: list[str] = []
    quiescent = True
    credentials = web.previous.CredentialRegistry(
        args.postgres_admin_url, args.redis_url, iam_owner_token
    )
    for raw in (args.postgres_admin_url, args.redis_url):
        credentials.add(unquote(urlsplit(raw).password or ""))
    # Raw diagnostics are anonymous, never retained or copied to the receipt.
    with tempfile.TemporaryFile(mode="w+b") as log:
        try:
            for owner, repo, allow_unpublished in (
                ("iam", IAM, args.allow_unpublished_iam_gitlink),
                ("bff", BFF, False),
                ("app", APP, False),
            ):
                sources[owner] = verify_source(
                    repo,
                    expected_sources[owner],
                    f"apps/kokoro-{owner}",
                    allow_unpublished,
                )
            stage = "runtime preflight"
            # Current owner engines: IAM/BFF >=24 <25; App >=22 <23.
            environments = {}
            for owner, node, package_bin in (
                ("iam", args.iam_node_bin, args.bff_node_bin.parent),
                ("bff", args.bff_node_bin, args.bff_node_bin.parent),
                ("app", args.web_node_bin, args.web_node_bin.parent),
            ):
                node_versions[owner] = observe_node_version(node)
                environments[owner] = session.node_environment(
                    node, "v" + REQUIRED_NODE_VERSIONS[owner], package_bin
                )
            iam_env, bff_env, web_env = (
                environments[owner] for owner in ("iam", "bff", "app")
            )
            stage = "resource allocation"
            resources = runtime.OwnedResources(
                args.postgres_admin_url, args.redis_url, run_id
            )
            stage = "BFF build"
            run_native_command(
                [str(args.bff_node_bin.parent / "corepack"), "pnpm", "build"],
                cwd=BFF,
                env=bff_env,
                log=log,
                processes=processes,
            )
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
                raise SmokeError("Redis unavailable")
            web_before = native_web_redis_keys(resources, web_origin)
            if web_before:
                raise SmokeError("Web Redis namespace already exists")
            iam_inventory = web.iam_owned_inventory(resources, iam_identity)
            if iam_inventory != (set(), set()):
                raise SmokeError("IAM named resources already exist")
            db_url = bff_owner_database_url(resources.create_database("bff"))
            bff_env.update(
                {
                    "KOKORO_BFF_POSTGRES_URL": db_url,
                    "KOKORO_BFF_REDIS_URL": args.redis_url,
                }
            )
            stage = "BFF schema installation"
            run_native_command(
                [str(args.bff_node_bin.parent / "corepack"), "pnpm", "db:apply-schema"],
                cwd=BFF,
                env=bff_env,
                log=log,
                processes=processes,
            )
            stage = "IAM host"
            iam_env.update(
                {
                    "IAM_TEST_ADMIN_URL": args.postgres_admin_url,
                    "IAM_TEST_REDIS_URL": args.redis_url,
                    "IAM_TEST_WEB_ORIGIN": web_origin,
                    "NODE_ENV": "test",
                    "TMPDIR": str(directory),
                    "IAM_TEST_RESOURCE_ID": iam_resource_id,
                    "IAM_TEST_RESOURCE_OWNER_TOKEN": iam_owner_token,
                }
            )
            # Keep the exact claim durable before the host can allocate anything.
            # This private file is not a receipt and never contains service URLs.
            with open(
                recovery_path,
                "x",
                opener=lambda path, flags: os.open(path, flags, 0o600),
            ) as recovery:
                json.dump(
                    {
                        "resource_id": iam_resource_id,
                        "database_name": iam_identity.database_name,
                        "redis_prefix": iam_identity.redis_prefix,
                        "owner_token": iam_owner_token,
                    },
                    recovery,
                )
                recovery.flush()
                os.fsync(recovery.fileno())
            iam = subprocess.Popen(
                [str(args.iam_node_bin), "--import", "tsx", str(IAM_HOST)],
                cwd=IAM,
                env=iam_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                start_new_session=True,
                bufsize=0,
            )
            processes.append(iam)
            iam_before = iam_inventory
            if iam.stdout is None:
                raise SmokeError("IAM host protocol absent")
            reader = session.ProtocolReader(iam.stdout.fileno())
            ready = session.validate_ready(reader.record())
            credentials.add(ready.access_token)
            receipt = native_command(iam, reader)
            credentials.add(receipt.cookie)
            for pair in receipt.cookie.split(";"):
                credentials.add(pair.partition("=")[2].strip())
            credential_path = Path(receipt.credential_file).resolve()
            if not credential_path.is_relative_to(directory.resolve()):
                raise SmokeError("IAM credential escaped run directory")
            credential = json.loads(credential_path.read_text())
            credentials.add(*(entry["secret"] for entry in credential["entries"]))
            if receipt.iam_web_origin != web_origin:
                raise SmokeError("IAM and Web origins diverged")
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
                    "KOKORO_IAM_WEB_ORIGIN": web_origin,
                    "KOKORO_IAM_ISSUER_URL": web_origin + "/iam",
                    "KOKORO_IAM_WEB_CALLBACK_URI": web_origin
                    + "/api/auth/callback/kokoro-iam",
                    "KOKORO_IAM_WEB_POST_LOGOUT_URI": web_origin + "/auth/sign-in",
                    "KOKORO_BFF_IAM_SESSION_ADMISSION_CREDENTIAL_FILE": receipt.credential_file,
                    "KOKORO_AGENT_ENABLED": "false",
                    "KOKORO_TENANT_ID": ready.tenant_id,
                    "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
                }
            )
            stage = "BFF startup"
            bff = runtime.start_process(args.bff_node_bin, BFF, bff_env, log)
            processes.append(bff)
            runtime.wait_ready(f"http://127.0.0.1:{bff_port}", bff)
            bff_proxy = web.Proxy(bff_port)
            proxies.append(bff_proxy)
            stage = "Web startup"
            next_root = web.isolated_next(directory)
            next_port = runtime.free_port()
            web_env.update(
                {
                    "NEXT_PUBLIC_SESSION_PREVIEW": "0",
                    "KOKORO_WEB_ORIGIN": web_origin,
                    "KOKORO_DOMAIN": host_name,
                    "KOKORO_BFF_BASE_URL": f"http://127.0.0.1:{bff_proxy.server_port}",
                    "KOKORO_INTERNAL_SECRET_WEB_BFF": secret,
                    "KOKORO_WEB_REDIS_URL": args.redis_url,
                    "KOKORO_TENANT_ID": ready.tenant_id,
                }
            )
            next_process = subprocess.Popen(
                [
                    str(args.web_node_bin),
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
            web_proxy = web.Proxy(
                next_port,
                host_name,
                web.certificate(directory, host_name),
                hmr_websocket=browser_mode,
            )
            proxies.append(web_proxy)
            stage = "Web HTTPS preflight"
            deadline = time.monotonic() + 30
            while True:
                try:
                    fixture = web.https_browser(
                        web_proxy.server_port, "/api/fixture-origin", web_origin
                    )
                    if fixture.status == 200:
                        break
                except (SmokeError, web.SmokeError, OSError):
                    pass
                if time.monotonic() >= deadline or next_process.poll() is not None:
                    raise SmokeError("Next origin fixture not ready")
                time.sleep(0.1)
            if browser_mode:
                stage = "browser journeys"
                broker = BrowserBroker(iam, reader, credentials=credentials)
                browser_receipt = validate_browser_receipt(
                    run_browser_journeys(
                        node=args.web_node_bin,
                        env=web_env,
                        broker=broker,
                        web_origin=web_origin,
                        proxy_port=web_proxy.server_port,
                        processes=processes,
                        browser_processes=browser_processes,
                        log=log,
                        work_dir=directory,
                    )
                )
            else:
                stage = "native session"
                session_response = web.https_browser(
                    web_proxy.server_port,
                    "/api/auth/session",
                    web_origin,
                    cookie=receipt.cookie,
                )
                body = require_json(session_response, 200, "native Web session")
                if (
                    body.get("authenticated") is not True
                    or body.get("mode") != "native"
                    or body.get("subject") != ready.user_id
                    or not isinstance(body.get("expires_at"), int)
                ):
                    raise SmokeError("native Web session response drift")
                cases += 1
                projects = web.https_browser(
                    web_proxy.server_port,
                    "/api/session/projects",
                    web_origin,
                    cookie=receipt.cookie,
                )
                project_body = require_json(projects, 200, "native Web BFF projects")
                if project_body != {"projects": []}:
                    raise SmokeError("native Web BFF project response drift")
                cases += 1
                if iam.stdin is None:
                    raise SmokeError("IAM host stdin unavailable")
                iam.stdin.write(b'{"command":"signout"}\n')
                iam.stdin.flush()
                result = reader.record()
                if result != {"kind": "result", "command": "signout", "status": "ok"}:
                    raise SmokeError("IAM signout receipt drift")
                signed_out = web.https_browser(
                    web_proxy.server_port,
                    "/api/auth/session",
                    web_origin,
                    cookie=receipt.cookie,
                )
                out_body = require_json(
                    signed_out, 401, "native Web signed-out session"
                )
                if out_body.get("error", {}).get("code") != "native_session_required":
                    raise SmokeError("native logout was not enforced")
                cases += 1
        except (Exception, KeyboardInterrupt) as error:
            if isinstance(error, BrowserJourneyError):
                stage = "browser " + error.stage
                browser_failure = error.diagnostic
            failures.append(stage + " failed")
        finally:
            try:
                close_native_resources(
                    processes,
                    proxies,
                    reader,
                    resources,
                    iam_process=iam,
                    browser_process=browser_processes[0] if browser_processes else None,
                    iam_identity=iam_identity,
                    iam_before=iam_before,
                    iam_owner_token=iam_owner_token,
                    web_origin=web_origin,
                    web_before=web_before,
                )
            except NativeCleanupError as error:
                cleanup_failures.extend(error.failures)
                quiescent = error.quiescent
            try:
                log.flush()
                log.seek(0)
                diagnostics = log.read()
                if any(
                    variant.encode() in diagnostics
                    for value in credentials.values()
                    for variant in {
                        value,
                        quote(value, safe=""),
                        quote_plus(value, safe=""),
                    }
                ):
                    raise SmokeError("credential log scan failed")
                credential_log_check = "passed"
                if not failures and not browser_mode:
                    cases += 1
            except Exception:
                credential_log_check = "failed"
                failures.append("credential log scan failed")
            if quiescent and not cleanup_failures:
                try:
                    shutil.rmtree(directory)
                except OSError:
                    cleanup_failures.append("owned files cleanup failed")
            report = {
                "status": "failed" if failures or cleanup_failures else "passed",
                "mode": "browser_journeys" if browser_mode else "minimal_http",
                "scope": (
                    "four native authentication browser journeys; not full product acceptance"
                    if browser_mode
                    else "minimal native HTTP smoke; not browser authentication journeys"
                ),
                "completed_journeys": 4 if browser_receipt is not None else 0,
                "browser": browser_receipt,
                "browser_failure": browser_failure,
                "credential_log_check": credential_log_check,
                "expected_sources": expected_sources,
                "sources": sources,
                "required_node_versions": REQUIRED_NODE_VERSIONS,
                "node_versions": node_versions,
                "stage": stage,
                "completed_checks": cases,
                "failures": failures,
                "cleanup": {
                    "status": "failed" if cleanup_failures else "passed",
                    "quiescent": quiescent,
                    "failures": cleanup_failures,
                    "owned_files_retained": directory.exists(),
                    "recovery_record": (
                        str(recovery_path.relative_to(evidence))
                        if recovery_path.is_file()
                        else None
                    ),
                },
            }
            receipt_path = evidence / "receipt.json"
            with open(
                receipt_path,
                "x",
                opener=lambda path, flags: os.open(path, flags, 0o600),
            ) as output:
                json.dump(report, output, indent=2)
                output.write("\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "completed_checks": cases,
                "receipt": str(receipt_path),
            }
        ),
        flush=True,
    )
    if failures or cleanup_failures:
        raise SmokeError("; ".join(failures + cleanup_failures))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (SmokeError, runtime.SmokeError, subprocess.SubprocessError, OSError):
        print("native smoke failed; inspect the sanitized run receipt", file=sys.stderr)
        sys.exit(1)

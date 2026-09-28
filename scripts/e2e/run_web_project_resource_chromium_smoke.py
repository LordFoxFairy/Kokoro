#!/usr/bin/env python3
"""Run-owned real Chromium Product Project → BFF → Storage resource smoke."""

from __future__ import annotations

import argparse
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
from urllib.parse import parse_qsl, urlencode, unquote, urlsplit, urlunsplit
from uuid import uuid4

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_web_bff_iam_product_session_smoke as product
import run_web_chat_chromium_smoke as chromium
import run_web_chat_worker_smoke as chat_worker


ROOT = Path(__file__).resolve().parents[2]
E2E = Path(__file__).resolve().parent
DRIVER = E2E / "web_project_resource_chromium.mjs"
WEB = ROOT / "apps/kokoro-app"
BFF = ROOT / "apps/kokoro-bff"
STORAGE = ROOT / "apps/kokoro-storage"
IAM = ROOT / "apps/kokoro-iam"


class SmokeError(RuntimeError):
    """A controlled error that contains no credential or request body."""


LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def check_configuration(env: dict[str, str]) -> dict[str, str]:
    required = (
        "KOKORO_W2_POSTGRES_ADMIN_URL",
        "KOKORO_W2_REDIS_URL",
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
    if env["KOKORO_W2_EXCLUSIVE_BUCKET"] != env["KOKORO_W2_TEST_BUCKET"]:
        raise SmokeError("exclusive bucket confirmation must match test bucket")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,62}", env["KOKORO_W2_TEST_BUCKET"]):
        raise SmokeError("test bucket name invalid")
    pg = urlsplit(env["KOKORO_W2_POSTGRES_ADMIN_URL"])
    if (
        pg.scheme not in {"postgres", "postgresql"}
        or not pg.hostname
        or pg.fragment
        or any(
            key.lower() in {"schema", "options", "search_path"}
            for key, _ in parse_qsl(pg.query)
        )
    ):
        raise SmokeError(
            "PostgreSQL admin URL must exclude owner schema and search-path options"
        )
    if pg.hostname not in LOCAL_HOSTS:
        raise SmokeError("local PostgreSQL endpoint required")
    redis = urlsplit(env["KOKORO_W2_REDIS_URL"])
    if (
        redis.scheme not in {"redis", "rediss"}
        or not redis.hostname
        or redis.query
        or redis.fragment
    ):
        raise SmokeError("explicit Redis URL without options required")
    if redis.hostname not in LOCAL_HOSTS:
        raise SmokeError("local Redis endpoint required")
    if redis.path != "/6":
        raise SmokeError(
            "W2 base Redis DB 6 required before distinct owner DB allocation"
        )
    for name in ("KOKORO_OBJECT_STORE_ENDPOINT", "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"):
        url = urlsplit(env[name])
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
        ):
            raise SmokeError(f"{name} must be an HTTP(S) origin")
        if url.hostname not in LOCAL_HOSTS:
            raise SmokeError("local object store endpoint required")
    if env.get("KOKORO_OBJECT_STORE_PROFILE") != "custom":
        raise SmokeError("explicit custom S3 profile required")
    if env.get("KOKORO_OBJECT_STORE_FORCE_PATH_STYLE") != "true":
        raise SmokeError("path-style test bucket required")
    if env.get("AWS_SESSION_TOKEN") or env.get("KOKORO_OBJECT_STORE_SESSION_TOKEN"):
        raise SmokeError("explicit test credentials cannot use a session token")
    try:
        scanner_port = int(env["KOKORO_SCANNER_PORT"])
    except ValueError:
        raise SmokeError("scanner port invalid") from None
    if scanner_port == 3310:
        raise SmokeError("scanner port 3310 is reserved for the shared Web preview")
    if not 1 <= scanner_port <= 65535:
        raise SmokeError("scanner port invalid")
    if env["KOKORO_SCANNER_HOST"] not in LOCAL_HOSTS:
        raise SmokeError("local scanner endpoint required")
    return {name: env[name] for name in required}


def _redis_db(base: str, number: int) -> str:
    parts = urlsplit(base)
    if (
        parts.scheme not in {"redis", "rediss"}
        or not parts.hostname
        or parts.query
        or parts.fragment
    ):
        raise SmokeError("explicit Redis URL without options required")
    return urlunsplit((parts.scheme, parts.netloc, f"/{number}", "", ""))


def _storage_database_url(bff_database_url: str) -> str:
    parts = urlsplit(bff_database_url)
    if not parts.path.startswith("/") or parts.fragment:
        raise SmokeError("run-owned PostgreSQL URL invalid")
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query)
        if key.lower() not in {"schema", "options", "search_path"}
    ]
    query.append(("schema", "kokoro_storage"))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def _isolated_owner(source: Path, directory: Path, name: str) -> Path:
    """Compile only an exact clean owner snapshot, never its live checkout."""
    destination = directory / name
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            ".git", "node_modules", "dist", ".next", ".tmp", "coverage"
        ),
    )
    (destination / "node_modules").symlink_to(
        source / "node_modules", target_is_directory=True
    )
    return destination


def _run_owner_command(
    command: list[str], *, cwd: Path, env: dict[str, str], log, timeout: float
) -> None:
    if (
        product.runtime.run_owned_command(
            command, cwd=cwd, env=env, log=log, timeout=timeout
        )
        != 0
    ):
        raise SmokeError(f"{cwd.name} owned build or schema command failed")


def _s3_operation(
    node: Path, action: str, bucket: str, prefix: str, env: dict[str, str]
) -> None:
    if action not in {"preflight", "cleanup"} or not prefix.endswith("/"):
        raise SmokeError("owned S3 operation invalid")
    # The W2 owner smoke owns the actual versioned-object admission and exact
    # VersionId+ETag deletion rules. This browser runner does not fork them.
    script = r"""
      import { createRequire } from 'node:module';
      import { pathToFileURL } from 'node:url';
      const [storagePackage, helperPath, action, bucket, prefix] = process.argv.slice(1);
      const requireStorage = createRequire(pathToFileURL(storagePackage));
      const { S3Client } = requireStorage('@aws-sdk/client-s3');
      const { preflightS3, cleanupObjects } = await import(pathToFileURL(helperPath));
      const s3 = new S3Client({ endpoint: process.env.KOKORO_OBJECT_STORE_ENDPOINT,
        region: process.env.KOKORO_OBJECT_STORE_REGION, forcePathStyle: true,
        credentials: { accessKeyId: process.env.KOKORO_OBJECT_STORE_ACCESS_KEY_ID,
          secretAccessKey: process.env.KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY }, maxAttempts: 1 });
      try {
        if (action === 'preflight') await preflightS3(s3, { bucket }, prefix);
        else await cleanupObjects(s3, bucket, prefix);
      } finally { s3.destroy(); }
    """
    try:
        result = subprocess.run(
            [
                str(node),
                "--input-type=module",
                "-e",
                script,
                str(STORAGE / "package.json"),
                str(E2E / "run_w2_bff_storage_smoke.mjs"),
                action,
                bucket,
                prefix,
            ],
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise SmokeError(f"owned S3 {action} command failed") from None
    if result.returncode != 0:
        raise SmokeError(
            f"owned S3 {action} failed; preserve object and database evidence"
        )


def _assert_empty_redis(
    resources: product.runtime.OwnedResources, url: str, label: str
) -> None:
    keys = resources.command(["redis-cli", "-e", "-u", url, "--scan"]).splitlines()
    if keys:
        raise SmokeError(
            f"{label} Redis logical database is not empty; refusing shared-state adoption"
        )


def _node_path(value: str | None, name: str) -> Path:
    if not value:
        raise SmokeError(f"{name} is required")
    path = Path(value).expanduser().resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise SmokeError(f"{name} must be an executable absolute Node binary")
    return path


def _verify_source(repo: Path, expected: str | None, label: str) -> dict[str, object]:
    if expected is None or re.fullmatch(r"[a-f0-9]{40}", expected) is None:
        raise SmokeError(f"expected {label} SHA must be a full commit")
    return product.session.verify_source(repo, expected, label)


def _driver_result(
    node: Path,
    origin: str,
    ready: product.previous.Ready,
    member: product.ActorIdentity,
    timeout: float,
    screenshot: Path,
    run_id: str,
) -> dict[str, object]:
    host = urlsplit(origin).hostname
    if host is None or ready.redirect_uri != origin + "/api/auth/callback/kokoro-iam":
        raise SmokeError("real Chromium origin or IAM redirect drift")
    input_value = {
        "web_origin": origin,
        "web_host": host,
        "web_root": str(WEB),
        "screenshot": str(screenshot),
        "owner_email": ready.email,
        "owner_password": ready.password,
        "member_email": member.email,
        "member_password": member.password,
        "filename": f"w2-{run_id}.txt",
        "file_content": f"W2 project resource browser bytes {run_id}",
        "timeout_ms": int(timeout * 1000),
    }
    try:
        completed = subprocess.run(
            [str(node), str(DRIVER)],
            input=json.dumps(input_value),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout + 90,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise SmokeError("real Chromium driver process failed") from None
    if completed.returncode != 0:
        stages = [
            line
            for line in completed.stderr.splitlines()
            if line.startswith("MILESTONE:")
        ]
        stage = stages[-1] if stages else "MILESTONE:unknown"
        phases = [
            line.removeprefix("FAILURE_PHASE:")
            for line in completed.stderr.splitlines()
            if re.fullmatch(r"FAILURE_PHASE:[a-z-]{1,48}", line)
        ]
        phase = phases[-1] if phases else "unknown"
        raise SmokeError(f"real Chromium driver failed after {stage}; phase={phase}")
    try:
        evidence = json.loads(completed.stdout)
    except (ValueError, UnicodeError):
        raise SmokeError("real Chromium evidence malformed") from None
    if (
        not isinstance(evidence, dict)
        or evidence.get("browser") != "chromium"
        or evidence.get("entry_url") != origin + "/login"
        or evidence.get("project_post_status") != 200
        or evidence.get("upload_status") != 200
        or evidence.get("owner_get_after_upload") is not True
        or evidence.get("owner_get_after_reload") is not True
        or evidence.get("privacy")
        != {
            "list_status": 404,
            "list_code": "project_not_found",
            "write_status": 404,
            "write_code": "project_not_found",
        }
        or not isinstance(evidence.get("owner_subject"), str)
        or evidence["owner_subject"] == member.user_id
        or evidence.get("member_subject") != member.user_id
        or not isinstance(evidence.get("project_slug"), str)
        or not isinstance(evidence.get("project_id"), str)
        or evidence["project_id"].startswith("preview-project")
        or not isinstance(evidence.get("asset_id"), str)
        or evidence.get("screenshot") != str(screenshot)
        or not screenshot.is_file()
        or screenshot.stat().st_size == 0
    ):
        raise SmokeError("real Chromium Product Project evidence drift")
    login = evidence.get("login")
    if not isinstance(login, dict) or set(login) != {"owner", "member"}:
        raise SmokeError("current tuple real IAM login evidence missing")
    for actor in ("owner", "member"):
        value = login[actor]
        if (
            not isinstance(value, dict)
            or value.get("form_status") != 200
            or value.get("callback_status") != 303
            or value.get("session_status") != 200
            or value.get("product_cookie") != "HttpOnly+Secure+Lax"
        ):
            raise SmokeError("current tuple real IAM login evidence drift")
    personal = evidence.get("personal")
    if (
        not isinstance(personal, dict)
        or not isinstance(personal.get("asset_id"), str)
        or re.fullmatch(r"asset:[a-f0-9]{64}", personal["asset_id"]) is None
        or not isinstance(personal.get("filename"), str)
        or re.fullmatch(r"personal-w2-[a-f0-9]{24}\.txt", personal["filename"])
        is None
        or not isinstance(personal.get("content_sha256"), str)
        or re.fullmatch(r"[a-f0-9]{64}", personal["content_sha256"]) is None
        or personal.get("post_status") != 200
        or not isinstance(personal.get("concurrent_statuses"), list)
        or sorted(personal["concurrent_statuses"]) not in ([200, 200], [200, 409])
        or personal.get("replay_status") != 200
        or personal.get("conflict_status") != 409
        or personal.get("infected_status") != 422
        or personal.get("infected_replay_status") != 422
        or not isinstance(personal.get("visible_asset_id"), str)
        or re.fullmatch(r"asset:[a-f0-9]{64}", personal["visible_asset_id"]) is None
        or personal["visible_asset_id"] == personal["asset_id"]
        or not isinstance(personal.get("visible_filename"), str)
        or re.fullmatch(r"visible-w2-[a-f0-9]{24}\.txt", personal["visible_filename"]) is None
        or not isinstance(personal.get("visible_content_sha256"), str)
        or re.fullmatch(r"[a-f0-9]{64}", personal["visible_content_sha256"]) is None
        or personal.get("visible_post_status") != 200
        or personal.get("visible_owner_get") is not True
        or personal.get("owner_get_after_post") is not True
        or personal.get("owner_get_after_reload") is not True
        or personal.get("member_get_status") != 200
        or personal.get("member_empty") is not True
    ):
        raise SmokeError("real Chromium personal Library evidence drift")
    return evidence


def _durable_owner_facts(
    resources: product.runtime.OwnedResources,
    database_url: str,
    ready: product.previous.Ready,
    browser: dict[str, object],
) -> None:
    named_values = (
        ("tenant", ready.tenant_id),
        ("owner", browser["owner_subject"]),
        ("project", browser["project_id"]),
        ("asset", browser["asset_id"]),
        ("personal_asset", browser["personal"]["asset_id"]),
        ("visible_asset", browser["personal"]["visible_asset_id"]),
        ("member", browser["member_subject"]),
    )
    for label, value in named_values:
        pattern = r"asset:[a-f0-9]{64}" if label in {"asset", "personal_asset", "visible_asset"} else r"[A-Za-z0-9_-]{1,191}"
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            raise SmokeError(
                f"browser {label} identifier invalid for durable verification"
            )
    values = tuple(value for _, value in named_values)
    tenant, owner, project, asset, personal_asset, visible_asset, member = values
    query = (
        "SELECT (SELECT count(*) FROM kokoro_bff.bff_project WHERE tenant_id='"
        + tenant
        + "' AND owner_id='"
        + owner
        + "' AND project_id='"
        + project
        + "')::text || ',' || "
        "(SELECT count(*) FROM kokoro_storage.storage_asset WHERE tenant_id='"
        + tenant
        + "' AND scope_kind='project' AND scope_id='"
        + project
        + "' AND asset_id='"
        + asset
        + "' AND scan_state='clean')::text || ',' || "
        "(SELECT count(*) FROM kokoro_storage.storage_asset WHERE tenant_id='"
        + tenant
        + "' AND scope_kind='personal' AND scope_id='"
        + owner
        + "' AND asset_id='"
        + personal_asset
        + "' AND scan_state='clean' AND upload_purpose='asset')::text || ',' || "
        "(SELECT count(*) FROM kokoro_storage.storage_upload WHERE tenant_id='"
        + tenant
        + "' AND scope_kind='personal' AND scope_id='"
        + owner
        + "' AND asset_id='"
        + personal_asset
        + "' AND state='completed')::text || ',' || "
        "(SELECT count(*) FROM kokoro_storage.storage_asset WHERE tenant_id='"
        + tenant
        + "' AND scope_kind='personal' AND scope_id='"
        + owner
        + "' AND asset_id='"
        + visible_asset
        + "' AND scan_state='clean' AND upload_purpose='asset')::text || ',' || "
        "(SELECT count(*) FROM kokoro_storage.storage_upload WHERE tenant_id='"
        + tenant
        + "' AND scope_kind='personal' AND scope_id='"
        + owner
        + "' AND asset_id='"
        + visible_asset
        + "' AND state='completed')::text || ',' || "
        "(SELECT count(*) FROM kokoro_storage.storage_asset WHERE tenant_id='"
        + tenant
        + "' AND scope_kind='personal' AND scope_id='"
        + member
        + "')::text || ',' || "
        "(SELECT count(*) FROM kokoro_bff.bff_idempotency_receipt WHERE status=200 AND response_body #>> '{data,file,asset_id}'='"
        + personal_asset
        + "')::text || ',' || "
        "(SELECT count(*) FROM kokoro_bff.bff_idempotency_receipt WHERE status=200 AND response_body #>> '{data,file,asset_id}'='"
        + visible_asset
        + "')::text || ',' || "
        "(SELECT count(*) FROM kokoro_bff.bff_idempotency_receipt WHERE status=200 AND scope LIKE '%personal-file-upload:v1%' AND response_body ? 'upload_id')::text || ',' || "
        "(SELECT count(*) FROM kokoro_bff.bff_idempotency_receipt WHERE status=422 AND response_body #>> '{error,code}'='library_file_infected')::text"
    )
    actual = resources.command(
        ["psql", database_url, "-X", "-v", "ON_ERROR_STOP=1", "-Atc", query]
    ).strip()
    if actual != "1,1,1,1,1,1,0,1,1,3,1":
        if re.fullmatch(r"[0-9]+(?:,[0-9]+){10}", actual) is None:
            raise SmokeError("Project or personal Library durable owner fact malformed")
        raise SmokeError(f"Project or personal Library durable owner fact drift: {actual}")


def _run_smoke(args: argparse.Namespace, config: dict[str, str]) -> dict[str, object]:
    iam_node = _node_path(args.iam_node_bin, "iam-node-bin")
    node22 = _node_path(args.node22_bin, "node22-bin")
    node24 = _node_path(args.node24_bin, "node24-bin")
    if not 20 <= args.timeout <= 600:
        raise SmokeError("timeout must be between 20 and 600 seconds")
    root_commit = product.runtime.command_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"]
    ).strip()
    sources = {
        "web": _verify_source(WEB, args.expected_web_sha, "apps/kokoro-app"),
        "bff": _verify_source(BFF, args.expected_bff_sha, "apps/kokoro-bff"),
        "storage": _verify_source(
            STORAGE, args.expected_storage_sha, "apps/kokoro-storage"
        ),
        "iam": _verify_source(IAM, args.expected_iam_sha, "apps/kokoro-iam"),
    }
    iam_env = product.session.node_environment(iam_node, "v24.20.0", node22.parent)
    node22_env = product.session.node_environment(node22, "v22.22.2", node22.parent)
    storage_env = product.session.node_environment(node24, "v24.20.0", node24.parent)
    storage_redis = _redis_db(config["KOKORO_W2_REDIS_URL"], 6)
    bff_redis = _redis_db(config["KOKORO_W2_REDIS_URL"], 8)
    web_iam_redis = _redis_db(config["KOKORO_W2_REDIS_URL"], 7)
    run_id = secrets.token_hex(12)
    iam_resource_id = str(uuid4())
    iam_identity = product.named_iam_identity(iam_resource_id)
    iam_owner_token = secrets.token_hex(16)
    bff_secret = secrets.token_urlsafe(32)
    storage_secret = secrets.token_urlsafe(32)
    infra = product.runtime.OwnedResources(
        config["KOKORO_W2_POSTGRES_ADMIN_URL"], web_iam_redis, run_id
    )
    credentials = product.previous.CredentialRegistry(
        config["KOKORO_W2_POSTGRES_ADMIN_URL"],
        storage_redis,
        bff_redis,
        web_iam_redis,
        config["KOKORO_OBJECT_STORE_ACCESS_KEY_ID"],
        config["KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY"],
        iam_owner_token,
        bff_secret,
        storage_secret,
    )
    for raw in (
        config["KOKORO_W2_POSTGRES_ADMIN_URL"],
        storage_redis,
        bff_redis,
        web_iam_redis,
    ):
        password = unquote(urlsplit(raw).password or "")
        if len(password) >= 12:
            credentials.add(password)
    process_list: list[subprocess.Popen[bytes]] = []
    proxies: list[object] = []
    reader: product.session.ProtocolReader | None = None
    before_web: set[str] | None = None
    iam_attempted = False
    s3_prefix: str | None = None
    s3_preflight = False
    stage = "preflight"
    error: BaseException | None = None
    cleanup_failures: list[str] = []
    browser: dict[str, object] | None = None
    owner_db_url: str | None = None
    directory = Path(tempfile.mkdtemp(prefix="kokoro-w2-web-project-", dir=ROOT.parent))
    os.chmod(directory, 0o700)
    with chromium.OwnedTlsReservation.reserve() as reservation:
        tls_port = reservation.port
        host = f"web-{run_id}.example.test"
        web_origin = f"https://{host}:{tls_port}"
        with (directory / "process.log").open("w+b") as log:
            try:
                stage = "infrastructure preflight"
                infra.command(
                    [
                        "psql",
                        config["KOKORO_W2_POSTGRES_ADMIN_URL"],
                        "-X",
                        "-v",
                        "ON_ERROR_STOP=1",
                        "-Atc",
                        "SELECT 1",
                    ]
                )
                for label, url in (("Storage", storage_redis), ("BFF", bff_redis)):
                    if (
                        infra.command(["redis-cli", "-e", "-u", url, "PING"]).strip()
                        != "PONG"
                    ):
                        raise SmokeError(f"{label} Redis unavailable")
                    _assert_empty_redis(infra, url, label)
                infra.claim_redis_prefix()
                before_web = product.web_redis_keys(web_iam_redis, web_origin, infra)
                if product.iam_owned_inventory(infra, iam_identity) != (set(), set()):
                    raise SmokeError("IAM named resources already exist")

                stage = "isolated owner source and schema"
                bff_root = _isolated_owner(BFF, directory, "bff")
                storage_root = _isolated_owner(STORAGE, directory, "storage")
                owner_db_url = infra.create_database("bff")
                bff_db_url = product.bff_owner_database_url(owner_db_url)
                storage_db_url = _storage_database_url(owner_db_url)
                bff_env = {
                    **node22_env,
                    "NODE_ENV": "development",
                    "KOKORO_BFF_POSTGRES_URL": bff_db_url,
                    "KOKORO_BFF_REDIS_URL": bff_redis,
                }
                storage_owner_env = {
                    **storage_env,
                    "NODE_ENV": "development",
                    "KOKORO_POSTGRES_URL": storage_db_url,
                    "KOKORO_REDIS_URL": storage_redis,
                }
                # Direct project-local tool binaries avoid package-manager
                # install hooks against symlinked live node_modules.
                _run_owner_command(
                    [
                        str(node22),
                        str(bff_root / "node_modules/typescript/bin/tsc"),
                        "-p",
                        "tsconfig.json",
                    ],
                    cwd=bff_root,
                    env=bff_env,
                    log=log,
                    timeout=120,
                )
                _run_owner_command(
                    [str(node22), "scripts/apply-schema.mjs"],
                    cwd=bff_root,
                    env=bff_env,
                    log=log,
                    timeout=90,
                )
                _run_owner_command(
                    [
                        str(node24),
                        str(storage_root / "node_modules/typescript/bin/tsc"),
                        "-p",
                        "tsconfig.build.json",
                    ],
                    cwd=storage_root,
                    env=storage_owner_env,
                    log=log,
                    timeout=120,
                )
                _run_owner_command(
                    [
                        str(node24),
                        str(storage_root / "node_modules/tsx/dist/cli.mjs"),
                        "scripts/apply-schema.ts",
                    ],
                    cwd=storage_root,
                    env=storage_owner_env,
                    log=log,
                    timeout=90,
                )

                stage = "real IAM host"
                iam_env.update(
                    {
                        "IAM_TEST_ADMIN_URL": config["KOKORO_W2_POSTGRES_ADMIN_URL"],
                        "IAM_TEST_REDIS_URL": web_iam_redis,
                        "IAM_TEST_WEB_ORIGIN": web_origin,
                        "IAM_TEST_RESOURCE_ID": iam_resource_id,
                        "IAM_TEST_RESOURCE_OWNER_TOKEN": iam_owner_token,
                        "NODE_ENV": "test",
                    }
                )
                iam_attempted = True
                iam = subprocess.Popen(
                    [str(iam_node), "--import", "tsx", str(product.HOST)],
                    cwd=IAM,
                    env=iam_env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=log,
                    start_new_session=True,
                    bufsize=0,
                )
                process_list.append(iam)
                if iam.stdout is None:
                    raise SmokeError("IAM host protocol absent")
                reader = product.session.ProtocolReader(iam.stdout.fileno())
                ready = product.validate_ready(reader.record(), web_origin)
                if (ready.database_name, ready.redis_prefix) != (
                    iam_identity.database_name,
                    iam_identity.redis_prefix,
                ):
                    raise SmokeError("IAM ready identity differs from run ownership")
                credentials.add(ready.client_secret, ready.password)
                actors = product.request_actor_matrix(iam, reader, ready, credentials)
                member = actors.same_tenant_member
                s3_prefix = ready.tenant_id + "/"
                stage = "exclusive S3 prefix admission"
                _s3_operation(
                    node24,
                    "preflight",
                    config["KOKORO_W2_TEST_BUCKET"],
                    s3_prefix,
                    dict(os.environ),
                )
                s3_preflight = True

                stage = "Storage real S3/ClamAV startup"
                storage_port = product.runtime.free_port()
                storage_base = f"http://127.0.0.1:{storage_port}"
                storage_owner_env.update(
                    {
                        "KOKORO_STORAGE_HOST": "127.0.0.1",
                        "KOKORO_STORAGE_PORT": str(storage_port),
                        "KOKORO_STORAGE_SERVICE_CREDENTIALS": f"web-bff={storage_secret}",
                        "KOKORO_OBJECT_STORE_DRIVER": "s3",
                        "KOKORO_OBJECT_STORE_PROFILE": "custom",
                        "KOKORO_OBJECT_STORE_BUCKET": config["KOKORO_W2_TEST_BUCKET"],
                        "KOKORO_OBJECT_STORE_REGION": config[
                            "KOKORO_OBJECT_STORE_REGION"
                        ],
                        "KOKORO_OBJECT_STORE_ENDPOINT": config[
                            "KOKORO_OBJECT_STORE_ENDPOINT"
                        ],
                        "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": config[
                            "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"
                        ],
                        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": config[
                            "KOKORO_OBJECT_STORE_ACCESS_KEY_ID"
                        ],
                        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY": config[
                            "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY"
                        ],
                        "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "true",
                        "KOKORO_SCANNER_DRIVER": "clamav",
                        "KOKORO_SCANNER_HOST": config["KOKORO_SCANNER_HOST"],
                        "KOKORO_SCANNER_PORT": config["KOKORO_SCANNER_PORT"],
                    }
                )
                storage = product.runtime.start_process(
                    node24, storage_root, storage_owner_env, log
                )
                process_list.append(storage)
                product.runtime.wait_ready(storage_base, storage)

                stage = "BFF real IAM/Storage startup"
                bff_port = product.runtime.free_port()
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
                        "KOKORO_AGENT_ENABLED": "false",
                        "KOKORO_TENANT_ID": ready.tenant_id,
                        "KOKORO_DOMAIN": f"{run_id}.smoke.localhost",
                        "KOKORO_BFF_STORAGE_SECRET": storage_secret,
                        "KOKORO_STORAGE_RPC_BASE_URL": storage_base,
                        "KOKORO_STORAGE_OBJECT_ORIGIN": config[
                            "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"
                        ],
                    }
                )
                bff = product.runtime.start_process(node22, bff_root, bff_env, log)
                process_list.append(bff)
                product.runtime.wait_ready(f"http://127.0.0.1:{bff_port}", bff)
                bff_proxy = chat_worker.BoundedObservingProxy(
                    bff_port, credentials=credentials
                )
                proxies.append(bff_proxy)

                stage = "isolated Web HTTPS production build"
                next_root = product.isolated_next(directory)
                browser_mode = chat_worker.BrowserOriginMode(
                    tls_port, lambda *_: None, lambda *_: {}
                )
                chat_worker._configure_next_browser_port(next_root, browser_mode)
                web_env = product.session.node_environment(
                    node22, "v22.22.2", node22.parent
                )
                web_env.update(
                    {
                        "KOKORO_WEB_ORIGIN": web_origin,
                        "KOKORO_DOMAIN": host,
                        "KOKORO_BFF_BASE_URL": f"http://127.0.0.1:{bff_proxy.server_port}",
                        "KOKORO_INTERNAL_SECRET_WEB_BFF": bff_secret,
                        "KOKORO_WEB_REDIS_URL": web_iam_redis,
                        "KOKORO_TENANT_ID": ready.tenant_id,
                        "KOKORO_OIDC_CLIENT_ID": ready.client_id,
                        "KOKORO_OIDC_CLIENT_SECRET": ready.client_secret,
                        "KOKORO_WEB_AUTH_SECRET": secrets.token_hex(32),
                        "NEXTAUTH_URL": web_origin + "/api/auth",
                    }
                )
                credentials.add(web_env["KOKORO_WEB_AUTH_SECRET"])
                _run_owner_command(
                    [
                        str(node22),
                        str(next_root / "node_modules/next/dist/bin/next"),
                        "build",
                    ],
                    cwd=next_root,
                    env=web_env,
                    log=log,
                    timeout=180,
                )
                web_env["NODE_ENV"] = "test"
                next_port = product.runtime.free_port()
                next_process = subprocess.Popen(
                    [str(node22), str(next_root / "server.cjs"), str(next_port), host],
                    cwd=next_root,
                    env=web_env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=log,
                    start_new_session=True,
                )
                process_list.append(next_process)
                web_proxy = chromium.OwnedBrowserTlsProxy.from_reservation(
                    reservation,
                    next_port,
                    host,
                    f"{host}:{tls_port}",
                    product.certificate(directory, host),
                )
                proxies.append(web_proxy)
                stage = "Web HTTPS origin preflight"
                deadline = time.monotonic() + 30
                while True:
                    try:
                        response = product.https_browser(
                            tls_port, "/api/fixture-origin", web_origin
                        )
                        if response.status == 200:
                            observed_origin = json.loads(response.body)
                            if observed_origin == {
                                "origin": web_origin,
                                "host": f"{host}:{tls_port}",
                                "proto": "https",
                            }:
                                break
                    except (product.SmokeError, ValueError, UnicodeError):
                        pass
                    if time.monotonic() >= deadline or next_process.poll() is not None:
                        raise SmokeError("isolated Next HTTPS origin not ready")
                    time.sleep(0.1)

                stage = "real Chromium Project and personal Library Product flows"
                screenshot = directory / "project-resource.png"
                browser = _driver_result(
                    node22, web_origin, ready, member, args.timeout, screenshot, run_id
                )
                browser["screenshot_sha256"] = hashlib.sha256(
                    screenshot.read_bytes()
                ).hexdigest()
                del browser["screenshot"]
                _durable_owner_facts(infra, owner_db_url, ready, browser)
                log.flush()
                product.previous.assert_log_clean(
                    directory / "process.log", credentials.values()
                )
            except BaseException as caught:
                error = caught
            finally:
                for proxy in reversed(proxies):
                    try:
                        proxy.close()
                    except Exception:
                        cleanup_failures.append("owned proxy cleanup")
                for process in reversed(process_list):
                    try:
                        product.runtime.stop_owned_process(process)
                    except Exception:
                        cleanup_failures.append("owned process cleanup")
                if not cleanup_failures:
                    if s3_preflight and s3_prefix is not None:
                        try:
                            _s3_operation(
                                node24,
                                "cleanup",
                                config["KOKORO_W2_TEST_BUCKET"],
                                s3_prefix,
                                dict(os.environ),
                            )
                        except Exception:
                            cleanup_failures.append(
                                "exact owned S3 object cleanup; database retained"
                            )
                    if not cleanup_failures:
                        try:
                            infra.cleanup()
                            infra.verify_clean()
                        except Exception:
                            cleanup_failures.append(
                                "owned BFF/Storage database cleanup"
                            )
                    if before_web is not None:
                        try:
                            chat_worker._cleanup_web_redis(
                                web_iam_redis, web_origin, infra, before_web
                            )
                        except Exception:
                            cleanup_failures.append("owned Web Redis cleanup")
                    if iam_attempted:
                        try:
                            product.reconcile_iam_identity(
                                infra, iam_identity, iam_owner_token
                            )
                        except Exception:
                            cleanup_failures.append("named IAM resource cleanup")
                    for label, url in (("Storage", storage_redis), ("BFF", bff_redis)):
                        try:
                            _assert_empty_redis(infra, url, label)
                        except Exception:
                            cleanup_failures.append(f"{label} Redis postrun inventory")
                if reader is not None:
                    try:
                        reader.close()
                    except Exception:
                        cleanup_failures.append("IAM protocol close")
                try:
                    log.flush()
                    product.previous.assert_log_clean(
                        directory / "process.log", credentials.values()
                    )
                except Exception:
                    cleanup_failures.append("credential log scan")
    if error is not None or cleanup_failures:
        safe_error = (
            str(error)
            if isinstance(error, SmokeError)
            else type(error).__name__
            if error is not None
            else "none"
        )
        evidence = directory.with_suffix(".evidence.json")
        metadata = {
            "stage": stage,
            "error": safe_error,
            "cleanup": cleanup_failures,
            "database_candidates": infra.database_names,
            "iam_database_candidate": iam_identity.database_name,
            "iam_redis_prefix": iam_identity.redis_prefix,
            "s3_bucket": config["KOKORO_W2_TEST_BUCKET"],
            "s3_prefix": s3_prefix,
            "sources": {name: source["sha"] for name, source in sources.items()},
        }
        fd = os.open(evidence, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, sort_keys=True)
        # The temporary owner copies and process log can contain OAuth details;
        # retain only safe ownership metadata, never the raw log or .next tree.
        shutil.rmtree(directory)
        raise SmokeError(
            f"{stage}: {safe_error}; cleanup={','.join(cleanup_failures) or 'none'}; ownership={evidence}"
        ) from None
    if browser is None:
        raise SmokeError("browser evidence missing")
    result = {
        "status": "PASS",
        "root_commit": root_commit,
        "sources": sources,
        "flow": "real IAM Chromium login → Web Project click/upload → concurrent same-key personal Product CLEAN/replay/conflict/EICAR → visible personal Library file-picker upload/GET/reload → Storage S3/ClamAV → member private",
        "login_boundary": {
            "source_tuple": {
                name: source["sha"]
                for name, source in sources.items()
                if name in {"web", "bff", "iam"}
            },
            "owner": browser["login"]["owner"],
            "member": browser["login"]["member"],
        },
        "browser": browser,
        "owned_postgres_databases_remaining": 0,
        "owned_redis_keys_remaining": 0,
        "owned_processes_remaining": 0,
        "owned_s3_versions_remaining": 0,
    }
    shutil.rmtree(directory)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--iam-node-bin")
    parser.add_argument("--node22-bin")
    parser.add_argument("--node24-bin")
    for owner in ("web", "bff", "storage", "iam"):
        parser.add_argument(f"--expected-{owner}-sha")
    parser.add_argument("--timeout", type=float, default=180)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    check_configuration(dict(os.environ))
    if args.check_config:
        print("W2 browser configuration shape valid; provider not contacted")
        return 0
    print(
        json.dumps(
            _run_smoke(args, check_configuration(dict(os.environ))), sort_keys=True
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeError as error:
        print(f"W2 Chromium smoke failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None

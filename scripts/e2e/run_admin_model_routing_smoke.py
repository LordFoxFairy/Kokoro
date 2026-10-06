#!/usr/bin/env python3
"""Owned real IAM qualification → BFF admin route → System PG acceptance."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

if __package__:
    from . import run_bff_iam_session_smoke as session
    from . import run_system_owner_smoke as system
    from . import capability_bff_smoke_runtime as runtime
    from .bff_owner_schema import bff_owner_database_url
else:
    import run_bff_iam_session_smoke as session
    import run_system_owner_smoke as system
    import capability_bff_smoke_runtime as runtime
    from bff_owner_schema import bff_owner_database_url

ROOT = Path(__file__).resolve().parents[2]
IAM = ROOT / "apps/kokoro-iam"
SYSTEM = ROOT / "apps/kokoro-system"
ARTIFACT_SHA = "94ed91655741cbba66ce80a4c41717b9179cc509cb6858534e0b78aa3e6dc059"
HOST = IAM / "test/fixtures/model-routing-admin-host.ts"


def require(condition: bool, code: str) -> None:
    if not condition:
        raise runtime.SmokeError(code)


def source(repo: Path, expected: str) -> str:
    require(re.fullmatch(r"[a-f0-9]{40}", expected) is not None, "invalid_source_sha")
    actual = runtime.command_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"]
    ).strip()
    require(actual == expected, "source_sha_mismatch")
    # Candidate test/source hashes are independently frozen by Root, not inferred from HEAD.
    return actual


def snapshot(
    resources: system.OwnedResources,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    databases = resources.command(
        [
            "psql",
            resources.postgres,
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-Atc",
            "SELECT datname FROM pg_database ORDER BY datname",
        ]
    ).splitlines()
    keys = resources.command(
        [
            "redis-cli",
            "-e",
            "-u",
            resources.redis,
            "--scan",
            "--pattern",
            "iam:test:model-routing-admin-host:*",
        ]
    ).splitlines()
    return tuple(databases), tuple(sorted(keys))


def system_database_url(url: str) -> str:
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query)
        if key.lower() not in {"schema", "options", "search_path"}
    ]
    query.append(("schema", "system"))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def seed_route(base: str, tenant: str, token: str, run_id: str) -> dict:
    """Only official owner commands; no table inserts or fixture publication bypass."""

    def mutate(
        path, body, *, method="POST", global_scope=True, version=None, create=False
    ):
        headers = {
            "authorization": "Bearer " + token,
            "x-kokoro-service": "system-admin",
            "x-kokoro-actor-id": "owned-routing-fixture",
            "x-kokoro-iam-permissions": "system:read,system:write,system:publish",
            "idempotency-key": secrets.token_hex(16),
            "x-request-id": secrets.token_hex(16),
        }
        if not global_scope:
            headers["x-kokoro-tenant-id"] = tenant
        if version is not None:
            headers["if-match"] = '"' + str(version) + '"'
        if create:
            headers["if-none-match"] = "*"
        expected = 200 if method == "PUT" or path.endswith("/publish") else 201
        response = system.http_json(
            base,
            "/v1/system/" + path,
            method=method,
            headers=headers,
            body=body,
            expected=expected,
        )
        require(set(response) == {"data"}, "seed_envelope_invalid")
        return system.data_of(response)

    product = mutate(
        "products",
        {"product_key": "routing-" + run_id, "name": "Owned routing product"},
    )
    feature = "chat." + run_id
    mutate(
        "features",
        {
            "global_feature_key": feature,
            "product_id": product["id"],
            "display_name": "Owned routing chat",
            "result_contract": {
                "schema_version": 1,
                "outcome_kind": "message",
                "media_types": ["text/plain"],
                "required_fields": ["content"],
            },
        },
    )
    provider = mutate(
        "model-catalog/providers",
        {
            "provider": "fixture",
            "provider_key": "fixture-" + run_id,
            "display_name": "Owned fixture provider",
            "secret_handle_ref": "secret://smoke/" + run_id,
            "transport": "litellm",
            "priority": 0,
        },
    )
    definition = mutate(
        "model-catalog/definitions",
        {"model_key": "fixture/" + run_id, "display_name": "Owned model"},
    )
    revision = mutate(
        "model-catalog/revisions",
        {
            "model_id": definition["id"],
            "provider_id": provider["id"],
            "revision": 1,
            "provider_model_name": "smoke-model",
            "display_name": "Owned model",
            "feature_key": feature,
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "transport": "litellm",
            "gateway_model_name": "smoke-model",
            "context_window": 8192,
            "max_output_tokens": 4096,
            "priority": 0,
        },
    )
    published = mutate(
        "model-catalog/revisions/" + revision["id"] + "/publish",
        None,
        version=revision["version"],
    )
    require(
        published.get("published_at") is not None
        and published.get("max_output_tokens") == 4096,
        "official_publish_failed",
    )
    label = mutate(
        "model-catalog/labels",
        {
            "label_key": "default-" + run_id,
            "display_name": "Owned route",
            "feature_key": feature,
            "default_revision_id": revision["id"],
        },
    )
    route = mutate(
        "model-catalog/routing-policies/" + label["id"],
        {
            "model_revision_id": revision["id"],
            "visible": True,
            "is_default": True,
            "priority": 0,
        },
        method="PUT",
        global_scope=False,
        create=True,
    )
    require(
        route.get("tenant_id") == tenant
        and route.get("label_id") == label["id"]
        and route.get("model_revision_id") == revision["id"]
        and route.get("version") == "1",
        "seed_route_identity_invalid",
    )
    return route


def route_read(base: str, tenant: str, token: str) -> dict:
    return system.data_of(
        system.http_json(
            base,
            "/v1/system/model-catalog/routing-policies",
            headers={
                "authorization": "Bearer " + token,
                "x-kokoro-service": "web-bff",
                "x-kokoro-tenant-id": tenant,
                "x-kokoro-iam-permissions": "system:read",
                "x-request-id": secrets.token_hex(16),
            },
        )
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "postgres-admin-url",
        "redis-url",
        "iam-node-bin",
        "bff-node-bin",
        "bff-source",
        "expected-iam-sha",
        "expected-bff-sha",
        "expected-system-sha",
    ):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    postgres = urlsplit(args.postgres_admin_url)
    if postgres.scheme != "postgresql" or not postgres.username:
        parser.error("explicit PostgreSQL role is required for the isolated CLI")
    for name in ("iam_node_bin", "bff_node_bin", "bff_source"):
        setattr(args, name, Path(getattr(args, name)).expanduser().resolve())
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    evidence = {
        "status": "failed",
        "stage": "preflight",
        "current_admin": False,
        "system_route_read": False,
        "target_status": None,
        "cleanup": "pending",
    }
    resources = system.OwnedResources(
        args.postgres_admin_url,
        args.redis_url,
        secrets.token_hex(12),
        command=runtime.command_output,
    )
    processes = []
    reader = None
    host = None
    before = None
    failure = None
    credential_values = []
    for endpoint in (args.postgres_admin_url, args.redis_url):
        credential_values.append(endpoint)
        parsed_endpoint = urlsplit(endpoint)
        for value in (parsed_endpoint.username, parsed_endpoint.password):
            if value:
                credential_values.extend((value, unquote(value)))
        for name, value in parse_qsl(parsed_endpoint.query):
            if value and name.lower() in {
                "user",
                "username",
                "password",
                "pass",
                "token",
                "secret",
            }:
                credential_values.append(value)
    try:
        evidence["sources"] = {
            "iam": source(IAM, args.expected_iam_sha),
            "bff": source(args.bff_source, args.expected_bff_sha),
            "system": source(SYSTEM, args.expected_system_sha),
        }
        artifact = SYSTEM / "contract/openapi/system.openapi.json"
        require(
            sha256(artifact.read_bytes()).hexdigest() == ARTIFACT_SHA,
            "immutable_system_artifact_mismatch",
        )
        evidence["system_contract_sha256"] = ARTIFACT_SHA
        node24 = session.node_environment(
            args.iam_node_bin, "v24.20.0", args.iam_node_bin.parent
        )
        node22 = session.node_environment(
            args.bff_node_bin, "v22.22.2", args.bff_node_bin.parent
        )
        before = snapshot(resources)
        with (
            tempfile.TemporaryDirectory(prefix="kokoro-admin-routing-") as temporary,
            ExitStack() as files,
        ):
            log_path = Path(temporary) / "process.log"
            log = files.enter_context(log_path.open("w+b"))
            os.chmod(log_path, 0o600)
            try:
                evidence["stage"] = "iam_real_qualification"
                host_env = {
                    **node24,
                    "NODE_ENV": "test",
                    "IAM_TEST_ADMIN_URL": args.postgres_admin_url,
                    "IAM_TEST_REDIS_URL": args.redis_url,
                }
                host = subprocess.Popen(
                    [str(args.iam_node_bin), "--import", "tsx", str(HOST)],
                    cwd=IAM,
                    env=host_env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=log,
                    start_new_session=True,
                    bufsize=0,
                )
                processes.append(host)
                require(host.stdout is not None, "host_pipe_missing")
                reader = session.ProtocolReader(host.stdout.fileno())
                ready = session.validate_ready(reader.record(timeout=120))
                credential_values.append(ready.access_token)
                system_token, agent_token, admin_token, web_secret = (
                    secrets.token_hex(32) for _ in range(4)
                )
                credential_values.extend(
                    (system_token, agent_token, admin_token, web_secret)
                )
                system_port = system.free_port()
                bff_port = system.free_port()
                while bff_port == system_port:
                    bff_port = system.free_port()
                system_base = f"http://127.0.0.1:{system_port}"
                bff_base = f"http://127.0.0.1:{bff_port}"
                system_env = {
                    **node24,
                    "NODE_ENV": "test",
                    "DATABASE_URL": system_database_url(
                        resources.create_database("system")
                    ),
                    "REDIS_URL": args.redis_url,
                    "KOKORO_SYSTEM_REDIS_NAMESPACE": resources.namespace,
                    "KOKORO_SYSTEM_HOST": "127.0.0.1",
                    "KOKORO_SYSTEM_PORT": str(system_port),
                    "KOKORO_SYSTEM_BFF_SERVICE_TOKEN": system_token,
                    "KOKORO_SYSTEM_AGENT_SERVICE_TOKEN": agent_token,
                    "KOKORO_SYSTEM_ADMIN_SERVICE_TOKEN": admin_token,
                }
                bff_env = {
                    **node22,
                    "NODE_ENV": "test",
                    "KOKORO_BFF_POSTGRES_URL": bff_owner_database_url(
                        resources.create_database("bff")
                    ),
                    "KOKORO_BFF_REDIS_URL": args.redis_url,
                    "KOKORO_BFF_HOST": "127.0.0.1",
                    "KOKORO_BFF_PORT": str(bff_port),
                    "KOKORO_BFF_MODE": "live",
                    "KOKORO_BFF_SHARED_SECRET": web_secret,
                    "KOKORO_IAM_BASE_URL": ready.base_url,
                    "KOKORO_INTERNAL_SECRET_BFF": system_token,
                    "KOKORO_SYSTEM_BASE_URL": system_base,
                    "KOKORO_AGENT_ENABLED": "false",
                    "KOKORO_TENANT_ID": ready.tenant_id,
                    "KOKORO_DOMAIN": resources.run_id + ".smoke.localhost",
                }
                for name, cwd, env, node, base in (
                    ("system", SYSTEM, system_env, args.iam_node_bin, system_base),
                    ("bff", args.bff_source, bff_env, args.bff_node_bin, bff_base),
                ):
                    evidence["stage"] = name + "_schema_start"
                    package = [str(node.parent / "corepack"), "pnpm"]
                    require(
                        runtime.run_owned_command(
                            [*package, "db:apply-schema"],
                            cwd=cwd,
                            env=env,
                            log=log,
                            timeout=60,
                        )
                        == 0,
                        "owned_schema_install_failed",
                    )
                    process = subprocess.Popen(
                        [*package, "dev"],
                        cwd=cwd,
                        env=env,
                        stdin=subprocess.DEVNULL,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                    processes.append(process)
                    system.wait_ready(base, process)
                evidence["stage"] = "system_official_seed"
                route = seed_route(
                    system_base, ready.tenant_id, admin_token, resources.run_id
                )
                owner_before = route_read(system_base, ready.tenant_id, system_token)
                require(
                    owner_before == {"items": [route], "next_cursor": None},
                    "system_read_positive_failed",
                )
                evidence["system_route_read"] = True
                evidence["stage"] = "bff_current_admin"
                headers = session.headers(ready, web_secret)
                status, body = session.request(bff_base, "/v1/me", headers=headers)
                identity = session.require_success(
                    status, body, "current administrator"
                )
                require(
                    identity
                    == {
                        "user_id": ready.user_id,
                        "tenant_id": ready.tenant_id,
                        "platform_admin": True,
                    },
                    "current_admin_positive_failed",
                )
                evidence["current_admin"] = True
                evidence["stage"] = "admin_model_routing_get"
                try:
                    status, body = session.request(
                        bff_base, "/v1/admin/model-routing", headers=headers
                    )
                    evidence["target_status"] = status
                    require(status == 200, "admin_model_routing_get_expected_200")
                    require(
                        set(body) == {"data", "meta"} and body["data"] == [route],
                        "admin_model_routing_projection_invalid",
                    )
                    meta = body.get("meta")
                    require(
                        isinstance(meta, dict)
                        and set(meta) == {"request_id", "next_cursor"}
                        and isinstance(meta["request_id"], str)
                        and bool(meta["request_id"])
                        and meta["next_cursor"] is None,
                        "admin_model_routing_meta_invalid",
                    )
                finally:
                    require(
                        route_read(system_base, ready.tenant_id, system_token)
                        == owner_before,
                        "read_changed_system_route",
                    )
                evidence["stage"] = "admin_owner_lists"
                for public_path, owner_path in (
                    ("/v1/admin/model-labels", "/v1/system/model-catalog/labels"),
                    (
                        "/v1/admin/model-revisions",
                        "/v1/system/model-catalog/revisions",
                    ),
                ):
                    authoritative = system.data_of(
                        system.http_json(
                            system_base,
                            owner_path,
                            headers={
                                "authorization": "Bearer " + system_token,
                                "x-kokoro-service": "web-bff",
                                "x-kokoro-tenant-id": ready.tenant_id,
                                "x-kokoro-iam-permissions": "system:read",
                                "x-request-id": secrets.token_hex(16),
                            },
                        )
                    )
                    status, body = session.request(
                        bff_base, public_path, headers=headers
                    )
                    require(
                        status == 200
                        and set(body) == {"data", "meta"}
                        and body["data"] == authoritative["items"]
                        and body["meta"]["next_cursor"] == authoritative["next_cursor"],
                        "admin_owner_list_projection_invalid",
                    )

                evidence["stage"] = "admin_visible_cas"
                write_body = {
                    "model_revision_id": route["model_revision_id"],
                    "visible": False,
                    "is_default": route["is_default"],
                    "priority": route["priority"],
                }
                write_headers = {
                    **headers,
                    "idempotency-key": secrets.token_hex(16),
                    "if-match": '"' + route["version"] + '"',
                }
                public_write_path = "/v1/admin/model-routing/" + route["label_id"]
                status, body = session.request(
                    bff_base,
                    public_write_path,
                    method="PUT",
                    headers=write_headers,
                    body=write_body,
                )
                saved = session.require_success(status, body, "routing CAS save")
                require(
                    saved
                    == {
                        **route,
                        **write_body,
                        "version": "2",
                        "updated_at": saved.get("updated_at"),
                    }
                    and isinstance(saved.get("updated_at"), str),
                    "admin_visible_cas_invalid",
                )
                authoritative_saved = route_read(
                    system_base, ready.tenant_id, system_token
                )
                require(
                    authoritative_saved == {"items": [saved], "next_cursor": None},
                    "admin_visible_authoritative_read_failed",
                )
                status, body = session.request(
                    bff_base, "/v1/admin/model-routing", headers=headers
                )
                require(
                    status == 200 and body.get("data") == [saved],
                    "admin_visible_public_read_failed",
                )

                evidence["stage"] = "admin_system_receipt_replay"
                status, body = session.request(
                    bff_base,
                    public_write_path,
                    method="PUT",
                    headers=write_headers,
                    body=write_body,
                )
                require(
                    status == 200 and body.get("data") == saved,
                    "admin_system_receipt_replay_failed",
                )
                for conflict_headers, conflict_body, expected_code in (
                    (
                        write_headers,
                        {**write_body, "visible": True},
                        "admin_model_routing_idempotency_conflict",
                    ),
                    (
                        {**write_headers, "idempotency-key": secrets.token_hex(16)},
                        write_body,
                        "admin_model_routing_version_conflict",
                    ),
                ):
                    status, body = session.request(
                        bff_base,
                        public_write_path,
                        method="PUT",
                        headers=conflict_headers,
                        body=conflict_body,
                    )
                    require(
                        status == 409
                        and set(body) == {"error", "meta"}
                        and body["error"]["code"] == expected_code,
                        "admin_write_conflict_invalid",
                    )
                evidence["stage"] = "admin_invalid_session_rejection"
                status, body = session.request(
                    bff_base,
                    "/v1/admin/model-routing",
                    headers={**headers, "authorization": "Bearer invalid-session"},
                )
                require(
                    status == 401
                    and set(body) == {"error", "meta"}
                    and body["error"]["code"]
                    in {"session_invalid", "session_authentication_required"},
                    "admin_invalid_session_not_rejected",
                )
                require(
                    route_read(system_base, ready.tenant_id, system_token)
                    == authoritative_saved,
                    "admin_replay_or_rejection_changed_owner",
                )
                evidence["owner_cas_replay_conflict_session_checks"] = "passed"
                evidence["status"] = "passed"
            except Exception as error:
                # Never format arbitrary parser, credential, SQL or process output.
                failure = type(error).__name__
            finally:
                cleanup_failures = []
                for process in reversed(processes):
                    try:
                        if (
                            process is host
                            and reader is not None
                            and host.poll() is None
                        ):
                            session.host_command(host, reader, "stop")
                            host.wait(timeout=30)
                            require(host.returncode == 0, "host_cleanup_exit")
                        runtime.stop_owned_process(process)
                    except Exception:
                        cleanup_failures.append("owned_process")
                        try:
                            runtime.stop_owned_process(process)
                        except Exception:
                            cleanup_failures.append("owned_process_force")
                if reader is not None:
                    reader.close()
                log.flush()
                diagnostic = log_path.read_bytes()
                host_stages = re.findall(rb"HOST_ERROR stage=([a-z-]+)", diagnostic)
                if host_stages:
                    evidence["iam_failure_stage"] = host_stages[-1].decode("ascii")
                if any(value.encode() in diagnostic for value in credential_values):
                    cleanup_failures.append("credential_log")
                else:
                    try:
                        retained_directory = (
                            ROOT
                            / "var/dev/r255-preserve"
                            / ("admin-model-routing-" + resources.run_id)
                        )
                        retained_directory.mkdir(mode=0o700)
                        retained_log = retained_directory / "process.log"
                        descriptor = os.open(
                            retained_log, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
                        )
                        with os.fdopen(descriptor, "wb") as retained:
                            retained.write(diagnostic)
                        evidence["diagnostic_path"] = str(retained_log)
                    except Exception:
                        cleanup_failures.append("diagnostic_retention")
                try:
                    # The reused helper uses FORCE; admit it only after every owned
                    # database is disconnected, never to hide a leaked backend.
                    for database in resources.created_databases:
                        require(
                            re.fullmatch(
                                r"system_smoke_[a-f0-9]{24}_(system|bff)", database
                            )
                            is not None,
                            "owned_database_identity_invalid",
                        )
                        active = resources.command(
                            [
                                "psql",
                                resources.postgres,
                                "-X",
                                "-v",
                                "ON_ERROR_STOP=1",
                                "-Atc",
                                "SELECT count(*) FROM pg_stat_activity WHERE datname = '"
                                + database
                                + "'",
                            ]
                        ).strip()
                        require(active == "0", "owned_database_connections_remaining")
                    resources.cleanup()
                except Exception:
                    cleanup_failures.append("owned_resources")
                try:
                    after = snapshot(resources)
                    require(after == before, "resource_inventory_changed")
                    evidence["database_count_before_after"] = [
                        len(before[0]),
                        len(after[0]),
                    ]
                    evidence["iam_key_count_before_after"] = [
                        len(before[1]),
                        len(after[1]),
                    ]
                except Exception:
                    cleanup_failures.append("resource_inventory")
                evidence["cleanup"] = "passed" if not cleanup_failures else "failed"
                if cleanup_failures:
                    evidence["cleanup_failures"] = cleanup_failures
                    failure = "CleanupFailure"
    except Exception as error:
        failure = type(error).__name__
    if failure:
        evidence["status"] = "failed"
        evidence["failure_class"] = failure
    print(json.dumps(evidence, sort_keys=True), flush=True)
    return (
        0 if evidence["status"] == "passed" and evidence["cleanup"] == "passed" else 1
    )


if __name__ == "__main__":
    sys.exit(main())

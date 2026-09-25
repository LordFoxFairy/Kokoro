from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.governance.iam_relay_policy import verify_iam_relay_policy
from scripts.governance.handbook_examples import ROOT

STATIC_2_1_ROUTES = {
    "/.well-known/openid-configuration": ["GET"],
    "/.well-known/oauth-authorization-server": ["GET"],
    "/jwks": ["GET"],
    "/oauth2/authorize": ["GET", "POST"],
    "/oauth2/token": ["POST"],
    "/oauth2/userinfo": ["GET"],
    "/oauth2/revoke": ["POST"],
    "/oauth2/end-session": ["GET", "POST"],
    "/oauth2/end-session/confirm": ["POST"],
    "/sign-up/email": ["POST"],
    "/sign-in/email": ["POST"],
    "/verify-email": ["GET"],
    "/sign-out": ["POST"],
    "/get-session": ["GET"],
    "/organization/set-active": ["POST"],
    "/oauth2/consent": ["POST"],
    "/oauth2/continue": ["POST"],
}


def git(path: Path, *args: str, input: bytes | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=path, input=input, capture_output=True, check=True
    )
    return result.stdout.decode().strip()


def write(path: Path, relative: str, value: str) -> None:
    target = path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value)


def commit(path: Path, message: str) -> str:
    git(path, "add", ".")
    git(path, "commit", "-qm", message)
    return git(path, "rev-parse", "HEAD")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@pytest.fixture()
def repositories(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, object]]:
    root = tmp_path / "root"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "fixture@example.test")
    paths = [root / "apps/kokoro-iam", root / "apps/kokoro-bff"]
    for path in paths:
        path.mkdir(parents=True)
        git(path, "init", "-q")
        git(path, "config", "user.name", "Fixture")
        git(path, "config", "user.email", "fixture@example.test")
    iam, bff = paths
    owner_routes = dict(STATIC_2_1_ROUTES)
    owner_routes["/organization/create"] = ["POST"]
    routes = (
        "export const AUTH_ROUTES: Readonly<Record<string, readonly string[]>> = {\n"
        + "".join(
            f"  {json.dumps(path)}: {json.dumps(methods)},\n"
            for path, methods in owner_routes.items()
        )
        + "};\n"
        "export const DISABLED_AUTH_PATHS = [\n"
        '  "/oauth2/register",\n'
        "];\n"
    )
    snapshot = '{"openapi":"3.1.1"}\n'
    openapi = invitation_openapi()
    write(iam, "src/modules/auth/ingress/auth-routes.constants.ts", routes)
    write(iam, "contract/vendor/better-auth.v1.7.3.json", snapshot)
    write(iam, "contract/openapi/iam.internal.v1.json", openapi)
    write(
        iam,
        "src/modules/audit/auth-audit.constants.ts",
        verify_email_constants(),
    )
    iam_commit = commit(iam, "iam 2.1.0 owner contract")
    policy: dict[str, object] = {
        "version": "2.1.0",
        "iamOwnerCommit": iam_commit,
        "iamAllowlistSha256": digest(routes),
        "iamSnapshotSha256": digest(snapshot),
        "routes": {"/oauth2/authorize": ["GET"], "/oauth2/token": ["POST"]},
    }
    strict_invitation_policy(policy, iam_commit, openapi)
    publish(root, bff, policy)
    return root, iam, bff, policy


INVITATION_ROUTE_FIELDS = (
    "template",
    "methods",
    "operationId",
    "owner",
    "visibility",
    "stability",
    "idempotency",
)
INVITATION_ROUTES = (
    (
        "/v1/tenants/{tenant_id}/invitations/{invitation_id}/context",
        "GET",
        "getTenantInvitationContext",
    ),
    (
        "/v1/tenants/{tenant_id}/invitations/{invitation_id}/accept",
        "POST",
        "acceptTenantInvitation",
    ),
    (
        "/v1/tenants/{tenant_id}/invitations/{invitation_id}/reject",
        "POST",
        "rejectTenantInvitation",
    ),
)
VERIFY_EMAIL_ERROR_CODES = (
    "TOKEN_EXPIRED",
    "INVALID_TOKEN",
    "USER_NOT_FOUND",
    "INVALID_USER",
)


def invitation_openapi(
    *, owner: str = "kokoro-iam", visibility: str = "browser-private"
) -> str:
    paths: dict[str, object] = {}
    for template, method, operation_id in INVITATION_ROUTES:
        paths[f"/iam{template}"] = {
            method.lower(): {
                "operationId": operation_id,
                "x-kokoro-owner": owner,
                "x-kokoro-visibility": visibility,
                "x-kokoro-stability": "stable",
                "x-kokoro-idempotency": "none",
            }
        }
    return (
        json.dumps(
            {
                "openapi": "3.1.1",
                "info": {"title": "Fixture IAM", "version": "0.4.0"},
                "paths": paths,
            },
            indent=2,
        )
        + "\n"
    )


def verify_email_constants(codes: tuple[str, ...] = VERIFY_EMAIL_ERROR_CODES) -> str:
    values = "".join(f'  "{code}",\n' for code in codes)
    return f"export const VERIFY_EMAIL_REDIRECT_ERROR_CODES = [\n{values}] as const;\n"


def strict_invitation_policy(
    policy: dict[str, object], iam_commit: str, openapi: str
) -> None:
    allowlist_sha256 = policy["iamAllowlistSha256"]
    snapshot_sha256 = policy["iamSnapshotSha256"]
    policy.clear()
    policy.update(
        {
            "version": "2.1.0",
            "iamOwnerCommit": iam_commit,
            "iamAllowlistSha256": allowlist_sha256,
            "iamSnapshotSha256": snapshot_sha256,
            "iamOpenapiPath": "contract/openapi/iam.internal.v1.json",
            "iamOpenapiVersion": "0.4.0",
            "iamOpenapiSha256": digest(openapi),
            "routes": {
                path: list(methods) for path, methods in STATIC_2_1_ROUTES.items()
            },
            "invitationRoutes": [
                {
                    "template": template,
                    "methods": [method],
                    "operationId": operation_id,
                    "owner": "kokoro-iam",
                    "visibility": "browser-private",
                    "stability": "stable",
                    "idempotency": "none",
                }
                for template, method, operation_id in INVITATION_ROUTES
            ],
            "invitationSignUp": {
                "route": "/sign-up/email",
                "method": "POST",
                "bodyFields": ["callbackURL", "email", "name", "password"],
                "callbackPath": "/iam/interactions/invitation",
                "callbackQueryParameter": "id",
            },
            "invitationLocation": {
                "sourceRoute": "/verify-email",
                "path": "/iam/interactions/invitation",
                "queryParameter": "id",
                "valueFormat": "canonical-lowercase-uuid",
                "errorQueryParameter": "error",
                "allowedErrorCodes": list(VERIFY_EMAIL_ERROR_CODES),
            },
            "requestHeaders": ["accept", "content-type", "origin", "cookie"],
            "responseHeaders": ["content-type", "location", "x-request-id"],
            "cookieNames": ["session_token"],
            "cookieNamePrefixes": ["kokoro-issuer."],
            "cookiePaths": {"default": "/iam"},
            "webInteractionPaths": ["/auth/sign-in"],
            "maxQueryBytes": 8192,
            "maxRequestBodyBytes": 65536,
            "maxHeaderBytes": 16384,
            "maxResponseBytes": 1048576,
            "maxDurationMs": 5000,
        }
    )


def publish(root: Path, bff: Path, policy: dict[str, object]) -> None:
    document = json.dumps(policy, indent=2) + "\n"
    write(bff, "contract/iam-relay-policy.json", document)
    write(
        bff,
        "src/http/routes/iam-protocol-relay.policy.ts",
        f"export const IAM_RELAY_POLICY = {json.dumps(policy)} as const\n",
    )
    bff_commit = commit(bff, "bff policy")
    iam_commit = str(policy["iamOwnerCommit"])
    git(
        root,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{iam_commit},apps/kokoro-iam",
    )
    git(
        root,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{bff_commit},apps/kokoro-bff",
    )
    git(root, "commit", "-qm", "gitlinks")


def test_accepts_exact_committed_gitlink_blobs(repositories) -> None:
    root, *_ = repositories
    assert verify_iam_relay_policy(root) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("iamOpenapiPath", "contract/openapi/other.json"),
        ("iamOpenapiVersion", "0.3.0"),
        ("iamOpenapiSha256", "0" * 64),
    ],
)
def test_rejects_2_1_openapi_evidence_drift(
    repositories, field: str, value: str
) -> None:
    root, _, bff, policy = repositories
    policy[field] = value
    publish(root, bff, policy)
    assert any(field in error for error in verify_iam_relay_policy(root))


def test_rejects_2_1_missing_static_invitation_sign_up(
    repositories,
) -> None:
    root, _, bff, policy = repositories
    routes = policy["routes"]
    assert isinstance(routes, dict)
    del routes["/sign-up/email"]
    publish(root, bff, policy)
    assert any("sign-up" in error for error in verify_iam_relay_policy(root))


def test_rejects_2_1_extra_owner_allowed_static_route(
    repositories,
) -> None:
    root, _, bff, policy = repositories
    routes = policy["routes"]
    assert isinstance(routes, dict)
    routes["/organization/create"] = ["POST"]
    publish(root, bff, policy)
    assert any("static routes" in error for error in verify_iam_relay_policy(root))


@pytest.mark.parametrize("mutation", ["order", "extra_route", "extra_field", "method"])
def test_rejects_2_1_invitation_route_drift(repositories, mutation: str) -> None:
    root, _, bff, policy = repositories
    invitation_routes = policy["invitationRoutes"]
    assert isinstance(invitation_routes, list)
    if mutation == "order":
        invitation_routes[0], invitation_routes[1] = (
            invitation_routes[1],
            invitation_routes[0],
        )
    elif mutation == "extra_route":
        invitation_routes.append(dict(invitation_routes[-1]))
    elif mutation == "extra_field":
        route = invitation_routes[0]
        assert isinstance(route, dict)
        route["unexpected"] = True
    else:
        route = invitation_routes[0]
        assert isinstance(route, dict)
        route["methods"] = ["POST"]
    publish(root, bff, policy)
    assert any("invitationRoutes" in error for error in verify_iam_relay_policy(root))


def test_rejects_2_1_owner_extension_drift_even_when_policy_matches(
    repositories,
) -> None:
    root, iam, bff, policy = repositories
    openapi = invitation_openapi(visibility="public")
    write(iam, "contract/openapi/iam.internal.v1.json", openapi)
    iam_commit = commit(iam, "drift owner visibility")
    policy["iamOwnerCommit"] = iam_commit
    policy["iamOpenapiSha256"] = digest(openapi)
    routes = policy["invitationRoutes"]
    assert isinstance(routes, list)
    for route in routes:
        assert isinstance(route, dict)
        route["visibility"] = "public"
    publish(root, bff, policy)
    assert any("invitationRoutes" in error for error in verify_iam_relay_policy(root))


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("invitationSignUp", "callbackPath", "/auth/invitation"),
        ("invitationSignUp", "bodyFields", ["email", "password"]),
        ("invitationSignUp", "unexpected", True),
        ("invitationLocation", "path", "/auth/invitation"),
        ("invitationLocation", "allowedErrorCodes", ["INVALID_TOKEN"]),
        ("invitationLocation", "unexpected", True),
    ],
)
def test_rejects_2_1_invitation_policy_field_drift(
    repositories, section: str, field: str, value: object
) -> None:
    root, _, bff, policy = repositories
    nested = policy[section]
    assert isinstance(nested, dict)
    nested[field] = value
    publish(root, bff, policy)
    assert any(section in error for error in verify_iam_relay_policy(root))


def test_rejects_2_1_owner_verify_email_error_code_drift(
    repositories,
) -> None:
    root, iam, bff, policy = repositories
    write(
        iam,
        "src/modules/audit/auth-audit.constants.ts",
        verify_email_constants(("INVALID_TOKEN",)),
    )
    iam_commit = commit(iam, "change owner redirect errors")
    policy["iamOwnerCommit"] = iam_commit
    publish(root, bff, policy)
    assert any("allowedErrorCodes" in error for error in verify_iam_relay_policy(root))


def test_rejects_2_1_extra_top_level_field(repositories) -> None:
    root, _, bff, policy = repositories
    policy["unexpected"] = True
    publish(root, bff, policy)
    assert any("fields" in error for error in verify_iam_relay_policy(root))


@pytest.mark.parametrize("version", ["2.0.0", "2.2.0"])
def test_rejects_2_1_policy_version_bypass(repositories, version: str) -> None:
    root, _, bff, policy = repositories
    policy["version"] = version
    publish(root, bff, policy)
    assert any("version" in error for error in verify_iam_relay_policy(root))


def test_rejects_legacy_2_0_policy_after_root_pin(repositories) -> None:
    root, _, bff, policy = repositories
    policy["version"] = "2.0.0"
    for field in (
        "iamOpenapiPath",
        "iamOpenapiVersion",
        "iamOpenapiSha256",
        "invitationRoutes",
        "invitationSignUp",
        "invitationLocation",
    ):
        del policy[field]
    publish(root, bff, policy)
    assert any("version" in error for error in verify_iam_relay_policy(root))


def test_rejects_dirty_child_worktree(repositories) -> None:
    root, iam, _, _ = repositories
    with (iam / "README.md").open("w") as stream:
        stream.write("untracked\n")
    assert any("dirty" in error for error in verify_iam_relay_policy(root))


def test_rejects_iam_digest_drift(repositories) -> None:
    root, _, bff, policy = repositories
    policy["iamAllowlistSha256"] = "0" * 64
    publish(root, bff, policy)
    assert any("iamAllowlistSha256" in error for error in verify_iam_relay_policy(root))


def test_rejects_snapshot_digest_drift(repositories) -> None:
    root, _, bff, policy = repositories
    policy["iamSnapshotSha256"] = "0" * 64
    publish(root, bff, policy)
    assert any("iamSnapshotSha256" in error for error in verify_iam_relay_policy(root))


def test_rejects_bff_route_not_in_iam(repositories) -> None:
    root, _, bff, policy = repositories
    policy["routes"] = {"/oauth2/register": ["POST"]}
    publish(root, bff, policy)
    assert any("disabled" in error for error in verify_iam_relay_policy(root))


def test_rejects_method_expansion(repositories) -> None:
    root, _, bff, policy = repositories
    policy["routes"] = {"/oauth2/token": ["GET"]}
    publish(root, bff, policy)
    assert any("method" in error for error in verify_iam_relay_policy(root))


@pytest.mark.parametrize(
    "route", ["/oauth2//token", "/oauth2/../token", "/oauth2/%74oken"]
)
def test_rejects_noncanonical_route(repositories, route: str) -> None:
    root, _, bff, policy = repositories
    policy["routes"] = {route: ["POST"]}
    publish(root, bff, policy)
    assert any("invalid route" in error for error in verify_iam_relay_policy(root))


def test_rejects_ts_json_drift(repositories) -> None:
    root, _, bff, _ = repositories
    source = bff / "src/http/routes/iam-protocol-relay.policy.ts"
    source.write_text(source.read_text().replace('"GET"', '"POST"'))
    publish_without_rewriting(root, bff)
    assert any("TypeScript" in error for error in verify_iam_relay_policy(root))


def publish_without_rewriting(root: Path, bff: Path) -> None:
    bff_commit = commit(bff, "drift")
    git(root, "update-index", "--cacheinfo", f"160000,{bff_commit},apps/kokoro-bff")
    git(root, "commit", "-qm", "update gitlink")


def test_rejects_gitlink_sha_mismatch(repositories) -> None:
    root, _, bff, _ = repositories
    write(bff, "README.md", "next commit\n")
    commit(bff, "advance without root gitlink")
    assert any("gitlink" in error for error in verify_iam_relay_policy(root))


def test_replace_ref_cannot_supply_missing_iam_blob(repositories) -> None:
    root, iam, bff, policy = repositories
    good_commit = git(iam, "rev-parse", "HEAD")
    git(iam, "rm", "src/modules/auth/ingress/auth-routes.constants.ts")
    bad_commit = commit(iam, "missing routes")
    git(iam, "replace", bad_commit, good_commit)
    policy["iamOwnerCommit"] = bad_commit
    publish(root, bff, policy)
    errors = verify_iam_relay_policy(root)
    assert any("missing commit blob" in error for error in errors), errors


def test_rejects_head_index_gitlink_mismatch(repositories) -> None:
    root, _, bff, _ = repositories
    write(bff, "README.md", "new\n")
    next_commit = commit(bff, "next")
    git(root, "update-index", "--cacheinfo", f"160000,{next_commit},apps/kokoro-bff")
    assert any("Root HEAD" in error for error in verify_iam_relay_policy(root))


def test_cli_reports_committed_fixture_and_negative_evidence(repositories) -> None:
    root, _, bff, policy = repositories
    command = [
        sys.executable,
        str(ROOT / "scripts/verify-iam-relay-policy.py"),
        "--root",
        str(root),
    ]
    green = subprocess.run(command, capture_output=True, text=True, check=False)
    assert green.returncode == 0
    assert json.loads(green.stdout) == {"status": "PASS"}

    policy["routes"] = {"/oauth2/register": ["POST"]}
    publish(root, bff, policy)
    red = subprocess.run(command, capture_output=True, text=True, check=False)
    assert red.returncode == 1
    assert json.loads(red.stdout)["status"] == "FAIL"
    assert "Traceback" not in red.stderr

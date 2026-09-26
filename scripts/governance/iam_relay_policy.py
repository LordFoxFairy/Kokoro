"""Verify the published BFF IAM relay policy against committed owner evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

IAM_REPOSITORY = "apps/kokoro-iam"
BFF_REPOSITORY = "apps/kokoro-bff"
IAM_ALLOWLIST = "src/modules/auth/ingress/auth-routes.constants.ts"
IAM_SNAPSHOT = "contract/vendor/better-auth.v1.7.3.json"
IAM_OPENAPI = "contract/openapi/iam.internal.v1.json"
IAM_REDIRECT_ERRORS = "src/modules/audit/auth-audit.constants.ts"
BFF_POLICY = "contract/iam-relay-policy.json"
BFF_SOURCE = "src/http/routes/iam-protocol-relay.policy.ts"
OID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
OPENAPI_VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
ROUTE = re.compile(r"/[a-z0-9./-]+")
METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})
POLICY_2_1_FIELDS = (
    "version",
    "iamOwnerCommit",
    "iamAllowlistSha256",
    "iamSnapshotSha256",
    "iamOpenapiPath",
    "iamOpenapiVersion",
    "iamOpenapiSha256",
    "routes",
    "invitationRoutes",
    "invitationSignUp",
    "invitationLocation",
    "requestHeaders",
    "responseHeaders",
    "cookieNames",
    "cookieNamePrefixes",
    "cookiePaths",
    "webInteractionPaths",
    "maxQueryBytes",
    "maxRequestBodyBytes",
    "maxHeaderBytes",
    "maxResponseBytes",
    "maxDurationMs",
)
INVITATION_ROUTE_FIELDS = (
    "template",
    "methods",
    "operationId",
    "owner",
    "visibility",
    "stability",
    "idempotency",
)
INVITATION_ROUTE_SPECS = (
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
INVITATION_SIGN_UP = {
    "route": "/sign-up/email",
    "method": "POST",
    "bodyFields": ["callbackURL", "email", "name", "password"],
    "callbackPath": "/iam/interactions/invitation",
    "callbackQueryParameter": "id",
}
INVITATION_LOCATION_BASE = {
    "sourceRoute": "/verify-email",
    "path": "/iam/interactions/invitation",
    "queryParameter": "id",
    "valueFormat": "canonical-lowercase-uuid",
    "errorQueryParameter": "error",
}
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


def _git(cwd: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", *args],
            cwd=cwd,
            capture_output=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f"git command unavailable: {error}") from None
    if result.returncode:
        raise ValueError(
            f"git {' '.join(args)}: {result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout


def _gitlink(root: Path, repository: str) -> str:
    head_entry = _git(root, "ls-tree", "HEAD", "--", repository).decode().strip()
    index_entry = _git(root, "ls-files", "--stage", "--", repository).decode().strip()
    head_match = re.fullmatch(
        rf"160000 commit ({OID.pattern})\t{re.escape(repository)}", head_entry
    )
    index_match = re.fullmatch(
        rf"160000 ({OID.pattern}) 0\t{re.escape(repository)}", index_entry
    )
    if not head_match:
        raise ValueError(f"{repository}: Root HEAD must contain one gitlink")
    if not index_match or index_match.group(1) != head_match.group(1):
        raise ValueError(f"{repository}: Root HEAD and index gitlink differ")
    checkout = root / repository
    if checkout.is_symlink() or not checkout.is_dir():
        raise ValueError(f"{repository}: child checkout is missing or symlinked")
    actual_root = Path(_git(checkout, "rev-parse", "--show-toplevel").decode().strip())
    if actual_root.resolve() != checkout.resolve():
        raise ValueError(f"{repository}: checkout is not the child repository root")
    if _git(checkout, "rev-parse", "HEAD").decode().strip() != head_match.group(1):
        raise ValueError(f"{repository}: child HEAD != Root gitlink")
    if _git(checkout, "status", "--porcelain", "--untracked-files=normal").strip():
        raise ValueError(f"{repository}: child worktree is dirty")
    return head_match.group(1)


def _blob(root: Path, repository: str, commit: str, relative: str) -> bytes:
    if not OID.fullmatch(commit):
        raise ValueError(f"{repository}: invalid commit OID")
    try:
        return _git(
            root / repository,
            "show",
            "--end-of-options",
            f"{commit}:{relative}",
        )
    except ValueError:
        raise ValueError(
            f"{repository}@{commit}:{relative}: missing commit blob"
        ) from None


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _canonical_route(value: str) -> bool:
    return bool(
        ROUTE.fullmatch(value)
        and not value.endswith("/")
        and "//" not in value
        and "/./" not in value
        and "/../" not in value
        and not value.endswith("/.")
        and not value.endswith("/..")
    )


def _json_object(blob: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError(f"{label}: must be UTF-8 JSON") from None
    if not isinstance(value, dict):
        raise ValueError(f"{label}: must be a JSON object")
    return value


def _iam_routes(blob: bytes) -> tuple[dict[str, set[str]], set[str]]:
    try:
        source = blob.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("IAM auth routes must be UTF-8") from None
    match = re.fullmatch(
        r"export const AUTH_ROUTES: Readonly<Record<string, readonly string\[\]>> = \{\n"
        r'(?P<routes>(?:  "[^"]+": \[(?:"[A-Z]+"(?:, "[A-Z]+")*)\],\n)+)'
        r"\};\nexport const DISABLED_AUTH_PATHS = \[\n"
        r'(?P<disabled>(?:  "[^"]+",\n)+)\];\n?',
        source,
    )
    if match is None:
        raise ValueError("IAM auth route declarations do not match the pinned parser")
    routes: dict[str, set[str]] = {}
    for line in match.group("routes").splitlines():
        key, raw_methods = line.strip().removesuffix(",").split(": ", 1)
        path = json.loads(key)
        methods = json.loads(raw_methods)
        if (
            not _canonical_route(path)
            or not methods
            or any(method not in METHODS for method in methods)
            or len(methods) != len(set(methods))
        ):
            raise ValueError(
                "IAM route declaration contains an invalid path or methods"
            )
        if path in routes:
            raise ValueError("IAM route declaration contains a duplicate path")
        routes[path] = set(methods)
    disabled = [
        json.loads(line.strip().removesuffix(","))
        for line in match.group("disabled").splitlines()
    ]
    if len(disabled) != len(set(disabled)) or any(
        not _canonical_route(path) for path in disabled
    ):
        raise ValueError("IAM disabled route declaration is invalid")
    if set(routes).intersection(disabled):
        raise ValueError("IAM enabled and disabled routes overlap")
    return routes, set(disabled)


def _iam_verify_email_error_codes(blob: bytes) -> list[str]:
    try:
        source = blob.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("IAM verify-email redirect constants must be UTF-8") from None
    matches = re.findall(
        r"export const VERIFY_EMAIL_REDIRECT_ERROR_CODES = \[\n"
        r'(?P<codes>(?:  "[A-Z_]+",\n)+)'
        r"\] as const;",
        source,
    )
    if len(matches) != 1:
        raise ValueError(
            "IAM VERIFY_EMAIL_REDIRECT_ERROR_CODES does not match the pinned parser"
        )
    codes = [
        json.loads(line.strip().removesuffix(",")) for line in matches[0].splitlines()
    ]
    if len(codes) != len(set(codes)):
        raise ValueError("IAM VERIFY_EMAIL_REDIRECT_ERROR_CODES contains duplicates")
    return codes


def _strict_object(
    value: object, expected: dict[str, object], label: str
) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or tuple(value) != tuple(expected)
        or value != expected
    ):
        raise ValueError(f"BFF policy {label} does not match the exact 2.1.0 shape")
    return value


def _verify_invitation_routes(policy: dict[str, Any], openapi: dict[str, Any]) -> None:
    paths = openapi.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("IAM OpenAPI paths must be an object")
    expected_policy_routes: list[dict[str, object]] = []
    for template, method, operation_id in INVITATION_ROUTE_SPECS:
        path_item = paths.get(f"/iam{template}")
        operation = (
            path_item.get(method.lower()) if isinstance(path_item, dict) else None
        )
        if not isinstance(operation, dict):
            raise ValueError(
                f"IAM OpenAPI missing invitation operation {method} /iam{template}"
            )
        expected_operation = {
            "operationId": operation_id,
            "x-kokoro-owner": "kokoro-iam",
            "x-kokoro-visibility": "browser-private",
            "x-kokoro-stability": "stable",
            "x-kokoro-idempotency": "none",
        }
        if any(
            operation.get(key) != value for key, value in expected_operation.items()
        ):
            raise ValueError(
                "BFF policy invitationRoutes owner metadata does not match IAM 2.1.0"
            )
        expected_policy_routes.append(
            {
                "template": template,
                "methods": [method],
                "operationId": operation["operationId"],
                "owner": operation["x-kokoro-owner"],
                "visibility": operation["x-kokoro-visibility"],
                "stability": operation["x-kokoro-stability"],
                "idempotency": operation["x-kokoro-idempotency"],
            }
        )
    invitation_routes = policy.get("invitationRoutes")
    if not isinstance(invitation_routes, list) or len(invitation_routes) != len(
        expected_policy_routes
    ):
        raise ValueError(
            "BFF policy invitationRoutes must contain exactly three routes"
        )
    for actual, expected in zip(invitation_routes, expected_policy_routes, strict=True):
        if (
            not isinstance(actual, dict)
            or tuple(actual) != INVITATION_ROUTE_FIELDS
            or actual != expected
        ):
            raise ValueError(
                "BFF policy invitationRoutes do not match IAM committed OpenAPI"
            )


def _verify_2_1_policy(
    root: Path,
    iam_commit: str,
    policy: dict[str, Any],
    routes: dict[str, Any],
) -> None:
    if tuple(policy) != POLICY_2_1_FIELDS:
        raise ValueError("BFF policy 2.1.0 fields do not match the exact shape")
    if policy.get("iamOpenapiPath") != IAM_OPENAPI:
        raise ValueError(f"BFF policy iamOpenapiPath must equal {IAM_OPENAPI}")
    openapi_blob = _blob(root, IAM_REPOSITORY, iam_commit, IAM_OPENAPI)
    if policy.get("iamOpenapiSha256") != _sha(openapi_blob):
        raise ValueError("BFF policy iamOpenapiSha256 != IAM committed blob sha256")
    openapi = _json_object(openapi_blob, "IAM internal OpenAPI")
    info = openapi.get("info")
    openapi_version = info.get("version") if isinstance(info, dict) else None
    if (
        not isinstance(openapi_version, str)
        or OPENAPI_VERSION.fullmatch(openapi_version) is None
        or policy.get("iamOpenapiVersion") != openapi_version
    ):
        raise ValueError("BFF policy iamOpenapiVersion != IAM committed OpenAPI version")
    if tuple(routes) != tuple(STATIC_2_1_ROUTES) or routes != STATIC_2_1_ROUTES:
        raise ValueError(
            "BFF policy 2.1.0 static routes including sign-up do not match the exact matrix"
        )
    _verify_invitation_routes(policy, openapi)
    _strict_object(
        policy.get("invitationSignUp"), INVITATION_SIGN_UP, "invitationSignUp"
    )
    redirect_blob = _blob(root, IAM_REPOSITORY, iam_commit, IAM_REDIRECT_ERRORS)
    invitation_location = dict(INVITATION_LOCATION_BASE)
    owner_error_codes = _iam_verify_email_error_codes(redirect_blob)
    raw_invitation_location = policy.get("invitationLocation")
    if (
        not isinstance(raw_invitation_location, dict)
        or raw_invitation_location.get("allowedErrorCodes") != owner_error_codes
    ):
        raise ValueError(
            "BFF policy invitationLocation.allowedErrorCodes != IAM owner constants"
        )
    invitation_location["allowedErrorCodes"] = owner_error_codes
    _strict_object(
        policy.get("invitationLocation"),
        invitation_location,
        "invitationLocation",
    )


def _typescript_policy(blob: bytes) -> dict[str, Any]:
    try:
        source = blob.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("BFF TypeScript policy must be UTF-8") from None
    match = re.search(
        r"export const IAM_RELAY_POLICY = (?P<object>\{[\s\S]*?\}) as const(?:;)?(?:\r?\n|$)",
        source,
    )
    if (
        match is None
        or len(re.findall(r"export const IAM_RELAY_POLICY\s*=", source)) != 1
    ):
        raise ValueError("BFF TypeScript policy must have one literal declaration")
    literal = match.group("object")
    literal = re.sub(r"([{,]\s*)([A-Za-z][A-Za-z0-9]*)(\s*:)", r'\1"\2"\3', literal)
    literal = re.sub(r",(?=\s*[}\]])", "", literal)
    return _json_object(literal.encode(), "BFF TypeScript policy")


def _verify(root: Path) -> None:
    iam_commit = _gitlink(root, IAM_REPOSITORY)
    bff_commit = _gitlink(root, BFF_REPOSITORY)
    allowlist_blob = _blob(root, IAM_REPOSITORY, iam_commit, IAM_ALLOWLIST)
    snapshot_blob = _blob(root, IAM_REPOSITORY, iam_commit, IAM_SNAPSHOT)
    _json_object(snapshot_blob, "IAM Better Auth snapshot")
    iam_routes, disabled = _iam_routes(allowlist_blob)
    policy_blob = _blob(root, BFF_REPOSITORY, bff_commit, BFF_POLICY)
    ts_blob = _blob(root, BFF_REPOSITORY, bff_commit, BFF_SOURCE)
    policy = _json_object(policy_blob, "BFF relay policy")
    if _typescript_policy(ts_blob) != policy:
        raise ValueError("BFF TypeScript policy and published JSON differ")
    if policy.get("iamOwnerCommit") != iam_commit:
        raise ValueError("BFF policy iamOwnerCommit != IAM gitlink")
    for field, blob in (
        ("iamAllowlistSha256", allowlist_blob),
        ("iamSnapshotSha256", snapshot_blob),
    ):
        if policy.get(field) != _sha(blob):
            raise ValueError(f"BFF policy {field} != IAM committed blob sha256")
    routes = policy.get("routes")
    if not isinstance(routes, dict) or not routes:
        raise ValueError("BFF policy routes must be a non-empty object")
    for path, declared_methods in routes.items():
        if not isinstance(path, str) or not _canonical_route(path):
            raise ValueError(f"BFF policy invalid route path: {path!r}")
        if path in disabled:
            raise ValueError(f"BFF policy exposes disabled IAM route {path}")
        if path not in iam_routes:
            raise ValueError(f"BFF policy route not in IAM allowlist: {path}")
        if (
            not isinstance(declared_methods, list)
            or not declared_methods
            or any(
                not isinstance(method, str) or method not in METHODS
                for method in declared_methods
            )
            or len(declared_methods) != len(set(declared_methods))
        ):
            raise ValueError(f"BFF policy invalid methods for {path}")
        if not set(declared_methods).issubset(iam_routes[path]):
            raise ValueError(f"BFF policy method expansion for {path}")
    version = policy.get("version")
    if version != "2.1.0":
        raise ValueError("BFF policy version must be 2.1.0")
    _verify_2_1_policy(root, iam_commit, policy, routes)


def verify_iam_relay_policy(root: Path) -> list[str]:
    """Return deterministic errors; never read policy bytes from child worktrees."""
    try:
        _verify(root)
    except ValueError as error:
        return [str(error)]
    return []

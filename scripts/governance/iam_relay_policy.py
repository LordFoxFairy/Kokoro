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
APP_REPOSITORY = "apps/kokoro-app"
APP_POLICY_SOURCE = "contract/bff-iam-relay-policy-source.json"
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
POLICY_FIELDS = (
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


NATIVE_ROUTES = {
    "/sign-up/email": ["POST"],
    "/sign-in/email": ["POST"],
    "/verify-email": ["GET"],
    "/sign-out": ["POST"],
    "/organization/set-active": ["POST"],
}
NATIVE_TRANSPORT_POLICY = {
    "requestHeaders": ["accept", "content-type", "origin", "cookie", "x-request-id"],
    "responseHeaders": [
        "content-type",
        "cache-control",
        "location",
        "retry-after",
        "content-security-policy",
        "x-content-type-options",
        "pragma",
        "x-request-id",
    ],
    "cookieNames": ["session_token", "session_data", "dont_remember"],
    "cookieNamePrefixes": ["kokoro-issuer.", "__Secure-kokoro-issuer."],
    "cookiePaths": {"default": "/"},
    "webInteractionPaths": [
        "/auth/sign-in",
        "/auth/select-tenant",
        "/iam/interactions/invitation",
    ],
    "maxQueryBytes": 8192,
    "maxRequestBodyBytes": 65536,
    "maxHeaderBytes": 16384,
    "maxResponseBytes": 1048576,
    "maxDurationMs": 5000,
}
RETIRED_IAM_WORKLOAD_PATH = "/internal/v1/platform-workload-tokens/introspect"
RETIRED_IAM_WORKLOAD_SCHEME = "platformResourceServerBasic"


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
        raise ValueError(f"BFF policy {label} does not match the exact shape")
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
                "BFF policy invitationRoutes owner metadata does not match IAM committed OpenAPI"
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


def _verify_policy_contract(
    root: Path,
    iam_commit: str,
    policy: dict[str, Any],
    routes: dict[str, Any],
) -> None:
    version = policy["version"]
    if tuple(policy) != POLICY_FIELDS:
        raise ValueError(f"BFF policy {version} fields do not match the exact shape")
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
        raise ValueError(
            "BFF policy iamOpenapiVersion != IAM committed OpenAPI version"
        )
    matrix = NATIVE_ROUTES if version == "3.0.0" else STATIC_2_1_ROUTES
    if tuple(routes) != tuple(matrix) or routes != matrix:
        raise ValueError(
            f"BFF policy {version} static routes including sign-up do not match the exact matrix"
        )
    if version == "3.0.0":
        actual = {key: policy.get(key) for key in NATIVE_TRANSPORT_POLICY}
        if json.dumps(actual, sort_keys=True) != json.dumps(
            NATIVE_TRANSPORT_POLICY, sort_keys=True
        ):
            raise ValueError(
                "BFF native relay transport policy differs from the exact matrix"
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


def _typescript_policy(blob: bytes, *, native: bool = False) -> dict[str, Any]:
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
    if native:
        literal = re.sub(r"(?m)^[ \t]*//[^\r\n]*", "", literal)
    literal = re.sub(r"([{,]\s*)([A-Za-z][A-Za-z0-9]*)(\s*:)", r'\1"\2"\3', literal)
    literal = re.sub(r",(?=\s*[}\]])", "", literal)
    return _json_object(literal.encode(), "BFF TypeScript policy")


def _source_anchor(
    root: Path, repository: str, anchor: object, selected: str, label: str
) -> str:
    if not isinstance(anchor, str) or OID.fullmatch(anchor) is None:
        raise ValueError(f"{label}: invalid commit")
    try:
        _git(root / repository, "merge-base", "--is-ancestor", anchor, selected)
    except ValueError:
        raise ValueError(f"{label}: must be an ancestor of the Root gitlink") from None
    return anchor


def _verify_current_iam(root: Path, anchor: str, selected: str) -> None:
    for path in (IAM_ALLOWLIST, IAM_SNAPSHOT, IAM_REDIRECT_ERRORS):
        if _blob(root, IAM_REPOSITORY, anchor, path) != _blob(
            root, IAM_REPOSITORY, selected, path
        ):
            raise ValueError(f"IAM native relay owner evidence differs: {path}")
    source = _blob(root, IAM_REPOSITORY, anchor, IAM_OPENAPI)
    current = _blob(root, IAM_REPOSITORY, selected, IAM_OPENAPI)
    if source == current:
        return
    # The published native policy still points to the contract preceding T-11.
    # Compare the entire retained contract, not just the relay operation list.
    approved = _json_object(source, "IAM relay source OpenAPI")
    try:
        if approved["info"]["version"] != "0.20.0":
            raise ValueError
        approved["info"]["version"] = "0.21.0"
        del approved["paths"][RETIRED_IAM_WORKLOAD_PATH]
        del approved["components"]["securitySchemes"][RETIRED_IAM_WORKLOAD_SCHEME]
    except (KeyError, TypeError, ValueError):
        raise ValueError("unapproved IAM OpenAPI drift from the relay source") from None
    if json.dumps(approved, sort_keys=True) != json.dumps(
        _json_object(current, "current IAM OpenAPI"), sort_keys=True
    ):
        raise ValueError("unapproved IAM OpenAPI drift from the relay source")


def _verify_app_relay(root: Path, bff_commit: str, bff_policy: bytes) -> None:
    app_commit = _gitlink(root, APP_REPOSITORY)
    pin = _json_object(
        _blob(root, APP_REPOSITORY, app_commit, APP_POLICY_SOURCE),
        "App relay policy pin",
    )
    anchor = _source_anchor(
        root,
        BFF_REPOSITORY,
        pin.get("owner_commit"),
        bff_commit,
        "App BFF relay source anchor",
    )
    if pin != {
        "owner": "kokoro-bff",
        "owner_commit": anchor,
        "source_path": BFF_POLICY,
        "source_sha256": _sha(bff_policy),
        "version": "3.0.0",
    }:
        raise ValueError("App relay policy pin does not match the current BFF artifact")
    generator = _blob(
        root, APP_REPOSITORY, app_commit, "scripts/generate-iam-relay-policy.mjs"
    )
    # The manifest and generated copies do not on their own prove the generator
    # admits the declared BFF source. Match the two assertions it actually uses.
    for subject, expected in (
        (b"pin.owner_commit", anchor),
        (b"digest", _sha(bff_policy)),
    ):
        locks = re.findall(
            rb"(?m)^[ \t]*assert\.equal\([ \t]*"
            + re.escape(subject)
            + rb"""[ \t]*,[ \t]*(['"])([a-f0-9]+)\1[ \t]*\);?[ \t]*\r?$""",
            generator,
        )
        if len(locks) != 1 or locks[0][1] != expected.encode():
            raise ValueError(
                "App relay generator source lock differs from the policy pin"
            )
    if _blob(root, BFF_REPOSITORY, anchor, BFF_POLICY) != bff_policy:
        raise ValueError("BFF published relay source differs from the current artifact")
    vendor = f"contract/vendor/kokoro-bff/{anchor}/iam-relay-policy.json"
    if _blob(root, APP_REPOSITORY, app_commit, vendor) != bff_policy:
        raise ValueError("App vendored relay policy differs from the BFF source")
    if (
        _blob(root, APP_REPOSITORY, app_commit, "src/generated/iam-relay-policy.json")
        != bff_policy
    ):
        raise ValueError("App generated relay policy differs from the BFF source")
    provenance = json.dumps(
        {
            "ownerRepository": "kokoro-bff",
            "ownerCommit": anchor,
            "policySha256": _sha(bff_policy),
        },
        separators=(",", ":"),
    )
    expected = (
        "// Generated by scripts/generate-iam-relay-policy.mjs. Do not edit.\n"
        f"export const IAM_RELAY_POLICY_PROVENANCE={provenance} as const\n"
    ).encode()
    if (
        _blob(root, APP_REPOSITORY, app_commit, "src/generated/iam-relay-provenance.ts")
        != expected
    ):
        raise ValueError("App generated relay provenance differs from its source pin")


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
    version = policy.get("version")
    native = version == "3.0.0"
    if _typescript_policy(ts_blob, native=native) != policy:
        raise ValueError("BFF TypeScript policy and published JSON differ")
    if native:
        iam_anchor = _source_anchor(
            root,
            IAM_REPOSITORY,
            policy.get("iamOwnerCommit"),
            iam_commit,
            "IAM relay source anchor",
        )
        _verify_current_iam(root, iam_anchor, iam_commit)
    else:
        if policy.get("iamOwnerCommit") != iam_commit:
            raise ValueError("BFF policy iamOwnerCommit != IAM gitlink")
        iam_anchor = iam_commit
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
    if version not in ("2.1.0", "3.0.0"):
        raise ValueError("BFF policy version must be 2.1.0 or 3.0.0")
    _verify_policy_contract(root, iam_anchor, policy, routes)
    if native:
        _verify_app_relay(root, bff_commit, policy_blob)


def verify_iam_relay_policy(root: Path) -> list[str]:
    """Return deterministic errors; never read policy bytes from child worktrees."""
    try:
        _verify(root)
    except ValueError as error:
        return [str(error)]
    return []

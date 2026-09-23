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
BFF_POLICY = "contract/iam-relay-policy.json"
BFF_SOURCE = "src/http/routes/iam-protocol-relay.policy.ts"
OID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
ROUTE = re.compile(r"/[a-z0-9./-]+")
METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})


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


def verify_iam_relay_policy(root: Path) -> list[str]:
    """Return deterministic errors; never read policy bytes from child worktrees."""
    try:
        _verify(root)
    except ValueError as error:
        return [str(error)]
    return []

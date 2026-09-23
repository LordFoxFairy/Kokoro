from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.governance.iam_relay_policy import verify_iam_relay_policy
from scripts.governance.handbook_examples import ROOT


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
    routes = (
        "export const AUTH_ROUTES: Readonly<Record<string, readonly string[]>> = {\n"
        '  "/oauth2/authorize": ["GET", "POST"],\n'
        '  "/oauth2/token": ["POST"],\n'
        "};\n"
        "export const DISABLED_AUTH_PATHS = [\n"
        '  "/oauth2/register",\n'
        "];\n"
    )
    snapshot = '{"openapi":"3.1.1"}\n'
    write(iam, "src/modules/auth/ingress/auth-routes.constants.ts", routes)
    write(iam, "contract/vendor/better-auth.v1.7.3.json", snapshot)
    iam_commit = commit(iam, "iam")
    policy: dict[str, object] = {
        "version": "1.0.0",
        "iamOwnerCommit": iam_commit,
        "iamAllowlistSha256": digest(routes),
        "iamSnapshotSha256": digest(snapshot),
        "routes": {"/oauth2/authorize": ["GET"], "/oauth2/token": ["POST"]},
    }
    publish(root, bff, policy)
    return root, iam, bff, policy


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

#!/usr/bin/env python3
"""Audit the active Kokoro repository topology without mutating any checkout.

This is a Root governance check.  It deliberately inspects repositories by
their own Git roots and never imports sibling source or opens a business
database.  It also verifies that every checkout and its origin expose only
the ``main`` branch.  ``--github`` adds read-only ``gh repo view`` checks; it
does not archive, delete, rename, push, or change package visibility.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Repository:
    directory: str
    remote: str


ACTIVE = (
    Repository(".", "LordFoxFairy/Kokoro"),
    Repository("kokoro", "LordFoxFairy/kokoro-app"),
    Repository("kokoro-bff", "LordFoxFairy/kokoro-bff"),
    Repository("kokoro-agent", "LordFoxFairy/kokoro-agent"),
    Repository("kokoro-iam", "LordFoxFairy/kokoro-iam"),
    Repository("kokoro-system", "LordFoxFairy/kokoro-system"),
    Repository("kokoro-model", "LordFoxFairy/kokoro-model"),
    Repository("kokoro-billing", "LordFoxFairy/kokoro-billing"),
    Repository("kokoro-capability", "LordFoxFairy/kokoro-capability"),
    Repository("kokoro-storage", "LordFoxFairy/kokoro-storage"),
    Repository("kokoro-scheduler", "LordFoxFairy/kokoro-scheduler"),
)

ARCHIVED = (
    "LordFoxFairy/kokoro-session",
    "LordFoxFairy/kokoro-gateway",
    "LordFoxFairy/kokoro-platform",
    "LordFoxFairy/kokoro-web",
)

RETIRED_LOCAL_NAMES = (
    "kokoro-session",
    "kokoro-gateway",
    "kokoro-platform",
    "kokoro-web",
    "kokoro-credit",
    "kokoro-site-kokoro",
)


COMMAND_TIMEOUT_S = 15


def run(command: list[str], *, cwd: Path = ROOT) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=COMMAND_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"command timed out after {COMMAND_TIMEOUT_S}s: {' '.join(command)}"
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def git_value(directory: Path, *args: str) -> tuple[int, str, str]:
    return run(["git", "-C", str(directory), *args])


def inspect_local(repo: Repository) -> dict[str, object]:
    directory = (ROOT / repo.directory).resolve()
    result: dict[str, object] = {
        "directory": repo.directory,
        "remote": repo.remote,
        "exists": directory.is_dir(),
        "git_root": None,
        "head": None,
        "origin": None,
        "clean": False,
        "current_branch": None,
        "local_branches": [],
        "remote_branches": [],
        "only_main_branch": False,
        "main_matches_head": None,
        "errors": [],
    }
    errors = result["errors"]
    assert isinstance(errors, list)
    if not directory.is_dir():
        errors.append("directory_missing")
        return result

    code, git_root, stderr = git_value(directory, "rev-parse", "--show-toplevel")
    if code != 0:
        errors.append(f"not_a_git_root:{stderr or git_root}")
        return result
    result["git_root"] = str(Path(git_root).resolve())
    if Path(git_root).resolve() != directory:
        errors.append(f"nested_git_root:{git_root}")

    code, head, stderr = git_value(directory, "rev-parse", "HEAD")
    if code == 0:
        result["head"] = head
    else:
        errors.append(f"head_unavailable:{stderr or head}")

    code, current_branch, stderr = git_value(directory, "branch", "--show-current")
    if code == 0:
        result["current_branch"] = current_branch
        if current_branch != "main":
            errors.append(f"not_on_main:{current_branch or 'detached'}")
    else:
        errors.append(f"current_branch_unavailable:{stderr or current_branch}")

    code, local_branches, stderr = git_value(
        directory, "for-each-ref", "--format=%(refname:short)", "refs/heads/"
    )
    if code == 0:
        branches = [branch for branch in local_branches.splitlines() if branch]
        result["local_branches"] = branches
        if branches != ["main"]:
            errors.append(f"unexpected_local_branches:{','.join(branches)}")
    else:
        errors.append(f"local_branches_unavailable:{stderr or local_branches}")

    code, origin, stderr = git_value(directory, "remote", "get-url", "origin")
    if code == 0:
        result["origin"] = origin
        if repo.remote.lower() not in origin.lower():
            errors.append(f"unexpected_origin:{origin}")
    else:
        errors.append(f"origin_unavailable:{stderr or origin}")

    code, status, stderr = git_value(directory, "status", "--porcelain=v1")
    if code == 0:
        result["clean"] = status == ""
        if status:
            errors.append("worktree_dirty")
    else:
        errors.append(f"status_unavailable:{stderr or status}")

    code, remote_head, stderr = git_value(directory, "ls-remote", "origin", "refs/heads/main")
    if code == 0 and head:
        remote_sha = remote_head.split()[0] if remote_head else ""
        result["main_matches_head"] = remote_sha == head
        if remote_sha != head:
            errors.append(f"origin_main_drift:{remote_sha}")
    else:
        result["main_matches_head"] = None
        errors.append(f"origin_main_unavailable:{stderr or remote_head}")

    code, remote_heads, stderr = git_value(directory, "ls-remote", "--heads", "origin")
    if code == 0:
        branches = [
            line.split("\t", 1)[1].removeprefix("refs/heads/")
            for line in remote_heads.splitlines()
            if line and "\trefs/heads/" in line
        ]
        result["remote_branches"] = branches
        result["only_main_branch"] = (
            result["current_branch"] == "main"
            and result["local_branches"] == ["main"]
            and branches == ["main"]
        )
        if branches != ["main"]:
            errors.append(f"unexpected_remote_branches:{','.join(branches)}")
    else:
        errors.append(f"origin_branches_unavailable:{stderr or remote_heads}")
    return result


def inspect_github(repository: str) -> dict[str, object]:
    code, stdout, stderr = run(
        [
            "gh",
            "repo",
            "view",
            repository,
            "--json",
            "nameWithOwner,isArchived,isPrivate,visibility,defaultBranchRef,url",
        ]
    )
    if code != 0:
        return {"repository": repository, "ok": False, "error": stderr or stdout}
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError:
        return {"repository": repository, "ok": False, "error": "invalid_gh_json"}
    return {"repository": repository, "ok": True, **value}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github", action="store_true", help="also read GitHub repository metadata via gh")
    parser.add_argument("--json", type=Path, help="write the evidence JSON to this path")
    args = parser.parse_args(argv)

    evidence: dict[str, object] = {
        "active": [inspect_local(repo) for repo in ACTIVE],
        "retired_local_names": [name for name in RETIRED_LOCAL_NAMES if (ROOT / name).exists()],
        "archived_github": [inspect_github(repo) for repo in ARCHIVED] if args.github else None,
        "status": "PASS",
        "errors": [],
    }
    errors = evidence["errors"]
    assert isinstance(errors, list)
    for item in evidence["active"]:
        assert isinstance(item, dict)
        for error in item["errors"]:
            errors.append(f"{item['directory']}:{error}")
    for name in evidence["retired_local_names"]:
        errors.append(f"retired_local_path:{name}")
    for item in evidence["archived_github"] or []:
        assert isinstance(item, dict)
        if not item.get("ok"):
            errors.append(f"github:{item['repository']}:{item.get('error', 'unknown')}")
        elif not item.get("isArchived"):
            errors.append(f"github_not_archived:{item['repository']}")
    if errors:
        evidence["status"] = "FAIL"

    encoded = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

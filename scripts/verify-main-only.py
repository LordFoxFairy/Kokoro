#!/usr/bin/env python3
"""Prove the Root and every initialized submodule retain only a clean main branch."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("repository_topology", SCRIPT_DIR / "verify-repository-topology.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load repository topology manifest")
topology = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topology)
MODULES = topology.MODULES
ROOT = topology.ROOT


def run(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "command failed").strip())
    return result.stdout.strip()


def branch_state(path: Path) -> dict[str, object]:
    local = tuple(filter(None, run("git", "for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=path).splitlines()))
    remote = tuple(filter(None, run("git", "ls-remote", "--heads", "origin", cwd=path).splitlines()))
    remote_names = tuple(line.split("refs/heads/", 1)[1] for line in remote if "refs/heads/" in line)
    return {
        "head": run("git", "branch", "--show-current", cwd=path),
        "local": local,
        "remote": remote_names,
        "dirty": run("git", "status", "--porcelain", cwd=path),
    }


def main() -> int:
    errors: list[str] = []
    evidence: dict[str, object] = {"status": "PASS", "repositories": {}}
    repositories = {"root": ROOT, **{name: ROOT / relative for name, (relative, _) in MODULES.items()}}
    for name, path in repositories.items():
        if not path.is_dir():
            errors.append(f"{name}: checkout is missing")
            continue
        try:
            state = branch_state(path)
        except RuntimeError as error:
            errors.append(f"{name}: cannot inspect Git state: {error}")
            continue
        evidence["repositories"][name] = state  # type: ignore[index]
        if state["head"] != "main":
            errors.append(f"{name}: checked out branch is not main")
        if state["local"] != ("main",):
            errors.append(f"{name}: local branches are {state['local']!r}, expected only ('main',)")
        if state["remote"] != ("main",):
            errors.append(f"{name}: origin branches are {state['remote']!r}, expected only ('main',)")
        if state["dirty"]:
            errors.append(f"{name}: worktree has uncommitted changes")
    if errors:
        evidence["status"] = "FAIL"
        evidence["errors"] = errors
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

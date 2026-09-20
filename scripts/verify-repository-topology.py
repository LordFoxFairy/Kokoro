#!/usr/bin/env python3
"""Verify Root's exact remote-named Git-submodule composition."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_MODULES = (
    "kokoro-app",
    "kokoro-bff",
    "kokoro-agent",
    "kokoro-iam",
    "kokoro-system",
    "kokoro-billing",
    "kokoro-capability",
    "kokoro-storage",
    "kokoro-scheduler",
)
MODULES = {
    "kokoro-app": ("apps/kokoro-app", "https://github.com/LordFoxFairy/kokoro-app.git"),
    "kokoro-mori": ("apps/kokoro-mori", "https://github.com/LordFoxFairy/kokoro-mori.git"),
    "kokoro-bff": ("apps/kokoro-bff", "https://github.com/LordFoxFairy/kokoro-bff.git"),
    "kokoro-agent": ("apps/kokoro-agent", "https://github.com/LordFoxFairy/kokoro-agent.git"),
    "kokoro-iam": ("apps/kokoro-iam", "https://github.com/LordFoxFairy/kokoro-iam.git"),
    "kokoro-system": ("apps/kokoro-system", "https://github.com/LordFoxFairy/kokoro-system.git"),
    "kokoro-billing": ("apps/kokoro-billing", "https://github.com/LordFoxFairy/kokoro-billing.git"),
    "kokoro-capability": ("apps/kokoro-capability", "https://github.com/LordFoxFairy/kokoro-capability.git"),
    "kokoro-storage": ("apps/kokoro-storage", "https://github.com/LordFoxFairy/kokoro-storage.git"),
    "kokoro-scheduler": ("apps/kokoro-scheduler", "https://github.com/LordFoxFairy/kokoro-scheduler.git"),
    "kokoro-web-shared": ("libs/kokoro-web-shared", "https://github.com/LordFoxFairy/kokoro-web-shared.git"),
}
ARCHIVED = frozenset({
    "kokoro-session",
    "kokoro-gateway",
    "kokoro-platform",
    "kokoro-web",
    "kokoro-credit",
    "kokoro-site-kokoro",
    "kokoro-model",
})


def run(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "command failed").strip())
    return result.stdout.strip()


def normalized_remote(value: str) -> str:
    return value.removesuffix(".git").rstrip("/")


def config(key: str) -> str:
    return run("git", "config", "--file", ".gitmodules", "--get", key)


def gitlink(path: str) -> str:
    output = run("git", "ls-files", "--stage", "--", path)
    fields = output.split()
    if len(fields) < 2 or fields[0] != "160000":
        raise RuntimeError(f"{path} is not a recorded gitlink")
    return fields[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-uninitialized",
        action="store_true",
        help="validate the Root manifest without requiring initialized submodule worktrees",
    )
    args = parser.parse_args(argv)
    errors: list[str] = []
    evidence: dict[str, object] = {"status": "PASS", "runtime_module_count": len(RUNTIME_MODULES), "modules": {}}

    try:
        module_keys = run("git", "config", "--file", ".gitmodules", "--name-only", "--list").splitlines()
    except RuntimeError as error:
        errors.append(f"cannot read .gitmodules: {error}")
        module_keys = []
    declared = {
        key.removeprefix("submodule.").rsplit(".", 1)[0]
        for key in module_keys
        if key.startswith("submodule.") and key.endswith((".path", ".url", ".branch"))
    }
    if declared != set(MODULES):
        errors.append(f".gitmodules names mismatch: {sorted(declared)} != {sorted(MODULES)}")

    for name, (relative_path, expected_remote) in MODULES.items():
        path = ROOT / relative_path
        try:
            declared_path = config(f"submodule.{name}.path")
            declared_remote = config(f"submodule.{name}.url")
            declared_branch = config(f"submodule.{name}.branch")
        except RuntimeError as error:
            errors.append(f"{name}: incomplete .gitmodules entry: {error}")
            continue
        if (declared_path, normalized_remote(declared_remote), declared_branch) != (relative_path, normalized_remote(expected_remote), "main"):
            errors.append(f"{name}: path/url/branch do not match the composition manifest")
        try:
            sha = gitlink(relative_path)
        except RuntimeError as error:
            errors.append(f"{name}: {error}")
            continue
        record: dict[str, str] = {"path": relative_path, "sha": sha, "remote": declared_remote}
        if path.is_dir():
            try:
                if Path(run("git", "rev-parse", "--show-toplevel", cwd=path)).resolve() != path.resolve():
                    errors.append(f"{name}: {relative_path} is not an independent Git worktree")
                actual_remote = run("git", "remote", "get-url", "origin", cwd=path)
                if normalized_remote(actual_remote) != normalized_remote(expected_remote):
                    errors.append(f"{name}: origin remote mismatch: {actual_remote!r}")
                if run("git", "rev-parse", "HEAD", cwd=path) != sha:
                    errors.append(f"{name}: checkout HEAD differs from recorded gitlink")
                record["checkout"] = "initialized"
            except RuntimeError as error:
                errors.append(f"{name}: invalid initialized checkout: {error}")
        elif args.allow_uninitialized:
            record["checkout"] = "not_initialized"
        else:
            errors.append(f"{name}: submodule checkout is missing at {relative_path}")
        evidence["modules"][name] = record  # type: ignore[index]

    for retired in ARCHIVED:
        for root_name in (retired, f"apps/{retired}", f"libs/{retired}"):
            if (ROOT / root_name).exists():
                errors.append(f"retired repository path remains: {root_name}")
    if errors:
        evidence["status"] = "FAIL"
        evidence["errors"] = errors
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

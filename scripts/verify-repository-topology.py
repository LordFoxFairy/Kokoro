#!/usr/bin/env python3
"""Verify the local Goal 2 repository topology and active boundary rules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVED = {
    "kokoro-session",
    "kokoro-gateway",
    "kokoro-platform",
    "kokoro-web",
    "kokoro-credit",
    "kokoro-site-kokoro",
}
ACTIVE = {
    "kokoro": "https://github.com/LordFoxFairy/kokoro-app.git",
    "kokoro-bff": "https://github.com/LordFoxFairy/kokoro-bff.git",
    "kokoro-agent": "https://github.com/LordFoxFairy/kokoro-agent.git",
    "kokoro-iam": "https://github.com/LordFoxFairy/kokoro-iam.git",
    "kokoro-system": "https://github.com/LordFoxFairy/kokoro-system.git",
    "kokoro-model": "https://github.com/LordFoxFairy/kokoro-model.git",
    "kokoro-billing": "https://github.com/LordFoxFairy/kokoro-billing.git",
    "kokoro-capability": "https://github.com/LordFoxFairy/kokoro-capability.git",
    "kokoro-storage": "https://github.com/LordFoxFairy/kokoro-storage.git",
    "kokoro-scheduler": "https://github.com/LordFoxFairy/kokoro-scheduler.git",
}
FORBIDDEN_CODE_MARKERS = ("kokoro-session", "kokoro-gateway", "kokoro-platform", "kokoro-credit")
FORBIDDEN_STORAGE_MARKERS = ("mysql", "mongodb", "pymongo", "motor")
# Historical migration/audit docs may mention retired systems.  The active
# boundary check is intentionally limited to runtime source and deployment
# inputs, where an old dependency would affect a clean standalone checkout.
RUNTIME_DIRS = ("src", ".github")
RUNTIME_FILES = (
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.local.yml",
    ".env.example",
)


def run(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "command failed").strip())
    return result.stdout.strip()


def repo_root(path: Path) -> Path:
    return Path(run("git", "rev-parse", "--show-toplevel", cwd=path)).resolve()


def scan_active_code(path: Path) -> list[str]:
    hits: list[str] = []
    candidates: list[Path] = []
    for relative in (*RUNTIME_DIRS, *RUNTIME_FILES):
        candidate = path / relative
        if candidate.is_file():
            candidates.append(candidate)
        elif candidate.is_dir():
            candidates.extend(
                item
                for item in candidate.rglob("*")
                if item.is_file()
                and ".git" not in item.parts
                and "node_modules" not in item.parts
                and ".venv" not in item.parts
                and "dist" not in item.parts
                and ".next" not in item.parts
            )
    for file in candidates:
        try:
            text = file.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        markers = FORBIDDEN_CODE_MARKERS
        if file.name in {"Dockerfile", "docker-compose.yml", "docker-compose.local.yml", ".env.example"} or "src" in file.parts:
            markers = (*FORBIDDEN_CODE_MARKERS, *FORBIDDEN_STORAGE_MARKERS)
        for marker in markers:
            if marker in text:
                hits.append(f"{file.relative_to(ROOT)}: {marker}")
    return hits


def main() -> int:
    errors: list[str] = []
    evidence: dict[str, object] = {"status": "PASS", "active": {}, "archived_absent": []}

    for name, expected_remote in ACTIVE.items():
        path = ROOT / name
        if not path.is_dir():
            errors.append(f"missing active repository directory: {name}")
            continue
        try:
            top = repo_root(path)
        except RuntimeError as exc:
            errors.append(f"not an independent git repository: {name}: {exc}")
            continue
        try:
            actual_remote = run("git", "remote", "get-url", "origin", cwd=path)
        except RuntimeError:
            actual_remote = ""
        if actual_remote.rstrip("/") not in {expected_remote.removesuffix(".git"), expected_remote}:
            errors.append(f"remote mismatch for {name}: {actual_remote!r} != {expected_remote!r}")
        hits = scan_active_code(path)
        if hits:
            errors.extend(f"active boundary violation: {hit}" for hit in hits[:40])
        evidence["active"][name] = {"path": str(path), "git_root": str(top), "remote": actual_remote, "code_hits": hits}  # type: ignore[index]

    for name in sorted(ARCHIVED):
        if (ROOT / name).exists():
            errors.append(f"archived repository still present in Root: {name}")
        else:
            evidence["archived_absent"].append(name)  # type: ignore[union-attr]

    gitmodules = (ROOT / ".gitmodules").read_text(encoding="utf-8") if (ROOT / ".gitmodules").exists() else ""
    for name in ARCHIVED:
        if name in gitmodules:
            errors.append(f"archived repository remains in .gitmodules: {name}")

    phase1 = (ROOT / "deploy/docker-compose.phase1.yml").read_text(encoding="utf-8")
    if "mysql" in phase1.lower() or "mongo" in phase1.lower():
        errors.append("Phase 1 compose still contains MySQL/Mongo")
    if "kokoro-session" in phase1 or "kokoro-gateway" in phase1:
        errors.append("Phase 1 compose still references archived runtime")

    manifest = json.loads((ROOT / "contract/goal2-repository-contract-manifest.json").read_text(encoding="utf-8"))
    if set(manifest.get("repositories", {})) != {
        "kokoro-iam", "kokoro-system", "kokoro-model", "kokoro-billing",
        "kokoro-capability", "kokoro-storage", "kokoro-scheduler",
    }:
        errors.append("Goal 2 manifest does not contain exactly seven owners")

    if errors:
        evidence["status"] = "FAIL"
        evidence["errors"] = errors
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

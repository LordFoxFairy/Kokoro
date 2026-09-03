#!/usr/bin/env python3
"""Verify the non-negotiable V1 backend rules across the seven child repositories.

This is intentionally a structural gate, not a replacement for a repository's
own lint, typecheck, test, build, or database checks.  It gives the root
workspace one deterministic answer to the questions that are otherwise easy
to miss during a multi-repository clean-slate rewrite.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TS_REPOSITORIES = (
    "kokoro-iam",
    "kokoro-system",
    "kokoro-model",
    "kokoro-billing",
    "kokoro-capability",
    "kokoro-storage",
)
REPOSITORIES = (*TS_REPOSITORIES, "kokoro-scheduler")
REQUIRED_TS_LAYERS = (
    "domain",
    "application",
    "infrastructure",
    "interfaces",
    "config",
    "bootstrap",
)
REQUIRED_SCHEDULER_LAYERS = (
    "domain",
    "application",
    "ports",
    "adapters",
    "transport",
)


@dataclass(frozen=True)
class Failure:
    repository: str
    rule: str
    detail: str


def tracked_or_worktree_files(repository: Path, relative_root: str) -> list[Path]:
    root = repository / relative_root
    if not root.exists():
        return []
    return [path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]


def source_files(repository: Path) -> list[Path]:
    return tracked_or_worktree_files(repository, "src")


def database_files(repository: Path) -> list[Path]:
    return tracked_or_worktree_files(repository, "database")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def package_scripts(repository: Path) -> dict[str, object]:
    package_json = repository / "package.json"
    if not package_json.is_file():
        return {}
    try:
        package = json.loads(read_text(package_json))
    except json.JSONDecodeError:
        return {}
    scripts = package.get("scripts", {})
    return scripts if isinstance(scripts, dict) else {}


def add(failures: list[Failure], repository: str, rule: str, detail: str) -> None:
    failures.append(Failure(repository, rule, detail))


def check_common(repository_name: str, failures: list[Failure]) -> None:
    repository = ROOT / repository_name
    if not repository.is_dir():
        add(failures, repository_name, "repository", "child repository directory is missing")
        return

    if not (repository / "AGENTS.md").is_file():
        add(failures, repository_name, "agent-contract", "AGENTS.md is missing")

    migrations = repository / "database" / "migrations"
    if migrations.is_dir():
        add(failures, repository_name, "canonical-schema", "database/migrations must not exist")

    sql_files = [path for path in database_files(repository) if path.suffix.lower() == ".sql"]
    if sql_files:
        canonical = repository / "database" / "schema.sql"
        if not canonical.is_file():
            add(failures, repository_name, "canonical-schema", "database/schema.sql is missing")

        non_canonical = [
            path.relative_to(repository).as_posix()
            for path in sql_files
            if path.name not in {"schema.sql", "seed.sql"} and "seed" not in path.relative_to(repository).parts
        ]
        if non_canonical:
            add(
                failures,
                repository_name,
                "canonical-schema",
                "additional executable SQL files: " + ", ".join(sorted(non_canonical)),
            )

        for path in sql_files:
            text = read_text(path)
            if re.search(r"\bFOREIGN\s+KEY\b|\bREFERENCES\b", text, re.IGNORECASE):
                add(
                    failures,
                    repository_name,
                    "relation-integrity",
                    f"{path.relative_to(repository)} contains FOREIGN KEY or REFERENCES",
                )
            if re.search(r"\bTIMESTAMP(?:\s*\([^)]*\))?\b(?!\s+WITH\s+TIME\s+ZONE)", text, re.IGNORECASE):
                add(
                    failures,
                    repository_name,
                    "utc-time",
                    f"{path.relative_to(repository)} contains a timestamp without time zone",
                )
            if re.search(r"\b[a-z0-9_]+_at_unix_seconds\b", text, re.IGNORECASE):
                add(
                    failures,
                    repository_name,
                    "utc-time",
                    f"{path.relative_to(repository)} stores a database fact as Unix seconds",
                )

    for path in source_files(repository):
        text = read_text(path)
        if re.search(r"\b(?:class|interface)\s+InMemory\w*|\bInMemory\w*Repository\b", text):
            add(failures, repository_name, "production-doubles", f"{path.relative_to(repository)} contains InMemory code")
        if re.search(r"\b(?:class|interface)\s+(?:Fake|Fixture)\w*", text):
            add(failures, repository_name, "production-doubles", f"{path.relative_to(repository)} contains Fake/Fixture code")
        if re.search(r"(?:=|IN|VALUES\s*\([^)]*)\s*\?", text, re.IGNORECASE):
            add(failures, repository_name, "sql-parameters", f"{path.relative_to(repository)} appears to use ? SQL placeholders")
        if re.search(
            r"\blegacy\b|\bcompatibility\s+(?:layer|alias|path|endpoint|mode)\b|"
            r"\b(?:keep|preserve|support|use)\s+(?:the\s+)?fallback\b",
            text,
            re.IGNORECASE,
        ):
            add(failures, repository_name, "clean-slate", f"{path.relative_to(repository)} contains a legacy/compat/fallback marker")


def check_typescript(repository_name: str, failures: list[Failure]) -> None:
    repository = ROOT / repository_name
    for layer in REQUIRED_TS_LAYERS:
        if not (repository / "src" / layer).is_dir():
            add(failures, repository_name, "layered-topology", f"src/{layer}/ is missing")

    scripts = package_scripts(repository)
    for script in ("lint", "typecheck", "test", "build", "db:apply-schema"):
        if script not in scripts:
            add(failures, repository_name, "quality-gates", f"package.json script {script!r} is missing")
    lint_command = str(scripts.get("lint", ""))
    if lint_command in {"npm run typecheck", "pnpm typecheck", "npm run check", "pnpm check"}:
        add(failures, repository_name, "quality-gates", "lint must be a real static-analysis command, not a typecheck/check alias")


def check_scheduler(failures: list[Failure]) -> None:
    repository_name = "kokoro-scheduler"
    repository = ROOT / repository_name
    for layer in REQUIRED_SCHEDULER_LAYERS:
        if not (repository / "internal" / layer).is_dir():
            add(failures, repository_name, "layered-topology", f"internal/{layer}/ is missing")
    if not (repository / "cmd" / "scheduler").is_dir():
        add(failures, repository_name, "layered-topology", "cmd/scheduler/ is missing")
    if not (repository / "go.mod").is_file():
        add(failures, repository_name, "go-tooling", "go.mod is missing")


def check_docs(failures: list[Failure]) -> None:
    required = (
        ROOT / "AGENTS.md",
        ROOT / "docs" / "ARCHITECTURE_STANDARD.md",
        ROOT / "docs" / "CURRENT.md",
        ROOT / "docs" / "CODEBASE_MAP.md",
    )
    for path in required:
        if not path.is_file():
            add(failures, "root", "governance", f"{path.relative_to(ROOT)} is missing")


def main() -> int:
    failures: list[Failure] = []
    check_docs(failures)
    for repository in REPOSITORIES:
        check_common(repository, failures)
    for repository in TS_REPOSITORIES:
        check_typescript(repository, failures)
    check_scheduler(failures)

    if failures:
        print(f"FAIL seven-repository-standard ({len(failures)} rule violations)")
        for failure in failures:
            print(f"- [{failure.repository}] {failure.rule}: {failure.detail}")
        return 1

    print(f"PASS seven-repository-standard ({len(REPOSITORIES)} repositories)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

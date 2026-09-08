"""Shared profiles, diagnostics and parsers for the ten-repository audit."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_NODE_ENGINE = ">=24 <25"
REQUIRED_TS_SOURCE_PATHS = ("modules", "config")
RETIRED_TS_TOP_LEVEL_DIRECTORIES = (
    "adapters",
    "application",
    "clients",
    "common",
    "contracts",
    "controllers",
    "domain",
    "dtos",
    "infrastructure",
    "interfaces",
    "middlewares",
    "models",
    "ports",
    "postgres",
    "prisma",
    "redis",
    "repositories",
    "services",
    "types",
    "utils",
)
REQUIRED_AGENT_SOURCE_PATHS = ("execution",)
RETIRED_AGENT_TOP_LEVEL_DIRECTORIES = (
    "application",
    "domain",
    "infrastructure",
    "interfaces",
    "modules",
    "ports",
    "repositories",
)
REQUIRED_SCHEDULER_LAYERS = (
    "domain",
    "application",
    "ports",
    "adapters",
    "transport",
)
REQUIRED_REPOSITORY_DOCUMENTS = (
    "README.md",
    "INDEX.md",
    "docs/INDEX.md",
    "docs/CURRENT.md",
    "docs/TECHNICAL_DESIGN.md",
    "docs/API_CONTRACT.md",
    "docs/DATA_MODEL.md",
    "docs/SECURITY.md",
    "docs/RELIABILITY.md",
    "docs/ACCEPTANCE.md",
    "docs/SLO.md",
    "docs/RUNBOOK.md",
)
REQUIRED_REPOSITORY_DIRECTORIES = ("docs/ADR",)
FILE_GRANULARITY_EXEMPT_PREFIXES = {
    "kokoro": ("src/i18n/",),
}
CONTRACT_README_FIELDS = (
    "owner",
    "visibility",
    "version",
    "generation",
    "breaking",
    "provenance",
)
REQUIRED_TS_COMPILER_OPTIONS = (
    "strict",
    "noUncheckedIndexedAccess",
    "exactOptionalPropertyTypes",
    "noImplicitOverride",
    "noImplicitReturns",
    "noFallthroughCasesInSwitch",
    "useUnknownInCatchVariables",
    "forceConsistentCasingInFileNames",
    "isolatedModules",
    "noEmitOnError",
)


@dataclass(frozen=True)
class RepositoryProfile:
    kind: str
    requires_schema: bool
    redis_database: int | None
    required_source_paths: tuple[str, ...] = ()


REPOSITORY_PROFILES = {
    "kokoro": RepositoryProfile("web", False, None),
    "kokoro-bff": RepositoryProfile(
        "typescript-service", True, 8, REQUIRED_TS_SOURCE_PATHS
    ),
    "kokoro-agent": RepositoryProfile(
        "python-service", True, 9, REQUIRED_AGENT_SOURCE_PATHS
    ),
    "kokoro-iam": RepositoryProfile(
        "typescript-service", True, 1, REQUIRED_TS_SOURCE_PATHS
    ),
    "kokoro-system": RepositoryProfile(
        "typescript-service", True, 2, REQUIRED_TS_SOURCE_PATHS
    ),
    "kokoro-billing": RepositoryProfile(
        "typescript-service", True, 4, REQUIRED_TS_SOURCE_PATHS
    ),
    "kokoro-capability": RepositoryProfile(
        "typescript-service", True, 5, REQUIRED_TS_SOURCE_PATHS
    ),
    "kokoro-storage": RepositoryProfile(
        "typescript-service", True, 6, REQUIRED_TS_SOURCE_PATHS
    ),
    "kokoro-scheduler": RepositoryProfile(
        "go-service", True, 7, REQUIRED_SCHEDULER_LAYERS
    ),
}
REPOSITORIES = tuple(REPOSITORY_PROFILES)
TS_REPOSITORIES = tuple(
    name
    for name, profile in REPOSITORY_PROFILES.items()
    if profile.kind in {"web", "typescript-service"}
)
LOCAL_REDIS_DATABASES = {
    name: profile.redis_database
    for name, profile in REPOSITORY_PROFILES.items()
    if profile.redis_database is not None
}


@dataclass(frozen=True)
class Failure:
    repository: str
    rule: str
    detail: str


def required_quality_scripts(repository_name: str) -> tuple[str, ...]:
    profile = REPOSITORY_PROFILES[repository_name]
    if profile.kind == "web":
        return ("lint", "typecheck", "test", "build", "test:e2e")
    if profile.kind == "typescript-service":
        return (
            "format:check",
            "lint",
            "typecheck",
            "test",
            "build",
            "db:apply-schema",
            "contract:check",
        )
    return ()


def tracked_or_worktree_files(repository: Path, relative_root: str) -> list[Path]:
    root = repository / relative_root
    if not root.exists():
        return []
    return [
        path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts
    ]


def source_files(repository: Path) -> list[Path]:
    return tracked_or_worktree_files(repository, "src")


def database_files(repository: Path) -> list[Path]:
    return tracked_or_worktree_files(repository, "database")


def contract_source_files(repository: Path) -> list[Path]:
    return [
        path
        for path in tracked_or_worktree_files(repository, "contract")
        if path.name.lower() != "readme.md"
        and "tests" not in path.relative_to(repository / "contract").parts
        and path.suffix.lower() in {".json", ".proto", ".yaml", ".yml"}
    ]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def sql_without_comments(text: str) -> str:
    """Remove SQL comments before applying lexical schema rules.

    The governance checks are intentionally lexical, but explanatory comments
    must not turn a valid schema into a false failure.  This helper is not a
    SQL parser; it only removes the comment forms used by the canonical
    schemas, while preserving line breaks for useful diagnostics.
    """
    without_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(line.split("--", 1)[0] for line in without_block.splitlines())


def has_exact_relative_file(repository: Path, relative: str) -> bool:
    current = repository
    for part in Path(relative).parts:
        try:
            entries = {entry.name: entry for entry in current.iterdir()}
        except OSError:
            return False
        matched = entries.get(part)
        if matched is None:
            return False
        current = matched
    return current.is_file()


def has_exact_relative_directory(repository: Path, relative: str) -> bool:
    current = repository
    for part in Path(relative).parts:
        try:
            entries = {entry.name: entry for entry in current.iterdir()}
        except OSError:
            return False
        matched = entries.get(part)
        if matched is None:
            return False
        current = matched
    return current.is_dir()


def package_manifest(repository: Path) -> dict[str, object]:
    package_json = repository / "package.json"
    if not package_json.is_file():
        return {}
    try:
        package = json.loads(read_text(package_json))
    except json.JSONDecodeError:
        return {}
    return package if isinstance(package, dict) else {}


def package_scripts(repository: Path) -> dict[str, object]:
    scripts = package_manifest(repository).get("scripts", {})
    return scripts if isinstance(scripts, dict) else {}


class TypeScriptConfigError(ValueError):
    """The installed compiler could not produce an authoritative configuration."""


def effective_ts_compiler_options(path: Path) -> dict[str, object]:
    """Delegate JSONC, extends and defaults to the repository's own compiler.

    Never download tools during audit or silently reinterpret invalid JSONC.
    The caller reports an explicit unresolved-toolchain diagnostic on failure.
    """
    compiler = path.parent / "node_modules" / "typescript" / "bin" / "tsc"
    if not path.is_file() or not compiler.is_file():
        raise TypeScriptConfigError("tsconfig.json or installed TypeScript is missing")
    try:
        result = subprocess.run(
            ["node", str(compiler), "--showConfig", "-p", str(path)],
            cwd=path.parent,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise TypeScriptConfigError("tsc --showConfig could not run") from error
    if result.returncode != 0:
        raise TypeScriptConfigError(
            "tsc --showConfig failed; run it in the repository for diagnostics"
        )
    try:
        config = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise TypeScriptConfigError("tsc --showConfig did not return JSON") from error
    options = config.get("compilerOptions") if isinstance(config, dict) else None
    if not isinstance(options, dict):
        raise TypeScriptConfigError("resolved compilerOptions are missing")
    return options


def add(failures: list[Failure], repository: str, rule: str, detail: str) -> None:
    failures.append(Failure(repository, rule, detail))


def appears_to_use_question_mark_sql(text: str) -> bool:
    has_statement = re.search(
        r"\b(?:SELECT\b|INSERT\s+INTO\b|UPDATE\s+[a-z0-9_]+\s+SET\b|DELETE\s+FROM\b|WITH\s+[a-z0-9_]+\s+AS\b)",
        text,
        re.IGNORECASE,
    )
    has_question_mark_parameter = re.search(
        r"(?:=|\bIN\s*\(|\bVALUES\s*\([^)]*)\s*\?", text, re.IGNORECASE
    )
    return has_statement is not None and has_question_mark_parameter is not None


def extract_redis_databases(text: str) -> set[int]:
    return {
        int(match.group(1))
        for match in re.finditer(
            r"rediss?://[^\s\"']+/(\d+)(?:[?\s\"']|$)", text, re.IGNORECASE
        )
    }


def has_clean_slate_marker(text: str) -> bool:
    code_without_line_comments = "\n".join(
        re.split(r"//|#", line, maxsplit=1)[0] for line in text.splitlines()
    )
    return (
        re.search(
            r"\b(?:legacy|compat)(?:[A-Z][A-Za-z0-9_]*|_[a-z0-9_]+)\b",
            code_without_line_comments,
        )
        is not None
    )


def missing_contract_readme_fields(text: str) -> tuple[str, ...]:
    normalized = text.lower()
    return tuple(field for field in CONTRACT_README_FIELDS if field not in normalized)


def is_granularity_exempt(repository_name: str, relative_path: str) -> bool:
    return any(
        relative_path.startswith(prefix)
        for prefix in FILE_GRANULARITY_EXEMPT_PREFIXES.get(repository_name, ())
    )

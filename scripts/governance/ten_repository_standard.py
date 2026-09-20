"""Shared profiles, diagnostics and parsers for the ten-repository audit."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]

RETIRED_TS_TOP_LEVEL_DIRECTORIES = (
    "application",
    "domain",
    "infrastructure",
    "interfaces",
    "ports",
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
    "kokoro-app": ("src/i18n/",),
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
    canonical_schema: str | None = None
    schema_kind: Literal["none", "sql", "prisma"] = "none"
    node_major: int | None = None
    required_source_paths: tuple[str, ...] = ()
    retired_source_paths: tuple[str, ...] = ()
    schema_drift_script: str | None = None
    schema_drift_checker: str | None = None
    upstream_openapi_snapshots: tuple[str, ...] = ()


# Current owner facts, not the future cutover target. BFF still uses Node 22
# and its existing layered tree; System/IAM/Storage have retired global layers.
REPOSITORY_PROFILES = {
    "kokoro-app": RepositoryProfile("web", False, None, node_major=22),
    "kokoro-bff": RepositoryProfile(
        "typescript-service",
        True,
        8,
        "database/schema.sql",
        "sql",
        22,
    ),
    "kokoro-agent": RepositoryProfile(
        "python-service",
        True,
        9,
        "database/schema.sql",
        "sql",
        required_source_paths=REQUIRED_AGENT_SOURCE_PATHS,
    ),
    "kokoro-iam": RepositoryProfile(
        "typescript-service",
        True,
        1,
        "prisma/schema.prisma",
        "prisma",
        24,
        retired_source_paths=RETIRED_TS_TOP_LEVEL_DIRECTORIES,
        upstream_openapi_snapshots=("contract/vendor/better-auth.v1.7.3.json",),
        # TECHNICAL_DESIGN §12 requires read-only persisted-schema drift, but
        # the current fresh-DDL fixture is not that checker. Keep the gap visible.
    ),
    "kokoro-system": RepositoryProfile(
        "typescript-service",
        True,
        2,
        "database/schema.sql",
        "sql",
        24,
        retired_source_paths=RETIRED_TS_TOP_LEVEL_DIRECTORIES,
    ),
    "kokoro-billing": RepositoryProfile(
        "typescript-service",
        True,
        4,
        "database/schema.sql",
        "sql",
        24,
    ),
    "kokoro-capability": RepositoryProfile(
        "typescript-service",
        True,
        5,
        "prisma/schema.prisma",
        "prisma",
        24,
        schema_drift_script="schema:check",
        schema_drift_checker="scripts/check-schema.ts",
    ),
    "kokoro-storage": RepositoryProfile(
        "typescript-service",
        True,
        6,
        "prisma/schema.prisma",
        "prisma",
        24,
        retired_source_paths=RETIRED_TS_TOP_LEVEL_DIRECTORIES,
        schema_drift_script="db:apply-schema",
        schema_drift_checker="scripts/apply-schema.ts",
    ),
    "kokoro-scheduler": RepositoryProfile(
        "go-service",
        True,
        7,
        "database/schema.sql",
        "sql",
        required_source_paths=REQUIRED_SCHEDULER_LAYERS,
    ),
}
REPOSITORY_PATHS = {name: Path("apps") / name for name in REPOSITORY_PROFILES}

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
        ) + (
            ("prisma:validate", "prisma:generate")
            if profile.schema_kind == "prisma"
            else ()
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


def yaml_document_body(text: str) -> str:
    """Consume complete preamble lines, preserving the root node's indentation."""
    lines = text.removeprefix("\ufeff").splitlines(keepends=True)
    marker_seen = False
    directive_seen = False
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if line.startswith("%"):
            if (
                marker_seen
                or directive_seen
                or not re.fullmatch(r"%YAML 1\.2(?:\s+#.*)?", stripped)
            ):
                raise ValueError("unsupported or repeated YAML directive")
            directive_seen = True
            index += 1
            continue
        if not marker_seen and re.match(r"---(?:\s|$)", line):
            marker_seen = True
            remainder = line[3:].lstrip(" \t")
            index += 1
            if remainder.strip() and not remainder.startswith("#"):
                body = remainder + "".join(lines[index:])
                try:
                    json.loads(body)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        "inline YAML document markers support JSON values only"
                    ) from error
                return body
            continue
        break
    if directive_seen and not marker_seen:
        raise ValueError("YAML directive requires a document-start marker")
    return "".join(lines[index:])


def openapi_contract_candidates(repository: Path) -> tuple[Path, ...]:
    """Enumerate managed inputs without guessing YAML identity from source text.

    Every YAML/JSON file under contract/openapi and the declared root JSON
    reaches the parser, even if malformed or unsupported. Other contract files
    are included only when the standard JSON parser proves a top-level OpenAPI
    key (JSON remains valid with a YAML extension). Candidates are not proof of
    ownership: only the contract checker can confirm that after parsing.
    """
    managed = set(tracked_or_worktree_files(repository, "contract/openapi"))
    root_json = repository / "contract/openapi.json"
    if root_json.is_file():
        managed.add(root_json)
    candidates: list[Path] = []
    profile = REPOSITORY_PROFILES.get(repository.name)
    snapshots = profile.upstream_openapi_snapshots if profile else ()
    provenance = read_text(repository / "contract/README.md")
    for path in sorted(managed | set(contract_source_files(repository))):
        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue
        relative = path.relative_to(repository).as_posix()
        # Only a profile-pinned snapshot with an exact README record is exempt.
        # A generic vendor directory or self-declared provenance is not a waiver.
        if relative in snapshots and any(
            re.search(
                r"(?<![\w./-])(?:"
                + re.escape(relative)
                + "|"
                + re.escape(path.name)
                + r")(?![\w./-])",
                line,
            )
            and re.search(r"\bsnapshot\b", line, re.IGNORECASE)
            and re.search(r"\bupstream\b|上游", line, re.IGNORECASE)
            for line in provenance.splitlines()
        ):
            continue
        if path in managed:
            candidates.append(path)
            continue
        text = read_text(path)
        try:
            if path.suffix.lower() in {".yaml", ".yml"}:
                text = yaml_document_body(text)
            document = json.loads(text)
        except ValueError:
            continue
        if isinstance(document, dict) and isinstance(document.get("openapi"), str):
            candidates.append(path)
    return tuple(candidates)


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

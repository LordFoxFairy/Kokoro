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
LOCAL_REDIS_DATABASES = {
    "kokoro-iam": 1,
    "kokoro-system": 2,
    "kokoro-model": 3,
    "kokoro-billing": 4,
    "kokoro-capability": 5,
    "kokoro-storage": 6,
    "kokoro-scheduler": 7,
}
REQUIRED_TS_LAYERS = (
    "domain",
    "application",
    "infrastructure",
    "interfaces",
    "config",
    "bootstrap",
)
REQUIRED_TS_COMPILER_OPTIONS = (
    "strict",
    "noUncheckedIndexedAccess",
    "exactOptionalPropertyTypes",
    "noImplicitOverride",
    "noImplicitReturns",
    "noUnusedLocals",
    "noUnusedParameters",
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


def package_manifest(repository: Path) -> dict[str, object]:
    package_json = repository / "package.json"
    if not package_json.is_file():
        return {}
    try:
        package = json.loads(read_text(package_json))
    except json.JSONDecodeError:
        return {}
    return package if isinstance(package, dict) else {}


def effective_ts_compiler_options(path: Path, visited: set[Path] | None = None) -> dict[str, object]:
    visited = visited or set()
    resolved = path.resolve()
    if resolved in visited or not path.is_file():
        return {}
    visited.add(resolved)
    try:
        config = json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}
    options: dict[str, object] = {}
    parent = config.get("extends")
    if isinstance(parent, str) and parent.startswith("."):
        parent_path = (path.parent / parent)
        if parent_path.suffix != ".json":
            parent_path = parent_path.with_suffix(".json")
        options.update(effective_ts_compiler_options(parent_path, visited))
    own = config.get("compilerOptions")
    if isinstance(own, dict):
        options.update(own)
    return options


def check_schema_naming(
    repository_name: str,
    canonical: Path,
    failures: list[Failure],
) -> None:
    """Keep database diagnostics stable by requiring explicit, readable names."""
    pending_constraint_name: str | None = None
    for line_number, line in enumerate(read_text(canonical).splitlines(), start=1):
        named_constraint = re.search(r"\bCONSTRAINT\s+([a-z0-9_]+)", line, re.IGNORECASE)
        if named_constraint:
            pending_constraint_name = named_constraint.group(1).lower()

        if re.search(r"\bCHECK\s*\(", line, re.IGNORECASE) and not (
            re.search(r"\bCONSTRAINT\s+ck_[a-z0-9_]+\b", line, re.IGNORECASE)
            or (pending_constraint_name or "").startswith("ck_")
        ):
            add(
                failures,
                repository_name,
                "sql-naming",
                f"database/schema.sql:{line_number} CHECK must have a ck_ constraint name",
            )
        if (
            re.search(r"\bUNIQUE(?:\s*\(|\s*[,)]?$)", line, re.IGNORECASE)
            and not re.search(r"\bCREATE\s+UNIQUE\s+INDEX\b", line, re.IGNORECASE)
            and not re.search(r"\bCONSTRAINT\s+uq_[a-z0-9_]+\b", line, re.IGNORECASE)
            and not (pending_constraint_name or "").startswith("uq_")
        ):
            add(
                failures,
                repository_name,
                "sql-naming",
                f"database/schema.sql:{line_number} UNIQUE must have a uq_ constraint name",
            )

        index_match = re.search(
            r"CREATE\s+(UNIQUE\s+)?INDEX(?:\s+IF\s+NOT\s+EXISTS)?\s+([a-z0-9_]+)",
            line,
            re.IGNORECASE,
        )
        if index_match:
            expected_prefix = "uq_" if index_match.group(1) else "ix_"
            if not index_match.group(2).lower().startswith(expected_prefix):
                add(
                    failures,
                    repository_name,
                    "sql-naming",
                    f"database/schema.sql:{line_number} index must start with {expected_prefix}",
                )

        constraint_match = re.search(r"\bCONSTRAINT\s+([a-z0-9_]+)", line, re.IGNORECASE)
        if constraint_match and not constraint_match.group(1).lower().startswith(
            ("ck_", "uq_", "pk_", "ex_")
        ):
            add(
                failures,
                repository_name,
                "sql-naming",
                f"database/schema.sql:{line_number} has a non-standard constraint name",
            )
        if re.search(r"\b(?:CHECK|UNIQUE|PRIMARY\s+KEY|EXCLUDE)\b", line, re.IGNORECASE):
            pending_constraint_name = None


def check_openapi_contract(
    repository_name: str,
    specification: Path,
    failures: list[Failure],
) -> None:
    lines = read_text(specification).splitlines()
    properties_indents: list[int] = []
    for line_number, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        while properties_indents and indent <= properties_indents[-1]:
            properties_indents.pop()
        if re.match(r"properties\s*:\s*$", stripped):
            properties_indents.append(indent)
            continue
        path_match = re.match(r"(/[^:]*):\s*$", stripped)
        if path_match and indent <= 4:
            route = path_match.group(1)
            internal_versioned = re.match(r"^/internal(?:/[a-z0-9._{}-]+)*/v[0-9]+(?:/|$)", route)
            if not (
                route.startswith(("/v1/", "/.well-known/"))
                or route in {"/v1", "/healthz", "/readyz", "/metrics"}
                or internal_versioned
            ):
                add(
                    failures,
                    repository_name,
                    "http-versioning",
                    f"{specification.relative_to(ROOT / repository_name)}:{line_number} has non-versioned path {route!r}",
                )
        if properties_indents and indent == properties_indents[-1] + 2:
            property_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*):", stripped)
            if property_match and re.search(r"[A-Z]", property_match.group(1)):
                add(
                    failures,
                    repository_name,
                    "wire-naming",
                    f"{specification.relative_to(ROOT / repository_name)}:{line_number} property {property_match.group(1)!r} is not snake_case",
                )


def add(failures: list[Failure], repository: str, rule: str, detail: str) -> None:
    failures.append(Failure(repository, rule, detail))


def check_common(repository_name: str, failures: list[Failure]) -> None:
    repository = ROOT / repository_name
    if not repository.is_dir():
        add(failures, repository_name, "repository", "child repository directory is missing")
        return

    if not (repository / "AGENTS.md").is_file():
        add(failures, repository_name, "agent-contract", "AGENTS.md is missing")

    env_example = repository / ".env.example"
    expected_redis = f"redis://127.0.0.1:56380/{LOCAL_REDIS_DATABASES[repository_name]}"
    if not env_example.is_file() or expected_redis not in read_text(env_example):
        add(
            failures,
            repository_name,
            "shared-local-infrastructure",
            f".env.example must use the shared Redis logical DB {expected_redis}",
        )

    migrations = repository / "database" / "migrations"
    if migrations.is_dir():
        add(failures, repository_name, "canonical-schema", "database/migrations must not exist")

    for compose in (*repository.glob("docker-compose*.yml"), *repository.glob("docker-compose*.yaml")):
        compose_text = read_text(compose)
        if re.search(r"^\s*image:\s*(?:postgres|redis)(?::|\s|$)", compose_text, re.MULTILINE | re.IGNORECASE):
            add(
                failures,
                repository_name,
                "shared-local-infrastructure",
                f"{compose.name} must not start a repository-local PostgreSQL or Redis",
            )
        if re.search(r"^\s*build:\s*", compose_text, re.MULTILINE):
            add(
                failures,
                repository_name,
                "source-local-runtime",
                f"{compose.name} must not use an application build as the local development entry",
            )

    sql_files = [path for path in database_files(repository) if path.suffix.lower() == ".sql"]
    if sql_files:
        canonical = repository / "database" / "schema.sql"
        if not canonical.is_file():
            add(failures, repository_name, "canonical-schema", "database/schema.sql is missing")
        else:
            check_schema_naming(repository_name, canonical, failures)

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


def check_delivery(repository_name: str, failures: list[Failure]) -> None:
    repository = ROOT / repository_name
    docs = repository / "docs"
    documentation_names = {
        path.name.lower()
        for path in docs.iterdir()
        if docs.is_dir() and path.is_file()
    } if docs.is_dir() else set()
    if "slo.md" not in documentation_names:
        add(failures, repository_name, "operability", "docs/SLO.md is missing")
    if "runbook.md" not in documentation_names:
        add(failures, repository_name, "operability", "docs/RUNBOOK.md or docs/runbook.md is missing")

    dockerfile = repository / "Dockerfile"
    if not dockerfile.is_file():
        add(failures, repository_name, "container", "Dockerfile is missing")
    else:
        docker_text = read_text(dockerfile)
        build_args = dict(re.findall(r"^ARG\s+([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)", docker_text, re.MULTILINE))
        declared_stages: set[str] = set()
        for match in re.finditer(r"^FROM\s+([^\s]+)(?:\s+AS\s+([^\s]+))?", docker_text, re.MULTILINE | re.IGNORECASE):
            image = match.group(1)
            variable = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", image)
            resolved_image = build_args.get(variable.group(1), "") if variable else image
            if image.lower() not in declared_stages and image.lower() != "scratch" and "@sha256:" not in resolved_image:
                add(
                    failures,
                    repository_name,
                    "container-reproducibility",
                    f"Dockerfile FROM source {image!r} must be pinned by sha256 digest",
                )
            if match.group(2):
                declared_stages.add(match.group(2).lower())
        runtime_users = re.findall(r"^USER\s+([^\s]+)", docker_text, re.MULTILINE | re.IGNORECASE)
        if not runtime_users or runtime_users[-1].lower() in {"0", "root", "root:root"}:
            add(failures, repository_name, "container", "runtime image must declare a non-root USER")
        if not re.search(r"^HEALTHCHECK\b", docker_text, re.MULTILINE | re.IGNORECASE):
            add(failures, repository_name, "container", "runtime image must declare HEALTHCHECK")

    workflows = repository / ".github" / "workflows"
    ci = workflows / "ci.yml"
    release = workflows / "release-image.yml"
    for workflow in (ci, release):
        if not workflow.is_file():
            continue
        text = read_text(workflow)
        for line_number, line in enumerate(text.splitlines(), start=1):
            action = re.search(r"\buses:\s*([^\s#]+)", line)
            if not action or action.group(1).startswith("./"):
                continue
            reference = action.group(1).rsplit("@", 1)[-1]
            if not re.fullmatch(r"[0-9a-f]{40}", reference):
                add(
                    failures,
                    repository_name,
                    "supply-chain",
                    f"{workflow.relative_to(repository)}:{line_number} action must be pinned to a full commit SHA",
                )

    if ci.is_file() and not re.search(
        r"trivy|grype|dependency-review|dependency\s+review|pnpm\s+audit|govulncheck|gitleaks",
        read_text(ci),
        re.IGNORECASE,
    ):
        add(failures, repository_name, "security-gate", ".github/workflows/ci.yml has no dependency/source/secret scan")
    if release.is_file():
        release_text = read_text(release)
        required_release_markers = {
            "image vulnerability scan": r"trivy|grype",
            "SBOM": r"\bsbom\s*:",
            "build provenance": r"\bprovenance\s*:",
            "digest signature or attestation": r"cosign\s+sign|attest-build-provenance|attestation",
        }
        for description, pattern in required_release_markers.items():
            if not re.search(pattern, release_text, re.IGNORECASE):
                add(
                    failures,
                    repository_name,
                    "supply-chain",
                    f".github/workflows/release-image.yml has no {description}",
                )
        push_match = re.search(r"^\s*push:\s*true\s*$", release_text, re.MULTILINE)
        if push_match:
            before_push = release_text[: push_match.start()]
            has_local_candidate = re.search(
                r"^\s*load:\s*true\s*$|\bdocker\s+build\b",
                before_push,
                re.MULTILINE | re.IGNORECASE,
            )
            has_candidate_scan = re.search(r"\bimage-ref\s*:", before_push, re.IGNORECASE)
            if not has_local_candidate or not has_candidate_scan:
                add(
                    failures,
                    repository_name,
                    "supply-chain",
                    ".github/workflows/release-image.yml must build and scan a local candidate before push",
                )


def check_typescript(repository_name: str, failures: list[Failure]) -> None:
    repository = ROOT / repository_name
    for layer in REQUIRED_TS_LAYERS:
        if not (repository / "src" / layer).is_dir():
            add(failures, repository_name, "layered-topology", f"src/{layer}/ is missing")

    package = package_manifest(repository)
    scripts = package_scripts(repository)
    if package.get("packageManager") != "pnpm@11.25.0":
        add(failures, repository_name, "toolchain", "packageManager must pin pnpm@11.25.0")
    if not (repository / "pnpm-lock.yaml").is_file():
        add(failures, repository_name, "toolchain", "pnpm-lock.yaml is missing")
    if (repository / "package-lock.json").exists():
        add(failures, repository_name, "toolchain", "package-lock.json must not coexist with pnpm")
    docker_text = read_text(repository / "Dockerfile")
    docker_install_count = len(re.findall(r"\bpnpm(?:@[^\s]+)?\s+install\b", docker_text))
    if docker_install_count and docker_text.count("--ignore-scripts") < docker_install_count:
        add(
            failures,
            repository_name,
            "container-supply-chain",
            "every Docker pnpm install must use --ignore-scripts; required generators run explicitly",
        )
    for script in ("lint", "typecheck", "test", "build", "db:apply-schema"):
        if script not in scripts:
            add(failures, repository_name, "quality-gates", f"package.json script {script!r} is missing")
    if "contract:check" not in scripts:
        add(failures, repository_name, "contract-owner", "package.json script 'contract:check' is missing")
    lint_command = str(scripts.get("lint", ""))
    if lint_command in {"npm run typecheck", "pnpm typecheck", "npm run check", "pnpm check"}:
        add(failures, repository_name, "quality-gates", "lint must be a real static-analysis command, not a typecheck/check alias")
    for script_name, command in scripts.items():
        if re.search(r"\bdb:migrate\b|database/migrations|schema_migrations", str(command), re.IGNORECASE):
            add(
                failures,
                repository_name,
                "canonical-schema",
                f"package.json script {script_name!r} still invokes migration tooling",
            )

    compiler_options = effective_ts_compiler_options(repository / "tsconfig.json")
    for option in REQUIRED_TS_COMPILER_OPTIONS:
        if compiler_options.get(option) is not True:
            add(
                failures,
                repository_name,
                "typescript-strictness",
                f"effective tsconfig option {option!r} must be true",
            )

    sql_literal = re.compile(
        r"(?:`|\"|')\s*(?:SELECT\b|INSERT\s+INTO\b|UPDATE\s+[a-z0-9_]+\s+SET\b|DELETE\s+FROM\b|WITH\s+[a-z0-9_]+\s+AS\b)",
        re.IGNORECASE,
    )
    forbidden_domain_import = re.compile(
        r"from\s+[\"'][^\"']*(?:infrastructure|interfaces|application|node:|pg|redis|prisma|fastify)[^\"']*[\"']",
        re.IGNORECASE,
    )
    for path in source_files(repository):
        if path.suffix != ".ts":
            continue
        relative_path = path.relative_to(repository).as_posix()
        text = read_text(path)
        if relative_path.startswith("src/domain/") and forbidden_domain_import.search(text):
            add(failures, repository_name, "dependency-direction", f"{relative_path} imports outside Domain")
        if relative_path.startswith(("src/application/", "src/interfaces/")) and sql_literal.search(text):
            add(failures, repository_name, "sql-boundary", f"{relative_path} contains persistence SQL")
        if relative_path.startswith("src/application/") and re.search(
            r"from\s+[\"'][^\"']*generated/", text
        ):
            add(failures, repository_name, "wire-boundary", f"{relative_path} imports generated wire types")
        if not relative_path.startswith("src/generated/") and len(text.splitlines()) > 800:
            add(failures, repository_name, "file-granularity", f"{relative_path} exceeds 800 lines")

        if relative_path.startswith("src/interfaces/http/"):
            for match in re.finditer(r"[\"'](/[^\"']*)[\"']", text):
                route = match.group(1)
                connect_rpc_route = re.fullmatch(
                    r"/[a-z][a-z0-9_.]*\.v[0-9]+\.[A-Za-z][A-Za-z0-9_]*/[A-Za-z][A-Za-z0-9_]*",
                    route,
                )
                if route.startswith(("/v1/", "/.well-known/")) or route in {
                    "/",
                    "/v1",
                    "/healthz",
                    "/readyz",
                    "/metrics",
                    "/docs",
                } or connect_rpc_route:
                    continue
                if route.startswith("/") and not route.startswith("//"):
                    add(
                        failures,
                        repository_name,
                        "http-versioning",
                        f"{relative_path} exposes non-versioned route literal {route!r}",
                    )

    http_sources = tracked_or_worktree_files(repository, "src/interfaces/http")
    if any(path.suffix == ".ts" for path in http_sources):
        openapi_root = repository / "contract" / "openapi"
        openapi_files = (
            [path for path in openapi_root.rglob("*") if path.suffix.lower() in {".yaml", ".yml", ".json"}]
            if openapi_root.is_dir()
            else []
        )
        if not openapi_files:
            add(
                failures,
                repository_name,
                "contract-owner",
                "HTTP surface exists but contract/openapi has no canonical specification",
            )
        else:
            for specification in openapi_files:
                check_openapi_contract(repository_name, specification, failures)

    for workflow_name in ("ci.yml", "release-image.yml"):
        workflow = repository / ".github" / "workflows" / workflow_name
        if not workflow.is_file():
            add(failures, repository_name, "quality-gates", f"{workflow.relative_to(repository)} is missing")
            continue
        workflow_text = read_text(workflow)
        if re.search(r"\bnpm\s+(?:ci|install|run)\b", workflow_text):
            add(
                failures,
                repository_name,
                "toolchain",
                f"{workflow.relative_to(repository)} still invokes npm",
            )
        if "db:apply-schema" not in workflow_text:
            add(
                failures,
                repository_name,
                "canonical-schema",
                f"{workflow.relative_to(repository)} does not install the canonical schema",
            )
        if not re.search(r"test:integration|runtime-real|smoke:infra", workflow_text):
            add(
                failures,
                repository_name,
                "real-integration",
                f"{workflow.relative_to(repository)} has no explicit real-infrastructure test gate",
            )


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
    elif not re.search(r"^go\s+1\.26\.8$", read_text(repository / "go.mod"), re.MULTILINE):
        add(failures, repository_name, "go-tooling", "go.mod must pin the current supported baseline go 1.26.8")
    openapi = repository / "contract" / "openapi" / "v1" / "openapi.yaml"
    if not openapi.is_file():
        add(failures, repository_name, "contract-owner", "canonical scheduler OpenAPI is missing")
    else:
        check_openapi_contract(repository_name, openapi, failures)


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
        check_delivery(repository, failures)
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

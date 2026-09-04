"""TypeScript toolchain, dependency direction and contract checks."""

from __future__ import annotations

import re

from .contract_checks import check_openapi_contract
from .ten_repository_standard import (
    REPOSITORY_PROFILES,
    REQUIRED_TS_COMPILER_OPTIONS,
    ROOT,
    Failure,
    add,
    effective_ts_compiler_options,
    is_granularity_exempt,
    package_manifest,
    package_scripts,
    read_text,
    required_quality_scripts,
    source_files,
    tracked_or_worktree_files,
)


def check_typescript(repository_name: str, failures: list[Failure]) -> None:
    repository = ROOT / repository_name
    profile = REPOSITORY_PROFILES[repository_name]
    for layer in profile.required_layers:
        if not (repository / "src" / layer).is_dir():
            add(
                failures,
                repository_name,
                "layered-topology",
                f"src/{layer}/ is missing",
            )

    package = package_manifest(repository)
    scripts = package_scripts(repository)
    if package.get("packageManager") != "pnpm@11.25.0":
        add(
            failures,
            repository_name,
            "toolchain",
            "packageManager must pin pnpm@11.25.0",
        )
    if not (repository / "pnpm-lock.yaml").is_file():
        add(failures, repository_name, "toolchain", "pnpm-lock.yaml is missing")
    if (repository / "package-lock.json").exists():
        add(
            failures,
            repository_name,
            "toolchain",
            "package-lock.json must not coexist with pnpm",
        )
    docker_text = read_text(repository / "Dockerfile")
    docker_install_count = len(
        re.findall(r"\bpnpm(?:@[^\s]+)?\s+install\b", docker_text)
    )
    if (
        docker_install_count
        and docker_text.count("--ignore-scripts") < docker_install_count
    ):
        add(
            failures,
            repository_name,
            "container-supply-chain",
            "every Docker pnpm install must use --ignore-scripts; required generators run explicitly",
        )
    for script in required_quality_scripts(repository_name):
        if script not in scripts:
            add(
                failures,
                repository_name,
                "quality-gates",
                f"package.json script {script!r} is missing",
            )
    lint_command = str(scripts.get("lint", ""))
    if lint_command in {
        "npm run typecheck",
        "pnpm typecheck",
        "npm run check",
        "pnpm check",
    }:
        add(
            failures,
            repository_name,
            "quality-gates",
            "lint must be a real static-analysis command, not a typecheck/check alias",
        )
    for script_name, command in scripts.items():
        if re.search(
            r"\bdb:migrate\b|database/migrations|schema_migrations",
            str(command),
            re.IGNORECASE,
        ):
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
        relative_path = path.relative_to(repository).as_posix()
        line_count = len(read_text(path).splitlines())
        if path.suffix.lower() == ".css" and line_count > 500:
            add(
                failures,
                repository_name,
                "file-granularity",
                f"{relative_path} exceeds the 500-line CSS hard limit",
            )
        if path.suffix == ".tsx" and line_count > 500:
            add(
                failures,
                repository_name,
                "file-granularity",
                f"{relative_path} exceeds the 500-line React hard limit",
            )
        if path.suffix not in {".ts", ".tsx"}:
            continue
        text = read_text(path)
        if relative_path.startswith("src/domain/") and forbidden_domain_import.search(
            text
        ):
            add(
                failures,
                repository_name,
                "dependency-direction",
                f"{relative_path} imports outside Domain",
            )
        if relative_path.startswith(
            ("src/application/", "src/interfaces/")
        ) and sql_literal.search(text):
            add(
                failures,
                repository_name,
                "sql-boundary",
                f"{relative_path} contains persistence SQL",
            )
        if relative_path.startswith("src/application/") and re.search(
            r"from\s+[\"'][^\"']*generated/", text
        ):
            add(
                failures,
                repository_name,
                "wire-boundary",
                f"{relative_path} imports generated wire types",
            )
        if (
            not relative_path.startswith("src/generated/")
            and not is_granularity_exempt(repository_name, relative_path)
            and path.suffix == ".ts"
            and line_count > 800
        ):
            add(
                failures,
                repository_name,
                "file-granularity",
                f"{relative_path} exceeds 800 lines",
            )

        if relative_path.startswith("src/interfaces/http/"):
            for match in re.finditer(r"[\"'](/[^\"']*)[\"']", text):
                route = match.group(1)
                connect_rpc_route = re.fullmatch(
                    r"/[a-z][a-z0-9_.]*\.v[0-9]+\.[A-Za-z][A-Za-z0-9_]*/[A-Za-z][A-Za-z0-9_]*",
                    route,
                )
                if (
                    route.startswith(("/v1/", "/.well-known/"))
                    or route
                    in {
                        "/",
                        "/v1",
                        "/healthz",
                        "/readyz",
                        "/metrics",
                        "/docs",
                    }
                    or connect_rpc_route
                ):
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
            [
                path
                for path in openapi_root.rglob("*")
                if path.suffix.lower() in {".yaml", ".yml", ".json"}
            ]
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
            add(
                failures,
                repository_name,
                "quality-gates",
                f"{workflow.relative_to(repository)} is missing",
            )
            continue
        workflow_text = read_text(workflow)
        if re.search(r"\bnpm\s+(?:ci|install|run)\b", workflow_text):
            add(
                failures,
                repository_name,
                "toolchain",
                f"{workflow.relative_to(repository)} still invokes npm",
            )
        if profile.requires_schema and "db:apply-schema" not in workflow_text:
            add(
                failures,
                repository_name,
                "canonical-schema",
                f"{workflow.relative_to(repository)} does not install the canonical schema",
            )
        integration_pattern = (
            r"test:e2e|playwright"
            if profile.kind == "web"
            else r"test:integration|runtime-real|smoke:infra"
        )
        if not re.search(integration_pattern, workflow_text):
            add(
                failures,
                repository_name,
                "real-integration",
                f"{workflow.relative_to(repository)} has no explicit real-infrastructure test gate",
            )

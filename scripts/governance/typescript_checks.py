"""TypeScript toolchain, dependency direction and contract checks."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from .contract_checks import check_openapi_contract
from .ten_repository_standard import (
    REPOSITORY_PROFILES,
    REPOSITORY_PATHS,
    REQUIRED_TS_COMPILER_OPTIONS,
    ROOT,
    Failure,
    TypeScriptConfigError,
    add,
    effective_ts_compiler_options,
    is_granularity_exempt,
    openapi_contract_candidates,
    package_manifest,
    package_scripts,
    read_text,
    required_quality_scripts,
    source_files,
)

ROUTE_CALL = re.compile(
    r"\b(?:app|server|router|fastify|instance)\s*\.\s*"
    r"(?:get|post|put|patch|delete|options|head)\s*\(\s*"
    r"(?P<quote>[\"'`])(?P<route>/[^\"'`]*)\1",
    re.IGNORECASE,
)
ROUTE_CONFIG = re.compile(
    r"\b(?:url|path)\s*:\s*(?P<quote>[\"'`])(?P<route>/[^\"'`]*)\1",
    re.IGNORECASE,
)


def route_literals(text: str) -> tuple[str, ...]:
    """Return explicit HTTP route declarations, not arbitrary slash-prefixed strings."""

    return tuple(
        match.group("route")
        for pattern in (ROUTE_CALL, ROUTE_CONFIG)
        for match in pattern.finditer(text)
    )


def script_is_noop(command: str) -> bool:
    """Catch known placebo gates; executing CI remains the authoritative proof."""
    segments = re.split(r"&&|\|\||[;\n]", command)
    try:
        words = [shlex.split(segment) for segment in segments if segment.strip()]
    except ValueError:
        return False
    return not words or all(
        not part or part[0] in {"echo", "printf", "true", ":", "exit"} for part in words
    )


def workflow_gate_commands(workflow: str, scripts: dict[str, str]) -> str:
    """Expand invoked pnpm gates, not unused scripts; lexical preflight, not CI proof."""
    commands: list[str] = []
    visited: set[str] = set()

    def visit(text: str) -> None:
        for line in text.splitlines():
            line = re.sub(r"^\s*-?\s*run:\s*", "", line).strip()
            if not line or line.startswith("#"):
                continue
            for segment in re.split(r"&&|;", line):
                try:
                    words = shlex.split(segment, comments=True)
                except ValueError:
                    continue
                if not words or words[0] in {"echo", "printf", "true", ":"}:
                    continue
                if words[0] != "pnpm":
                    if words[0] in {"vitest", "tsx", "node", "playwright"}:
                        commands.append(shlex.join(words))
                    continue
                rest = words[1:]
                if rest and rest[0] == "run":
                    rest = rest[1:]
                if not rest:
                    continue
                name = rest[0]
                body = scripts.get(name)
                if body is None:
                    commands.append(shlex.join(words))
                elif name not in visited and not script_is_noop(body):
                    visited.add(name)
                    commands.append(shlex.join(words))
                    visit(body)

    visit(workflow)
    return "\n".join(commands)


def forbidden_business_dependencies(text: str) -> tuple[str, ...]:
    """Lexical preflight only; child ESLint must enforce the complete AST graph."""
    specifiers = re.findall(
        r"(?:\bfrom\s*|\bimport\s*(?:\(\s*)?|\brequire\s*\(\s*)[\"']([^\"']+)[\"']",
        text,
    )
    packages = {
        "pg",
        "postgres",
        "redis",
        "ioredis",
        "fastify",
        "stripe",
        "drizzle-orm",
        "@prisma/client",
    }
    return tuple(
        specifier
        for specifier in specifiers
        if any(
            specifier == name or specifier.startswith(name + "/") for name in packages
        )
        or specifier.startswith(("@connectrpc/", "@aws-sdk/"))
    )


def node_major(value: object, *, engine: bool = False) -> int | None:
    """Recognize a single declared major, not an unbounded or multi-major range."""
    if not isinstance(value, str):
        return None
    value = value.strip().strip("\"'")
    version = r"v?(\d+)(?:\.(?:\d+|x|\*)){0,2}"
    match = re.fullmatch(version, value)
    if match:
        return int(match.group(1))
    if engine:
        match = re.fullmatch(r">=" + version + r"\s+<(\d+)(?:\.0(?:\.0)?)?", value)
        if match and int(match.group(2)) == int(match.group(1)) + 1:
            return int(match.group(1))
        match = re.fullmatch(r"\^" + version, value)
        if match:
            return int(match.group(1))
    return None


def check_node_consistency(
    repository_name: str, repository: Path, failures: list[Failure]
) -> None:
    expected = REPOSITORY_PROFILES[repository_name].node_major
    engines = package_manifest(repository).get("engines", {})
    declared = engines.get("node") if isinstance(engines, dict) else None
    declarations = [("package.json engines.node", node_major(declared, engine=True))]
    version_file = repository / ".node-version"
    if version_file.exists():
        declarations.append((".node-version", node_major(read_text(version_file))))
    docker = "\n".join(
        line
        for line in read_text(repository / "Dockerfile").splitlines()
        if not line.lstrip().startswith("#")
    )
    for match in re.finditer(
        r"(?im)^(?:FROM\s+(?:--platform=\S+\s+)?|ARG\s+\w+=)node:([^\s]+)", docker
    ):
        declarations.append(
            (
                "Dockerfile node image",
                node_major(match.group(1).split("-")[0].split("@")[0]),
            )
        )
    workflows = repository / ".github/workflows"
    for workflow in sorted(workflows.glob("*")):
        if workflow.suffix not in {".yml", ".yaml"}:
            continue
        lines = read_text(workflow).splitlines()
        for index, line in enumerate(lines):
            if not re.search(
                r"^\s*(?:-\s*)?uses:\s*(?:['\"])?actions/setup-node@", line
            ):
                continue
            step_indent = (
                len(line)
                - len(line.lstrip())
                - (0 if line.lstrip().startswith("-") else 2)
            )
            block: list[str] = []
            for nested in lines[index + 1 :]:
                if nested.strip() and not nested.lstrip().startswith("#"):
                    if len(nested) - len(nested.lstrip()) <= step_indent:
                        break
                block.append(nested)
            settings = "\n".join(block)
            value = re.search(r"(?m)^\s*node-version:\s*(.+?)\s*(?:#.*)?$", settings)
            filename = re.search(r"(?m)^\s*node-version-file:\s*([^#\n]+)", settings)
            label = f"{workflow.relative_to(repository)} actions/setup-node"
            if value:
                declarations.append((label, node_major(value.group(1))))
            elif filename:
                relative = Path(filename.group(1).strip().strip("\"'"))
                contents = (
                    read_text(repository / relative)
                    if not relative.is_absolute() and ".." not in relative.parts
                    else ""
                )
                declarations.append(
                    (label + " node-version-file", node_major(contents))
                )
            else:
                declarations.append((label, None))
    for source, actual in declarations:
        if actual != expected:
            add(
                failures,
                repository_name,
                "toolchain",
                f"{source} must declare profile Node major {expected}; resolved {actual!r}",
            )


def check_typescript(
    repository_name: str,
    failures: list[Failure],
    unverified: list[Failure] | None = None,
) -> None:
    repository = ROOT / REPOSITORY_PATHS[repository_name]
    profile = REPOSITORY_PROFILES[repository_name]
    for source_path in profile.required_source_paths:
        if not (repository / "src" / source_path).is_dir():
            add(
                failures,
                repository_name,
                "module-topology",
                f"src/{source_path}/ is missing",
            )
    if profile.kind == "typescript-service":
        retired = [
            name
            for name in profile.retired_source_paths
            if (repository / "src" / name).is_dir()
        ]
        if retired:
            add(
                failures,
                repository_name,
                "module-topology",
                "retired top-level source directories exist: "
                + ", ".join(f"src/{name}/" for name in retired)
                + "; restore the approved feature-first owner design",
            )

    package = package_manifest(repository)
    scripts = package_scripts(repository)
    # TS handbook §2.4: pin each repository's verified stable version, not an
    # obsolete global patch. A Corepack integrity suffix may accompany the pin.
    package_manager = package.get("packageManager")
    if not isinstance(package_manager, str) or not re.fullmatch(
        r"pnpm@(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:\+sha(?:224\.[a-fA-F0-9]{56}|256\.[a-fA-F0-9]{64}|"
        r"384\.[a-fA-F0-9]{96}|512\.[a-fA-F0-9]{128}))?",
        package_manager,
    ):
        add(
            failures,
            repository_name,
            "toolchain",
            "packageManager must pin an exact stable pnpm version (pnpm@x.y.z)",
        )
    check_node_consistency(repository_name, repository, failures)
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
    if (
        re.search(r"\bpnpm(?:@[^\s]+)?\s+install\b", docker_text)
        and "--frozen-lockfile" not in docker_text
    ):
        add(
            failures,
            repository_name,
            "container-supply-chain",
            "Docker pnpm install must use a frozen lockfile",
        )
    # Explicit policy is a preflight; pnpm itself validates full YAML and approved builds during installation.
    workspace = read_text(repository / "pnpm-workspace.yaml")
    if not re.search(r"(?m)^strictDepBuilds:\s*true\s*(?:#.*)?$", workspace):
        add(
            failures,
            repository_name,
            "dependency-build-policy",
            "pnpm-workspace.yaml must explicitly enable strictDepBuilds",
        )
    if not re.search(r"(?m)^allowBuilds:", workspace) or re.search(
        r"(?m)^dangerouslyAllowAllBuilds:\s*true", workspace
    ):
        add(
            failures,
            repository_name,
            "dependency-build-policy",
            "declare reviewed allowBuilds; do not allow all dependency builds",
        )
    for script in required_quality_scripts(repository_name):
        if script not in scripts or script_is_noop(str(scripts[script])):
            add(
                failures,
                repository_name,
                "quality-gates",
                f"package.json script {script!r} is missing or a no-op",
            )
    if profile.schema_kind == "prisma":
        drift_script = profile.schema_drift_script
        checker = profile.schema_drift_checker
        if (
            not drift_script
            or not checker
            or not (repository / checker).is_file()
            or script_is_noop(str(scripts.get(drift_script, "")))
            or checker not in str(scripts.get(drift_script, ""))
        ):
            add(
                failures,
                repository_name,
                "schema-drift",
                f"approved persisted-schema drift checker {drift_script or '(not implemented)'} is missing or a no-op; Prisma validate/fresh DDL alone is not drift proof",
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

    try:
        compiler_options = effective_ts_compiler_options(repository / "tsconfig.json")
    except TypeScriptConfigError as error:
        if unverified is not None:
            add(unverified, repository_name, "typescript-configuration", str(error))
        compiler_options = None
    if compiler_options is not None:
        for option in REQUIRED_TS_COMPILER_OPTIONS:
            if compiler_options.get(option) is not True:
                add(
                    failures,
                    repository_name,
                    "typescript-strictness",
                    f"effective tsconfig option {option!r} must be true",
                )
        if compiler_options.get("skipLibCheck") is True:
            add(
                failures,
                repository_name,
                "typescript-strictness",
                "skipLibCheck must not hide dependency type errors",
            )
        if profile.kind == "typescript-service":
            expected_options = {
                "module": "nodenext",
                "moduleResolution": "nodenext",
                "moduleDetection": "force",
                "target": "es2024",
                "verbatimModuleSyntax": True,
            }
            for option, expected in expected_options.items():
                if compiler_options.get(option) != expected:
                    add(
                        failures,
                        repository_name,
                        "typescript-modules",
                        f"effective {option} must be {expected!r}",
                    )
            if compiler_options.get("lib") != ["es2024"]:
                add(
                    failures,
                    repository_name,
                    "typescript-modules",
                    "backend lib must be ES2024 without browser DOM globals",
                )
    if profile.kind == "typescript-service" and package.get("type") != "module":
        add(
            failures,
            repository_name,
            "typescript-modules",
            "package.json type must be module",
        )

    sql_literal = re.compile(
        r"(?:`|\"|')\s*(?:SELECT\b|INSERT\s+INTO\b|UPDATE\s+[a-z0-9_]+\s+SET\b|DELETE\s+FROM\b|WITH\s+[a-z0-9_]+\s+AS\b)",
        re.IGNORECASE,
    )
    http_sources: list[Path] = []
    for path in source_files(repository):
        relative_path = path.relative_to(repository).as_posix()
        relative_parts = path.relative_to(repository / "src").parts
        if relative_path.startswith("src/generated/"):
            continue
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
        if path.name in {
            "base-repository.ts",
            "base-service.ts",
            "command-executor.ts",
        } or path.name.endswith("-command-executor.ts"):
            add(
                failures,
                repository_name,
                "speculative-abstraction",
                f"{relative_path} uses a banned generic abstraction name",
            )
        if re.search(
            r"\b(?:abstract\s+)?class\s+(?:BaseRepository|BaseService)\b", text
        ):
            add(
                failures,
                repository_name,
                "speculative-abstraction",
                f"{relative_path} defines a generic BaseRepository/BaseService hierarchy",
            )
        is_domain_rule = "domain" in relative_parts
        is_transport = relative_path.startswith("src/transport/") or path.name.endswith(
            (
                ".routes.ts",
                ".rpc.ts",
                ".connect.ts",
                ".controller.ts",
                "-rpc.service.ts",
            )
        )
        is_http_transport = (
            path.name.endswith((".routes.ts", ".controller.ts"))
            or "http" in relative_parts[:-1]
        )
        # Process integrations are not business rules. Domain always wins, and
        # controllers retain the SQL boundary even at these process locations.
        is_process_service = (
            relative_path.startswith(("src/database/", "src/integrations/"))
            and not is_transport
        )
        is_cache_service = (
            len(relative_parts) == 2
            and relative_parts[0] == "cache"
            and path.name.endswith(".service.ts")
            and not is_transport
        )
        is_business_service = (
            not is_transport
            and not is_process_service
            and not is_cache_service
            and (
                path.name.endswith((".service.ts", ".policy.ts"))
                or any(
                    part in {"use-cases", "services", "commands"}
                    for part in relative_parts[:-1]
                )
            )
        )
        forbidden_dependencies = forbidden_business_dependencies(text)
        # Keep the existing narrow database/cache driver guard: process scope is
        # not permission to import arbitrary providers into the database owner.
        technical_driver = (
            "redis"
            if is_cache_service
            else "pg"
            if relative_path.startswith("src/database/") and is_process_service
            else None
        )
        if technical_driver and not is_domain_rule:
            unexpected = tuple(
                dep
                for dep in forbidden_dependencies
                if not (
                    dep == technical_driver
                    or dep.startswith(technical_driver + "/")
                    or (technical_driver == "pg" and dep == "@prisma/client")
                )
            )
            if unexpected:
                add(
                    failures,
                    repository_name,
                    "dependency-direction",
                    f"{relative_path} imports an unrelated provider into a process database/cache service",
                )
        if (is_domain_rule or is_business_service) and forbidden_dependencies:
            add(
                failures,
                repository_name,
                "dependency-direction",
                f"{relative_path} imports a framework, database, cache or provider implementation from business rules",
            )
        if (
            is_transport
            or is_http_transport
            or is_domain_rule
            or is_business_service
            or is_cache_service
        ) and sql_literal.search(text):
            add(
                failures,
                repository_name,
                "sql-boundary",
                f"{relative_path} contains persistence SQL outside a repository/query",
            )
        if (is_domain_rule or is_business_service) and re.search(
            r"(?:\bfrom\s*|\bimport\s*(?:\(\s*)?|\brequire\s*\(\s*)[\"'][^\"']*generated/",
            text,
        ):
            add(
                failures,
                repository_name,
                "wire-boundary",
                f"{relative_path} imports generated wire types into business code",
            )
        if (
            profile.kind == "typescript-service"
            and "process.env" in text
            and relative_path != "src/main.ts"
            and not relative_path.startswith(("src/config/", "src/bootstrap/"))
        ):
            add(
                failures,
                repository_name,
                "configuration-boundary",
                f"{relative_path} reads process.env outside config/bootstrap",
            )
        if (
            profile.kind == "typescript-service"
            and "modules" in relative_parts
            and any(
                part in {"postgres", "redis", "prisma"} for part in relative_parts[:-1]
            )
        ):
            add(
                failures,
                repository_name,
                "technology-directory",
                f"{relative_path} is grouped by a database/cache brand inside a business module; use repository/query/cache/event responsibilities",
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

        if profile.kind == "typescript-service" and is_http_transport:
            http_sources.append(path)
            for route in route_literals(text):
                connect_rpc_route = re.fullmatch(
                    r"/[a-z][a-z0-9_.]*\.v[0-9]+\.[A-Za-z][A-Za-z0-9_]*/[A-Za-z][A-Za-z0-9_]*",
                    route,
                )
                if (
                    route.startswith(("/v1/", "/internal/v1/", "/.well-known/"))
                    or route
                    in {
                        "/",
                        "/v1",
                        "/healthz",
                        "/livez",
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

    confirmed_openapi = [
        check_openapi_contract(repository_name, specification, failures)
        for specification in openapi_contract_candidates(repository)
    ]
    if http_sources and not any(confirmed_openapi):
        add(
            failures,
            repository_name,
            "contract-owner",
            "HTTP surface exists but contract/ has no owned published or generated OpenAPI specification",
        )
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
        workflow_text = "\n".join(
            line
            for line in workflow_text.splitlines()
            if not line.lstrip().startswith("#")
        )
        gate_commands = workflow_gate_commands(workflow_text, scripts)
        if profile.requires_schema and not re.search(
            r"\b(?:db:apply-schema|test:schema:fresh)\b", gate_commands
        ):
            add(
                failures,
                repository_name,
                "canonical-schema",
                f"{workflow.relative_to(repository)} does not install the canonical schema",
            )
        integration_pattern = (
            r"test:e2e|playwright"
            if profile.kind == "web"
            else r"test:integration|runtime-real|smoke:infra|^vitest run(?: --no-file-parallelism)?$"
        )
        if not re.search(integration_pattern, gate_commands, re.MULTILINE):
            add(
                failures,
                repository_name,
                "real-integration",
                f"{workflow.relative_to(repository)} has no explicit real-infrastructure test gate",
            )

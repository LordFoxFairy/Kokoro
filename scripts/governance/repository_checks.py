"""Cross-cutting repository, delivery, TypeScript and Scheduler checks."""

from __future__ import annotations

import re

from .contract_checks import check_openapi_contract, check_schema_naming
from .ten_repository_standard import (
    REPOSITORY_PROFILES,
    REQUIRED_SCHEDULER_LAYERS,
    ROOT,
    Failure,
    add,
    appears_to_use_question_mark_sql,
    contract_source_files,
    database_files,
    extract_redis_databases,
    has_clean_slate_marker,
    has_exact_relative_file,
    missing_contract_readme_fields,
    read_text,
    source_files,
    sql_without_comments,
)


def check_common(repository_name: str, failures: list[Failure]) -> None:
    repository = ROOT / repository_name
    profile = REPOSITORY_PROFILES[repository_name]
    if not repository.is_dir():
        add(
            failures,
            repository_name,
            "repository",
            "child repository directory is missing",
        )
        return

    if not (repository / "AGENTS.md").is_file():
        add(failures, repository_name, "agent-contract", "AGENTS.md is missing")

    redis_database = profile.redis_database
    if redis_database is not None:
        env_example = repository / ".env.example"
        configured_databases = extract_redis_databases(read_text(env_example))
        if not env_example.is_file() or redis_database not in configured_databases:
            add(
                failures,
                repository_name,
                "shared-local-infrastructure",
                f".env.example must use shared Redis logical DB {redis_database}",
            )

    migrations = repository / "database" / "migrations"
    if migrations.is_dir():
        add(
            failures,
            repository_name,
            "canonical-schema",
            "database/migrations must not exist",
        )

    for compose in (
        *repository.glob("docker-compose*.yml"),
        *repository.glob("docker-compose*.yaml"),
    ):
        compose_text = read_text(compose)
        if re.search(
            r"^\s*image:\s*(?:postgres|redis)(?::|\s|$)",
            compose_text,
            re.MULTILINE | re.IGNORECASE,
        ):
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

    sql_files = [
        path for path in database_files(repository) if path.suffix.lower() == ".sql"
    ]
    canonical = repository / "database" / "schema.sql"
    if profile.requires_schema and not canonical.is_file():
        add(
            failures,
            repository_name,
            "canonical-schema",
            "database/schema.sql is missing",
        )
    if not profile.requires_schema and sql_files:
        add(
            failures,
            repository_name,
            "schema-ownership",
            "this repository profile must not own executable database SQL",
        )
    if canonical.is_file():
        check_schema_naming(repository_name, canonical, failures)

    if sql_files:
        non_canonical = [
            path.relative_to(repository).as_posix()
            for path in sql_files
            if path.name not in {"schema.sql", "seed.sql"}
            and "seed" not in path.relative_to(repository).parts
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
            executable_sql = sql_without_comments(text)
            if re.search(r"\bFOREIGN\s+KEY\b|\bREFERENCES\b", text, re.IGNORECASE):
                add(
                    failures,
                    repository_name,
                    "relation-integrity",
                    f"{path.relative_to(repository)} contains FOREIGN KEY or REFERENCES",
                )
            if re.search(
                r"\bTIMESTAMPTZ\b(?!\s*\(\s*3\s*\))",
                executable_sql,
                re.IGNORECASE,
            ):
                add(
                    failures,
                    repository_name,
                    "utc-time",
                    f"{path.relative_to(repository)} must use TIMESTAMPTZ(3) for database instants",
                )
            if re.search(
                r"\bCURRENT_TIMESTAMP\b(?!\s*\(\s*3\s*\))",
                executable_sql,
                re.IGNORECASE,
            ):
                add(
                    failures,
                    repository_name,
                    "utc-time",
                    f"{path.relative_to(repository)} must use CURRENT_TIMESTAMP(3) for timestamp defaults",
                )
            if re.search(
                r"\bTIMESTAMP(?:\s*\([^)]*\))?\b(?!\s+WITH\s+TIME\s+ZONE)",
                executable_sql,
                re.IGNORECASE,
            ):
                add(
                    failures,
                    repository_name,
                    "utc-time",
                    f"{path.relative_to(repository)} contains a timestamp without time zone",
                )
            if re.search(
                r"\b[a-z0-9_]+_at_unix_seconds\b", executable_sql, re.IGNORECASE
            ):
                add(
                    failures,
                    repository_name,
                    "utc-time",
                    f"{path.relative_to(repository)} stores a database fact as Unix seconds",
                )

    machine_contracts = contract_source_files(repository)
    if machine_contracts:
        contract_readme = repository / "contract" / "README.md"
        if not has_exact_relative_file(repository, "contract/README.md"):
            add(
                failures,
                repository_name,
                "contract-provenance",
                "contract/README.md is required for machine contract owner/version/generation/breaking/provenance",
            )
        else:
            missing_fields = missing_contract_readme_fields(read_text(contract_readme))
            if missing_fields:
                add(
                    failures,
                    repository_name,
                    "contract-provenance",
                    "contract/README.md lacks: " + ", ".join(missing_fields),
                )

    for path in source_files(repository):
        text = read_text(path)
        if re.search(
            r"\b(?:class|interface)\s+InMemory\w*|\bInMemory\w*Repository\b", text
        ):
            add(
                failures,
                repository_name,
                "production-doubles",
                f"{path.relative_to(repository)} contains InMemory code",
            )
        if re.search(r"\b(?:class|interface)\s+(?:Fake|Fixture)\w*", text):
            add(
                failures,
                repository_name,
                "production-doubles",
                f"{path.relative_to(repository)} contains Fake/Fixture code",
            )
        if profile.requires_schema and appears_to_use_question_mark_sql(text):
            add(
                failures,
                repository_name,
                "sql-parameters",
                f"{path.relative_to(repository)} appears to use ? SQL placeholders",
            )
        path_has_retired_marker = any(
            part.lower() in {"legacy", "compat", "compatibility"}
            for part in path.relative_to(repository).parts
        )
        if path_has_retired_marker or has_clean_slate_marker(text):
            add(
                failures,
                repository_name,
                "clean-slate",
                f"{path.relative_to(repository)} contains a retired compatibility marker",
            )


def check_scheduler(failures: list[Failure]) -> None:
    repository_name = "kokoro-scheduler"
    repository = ROOT / repository_name
    for layer in REQUIRED_SCHEDULER_LAYERS:
        if not (repository / "internal" / layer).is_dir():
            add(
                failures,
                repository_name,
                "layered-topology",
                f"internal/{layer}/ is missing",
            )
    if not (repository / "cmd" / "scheduler").is_dir():
        add(failures, repository_name, "layered-topology", "cmd/scheduler/ is missing")
    if not (repository / "go.mod").is_file():
        add(failures, repository_name, "go-tooling", "go.mod is missing")
    elif not re.search(
        r"^go\s+1\.26\.8$", read_text(repository / "go.mod"), re.MULTILINE
    ):
        add(
            failures,
            repository_name,
            "go-tooling",
            "go.mod must pin the current supported baseline go 1.26.8",
        )
    openapi = repository / "contract" / "openapi" / "v1" / "openapi.yaml"
    if not openapi.is_file():
        add(
            failures,
            repository_name,
            "contract-owner",
            "canonical scheduler OpenAPI is missing",
        )
    else:
        check_openapi_contract(repository_name, openapi, failures)


def check_docs(failures: list[Failure]) -> None:
    required = (
        ROOT / "AGENTS.md",
        ROOT / "docs" / "INDEX.md",
        ROOT / "docs" / "ARCHITECTURE_STANDARD.md",
        ROOT / "docs" / "CURRENT.md",
        ROOT / "docs" / "CODEBASE_MAP.md",
        ROOT / "docs" / "kokoro-handbook" / "standards" / "03-sql-and-postgresql.md",
        ROOT
        / "docs"
        / "kokoro-handbook"
        / "standards"
        / "08-typescript-backend-engineering.md",
        ROOT
        / "docs"
        / "kokoro-handbook"
        / "standards"
        / "09-python-backend-engineering.md",
    )
    for path in required:
        if not path.is_file():
            add(failures, "root", "governance", f"{path.relative_to(ROOT)} is missing")

    agents = read_text(ROOT / "AGENTS.md")
    for manual in (
        "03-sql-and-postgresql.md",
        "08-typescript-backend-engineering.md",
        "09-python-backend-engineering.md",
    ):
        if manual not in agents:
            add(
                failures,
                "root",
                "governance",
                f"AGENTS.md does not reference {manual}",
            )

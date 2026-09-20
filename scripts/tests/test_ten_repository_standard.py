from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.governance import (
    contract_checks,
    repository_checks,
    surface_checks,
    ten_repository_standard,
    typescript_checks,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify-ten-repository-standard.py"


def load_verifier() -> SimpleNamespace:
    exports = vars(ten_repository_standard) | {
        "missing_openapi_operation_extensions": contract_checks.missing_openapi_operation_extensions,
    }
    return SimpleNamespace(**exports)


def test_verifier_targets_nine_active_repositories_after_system_model_cutover() -> None:
    verifier = load_verifier()

    assert verifier.REPOSITORIES == (
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


def test_repository_profiles_encode_runtime_and_persistence_boundaries() -> None:
    verifier = load_verifier()

    assert verifier.REPOSITORY_PROFILES["kokoro-app"].kind == "web"
    assert verifier.REPOSITORY_PROFILES["kokoro-app"].requires_schema is False
    assert verifier.REPOSITORY_PROFILES["kokoro-bff"].kind == "typescript-service"
    assert verifier.REPOSITORY_PROFILES["kokoro-bff"].requires_schema is True
    assert verifier.REPOSITORY_PROFILES["kokoro-agent"].kind == "python-service"
    assert verifier.REPOSITORY_PROFILES["kokoro-agent"].requires_schema is True
    assert verifier.REPOSITORY_PROFILES["kokoro-scheduler"].kind == "go-service"
    assert verifier.REPOSITORY_PROFILES["kokoro-scheduler"].requires_schema is True


def test_language_profiles_use_native_module_first_topology() -> None:
    verifier = load_verifier()

    assert verifier.REPOSITORY_PROFILES["kokoro-app"].node_major == 22
    assert verifier.REPOSITORY_PROFILES["kokoro-system"].node_major == 24
    assert verifier.REQUIRED_AGENT_SOURCE_PATHS == ("execution",)
    assert (
        "modules"
        not in verifier.REPOSITORY_PROFILES["kokoro-bff"].required_source_paths
    )
    assert verifier.REPOSITORY_PROFILES["kokoro-agent"].required_source_paths == (
        "execution",
    )
    assert verifier.RETIRED_TS_TOP_LEVEL_DIRECTORIES == (
        "application",
        "domain",
        "infrastructure",
        "interfaces",
        "ports",
    )
    assert "application" in verifier.RETIRED_AGENT_TOP_LEVEL_DIRECTORIES
    assert "infrastructure" in verifier.RETIRED_AGENT_TOP_LEVEL_DIRECTORIES
    assert "ports" in verifier.RETIRED_AGENT_TOP_LEVEL_DIRECTORIES


def test_shared_redis_database_mapping_reserves_zero_and_covers_stateful_services() -> (
    None
):
    verifier = load_verifier()

    assert verifier.LOCAL_REDIS_DATABASES == {
        "kokoro-iam": 1,
        "kokoro-system": 2,
        "kokoro-billing": 4,
        "kokoro-capability": 5,
        "kokoro-storage": 6,
        "kokoro-scheduler": 7,
        "kokoro-bff": 8,
        "kokoro-agent": 9,
    }
    assert 0 not in verifier.LOCAL_REDIS_DATABASES.values()
    assert 3 not in verifier.LOCAL_REDIS_DATABASES.values()
    assert "kokoro-app" not in verifier.LOCAL_REDIS_DATABASES
    assert verifier.extract_redis_databases("REDIS_URL=redis://cache.local:6379/8") == {
        8
    }


@pytest.mark.parametrize("directory", ["database", "http"])
def test_nest_process_directories_are_not_retired(
    directory, tmp_path, monkeypatch
) -> None:
    repository = tmp_path / "apps" / "kokoro-system"
    (repository / "src" / directory).mkdir(parents=True)
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []

    typescript_checks.check_typescript("kokoro-system", failures)

    assert not any("retired top-level" in failure.detail for failure in failures)


@pytest.mark.parametrize(
    ("package_manager", "valid"),
    [
        ("pnpm@11.25.0", True),
        ("pnpm@12.3.4", True),
        ("pnpm@12.3.4+sha512." + "a" * 128, True),
        ("pnpm@latest", False),
        ("pnpm@^12.3.4", False),
        ("pnpm@12", False),
        ("pnpm@12.03.4", False),
        ("pnpm@12.3.4-beta.1", False),
        ("npm@12.3.4", False),
        (None, False),
    ],
)
def test_package_manager_requires_an_exact_stable_pnpm_pin(
    package_manager, valid, tmp_path, monkeypatch
) -> None:
    repository = tmp_path / "apps" / "kokoro-system"
    repository.mkdir(parents=True)
    (repository / "package.json").write_text(
        json.dumps({"packageManager": package_manager}), encoding="utf-8"
    )
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []

    typescript_checks.check_typescript("kokoro-system", failures)

    pin_failures = [
        failure for failure in failures if "packageManager" in failure.detail
    ]
    assert (not pin_failures) is valid


def test_documentation_matrix_matches_the_governance_manual() -> None:
    verifier = load_verifier()

    assert verifier.REQUIRED_REPOSITORY_DOCUMENTS == (
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
    assert verifier.REQUIRED_REPOSITORY_DIRECTORIES == ("docs/ADR",)


def test_root_governance_has_a_dedicated_document_index() -> None:
    assert (ROOT / "docs" / "INDEX.md").is_file()


def test_root_governance_has_language_and_sql_manuals() -> None:
    standards = ROOT / "docs" / "kokoro-handbook" / "standards"

    assert (standards / "03-sql-and-postgresql.md").is_file()
    assert (standards / "08-typescript-backend-engineering.md").is_file()
    assert (standards / "09-python-backend-engineering.md").is_file()
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "03-sql-and-postgresql.md" in agents
    assert "08-typescript-backend-engineering.md" in agents
    assert "09-python-backend-engineering.md" in agents


def test_typescript_strictness_includes_unknown_catch_variables() -> None:
    verifier = load_verifier()

    assert verifier.REQUIRED_TS_COMPILER_OPTIONS == (
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


def test_required_quality_scripts_are_profile_specific() -> None:
    verifier = load_verifier()

    assert verifier.required_quality_scripts("kokoro-app") == (
        "lint",
        "typecheck",
        "test",
        "build",
        "test:e2e",
    )
    assert verifier.required_quality_scripts("kokoro-bff") == (
        "format:check",
        "lint",
        "typecheck",
        "test",
        "build",
        "db:apply-schema",
        "contract:check",
    )
    assert verifier.required_quality_scripts("kokoro-agent") == ()


def test_route_literal_detection_ignores_regex_and_payload_strings() -> None:
    source = """
    app.post("/v1/sites", handler);
    const parserPattern = "/iu.exec(disposition)";
    const payload = { value: "/not-a-route" };
    const route = { method: "GET", url: "/v1/sites/:siteId" };
    """

    assert typescript_checks.route_literals(source) == (
        "/v1/sites",
        "/v1/sites/:siteId",
    )


def test_missing_optional_file_is_reported_as_empty_instead_of_crashing(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()

    assert verifier.read_text(tmp_path / "missing.sql") == ""


def test_question_mark_sql_detection_ignores_ui_ternaries() -> None:
    verifier = load_verifier()

    assert (
        verifier.appears_to_use_question_mark_sql("const label = ready ? 'yes' : 'no'")
        is False
    )
    assert (
        verifier.appears_to_use_question_mark_sql("SELECT id FROM run WHERE id = ?")
        is True
    )


def test_sql_comment_stripping_preserves_executable_schema_rules() -> None:
    verifier = load_verifier()

    sql = """
    -- TIMESTAMPTZ and CURRENT_TIMESTAMP in this explanation are not SQL.
    CREATE TABLE sample (
      created_at TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
    ); /* TIMESTAMPTZ without precision is also only documentation here. */
    """

    assert "TIMESTAMPTZ(3)" in verifier.sql_without_comments(sql)
    assert "TIMESTAMPTZ and CURRENT_TIMESTAMP" not in verifier.sql_without_comments(sql)
    assert "without precision" not in verifier.sql_without_comments(sql)


def test_exact_document_check_does_not_accept_wrong_case(tmp_path: Path) -> None:
    verifier = load_verifier()
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "runbook.md").write_text("lower-case alias", encoding="utf-8")

    assert verifier.has_exact_relative_file(tmp_path, "docs/runbook.md") is True
    assert verifier.has_exact_relative_file(tmp_path, "docs/RUNBOOK.md") is False


def test_clean_slate_detection_ignores_explanatory_comments_and_catches_code_markers() -> (
    None
):
    verifier = load_verifier()

    assert verifier.has_clean_slate_marker("// Reject legacy browser headers") is False
    assert verifier.has_clean_slate_marker("const legacyTokenAlias = token") is True


def test_contract_readme_requires_provenance_fields() -> None:
    verifier = load_verifier()

    assert verifier.missing_contract_readme_fields("# Contract") == (
        "owner",
        "visibility",
        "version",
        "generation",
        "breaking",
        "provenance",
    )
    assert (
        verifier.missing_contract_readme_fields(
            "owner visibility version generation breaking provenance"
        )
        == ()
    )


def test_i18n_catalog_has_an_explicit_granularity_exemption() -> None:
    verifier = load_verifier()

    assert verifier.is_granularity_exempt("kokoro-app", "src/i18n/en.ts") is True
    assert (
        verifier.is_granularity_exempt("kokoro-app", "src/engine/machine.ts") is False
    )


def test_openapi_operation_extensions_are_machine_checked() -> None:
    verifier = load_verifier()
    yaml = """
openapi: 3.1.0
paths:
  /v1/runs:
    post:
      operationId: createRun
      x-kokoro-owner: kokoro-bff
      x-kokoro-visibility: public
"""

    assert verifier.missing_openapi_operation_extensions(yaml, ".yaml") == (
        (
            "/v1/runs",
            "post",
            ("x-kokoro-stability", "x-kokoro-idempotency", "x-kokoro-permission"),
        ),
    )


def test_cli_runs_from_the_root_and_emits_valid_json() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--format", "json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode in {0, 1}, result.stderr
    assert json.loads(result.stdout)["repository_count"] == 9


def test_documentation_gate_and_single_manual_routes_are_explicit() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert not agents.startswith("@CLAUDE.md")
    assert "### 8.1 子仓实现前的文档门" in agents
    for required in (
        "docs/TECHNICAL_DESIGN.md",
        "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md",
    ):
        assert required in agents
    assert "文档门未通过时" in agents


def test_quality_gate_rejects_placebo_scripts() -> None:
    for command in ("", "true", "echo ok", "printf tsc && exit 0", "echo eslint; true"):
        assert typescript_checks.script_is_noop(command)
    for command in ("eslint . --max-warnings=0", "pnpm lint:source", "tsc --noEmit"):
        assert not typescript_checks.script_is_noop(command)


def test_dependency_preflight_checks_exact_packages_and_dynamic_imports() -> None:
    source = """
    import type { Pool } from "pg";
    const driver = await import("redis");
    const schema = require("@prisma/client");
    import { name } from "./redistribution.policy.js";
    import type { Record } from "./database-record.js";
    """
    assert typescript_checks.forbidden_business_dependencies(source) == (
        "pg",
        "redis",
        "@prisma/client",
    )


def test_tsconfig_resolution_delegates_jsonc_to_installed_compiler(
    tmp_path, monkeypatch
) -> None:
    config = tmp_path / "tsconfig.json"
    config.write_text(
        '{ /* valid JSONC */ "extends": ["@scope/base", "./strict.json"], }'
    )
    compiler = tmp_path / "node_modules/typescript/bin/tsc"
    compiler.parent.mkdir(parents=True)
    compiler.touch()
    seen = []

    def show_config(command, **kwargs):
        seen.append((command, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout='{"compilerOptions":{"strict":true,"module":"nodenext"}}',
        )

    monkeypatch.setattr(ten_repository_standard.subprocess, "run", show_config)
    assert ten_repository_standard.effective_ts_compiler_options(config) == {
        "strict": True,
        "module": "nodenext",
    }
    assert seen[0][0][-3:] == ["--showConfig", "-p", str(config)]


def test_tsconfig_missing_compiler_is_reported_not_silently_parsed(tmp_path) -> None:
    import pytest

    config = tmp_path / "tsconfig.json"
    config.write_text('{"compilerOptions":{"strict":true}}')
    with pytest.raises(
        ten_repository_standard.TypeScriptConfigError, match="installed TypeScript"
    ):
        ten_repository_standard.effective_ts_compiler_options(config)


@pytest.mark.parametrize(
    ("relative", "allowed"),
    [
        ("database/database.service.ts", True),
        ("cache/cache.service.ts", True),
        ("modules/sites/sites.service.ts", False),
        ("modules/sites/database/database.service.ts", False),
        ("modules/sites/cache/cache.service.ts", False),
        ("modules/sites/domain/site.policy.ts", False),
        ("database/query.controller.ts", False),
    ],
)
def test_process_services_are_not_misclassified_as_business_rules(
    relative, allowed, tmp_path, monkeypatch
) -> None:
    repository = tmp_path / "apps" / "kokoro-system"
    path = repository / "src" / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        'import { createClient } from "redis";\n'
        if relative == "cache/cache.service.ts"
        else 'import { Pool } from "pg";\nconst ready = "SELECT 1 AS healthy";\n'
    )
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-system", failures)
    boundary = [
        failure
        for failure in failures
        if failure.rule in {"dependency-direction", "sql-boundary"}
    ]
    assert (not boundary) is allowed


@pytest.mark.parametrize(
    ("relative", "source"),
    [
        ("cache/cache.service.ts", 'import { Pool } from "pg";'),
        ("cache/cache.service.ts", 'const sql = "SELECT id FROM system_site";'),
        ("database/database.service.ts", 'import Stripe from "stripe";'),
    ],
)
def test_technical_service_exception_is_limited_to_its_driver(
    relative, source, tmp_path, monkeypatch
) -> None:
    repository = tmp_path / "apps" / "kokoro-system"
    path = repository / "src" / relative
    path.parent.mkdir(parents=True)
    path.write_text(source)
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-system", failures)
    assert any(
        failure.rule in {"dependency-direction", "sql-boundary"} for failure in failures
    )


@pytest.mark.parametrize(
    ("relative", "allowed"),
    [
        ("main.ts", True),
        ("bootstrap/start.ts", True),
        ("config/environment.ts", True),
        ("modules/sites/main.ts", False),
        ("modules/sites/bootstrap/start.ts", False),
        ("http/request.ts", False),
    ],
)
def test_environment_reads_stay_at_process_configuration_boundary(
    relative, allowed, tmp_path, monkeypatch
):
    path = tmp_path / "apps" / "kokoro-system" / "src" / relative
    path.parent.mkdir(parents=True)
    path.write_text("const environment = process.env;")
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-system", failures)
    assert (not any(f.rule == "configuration-boundary" for f in failures)) is allowed


def test_workflow_gate_expansion_follows_only_invoked_package_scripts():
    scripts = {
        "verify": "pnpm check && pnpm test && pnpm test:schema:fresh",
        "check": "pnpm lint",
        "lint": "eslint src",
        "test": "vitest run --no-file-parallelism",
        "test:schema:fresh": "tsx scripts/verify-system-fresh-schema.ts",
        "unused": "pnpm test:integration",
    }
    result = typescript_checks.workflow_gate_commands("- run: pnpm verify", scripts)
    assert "pnpm test:schema:fresh" in result
    assert "vitest run --no-file-parallelism" in result
    assert "test:integration" not in result
    assert "test:schema:fresh" not in typescript_checks.workflow_gate_commands(
        "- run: pnpm lint", scripts
    )


def test_workflow_gate_expansion_ignores_comments_echo_and_cycles():
    scripts = {"a": "pnpm b", "b": "pnpm a", "test:integration": "echo skipped"}
    result = typescript_checks.workflow_gate_commands(
        '# pnpm test:integration\n- run: echo "pnpm test:integration"\n- run: pnpm a',
        scripts,
    )
    assert "test:integration" not in result
    assert len(result) < 200


def test_release_gate_recognizes_digest_bound_attestations(tmp_path, monkeypatch):
    from scripts.governance import delivery_checks

    workflow = tmp_path / "apps/kokoro-system/.github/workflows/release-image.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("""steps:
  - uses: aquasecurity/trivy-action@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  - uses: actions/attest-build-provenance@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    with:
      subject-digest: sha256:fixture
  - uses: actions/attest@cccccccccccccccccccccccccccccccccccccccc
    with:
      sbom-path: system-sbom.json
      subject-digest: sha256:fixture
""")
    monkeypatch.setattr(delivery_checks, "ROOT", tmp_path)
    failures = []
    delivery_checks.check_delivery("kokoro-system", failures)
    assert not [f for f in failures if f.rule == "supply-chain"]
    workflow.write_text("steps: []\n")
    failures = []
    delivery_checks.check_delivery("kokoro-system", failures)
    assert any("SBOM" in f.detail for f in failures)
    assert any("build provenance" in f.detail for f in failures)


@pytest.mark.parametrize("name", ["kokoro-iam", "kokoro-capability", "kokoro-storage"])
def test_orm_profile_uses_prisma_as_its_only_canonical_schema(name):
    profile = ten_repository_standard.REPOSITORY_PROFILES[name]
    assert profile.canonical_schema == "prisma/schema.prisma"
    assert profile.schema_kind == "prisma"


def test_profile_declares_the_only_non_default_read_only_generated_source_path():
    assert ten_repository_standard.is_profile_read_only_generated_source(
        "kokoro-billing", "src/generated/client.ts"
    )
    assert not ten_repository_standard.is_profile_read_only_generated_source(
        "kokoro-billing", "src/database/prisma-client/client.ts"
    )
    assert ten_repository_standard.is_profile_read_only_generated_source(
        "kokoro-iam", "src/database/prisma-client/client.ts"
    )
    assert not ten_repository_standard.is_profile_read_only_generated_source(
        "kokoro-iam", "src/database/prisma-client-copy/client.ts"
    )


@pytest.mark.parametrize(
    ("relative", "expected_typescript_rules", "expected_common_rules"),
    [
        ("database/prisma-client/client.ts", set(), set()),
        (
            "database/prisma-client-copy/client.ts",
            {"configuration-boundary", "file-granularity"},
            {"production-doubles"},
        ),
        (
            "modules/identity/identity.service.ts",
            {
                "configuration-boundary",
                "dependency-direction",
                "file-granularity",
            },
            {"production-doubles"},
        ),
    ],
)
def test_read_only_generated_source_exemption_is_profile_exact_and_shared(
    relative, expected_typescript_rules, expected_common_rules, tmp_path, monkeypatch
):
    """Only a profile-declared generated path skips handwritten-source audits."""
    repository = tmp_path / "apps/kokoro-iam"
    source = repository / "src" / relative
    source.parent.mkdir(parents=True)
    source.write_text(
        'import { Pool } from "pg";\n'
        "const environment = process.env;\n"
        "class InMemoryGeneratedClient {}\n"
        + "// generated output\n" * 801,
        encoding="utf-8",
    )
    monkeypatch.setattr(repository_checks, "ROOT", tmp_path)
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )

    common_failures = []
    repository_checks.check_common("kokoro-iam", common_failures)
    assert {
        failure.rule
        for failure in common_failures
        if failure.rule == "production-doubles"
    } == expected_common_rules

    typescript_failures = []
    typescript_checks.check_typescript("kokoro-iam", typescript_failures)
    assert {
        failure.rule
        for failure in typescript_failures
        if failure.rule
        in {"configuration-boundary", "dependency-direction", "file-granularity"}
    } == expected_typescript_rules


def test_owned_openapi_excludes_vendor_snapshot_and_accepts_root_json(tmp_path):
    for relative, text in {
        "contract/vendor/upstream.json": '{"openapi":"3.1.0","paths":{}}',
        "contract/openapi.json": '{"openapi":"3.1.0","paths":{}}',
        "contract/openapi/nested/api.yaml": "openapi: 3.1.0\npaths: {}\n",
        "contract/provenance.json": '{"nested":{"openapi":"3.1.0"}}',
        "contract/buf.yaml": "version: v2\n",
    }.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    (tmp_path / "contract/README.md").write_text(
        "contract/vendor/upstream.json — upstream snapshot provenance: https://example.test/spec\n"
    )
    assert ten_repository_standard.openapi_contract_candidates(tmp_path) == (
        tmp_path / "contract/openapi/nested/api.yaml",
        tmp_path / "contract/openapi.json",
        tmp_path / "contract/vendor/upstream.json",
    )


@pytest.mark.parametrize(
    "extra",
    [None, "database/schema.sql", "prisma/migrations/one.sql", "prisma/second.prisma"],
)
def test_orm_canonical_excludes_parallel_schemas_and_migrations(
    extra, tmp_path, monkeypatch
):
    from scripts.governance import repository_checks

    repository = tmp_path / "apps/kokoro-capability"
    canonical = repository / "prisma/schema.prisma"
    canonical.parent.mkdir(parents=True)
    canonical.write_text(
        'datasource db {\n provider = "postgresql"\n relationMode = "prisma"\n}\n'
    )
    if extra:
        path = repository / extra
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("-- fixture")
    monkeypatch.setattr(repository_checks, "ROOT", tmp_path)
    failures = []
    repository_checks.check_common("kokoro-capability", failures)
    assert bool([f for f in failures if f.rule == "canonical-schema"]) is bool(extra)


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize(
    "route,allowed",
    [
        ("/v1/items", True),
        ("/internal/v1/items", True),
        ("/.well-known/jwks.json", True),
        ("/livez", True),
        ("/v2/items", False),
        ("/internal/v2/items", False),
        ("/internal/admin/v1/items", False),
        ("/items", False),
    ],
)
def test_openapi_version_policy_is_identical_for_yaml_and_json(
    suffix, route, allowed, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / ("contract/openapi" + suffix)
    spec.parent.mkdir(parents=True)
    spec.write_text(
        json.dumps({"openapi": "3.1.0", "paths": {route: {}}})
        if suffix == ".json"
        else f'openapi: 3.1.0\npaths:\n  "{route}": {{}}\n'
    )
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    violations = [f for f in failures if f.rule == "http-versioning"]
    assert (not violations) is allowed
    if violations:
        assert "first-release v1 baseline" in violations[0].detail


@pytest.mark.parametrize(
    "surface", ["manifest", "version-file", "docker", "ci", "release"]
)
@pytest.mark.parametrize("major,valid", [(24, True), (22, False)])
def test_node_major_consistency_covers_each_declared_surface(
    surface, major, valid, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-storage"
    (repository / ".github/workflows").mkdir(parents=True)
    (repository / "package.json").write_text(
        json.dumps(
            {
                "engines": {
                    "node": f">={major if surface == 'manifest' else 24}.20.0 <25"
                }
            }
        )
    )
    (repository / ".node-version").write_text(
        f"{major if surface == 'version-file' else 24}.20.0\n"
    )
    (repository / "Dockerfile").write_text(
        f"ARG NODE_IMAGE=node:{major if surface == 'docker' else 24}.20.0-slim\nFROM ${{NODE_IMAGE}}\n"
    )
    for workflow, name in [("ci", "ci.yml"), ("release", "release-image.yml")]:
        (repository / ".github/workflows" / name).write_text(
            f"steps:\n  - uses: actions/setup-node@{'a' * 40}\n    with:\n      node-version: {major if surface == workflow else 24}\n"
        )
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-storage", failures)
    assert (
        not [f for f in failures if f.rule == "toolchain" and "Node" in f.detail]
    ) is valid


@pytest.mark.parametrize(
    "relative,allowed",
    [
        ("generated/prisma/runtime.ts", True),
        ("transport/execution.service.ts", True),
        ("modules/skills/skill-rpc.service.ts", True),
        ("integrations/iam/iam.service.ts", True),
        ("modules/skills/skill.service.ts", False),
        ("modules/skills/domain/model.ts", False),
        ("modules/skills/integrations/iam.service.ts", False),
        ("modules/skills/events/skill.service.ts", False),
    ],
)
def test_generated_transport_and_process_roles_do_not_exempt_business_rules(
    relative, allowed, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-capability"
    path = repository / "src" / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        'import { client } from "@connectrpc/connect";\nimport { Wire } from "../../generated/proto.js";\n'
    )
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-capability", failures)
    assert (
        not [f for f in failures if f.rule in {"wire-boundary", "dependency-direction"}]
    ) is allowed


def load_cli(monkeypatch):
    import runpy

    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    namespace = runpy.run_path(str(SCRIPT))
    return namespace["main"].__globals__


def test_missing_typescript_is_unverified_unless_requested(monkeypatch, capsys):
    cli = load_cli(monkeypatch)

    def missing(_):
        raise ten_repository_standard.TypeScriptConfigError("missing")

    monkeypatch.setattr(typescript_checks, "effective_ts_compiler_options", missing)
    monkeypatch.setitem(cli, "check_typescript", typescript_checks.check_typescript)
    failures, unverified = cli["collect_audit"]()
    assert not [item for item in failures if item.rule == "typescript-configuration"]
    assert (
        len([item for item in unverified if item.rule == "typescript-configuration"])
        == 7
    )
    monkeypatch.setitem(cli, "collect_audit", lambda: ([], unverified))
    assert cli["main"](["--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "UNVERIFIED"
    assert result["unverified_count"] == 7
    assert cli["main"](["--format", "json", "--require-installed-tools"]) == 1
    assert json.loads(capsys.readouterr().out)["violations"] == []


@pytest.mark.parametrize(
    "name,retired", [("kokoro-bff", False), ("kokoro-system", True)]
)
def test_retired_topology_is_an_explicit_owner_profile(
    name, retired, tmp_path, monkeypatch
):
    (tmp_path / "apps" / name / "src/application").mkdir(parents=True)
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript(name, failures)
    assert bool([f for f in failures if "retired top-level" in f.detail]) is retired
    assert not [f for f in failures if "src/modules/ is missing" in f.detail]


def test_orm_quality_gates_require_validate_generate_and_drift(tmp_path, monkeypatch):
    repository = tmp_path / "apps/kokoro-capability"
    repository.mkdir(parents=True)
    (repository / "package.json").write_text(
        json.dumps(
            {"scripts": {"prisma:validate": "echo pass", "prisma:generate": "true"}}
        )
    )
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-capability", failures)
    for name in ("prisma:validate", "prisma:generate", "schema:check"):
        assert any(name in f.detail for f in failures)


def test_openapi_upstream_exemption_requires_pinned_owner_provenance(tmp_path):
    repository = tmp_path / "kokoro-iam"
    vendor = repository / "contract/vendor/better-auth.v1.7.3.json"
    legacy = repository / "contract/openapi/better-auth.v1.7.3.json"
    vendor.parent.mkdir(parents=True)
    legacy.parent.mkdir(parents=True)
    vendor.write_text('{"openapi":"3.1.0", "paths":{}}')
    legacy.write_text('{"openapi":"3.1.0", "paths":{}}')
    readme = repository / "contract/README.md"
    readme.write_text(
        "contract/vendor/better-auth.v1.7.3.json # upstream schema snapshot\n"
    )
    assert ten_repository_standard.openapi_contract_candidates(repository) == (
        legacy,
    )
    readme.write_text("owned specification\n")
    assert ten_repository_standard.openapi_contract_candidates(repository) == (
        legacy,
        vendor,
    )


def test_agent_http_contract_owner_requires_a_confirmed_openapi_input(
    tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-agent"
    for relative, contents in {
        "contract/provenance.json": '{"http_contract":"openapi/v1/openapi.json"}',
        "contract/execution-proof/v1/schema.json": '{"$schema":"https://json-schema.org/draft/2020-12/schema"}',
    }.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    monkeypatch.setattr(surface_checks, "ROOT", tmp_path)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)

    failures = []
    surface_checks.check_agent(failures)

    assert any(
        failure.rule == "contract-owner"
        and "HTTP boundary has no owned published or generated OpenAPI" in failure.detail
        for failure in failures
    )


def test_agent_http_contract_owner_accepts_a_confirmed_openapi_input(
    tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-agent"
    specification = repository / "contract/openapi/v1/openapi.json"
    specification.parent.mkdir(parents=True)
    specification.write_text('{"openapi":"3.1.0","paths":{}}', encoding="utf-8")
    monkeypatch.setattr(surface_checks, "ROOT", tmp_path)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)

    failures = []
    surface_checks.check_agent(failures)

    assert not any(
        failure.rule == "contract-owner"
        and "HTTP boundary has no owned published or generated OpenAPI" in failure.detail
        for failure in failures
    )


def test_current_agent_openapi_is_a_confirmed_owner_contract():
    repository = ROOT / "apps/kokoro-agent"
    specification = repository / "contract/openapi/v1/openapi.json"
    failures = []

    assert specification in ten_repository_standard.openapi_contract_candidates(
        repository
    )
    assert contract_checks.check_openapi_contract(
        "kokoro-agent", specification, failures
    )
    assert failures == []


def test_named_setup_node_step_and_docker_chown_are_not_false_majors(
    tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-iam"
    (repository / ".github/workflows").mkdir(parents=True)
    (repository / "package.json").write_text('{"engines":{"node":">=24 <25"}}')
    (repository / ".node-version").write_text("24.20.0\n")
    (repository / "Dockerfile").write_text(
        "FROM node:24.20.0-slim\nCOPY --chown=node:node . /app\n"
    )
    workflow = repository / ".github/workflows/ci.yml"
    workflow.write_text(
        "steps:\n  - name: Setup\n    uses: actions/setup-node@fixture\n    with:\n      node-version-file: .node-version\n  - run: pnpm test\n"
    )
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    failures = []
    typescript_checks.check_node_consistency("kokoro-iam", repository, failures)
    assert failures == []


def test_common_directory_is_not_itself_a_retired_global_layer(tmp_path, monkeypatch):
    (tmp_path / "apps/kokoro-storage/src/common").mkdir(parents=True)
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-storage", failures)
    assert not [f for f in failures if "retired top-level" in f.detail]


@pytest.mark.parametrize(
    "relative", ["modules/skills/skill.service.ts", "modules/skills/domain/model.ts"]
)
@pytest.mark.parametrize(
    "source",
    [
        'const wire = await import("../../generated/proto.js");',
        'const wire = require("../../generated/proto.js");',
    ],
)
def test_dynamic_generated_imports_stay_out_of_business_code(
    relative, source, tmp_path, monkeypatch
):
    path = tmp_path / "apps/kokoro-capability/src" / relative
    path.parent.mkdir(parents=True)
    path.write_text(source)
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-capability", failures)
    assert any(f.rule == "wire-boundary" for f in failures)


def test_schema_drift_script_must_call_the_approved_checker(tmp_path, monkeypatch):
    repository = tmp_path / "apps/kokoro-capability"
    (repository / "scripts").mkdir(parents=True)
    (repository / "scripts/check-schema.ts").write_text("checkPersistedSchema();")
    (repository / "package.json").write_text(
        '{"scripts":{"schema:check":"node unrelated.js"}}'
    )
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-capability", failures)
    assert any(f.rule == "schema-drift" for f in failures)


@pytest.mark.parametrize(
    "paths",
    [
        "paths: { /v2/items: {} }\n",
        "paths: &routes\n  /v2/items: {}\n",
        "x-paths: &routes\n  /v2/items: {}\npaths: *routes\n",
        "x-paths: &routes\n  /v2/items: {}\npaths:\n  <<: *routes\n",
        "x-document: &document\n  paths:\n    /v2/items: {}\n<<: *document\n",
    ],
)
def test_review_yaml_non_block_paths_fail_closed(paths, tmp_path, monkeypatch):
    spec = tmp_path / "apps/kokoro-billing/contract/openapi.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text("openapi: 3.1.0\n" + paths)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    assert any(item.rule in {"http-versioning", "openapi-parsing"} for item in failures)


@pytest.mark.parametrize(
    "provenance,excluded",
    [
        ("", False),
        (
            "other-better-auth.v1.7.3.json — upstream snapshot provenance: https://example.test/spec",
            False,
        ),
        ("better-auth.v1.7.3.json", False),
        (
            "contract/vendor/better-auth.v1.7.3.json — upstream snapshot provenance: https://example.test/spec",
            True,
        ),
        (
            "better-auth.v1.7.3.json upstream snapshot provenance: https://example.test/spec",
            False,
        ),
    ],
)
def test_review_vendor_exemption_requires_exact_provenance(
    provenance, excluded, tmp_path
):
    repository = tmp_path / "kokoro-iam"
    spec = repository / "contract/vendor/better-auth.v1.7.3.json"
    spec.parent.mkdir(parents=True)
    spec.write_text('{"openapi":"3.1.0", "paths":{"/v2/items":{}}}')
    (repository / "contract/README.md").write_text(provenance)
    assert (
        spec not in ten_repository_standard.openapi_contract_candidates(repository)
    ) is excluded


@pytest.mark.parametrize(
    "name",
    [
        "kokoro-bff",
        "kokoro-agent",
        "kokoro-system",
        "kokoro-billing",
        "kokoro-scheduler",
    ],
)
def test_review_sql_canonical_rejects_editable_prisma_schema(
    name, tmp_path, monkeypatch
):
    from scripts.governance import repository_checks

    repository = tmp_path / "apps" / name
    (repository / "database").mkdir(parents=True)
    (repository / "database/schema.sql").write_text("CREATE TABLE fixture (id UUID);")
    (repository / "prisma").mkdir()
    (repository / "prisma/schema.prisma").write_text("model Fixture { id String @id }")
    monkeypatch.setattr(repository_checks, "ROOT", tmp_path)
    failures = []
    repository_checks.check_common(name, failures)
    assert any(
        item.rule == "canonical-schema" and "prisma/schema.prisma" in item.detail
        for item in failures
    )


@pytest.mark.parametrize("quote", ["", "'", '"'])
@pytest.mark.parametrize("major,valid", [(22, False), (24, True)])
def test_review_setup_node_quotes_do_not_skip_major_check(
    quote, major, valid, tmp_path
):
    repository = tmp_path / "kokoro-system"
    workflow = repository / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    (repository / "package.json").write_text('{"engines":{"node":">=24 <25"}}')
    workflow.write_text(
        f"steps:\n  - uses: {quote}actions/setup-node@fixture{quote}\n    with:\n      node-version: {major}\n"
    )
    failures = []
    typescript_checks.check_node_consistency("kokoro-system", repository, failures)
    assert (not failures) is valid


@pytest.mark.parametrize("route", ["/v1/items", "/v2/items"])
def test_review_json_document_is_supported_as_yaml_subset(route):
    text = json.dumps({"openapi": "3.1.0", "paths": {route: {}}})
    assert contract_checks.openapi_paths(text, ".yaml") == (route,)


@pytest.mark.parametrize(
    "name,text",
    [
        ("flow.yaml", "{openapi: 3.1.0, paths: {/v2/items: {}}}"),
        (
            "flow.yml",
            "{info: {title: fixture}, openapi: 3.1.0, paths: {/v2/items: {}}}",
        ),
        ("json-as-yaml.yaml", '{"openapi":"3.1.0","paths":{"/v2/items":{}}}'),
        ("openapi.json", '{"openapi":"3.1.0","paths":{"/v2/items":{}}}'),
    ],
)
def test_review_discovery_checks_root_flow_and_json_yaml_end_to_end(
    name, text, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / "contract/openapi" / name
    spec.parent.mkdir(parents=True)
    spec.write_text(text)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    discovered = ten_repository_standard.openapi_contract_candidates(repository)
    assert discovered == (spec,)
    failures = []
    for path in discovered:
        contract_checks.check_openapi_contract("kokoro-billing", path, failures)
    assert any(item.rule in {"http-versioning", "openapi-parsing"} for item in failures)


@pytest.mark.parametrize(
    "text",
    [
        "{nested: {openapi: 3.1.0}, paths: {}}",
        '{info: {title: "openapi: 3.1.0"}, paths: {}}',
        '{"nested":{"openapi":"3.1.0"}}',
    ],
)
def test_review_discovery_does_not_promote_nested_flow_openapi(text, tmp_path):
    spec = tmp_path / "contract/provenance.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text(text)
    assert ten_repository_standard.openapi_contract_candidates(tmp_path) == ()


@pytest.mark.parametrize(
    "prefix",
    [
        "# owned contract\n",
        "---\n# owned contract\n",
        "--- ",
        "\ufeff\n# owned\n\n--- # document\n# contract\n",
        "%YAML 1.2\n---\n# owned contract\n",
    ],
)
@pytest.mark.parametrize(
    "body",
    [
        "{openapi: 3.1.0, paths: {/v2/items: {}}}",
        '{"openapi":"3.1.0","paths":{"/v2/items":{}}}',
    ],
)
def test_review_yaml_document_prefixes_reach_contract_check(
    prefix, body, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / "contract/openapi/api.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text(prefix + body)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    discovered = ten_repository_standard.openapi_contract_candidates(repository)
    assert discovered == (spec,)
    failures = []
    for path in discovered:
        contract_checks.check_openapi_contract("kokoro-billing", path, failures)
    assert any(item.rule in {"http-versioning", "openapi-parsing"} for item in failures)


@pytest.mark.parametrize(
    "body",
    [
        "{nested: {openapi: 3.1.0}, paths: {}}",
        '{info: {title: "openapi: 3.1.0"}, paths: {}}',
    ],
)
def test_review_yaml_prefixes_preserve_top_level_discovery_boundary(body, tmp_path):
    spec = tmp_path / "contract/provenance.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text("# provenance\n--- " + body)
    assert ten_repository_standard.openapi_contract_candidates(tmp_path) == ()


@pytest.mark.parametrize(
    "text",
    [
        "&doc {openapi: 3.1.0, paths: {/v2/items: {}}}",
        "openapi: &version 3.1.0\npaths:\n  /v2/items: {}\n",
        "x-version: &version 3.1.0\nopenapi: *version\npaths:\n  /v2/items: {}\n",
        "x-doc: &doc\n  openapi: 3.1.0\n  paths:\n    /v2/items: {}\n<<: *doc\n",
        "  openapi: 3.1.0\n  paths:\n    /v2/items: {}\n",
        "# comment\n--- # document\n# body\n  openapi: 3.1.0\n  paths:\n    /v2/items: {}\n",
        "--- &doc {openapi: 3.1.0, paths: {/v2/items: {}}}",
        '--- {"openapi":"3.1.0","paths":{"/v2/items":{}}}',
        "--- {openapi: 3.1.0, paths: {/v2/items: {}}}",
        '"openapi": 3.1.0\n"paths":\n  /v2/items: {}\n',
        "? openapi\n: 3.1.0\npaths:\n  /v2/items: {}\n",
        "!!map\nopenapi: 3.1.0\npaths:\n  /v2/items: {}\n",
        "openapi: 3.1.0\npaths: {}\n---\nopenapi: 3.1.0\npaths:\n  /v2/items: {}\n",
        "{ malformed",
        "",
    ],
)
@pytest.mark.parametrize(
    "relative", ["contract/openapi/v1/api.yaml", "contract/openapi/tests/api.yml"]
)
def test_review_managed_candidates_never_silently_skip_yaml(
    text, relative, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / relative
    spec.parent.mkdir(parents=True)
    spec.write_text(text)
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-billing", failures)
    diagnostics = [item for item in failures if relative in item.detail]
    assert any(
        item.rule in {"http-versioning", "openapi-parsing", "contract-owner"}
        for item in diagnostics
    ), diagnostics


@pytest.mark.parametrize(
    "text,expected_parsing",
    [
        ("{nested: {\nopenapi: 3.1.0\n}, paths: {}}", True),
        ('"some text\nopenapi: 3.1.0\nmore text"', True),
        ("nested:\n  openapi: 3.1.0\n  paths:\n    /v2/items: {}\n", False),
        ('"openapi: 3.1.0"', False),
        ('{"nested":{"openapi":"3.1.0","paths":{"/v2/items":{}}}}', False),
    ],
)
def test_review_non_openapi_content_is_not_an_owned_spec(
    text, expected_parsing, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    provenance = repository / "contract/provenance.yaml"
    provenance.parent.mkdir(parents=True)
    provenance.write_text(text)
    assert ten_repository_standard.openapi_contract_candidates(repository) == ()
    # A managed YAML file is a candidate, not proof of an owned OpenAPI document.
    # Ambiguous/unsupported content must diagnose parsing instead of applying API rules.
    spec = repository / "contract/openapi/candidate.yaml"
    spec.parent.mkdir()
    spec.write_text(text)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    assert not contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    assert bool(failures) is expected_parsing
    assert all(item.rule == "openapi-parsing" for item in failures)


@pytest.mark.parametrize("suffix", ["json", "yaml", "yml"])
def test_review_managed_malformed_json_reaches_parser(suffix, tmp_path, monkeypatch):
    repository = tmp_path / "apps/kokoro-billing"
    relative = (
        "contract/openapi.json"
        if suffix == "json"
        else f"contract/openapi/api.{suffix}"
    )
    spec = repository / relative
    spec.parent.mkdir(parents=True)
    spec.write_text('{"openapi":"3.1.0",')
    assert ten_repository_standard.openapi_contract_candidates(repository) == (spec,)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    for path in ten_repository_standard.openapi_contract_candidates(repository):
        contract_checks.check_openapi_contract("kokoro-billing", path, failures)
    assert [item.rule for item in failures] == ["openapi-parsing"]


@pytest.mark.parametrize(
    "text",
    [
        '"not an OpenAPI document"',
        '{"nested":{"openapi":"3.1.0"}}',
        "nested:\n  openapi: 3.1.0\n",
        "description: |\n  openapi: 3.1.0\n",
        "&doc {openapi: 3.1.0, paths: {}}",
    ],
)
def test_review_candidates_do_not_replace_confirmed_contract_owner(
    text, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / "contract/openapi/candidate.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text(text)
    transport = repository / "src/items.routes.ts"
    transport.parent.mkdir()
    transport.write_text('app.get("/v1/items", handler);')
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-billing", failures)
    assert any(item.rule == "contract-owner" for item in failures)
    assert not any(item.rule == "openapi-governance" for item in failures)


def test_review_valid_sibling_does_not_hide_unreadable_candidate(tmp_path, monkeypatch):
    repository = tmp_path / "apps/kokoro-billing"
    valid = repository / "contract/openapi/valid.json"
    valid.parent.mkdir(parents=True)
    valid.write_text('{"openapi":"3.1.0","paths":{}}')
    unreadable = valid.with_name("unreadable.yaml")
    unreadable.write_bytes(b"\xff")
    auxiliary = valid.with_name("breaking-policy.json")
    auxiliary.write_text('{"breaking":"reject"}')
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )
    failures = []
    typescript_checks.check_typescript("kokoro-billing", failures)
    parsing = [item for item in failures if item.rule == "openapi-parsing"]
    assert len(parsing) == 1 and "unreadable.yaml" in parsing[0].detail
    assert not any("breaking-policy.json" in item.detail for item in failures)


@pytest.mark.parametrize("suffix", [".json", ".yaml", ".yml"])
def test_review_json_operation_checks_are_extension_independent(
    suffix, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / f"contract/openapi/api{suffix}"
    spec.parent.mkdir(parents=True)
    spec.write_text('{"openapi":"3.1.0","paths":{"/v1/items":{"get":{}}}}')
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    assert contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    assert [item.rule for item in failures] == ["openapi-governance"]


@pytest.mark.parametrize(
    "body",
    [
        "  /v1/items: *item\n",
        "  /v1/items: {get: {}}\n",
        "  /v1/items:\n    get: {responses: {}}\n",
        "  /v1/items:\n    get: *operation\n",
        "  /v1/items:\n    <<: *item\n",
    ],
)
def test_review_indirect_yaml_operations_do_not_silently_pass(
    body, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / "contract/openapi/api.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text("openapi: 3.1.0\npaths:\n" + body)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    assert not contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    assert [item.rule for item in failures] == ["openapi-parsing"]


@pytest.mark.parametrize("name", ["kokoro-agent", "kokoro-scheduler"])
def test_review_non_typescript_owners_check_every_managed_candidate(
    name, tmp_path, monkeypatch
):
    from scripts.governance import repository_checks

    repository = tmp_path / "apps" / name
    spec = repository / "contract/openapi/extra.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text("&doc {openapi: 3.1.0, paths: {/v2/items: {}}}")
    monkeypatch.setattr(repository_checks, "ROOT", tmp_path)
    monkeypatch.setattr(surface_checks, "ROOT", tmp_path)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    repository_checks.check_common(name, failures)
    if name == "kokoro-agent":
        surface_checks.check_agent(failures)
    else:
        repository_checks.check_scheduler(failures)
    assert any(
        item.rule == "openapi-parsing" and "contract/openapi/extra.yaml" in item.detail
        for item in failures
    )


@pytest.mark.parametrize(
    "text",
    [
        "--- openapi: 3.1.0\npaths: {}\n",
        "%YAML nonsense\n---\nopenapi: 3.1.0\npaths: {}\n",
        "%YAML 1.2\n%YAML 1.2\n---\nopenapi: 3.1.0\npaths: {}\n",
        "%YAML 1.2\nopenapi: 3.1.0\npaths: {}\n",
        "%TAG nonsense\n---\nopenapi: 3.1.0\npaths: {}\n",
        "openapi: 3.1.0\npaths:\n  /v1/items:\n    GET: {}\n",
        "openapi: 3.1.0\npaths:\n  /v1/items:\n    unknown: {}\n",
    ],
)
def test_review_unsupported_envelope_is_not_confirmed_owner(
    text, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / "contract/openapi/api.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text(text)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    assert not contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    assert [item.rule for item in failures] == ["openapi-parsing"]


@pytest.mark.parametrize("name", ["kokoro-iam", "kokoro-billing"])
def test_review_generic_vendor_provenance_does_not_skip_managed_candidates(
    name, tmp_path
):
    repository = tmp_path / name
    spec = repository / "contract/openapi/vendor/upstream.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text("&doc {openapi: 3.1.0, paths: {}}")
    (repository / "contract/README.md").write_text(
        "contract/openapi/vendor/upstream.yaml upstream snapshot provenance: https://example.test/spec"
    )
    assert ten_repository_standard.openapi_contract_candidates(repository) == (spec,)


@pytest.mark.parametrize("suffix", [".json", ".yaml", ".yml"])
@pytest.mark.parametrize(
    "item",
    [
        "opaque",
        {"get": "opaque"},
        {
            "GET": dict.fromkeys(
                contract_checks.REQUIRED_OPENAPI_OPERATION_EXTENSIONS, "x"
            )
        },
        {"$ref": "#/components/pathItems/Items"},
        {"unknown": {}},
    ],
)
def test_review_json_path_item_shape_fails_closed(suffix, item, tmp_path, monkeypatch):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / f"contract/openapi/api{suffix}"
    spec.parent.mkdir(parents=True)
    spec.write_text(json.dumps({"openapi": "3.1.0", "paths": {"/v1/items": item}}))
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    assert not contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    assert [item.rule for item in failures] == ["openapi-parsing"]


@pytest.mark.parametrize("suffix", [".json", ".yaml", ".yml"])
def test_review_paths_extensions_are_not_http_operations(suffix, tmp_path, monkeypatch):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / f"contract/openapi/api{suffix}"
    spec.parent.mkdir(parents=True)
    spec.write_text('{"openapi":"3.1.0","paths":{"x-example":{"get":{}}}}')
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    assert contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    assert failures == []


@pytest.mark.parametrize(
    "body",
    [
        "paths:\n  /v1/items:\n    summary: scalar\n      get: {}\n",
        "paths:\n  /v1/items:\n    description: 'scalar'\n      post: {}\n",
        'paths:\n  /v1/items:\n    x-note: "scalar" # comment\n      get: {}\n',
        "paths:\n  /v1/items:\n    parameters: []\n      get: {}\n",
        "paths:\n  /v1/items:\n    x-note: {}\n      get: {}\n",
        "paths:\n  /v1/items:\n    get:\n      summary: scalar\n        responses: {}\n",
        "x-note: scalar\n  nested: {}\npaths: {}\n",
        "paths:\n  x-note: scalar\n    /v1/items: {}\n",
        # Legal multiline plain scalars are outside this preflight's subset.
        "paths:\n  /v1/items:\n    summary: first line\n      more text\n",
        "paths:\n  /v1/items:\n    description: | invalid header\n      get: {}\n",
        "paths:\n  /v1/items:\n    description: | invalid header\n",
        "paths:\n  /v1/items:\n    description: |\n        first line\n      get: {}\n",
        "paths:\n  /v1/items:\n    description: |\n        # scalar content\n      get: {}\n",
        # Explicit indentation indicators are not in the supported scalar subset.
        "paths:\n  /v1/items:\n    description: |2\n      get: {}\n",
        # Preserving comments for literal scalar text must not turn null into {}.
        "paths:\n  # no mapping entries\n",
        "paths:\n  /v1/items:\n    # no mapping entries\n",
        "paths:\n  /v1/items:\n    get:\n      # no mapping entries\n",
        "paths:\n  /v1/items:\n    description: |\n      text\n    # closed scalar\n      get: {}\n",
        "paths:\n  /v1/items:\n    description: |\n    # closed scalar\n      get: {}\n",
        "paths:\n  /v1/items:\n    description: |\n      text\n  # closed scalar\n      get: {}\n",
        "paths:\n  /v1/items:\n    description: |\n      text\n# closed scalar\n      get: {}\n",
    ],
)
@pytest.mark.parametrize("suffix", [".yaml", ".yml"])
def test_review_inline_yaml_values_never_swallow_indented_content(
    body, suffix, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    relative = f"contract/openapi/api{suffix}"
    spec = repository / relative
    spec.parent.mkdir(parents=True)
    spec.write_text("openapi: 3.1.0\n" + body)
    transport = repository / "src/items.routes.ts"
    transport.parent.mkdir()
    transport.write_text('app.get("/v1/items", handler);')
    monkeypatch.setattr(typescript_checks, "ROOT", tmp_path)
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    monkeypatch.setattr(
        typescript_checks, "effective_ts_compiler_options", lambda _: {}
    )

    candidates = ten_repository_standard.openapi_contract_candidates(repository)
    assert candidates == (spec,)
    failures = []
    assert not contract_checks.check_openapi_contract(
        "kokoro-billing", candidates[0], failures
    )
    assert [item.rule for item in failures] == ["openapi-parsing"]
    assert relative in failures[0].detail

    failures = []
    typescript_checks.check_typescript("kokoro-billing", failures)
    assert len([item for item in failures if item.rule == "openapi-parsing"]) == 1
    assert any(item.rule == "contract-owner" for item in failures)
    assert not any(item.rule == "openapi-governance" for item in failures)


@pytest.mark.parametrize("value", ["scalar", "'scalar'", '"scalar"', "{}", "[]"])
def test_review_inline_yaml_values_keep_sibling_operations(
    value, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / "contract/openapi/api.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "openapi: 3.1.0\npaths:\n  /v1/items:\n"
        f"    x-note: {value} # comment\n"
        "      # An indented comment is not a child node.\n"
        "    get: {}\n"
    )
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    assert contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    assert [item.rule for item in failures] == ["openapi-governance"]
    assert "GET /v1/items" in failures[0].detail


@pytest.mark.parametrize("header", ["|", ">", "|-", ">+ # comment"])
def test_review_yaml_block_scalar_content_is_not_an_operation(
    header, tmp_path, monkeypatch
):
    repository = tmp_path / "apps/kokoro-billing"
    spec = repository / "contract/openapi/api.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "openapi: 3.1.0\npaths:\n  /v1/items:\n"
        f"    description: {header}\n"
        "      # scalar content\n        get: {}\n      scalar text\n"
        "    # The scalar is closed; a same-level sibling remains valid.\n"
        "    post: {}\n"
    )
    monkeypatch.setattr(contract_checks, "ROOT", tmp_path)
    failures = []
    assert contract_checks.check_openapi_contract("kokoro-billing", spec, failures)
    assert [item.rule for item in failures] == ["openapi-governance"]
    assert "POST /v1/items" in failures[0].detail

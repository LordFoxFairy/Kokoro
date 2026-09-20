from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.governance import (
    contract_checks,
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

    assert verifier.REQUIRED_NODE_ENGINE == ">=24 <25"
    assert verifier.REQUIRED_TS_SOURCE_PATHS == ("modules", "config")
    assert verifier.REQUIRED_AGENT_SOURCE_PATHS == ("execution",)
    assert verifier.REPOSITORY_PROFILES["kokoro-bff"].required_source_paths == (
        "modules",
        "config",
    )
    assert verifier.REPOSITORY_PROFILES["kokoro-agent"].required_source_paths == (
        "execution",
    )
    assert "application" in verifier.RETIRED_TS_TOP_LEVEL_DIRECTORIES
    assert "infrastructure" in verifier.RETIRED_TS_TOP_LEVEL_DIRECTORIES
    assert "ports" in verifier.RETIRED_TS_TOP_LEVEL_DIRECTORIES
    assert "services" in verifier.RETIRED_TS_TOP_LEVEL_DIRECTORIES
    assert "repositories" in verifier.RETIRED_TS_TOP_LEVEL_DIRECTORIES
    assert "postgres" in verifier.RETIRED_TS_TOP_LEVEL_DIRECTORIES
    assert "redis" in verifier.RETIRED_TS_TOP_LEVEL_DIRECTORIES
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
    assert verifier.is_granularity_exempt("kokoro-app", "src/engine/machine.ts") is False


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

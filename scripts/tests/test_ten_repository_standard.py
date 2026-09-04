from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from scripts.governance import contract_checks, ten_repository_standard


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify-ten-repository-standard.py"


def load_verifier() -> SimpleNamespace:
    exports = vars(ten_repository_standard) | {
        "missing_openapi_operation_extensions": contract_checks.missing_openapi_operation_extensions,
    }
    return SimpleNamespace(**exports)


def test_verifier_targets_exactly_the_ten_active_repositories() -> None:
    verifier = load_verifier()

    assert verifier.REPOSITORIES == (
        "kokoro",
        "kokoro-bff",
        "kokoro-agent",
        "kokoro-iam",
        "kokoro-system",
        "kokoro-model",
        "kokoro-billing",
        "kokoro-capability",
        "kokoro-storage",
        "kokoro-scheduler",
    )


def test_repository_profiles_encode_runtime_and_persistence_boundaries() -> None:
    verifier = load_verifier()

    assert verifier.REPOSITORY_PROFILES["kokoro"].kind == "web"
    assert verifier.REPOSITORY_PROFILES["kokoro"].requires_schema is False
    assert verifier.REPOSITORY_PROFILES["kokoro-bff"].kind == "typescript-service"
    assert verifier.REPOSITORY_PROFILES["kokoro-bff"].requires_schema is True
    assert verifier.REPOSITORY_PROFILES["kokoro-agent"].kind == "python-service"
    assert verifier.REPOSITORY_PROFILES["kokoro-agent"].requires_schema is True
    assert verifier.REPOSITORY_PROFILES["kokoro-scheduler"].kind == "go-service"
    assert verifier.REPOSITORY_PROFILES["kokoro-scheduler"].requires_schema is False


def test_shared_redis_database_mapping_reserves_zero_and_covers_stateful_services() -> (
    None
):
    verifier = load_verifier()

    assert verifier.LOCAL_REDIS_DATABASES == {
        "kokoro-iam": 1,
        "kokoro-system": 2,
        "kokoro-model": 3,
        "kokoro-billing": 4,
        "kokoro-capability": 5,
        "kokoro-storage": 6,
        "kokoro-scheduler": 7,
        "kokoro-bff": 8,
        "kokoro-agent": 9,
    }
    assert 0 not in verifier.LOCAL_REDIS_DATABASES.values()
    assert "kokoro" not in verifier.LOCAL_REDIS_DATABASES
    assert verifier.extract_redis_databases("REDIS_URL=redis://cache.local:6379/8") == {
        8
    }


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


def test_typescript_strictness_includes_unknown_catch_variables() -> None:
    verifier = load_verifier()

    assert verifier.REQUIRED_TS_COMPILER_OPTIONS == (
        "strict",
        "noUncheckedIndexedAccess",
        "exactOptionalPropertyTypes",
        "noImplicitOverride",
        "noImplicitReturns",
        "noUnusedLocals",
        "noUnusedParameters",
        "useUnknownInCatchVariables",
    )


def test_required_quality_scripts_are_profile_specific() -> None:
    verifier = load_verifier()

    assert verifier.required_quality_scripts("kokoro") == (
        "lint",
        "typecheck",
        "test",
        "build",
        "test:e2e",
    )
    assert verifier.required_quality_scripts("kokoro-bff") == (
        "lint",
        "typecheck",
        "test",
        "build",
        "db:apply-schema",
        "contract:check",
    )
    assert verifier.required_quality_scripts("kokoro-agent") == ()


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

    assert verifier.is_granularity_exempt("kokoro", "src/i18n/en.ts") is True
    assert verifier.is_granularity_exempt("kokoro", "src/engine/machine.ts") is False


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
    assert json.loads(result.stdout)["repository_count"] == 10

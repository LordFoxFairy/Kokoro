"""Owner-schema guards shared by Root BFF composition smokes."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
from urllib.parse import parse_qsl, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/e2e/bff_owner_schema.py"
RUNNERS = (
    ROOT / "scripts/e2e/run_bff_iam_session_smoke.py",
    ROOT / "scripts/e2e/run_bff_iam_oidc_smoke.py",
    ROOT / "scripts/e2e/run_capability_bff_smoke.py",
    ROOT / "scripts/e2e/run_scheduler_bff_smoke.py",
    ROOT / "scripts/e2e/run_system_owner_smoke.py",
)


def load_helper():
    assert HELPER.is_file(), "Root BFF owner-schema URL helper is missing"
    spec = importlib.util.spec_from_file_location("bff_owner_schema", HELPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def dictionary_keys(node: ast.Dict) -> set[str]:
    return {
        key.value
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def test_bff_url_targets_exact_owner_schema_without_connection_overrides() -> None:
    helper = load_helper()
    actual = helper.bff_owner_database_url(
        "postgresql://user:password@localhost/app?"
        "sslmode=require&options=-csearch_path%3Dpublic&Search_Path=public&schema=public"
    )
    parsed = urlsplit(actual)
    query = parse_qsl(parsed.query, keep_blank_values=True)
    assert parsed.scheme == "postgresql"
    assert parsed.netloc == "user:password@localhost"
    assert parsed.path == "/app"
    assert query == [("sslmode", "require"), ("schema", "kokoro_bff")]
    assert parsed.fragment == ""


@pytest.mark.parametrize(
    "database_url",
    [
        "http://localhost/app",
        "postgresql://localhost/app#fragment",
        "postgresql://localhost:invalid/app",
    ],
)
def test_bff_url_rejects_non_postgres_or_ambiguous_input(database_url: str) -> None:
    helper = load_helper()
    with pytest.raises(ValueError, match="PostgreSQL"):
        helper.bff_owner_database_url(database_url)


def test_all_bff_runners_use_owner_helper_and_never_override_its_search_path() -> None:
    for runner in RUNNERS:
        source = runner.read_text()
        assert "bff_owner_database_url(" in source, runner
        assert "public.bff_" not in source and "FROM public." not in source, runner
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Dict):
                keys = dictionary_keys(node)
                if "KOKORO_BFF_POSTGRES_URL" in keys:
                    assert "PGOPTIONS" not in keys, runner


def test_session_smoke_keeps_psql_url_free_of_app_schema_parameter() -> None:
    source = (ROOT / "scripts/e2e/run_bff_iam_session_smoke.py").read_text()
    assert 'db_url = resources.create_database("bff")' in source
    assert '"KOKORO_BFF_POSTGRES_URL": bff_owner_database_url(db_url)' in source
    assert 'resources.command(["psql", db_url,' in source


def test_scheduler_smoke_observes_bff_outbox_in_owner_schema() -> None:
    source = (ROOT / "scripts/e2e/scheduler_bff_smoke_cases.py").read_text()
    assert source.count("FROM kokoro_bff.bff_scheduled_task_outbox") == 2
    assert "FROM bff_scheduled_task_outbox" not in source

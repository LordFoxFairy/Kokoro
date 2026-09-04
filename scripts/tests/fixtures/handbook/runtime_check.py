"""Tests for extracted handbook code; dependencies and DB belong to the caller."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from kokoro_agent.runs.models import Run
from kokoro_agent.runs.schemas import CreateRunRequest
from kokoro_agent.runs.service import CreateRun, create_run
from kokoro_agent.settings import load_settings
from pydantic import ValidationError


def test_settings_load_uppercase_environment_and_file_precedence(
    tmp_path: Path, monkeypatch
):
    for key in list(os.environ):
        if key.startswith("KOKORO_AGENT_"):
            monkeypatch.delenv(key)
    base = tmp_path / ".env.test"
    override = tmp_path / ".env.test.local"
    base.write_text(
        "KOKORO_AGENT_ENVIRONMENT=test\nKOKORO_AGENT_DATABASE_URL=postgresql://base/db\n"
    )
    override.write_text("KOKORO_AGENT_DATABASE_URL=postgresql://override/db\n")
    assert (
        load_settings((str(base), str(override))).database_url.get_secret_value()
        == "postgresql://override/db"
    )
    monkeypatch.setenv("KOKORO_AGENT_DATABASE_URL", "postgresql://shell/db")
    assert (
        load_settings((str(base), str(override))).database_url.get_secret_value()
        == "postgresql://shell/db"
    )
    with pytest.raises(ValidationError):
        load_settings()  # Explicit production-style loading does not pick up development files.
    monkeypatch.setenv("KOKORO_AGENT_ENVIRONMENT", "test")
    assert load_settings().environment == "test"
    assert "postgresql://shell/db" not in repr(load_settings())


def test_api_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        CreateRunRequest.model_validate({"prompt": "Hello", "tenant_id": "forged"})
    assert CreateRunRequest.model_validate({"prompt": "Hello"}).prompt == "Hello"


def test_structural_dependency_and_fixed_clock():
    saved: list[Run] = []

    class Records:
        async def insert(self, run: Run) -> None:
            saved.append(run)

    now = datetime(2026, 9, 4, tzinfo=UTC)
    run = asyncio.run(
        create_run(
            CreateRun(tenant_id="tenant"),
            records=Records(),
            new_id=lambda: "run",
            clock=lambda: now,
        )
    )
    assert saved == [run]
    assert run.created_at == now


def test_postgresql_schema_uuid_time_and_transaction_rollback():
    identifier = uuid4()
    with psycopg.connect(
        os.environ["HANDBOOK_DATABASE_URL"], autocommit=True
    ) as connection:
        with pytest.raises(RuntimeError, match="rollback"), connection.transaction():
            row = connection.execute(
                "INSERT INTO system_site (id, tenant_id, site_key, display_name) VALUES (%s, %s, %s, %s) RETURNING id, created_at, deleted_at",
                (identifier, uuid4(), "python-example", "Python example"),
            ).fetchone()
            assert row is not None
            assert isinstance(row[0], UUID)
            assert row[1].tzinfo is not None
            assert row[2] is None
            raise RuntimeError("rollback")
        assert (
            connection.execute(
                "SELECT id FROM system_site WHERE id = %s", (identifier,)
            ).fetchone()
            is None
        )

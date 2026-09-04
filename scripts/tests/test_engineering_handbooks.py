from __future__ import annotations

import ast
import json
import re
import tomllib
from pathlib import Path

import pytest

from scripts.governance.handbook_examples import (
    ROOT,
    STANDARDS,
    code_blocks,
    extract_examples,
)


def test_examples_extract_from_the_current_manuals(tmp_path: Path) -> None:
    paths = extract_examples(tmp_path)
    assert len(paths) == 18
    assert (tmp_path / "typescript/src/app.ts").is_file()
    assert (tmp_path / "typescript/src/modules/sites/site.ts").is_file()
    assert (tmp_path / "python/src/kokoro_agent/runs/service.py").is_file()
    for path in paths:
        if path.suffix == ".py":
            ast.parse(path.read_text())
        elif path.suffix == ".json":
            json.loads(path.read_text())
        elif path.suffix == ".toml":
            tomllib.loads(path.read_text())
    with pytest.raises(ValueError, match="empty"):
        extract_examples(tmp_path)


def test_sql_example_does_not_imply_every_table_needs_status_or_constraints() -> None:
    sql = (STANDARDS / "03-sql-and-postgresql.md").read_text()
    schema = code_blocks(sql, "sql")[0]
    for forbidden in (
        "status",
        "version",
        "CHECK",
        "UNIQUE",
        "REFERENCES",
        "FOREIGN KEY",
    ):
        assert forbidden not in schema
    assert "deleted_at TIMESTAMPTZ(3) NULL" in schema
    assert re.search(r"\| `status`\s*\| \*\*默认不加\*\*", sql)
    assert "字符而非字节" in sql


def test_canonical_manuals_have_sources_and_balanced_code_fences() -> None:
    for name in (
        "03-sql-and-postgresql.md",
        "08-typescript-backend-engineering.md",
        "09-python-backend-engineering.md",
    ):
        text = (STANDARDS / name).read_text()
        assert len(re.findall(r"^```", text, re.MULTILINE)) % 2 == 0
        assert "参考依据" in text
        assert "https://" in text
    agents = (ROOT / "AGENTS.md").read_text()
    assert not code_blocks(agents, "ts")
    assert not code_blocks(agents, "python")
    assert not code_blocks(agents, "sql")

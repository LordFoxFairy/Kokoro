from __future__ import annotations

import json
import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATABASE = ROOT / "database"


def test_database_toolchain_is_scoped_and_exactly_pinned() -> None:
    project = tomllib.loads((DATABASE / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"] == {
        "name": "kokoro-database-tooling",
        "version": "0.0.0",
        "requires-python": ">=3.11,<3.14",
        "dependencies": [
            "langgraph-checkpoint-postgres==3.1.0",
            "psycopg[binary]==3.3.4",
        ],
    }
    assert project["dependency-groups"] == {"dev": ["pytest==8.4.2"]}

    package = json.loads((DATABASE / "package.json").read_text(encoding="utf-8"))
    assert package == {
        "name": "kokoro-database-tooling",
        "private": True,
        "packageManager": "pnpm@11.2.2",
        "engines": {"node": ">=22 <25"},
        "devDependencies": {"prisma": "6.19.3"},
    }
    assert (DATABASE / "pnpm-workspace.yaml").read_text(encoding="utf-8") == (
        "allowBuilds:\n"
        "  '@prisma/engines': true\n"
        "  prisma: true\n"
    )


def test_database_lockfiles_pin_the_declared_tools() -> None:
    uv_lock = (DATABASE / "uv.lock").read_text(encoding="utf-8")
    for name, version in (
        ("langgraph-checkpoint-postgres", "3.1.0"),
        ("psycopg", "3.3.4"),
        ("psycopg-binary", "3.3.4"),
        ("pytest", "8.4.2"),
    ):
        assert f'name = "{name}"\nversion = "{version}"' in uv_lock

    pnpm_lock = (DATABASE / "pnpm-lock.yaml").read_text(encoding="utf-8")
    assert "prisma:\n        specifier: 6.19.3\n        version: 6.19.3" in pnpm_lock


def test_database_gitignore_is_precise_and_keeps_sources_visible(tmp_path: Path) -> None:
    expected = (
        "/.venv/\n"
        "/node_modules/\n"
        "/.pytest_cache/\n"
        "/.ruff_cache/\n"
        "/.mypy_cache/\n"
        "**/__pycache__/\n"
        "/baseline/kokoro.sql\n"
        "/baseline/manifest.json\n"
    )
    actual = (DATABASE / ".gitignore").read_text(encoding="utf-8")
    assert actual == expected

    (tmp_path / ".gitignore").write_text(actual, encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    ignored = [
        ".venv/state",
        "node_modules/tool/index.js",
        ".pytest_cache/state",
        ".ruff_cache/state",
        ".mypy_cache/state",
        "tests/__pycache__/test.cpython.pyc",
        "baseline/kokoro.sql",
        "baseline/manifest.json",
    ]
    visible = [
        "schema/00-foundation.sql",
        "slices/slice-a.json",
        "pyproject.toml",
        "uv.lock",
        "package.json",
        "pnpm-lock.yaml",
    ]
    for relative in ignored + visible:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    result = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        cwd=tmp_path,
        input="\n".join(ignored + visible) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == ignored

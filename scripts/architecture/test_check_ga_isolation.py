"""Negative fixtures for the GA isolation gate.

Each case is a realistic way the boundary erodes: a convenience field on a run
request, or a namespace built from a business identity.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from check_ga_isolation import GaIsolationError, run


def write(tmp_path: Path, body: str, name: str = "runtime.py") -> Path:
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / name).write_text(body, encoding="utf-8")
    return src


def test_clean_source_passes(tmp_path: Path) -> None:
    source = write(tmp_path, "def start(namespace: str) -> None:\n    return None\n")
    line = run(source)
    assert line.startswith("ga_isolation_ok:")
    assert "1 GA source files" in line


@pytest.mark.parametrize(
    "axis", ["site_id", "siteId", "owner_id", "ownerId", "workspace_id", "workspaceId", "user_id", "userId"]
)
def test_every_platform_identity_axis_is_rejected(tmp_path: Path, axis: str) -> None:
    source = write(tmp_path, f"def start(namespace: str, {axis}: str) -> None:\n    return None\n")
    with pytest.raises(GaIsolationError) as excinfo:
        run(source)
    assert excinfo.value.code == "ga_isolation_identity_axis"
    assert axis in str(excinfo.value)


@pytest.mark.parametrize("prefix", ["user", "team", "site", "workspace", "owner", "tenant"])
def test_composed_namespace_is_rejected(tmp_path: Path, prefix: str) -> None:
    """A namespace built from a business identity is tenancy in disguise."""
    source = write(tmp_path, f'def ns(identity: str) -> str:\n    return f"{prefix}:{{identity}}"\n')
    with pytest.raises(GaIsolationError) as excinfo:
        run(source)
    assert excinfo.value.code == "ga_isolation_namespace_composed"


def test_opaque_namespace_is_allowed(tmp_path: Path) -> None:
    source = write(tmp_path, 'def ns(value: str) -> str:\n    return f"ns_{value}"\n')
    assert "ga_isolation_ok" in run(source)


def test_all_violations_are_reported_together(tmp_path: Path) -> None:
    source = write(
        tmp_path,
        'def start(site_id: str, userId: str) -> str:\n    return f"team:{site_id}"\n',
    )
    with pytest.raises(GaIsolationError) as excinfo:
        run(source)
    message = str(excinfo.value)
    assert "site_id" in message
    assert "userId" in message
    assert "ga_isolation_namespace_composed" in message


def test_generated_and_cache_directories_are_skipped(tmp_path: Path) -> None:
    src = write(tmp_path, "def start(namespace: str) -> None:\n    return None\n")
    cache = src / "__pycache__"
    cache.mkdir()
    (cache / "stale.py").write_text("site_id = 1\n", encoding="utf-8")
    assert "ga_isolation_ok" in run(src)


def test_missing_source_tree_fails(tmp_path: Path) -> None:
    with pytest.raises(GaIsolationError) as excinfo:
        run(tmp_path / "absent")
    assert excinfo.value.code == "ga_isolation_source_missing"


def test_empty_source_tree_fails(tmp_path: Path) -> None:
    """An empty scan must not be mistaken for a clean one."""
    empty = tmp_path / "src"
    empty.mkdir()
    with pytest.raises(GaIsolationError) as excinfo:
        run(empty)
    assert excinfo.value.code == "ga_isolation_no_sources"

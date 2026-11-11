from __future__ import annotations

import json
import re
import runpy
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_repository_topology_script_declares_exact_remote_named_composition() -> None:
    topology = runpy.run_path(str(ROOT / "scripts/verify-repository-topology.py"))
    assert topology["RUNTIME_MODULES"] == (
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
    modules = topology["MODULES"]
    assert modules["kokoro-app"] == ("apps/kokoro-app", "https://github.com/LordFoxFairy/kokoro-app.git")
    assert modules["kokoro-mori"][0] == "apps/kokoro-mori"
    assert modules["kokoro-admin"] == ("apps/kokoro-admin", "https://github.com/LordFoxFairy/kokoro-admin.git")
    assert "kokoro-admin" not in topology["RUNTIME_MODULES"]
    assert modules["kokoro-web-shared"][0] == "libs/kokoro-web-shared"
    assert "kokoro-model" not in modules


def test_root_metadata_uses_remote_names_without_a_web_alias() -> None:
    status = (ROOT / "docs/REPOSITORY_STATUS.md").read_text()
    codebase_map = (ROOT / "docs/CODEBASE_MAP.md").read_text()
    gitmodules = (ROOT / ".gitmodules").read_text()
    paths = [line.split("=", 1)[1].strip() for line in gitmodules.splitlines() if line.strip().startswith("path =")]
    assert paths == [
        "apps/kokoro-app", "apps/kokoro-mori", "apps/kokoro-bff", "apps/kokoro-agent",
        "apps/kokoro-iam", "apps/kokoro-system", "apps/kokoro-billing", "apps/kokoro-capability",
        "apps/kokoro-storage", "apps/kokoro-scheduler", "libs/kokoro-web-shared", "apps/kokoro-admin",
    ]
    assert "`apps/kokoro-app`" in status
    assert "`apps/kokoro-app`" in codebase_map
    assert "| `apps/kokoro/` |" not in status
    names = re.findall(r'(?m)^\[submodule "([^\"]+)"\]$', gitmodules)
    topology = runpy.run_path(str(ROOT / "scripts/verify-repository-topology.py"))
    assert set(names) == set(topology["MODULES"])
    admin = gitmodules.split('[submodule "kokoro-admin"]', 1)[1]
    assert "branch = main" in admin


def test_root_current_distinguishes_root_governance_tests_from_subrepository_tests() -> None:
    current = (ROOT / "docs/CURRENT.md").read_text()
    assert "子仓的 tests 不迁入 Root" in current
    assert "`scripts/tests/` 只覆盖 Root 治理脚本" in current
    assert "`verification/`" in current


def test_model_retirement_keeps_it_out_of_active_composition() -> None:
    topology = runpy.run_path(str(ROOT / "scripts/verify-repository-topology.py"))
    assert "kokoro-model" not in topology["MODULES"]
    assert "kokoro-model" in topology["ARCHIVED"]
    clone = (ROOT / "deploy/clone-active-repositories.sh").read_text()
    assert '"kokoro-model|kokoro-model"' not in clone



def test_codebase_map_keeps_scheduler_postgres_truth() -> None:
    map_text = (ROOT / "docs/ARCHITECTURE_STANDARD.md").read_text()
    assert "Scheduler" in map_text
    assert "PostgreSQL" in map_text


def test_active_production_plan_keeps_nine_runtime_owners() -> None:
    plan = (ROOT / "docs/superpowers/plans/2026-09-03-kokoro-production-closure.md").read_text()
    scope = plan.split("## 1. 范围与完成定义", 1)[1].split("## 2. 固定架构裁决", 1)[0]
    repositories = re.findall(r"(?m)^\d+\. `([^`]+)`", scope)
    assert repositories == [
        "kokoro", "kokoro-bff", "kokoro-agent", "kokoro-iam", "kokoro-system",
        "kokoro-billing", "kokoro-capability", "kokoro-storage", "kokoro-scheduler",
    ]
    assert "model-catalog" in scope


@pytest.mark.parametrize("head_matches_gitlink", [True, False])
def test_pinned_detached_checkout_and_other_topic_are_valid_but_wrong_pin_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], head_matches_gitlink: bool
) -> None:
    """Composition follows the recorded commit, not branch-name cleanup policy."""
    checkout = tmp_path / "root"
    child = checkout / "apps/fixture"
    remote = tmp_path / "origin.git"
    child.mkdir(parents=True)

    def git(*args: str, cwd: Path = checkout) -> str:
        return subprocess.check_output(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args],
            cwd=cwd, text=True, stderr=subprocess.DEVNULL,
        ).strip()

    git("init", "-q", "-b", "main")
    git("init", "-q", "-b", "main", cwd=child)
    git("config", "user.name", "Fixture", cwd=child)
    git("config", "user.email", "fixture@example.test", cwd=child)
    (child / "source.txt").write_text("pinned\n")
    git("add", "source.txt", cwd=child)
    git("commit", "-qm", "fixture", cwd=child)
    pin = git("rev-parse", "HEAD", cwd=child)
    git("branch", "codex/other-owner", cwd=child)
    git("clone", "--bare", "--quiet", str(child), str(remote))
    git("remote", "add", "origin", str(remote), cwd=child)
    git("checkout", "--detach", "--quiet", cwd=child)
    if not head_matches_gitlink:
        (child / "source.txt").write_text("different commit\n")
        git("add", "source.txt", cwd=child)
        git("commit", "-qm", "different", cwd=child)

    for key, value in (("path", "apps/fixture"), ("url", str(remote)), ("branch", "main")):
        git("config", "--file", ".gitmodules", f"submodule.fixture.{key}", value)
    git("add", ".gitmodules")
    git("update-index", "--add", "--cacheinfo", f"160000,{pin},apps/fixture")
    assert git("branch", "--show-current", cwd=child) == ""
    assert git("--git-dir", str(remote), "show-ref", "--verify", "refs/heads/codex/other-owner")

    topology = runpy.run_path(str(ROOT / "scripts/verify-repository-topology.py"))
    main = topology["main"]
    globals_ = main.__globals__
    real_run = topology["run"]
    monkeypatch.setitem(globals_, "ROOT", checkout)
    monkeypatch.setitem(globals_, "MODULES", {"fixture": ("apps/fixture", str(remote))})
    monkeypatch.setitem(globals_, "RUNTIME_MODULES", ("fixture",))
    monkeypatch.setitem(globals_, "ARCHIVED", frozenset())
    monkeypatch.setitem(globals_, "run", lambda *args, cwd=checkout: real_run(*args, cwd=cwd))
    assert main([]) == (0 if head_matches_gitlink else 1)
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["status"] == ("PASS" if head_matches_gitlink else "FAIL")
    if not head_matches_gitlink:
        assert evidence["errors"] == ["fixture: checkout HEAD differs from recorded gitlink"]

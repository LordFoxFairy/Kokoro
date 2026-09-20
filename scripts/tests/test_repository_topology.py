from __future__ import annotations

import re
import runpy
import subprocess
import sys
from pathlib import Path

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
        "apps/kokoro-storage", "apps/kokoro-scheduler", "libs/kokoro-web-shared",
    ]
    assert "`apps/kokoro-app`" in status
    assert "`apps/kokoro-app`" in codebase_map
    assert "| `apps/kokoro/` |" not in status


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


def test_unsafe_legacy_runners_are_paused_before_touching_infrastructure() -> None:
    for relative, interpreter in (
        ("scripts/e2e/run_stage2_owner_health.py", sys.executable),
        ("scripts/verify-ten-repository-full.sh", "bash"),
    ):
        path = ROOT / relative
        source = path.read_text()
        assert "FLUSHDB" not in source and "DROP DATABASE" not in source
        assert "VERIFICATION_ENTRY_PAUSED" in source
        result = subprocess.run([interpreter, str(path)], capture_output=True, text=True, timeout=5)
        assert result.returncode == 2
        assert "VERIFICATION_ENTRY_PAUSED" in result.stderr
        assert "run_system_owner_smoke.py" in result.stderr


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

from pathlib import Path


def test_repository_topology_script_exists() -> None:
    path = Path(__file__).parents[1] / "verify-repository-topology.py"
    assert path.is_file()


def test_model_retirement_keeps_checkout_without_active_or_archive_classification() -> (
    None
):
    import runpy

    root = Path(__file__).resolve().parents[2]
    topology = runpy.run_path(str(root / "scripts/verify-repository-topology.py"))
    assert "kokoro-model" not in topology["ACTIVE"]
    assert "kokoro-model" not in topology["ARCHIVED"]
    assert len(topology["ACTIVE"]) == 9
    assert topology["ACTIVE"]["kokoro-system"].endswith("kokoro-system.git")
    clone = (root / "deploy/clone-active-repositories.sh").read_text()
    assert '"kokoro-model|kokoro-model"' not in clone


def test_model_retirement_covers_active_verification_and_owner_processes() -> None:
    root = Path(__file__).resolve().parents[2]
    for path in (
        "scripts/audit-repository-state.py",
        "scripts/e2e/run_stage2_owner_health.py",
        "scripts/verify-ten-repository-full.sh",
    ):
        assert "kokoro-model" not in (root / path).read_text(), path
    full = (root / "scripts/verify-ten-repository-full.sh").read_text()
    assert "MODEL_DATABASE_URL" not in full
    assert "kokoro_gate_model" not in full


def test_unsafe_legacy_runners_are_paused_before_touching_infrastructure() -> None:
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[2]
    for relative, interpreter in (
        ("scripts/e2e/run_stage2_owner_health.py", sys.executable),
        ("scripts/verify-ten-repository-full.sh", "bash"),
    ):
        path = root / relative
        source = path.read_text()
        # Inspect before executing: the RED run must never execute the old cleanup.
        assert "FLUSHDB" not in source and "DROP DATABASE" not in source
        assert "VERIFICATION_ENTRY_PAUSED" in source
        result = subprocess.run(
            [interpreter, str(path)], capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 2
        assert "VERIFICATION_ENTRY_PAUSED" in result.stderr
        assert "run_system_owner_smoke.py" in result.stderr


def test_codebase_map_does_not_replace_scheduler_postgres_truth() -> None:
    root = Path(__file__).resolve().parents[2]
    map_text = (root / "docs/CODEBASE_MAP.md").read_text()
    scheduler_row = next(
        line
        for line in map_text.splitlines()
        if line.startswith("| `kokoro-scheduler` |")
    )
    assert "PostgreSQL" in scheduler_row
    assert "no business DB" not in scheduler_row


def test_current_web_path_is_not_claimed_as_an_apps_gitlink() -> None:
    root = Path(__file__).resolve().parents[2]
    status = (root / "docs/REPOSITORY_STATUS.md").read_text()
    gitmodules = (root / ".gitmodules").read_text()
    codebase_map = (root / "docs/CODEBASE_MAP.md").read_text()
    assert "| kokoro | LordFoxFairy/kokoro-app |" in status
    paths = [
        line.split("=", 1)[1].strip()
        for line in gitmodules.splitlines()
        if line.strip().startswith("path =")
    ]
    # An approved Submodule cutover must update this assertion with .gitmodules and map changes.
    assert paths == ["kokoro-agent"]
    assert "当前九个正式运行仓只有 `kokoro-agent` 通过 Root gitlink 声明" in codebase_map
    assert "目标 `apps/` 部署容器及其 Git 路径尚未实施" in codebase_map
    assert "当前 Web 仍位于 `kokoro/`" in codebase_map


def test_root_current_marks_apps_and_full_gate_as_unfinished() -> None:
    root = Path(__file__).resolve().parents[2]
    current = (root / "docs/CURRENT.md").read_text()
    assert "`apps/` 尚未实施" in current
    assert "`scripts/verify-ten-repository-full.sh` 仍暂停" in current


def test_repository_status_lists_exact_nine_directories_and_web_remote() -> None:
    root = Path(__file__).resolve().parents[2]
    status = (root / "docs/REPOSITORY_STATUS.md").read_text()
    table = status.split("## 正式仓库与 GitHub 映射", 1)[1].split("## 归属裁决", 1)[0]
    rows = [line for line in table.splitlines() if line.startswith("| kokoro")]
    assert len(rows) == 9
    names = [row.split("|", 2)[1].strip() for row in rows]
    assert names == [
        "kokoro",
        "kokoro-bff",
        "kokoro-agent",
        "kokoro-iam",
        "kokoro-system",
        "kokoro-billing",
        "kokoro-capability",
        "kokoro-storage",
        "kokoro-scheduler",
    ]
    assert "| kokoro | LordFoxFairy/kokoro-app |" in rows[0]
    assert "仅 Agent 是 Root gitlink" in status

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

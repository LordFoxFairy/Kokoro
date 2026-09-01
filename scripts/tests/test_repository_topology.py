from pathlib import Path


def test_repository_topology_script_exists() -> None:
    path = Path(__file__).parents[1] / "verify-repository-topology.py"
    assert path.is_file()

from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from contract.generate import GenerationError, generate_consumer, main


MANIFEST = json.loads((ROOT / "contract/slice-a-contract-manifest.yaml").read_text())
CONSUMERS = json.loads((ROOT / "contract/consumers.yaml").read_text())


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, text=True, capture_output=True).stdout.strip()


@pytest.fixture
def committed_source(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "source"
    source.mkdir()
    for relative in (
        ".node-version",
        "package.json",
        "pnpm-lock.yaml",
        "pnpm-workspace.yaml",
        "pyproject.toml",
        "uv.lock",
        "contract/slice-a-contract-manifest.yaml",
        "contract/validate_slice_a_manifest.py",
        "contract/consumers.yaml",
        "contract/openapi/slice-a-web-v1.yaml",
        "contract/generate.py",
    ):
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    shutil.copytree(ROOT / "contract/proto", source / "contract/proto")
    _git(source, "init", "-q")
    _git(source, "config", "user.email", "contract@example.invalid")
    _git(source, "config", "user.name", "Contract Test")
    _git(source, "add", ".")
    _git(source, "commit", "-qm", "fixture")
    return source, _git(source, "rev-parse", "HEAD")


def test_consumer_registry_is_exact_machine_closure() -> None:
    assert CONSUMERS["version"] == 1
    assert set(CONSUMERS["consumers"]) == set(MANIFEST["consumerFileClosure"])
    for name, closure in MANIFEST["consumerFileClosure"].items():
        assert CONSUMERS["consumers"][name]["protoFiles"] == closure


def test_python_generation_is_deterministic_provenanced_and_checkable(
    committed_source: tuple[Path, str], tmp_path: Path
) -> None:
    source, commit = committed_source
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir(); second.mkdir()
    first_provenance = generate_consumer(
        source_root=source, source_commit=commit, consumer="root-e2e", repo=first, check=False
    )
    second_provenance = generate_consumer(
        source_root=source, source_commit=commit, consumer="root-e2e", repo=second, check=False
    )
    first_output = first / "scripts/e2e/generated"
    second_output = second / "scripts/e2e/generated"
    assert first_provenance == second_provenance
    assert {
        path.relative_to(first_output).as_posix(): path.read_bytes()
        for path in first_output.rglob("*") if path.is_file()
    } == {
        path.relative_to(second_output).as_posix(): path.read_bytes()
        for path in second_output.rglob("*") if path.is_file()
    }
    assert first_provenance["sourceRootCommit"] == commit
    assert first_provenance["manifestSha256"] == hashlib.sha256(
        (source / "contract/slice-a-contract-manifest.yaml").read_bytes()
    ).hexdigest()
    assert set(first_provenance["registeredSourceSha256"]) == {
        ".node-version", "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml",
        "pyproject.toml", "uv.lock", "contract/slice-a-contract-manifest.yaml",
        "contract/validate_slice_a_manifest.py", "contract/consumers.yaml",
        "contract/openapi/slice-a-web-v1.yaml", "contract/generate.py",
        *(f"contract/proto/{item['path']}" for item in MANIFEST["protobuf"]["files"]),
    }
    assert not any(part in {"agent", "model", "capability"} for path in first_output.rglob("*") for part in path.parts)
    assert all(
        path.read_text().startswith("# GENERATED — DO NOT EDIT. Source Root commit:")
        for path in first_output.rglob("*.py")
    )
    sys.path.insert(0, str(first))
    try:
        importlib.import_module("scripts.e2e.generated.kokoro.chat.v1.chat_pb2_grpc")
    finally:
        sys.path.remove(str(first))
    generate_consumer(
        source_root=source, source_commit=commit, consumer="root-e2e", repo=first, check=True
    )
    generated = next(first_output.rglob("*_pb2.py"))
    generated.write_text(generated.read_text() + "# drift\n")
    with pytest.raises(GenerationError, match="consumer output drift"):
        generate_consumer(
            source_root=source, source_commit=commit, consumer="root-e2e", repo=first, check=True
        )


def test_typescript_web_generation_contains_only_public_closure(
    committed_source: tuple[Path, str], tmp_path: Path
) -> None:
    source, commit = committed_source
    repo = tmp_path / "web"; repo.mkdir()
    generate_consumer(source_root=source, source_commit=commit, consumer="kokoro-web", repo=repo, check=False)
    output = repo / "apps/user/src/generated/proto"
    assert (output / "http/slice-a-web-v1.yaml").is_file()
    assert list(output.rglob("*_pb.ts"))
    assert not any(part in {"agent", "model", "capability"} for path in output.rglob("*") for part in path.parts)


def test_generation_rejects_unknown_consumer_and_dirty_source(
    committed_source: tuple[Path, str], tmp_path: Path
) -> None:
    source, commit = committed_source
    repo = tmp_path / "repo"; repo.mkdir()
    with pytest.raises(GenerationError, match="unknown consumer"):
        generate_consumer(source_root=source, source_commit=commit, consumer="unknown", repo=repo, check=False)
    manifest = source / "contract/slice-a-contract-manifest.yaml"
    manifest.write_text(manifest.read_text() + "\n")
    with pytest.raises(GenerationError, match="registered contract source is dirty"):
        generate_consumer(source_root=source, source_commit=commit, consumer="root-e2e", repo=repo, check=False)


def test_generation_rejects_symlink_output(
    committed_source: tuple[Path, str], tmp_path: Path
) -> None:
    source, commit = committed_source
    repo = tmp_path / "repo"; repo.mkdir()
    outside = tmp_path / "outside"; outside.mkdir()
    (repo / "scripts").symlink_to(outside, target_is_directory=True)
    with pytest.raises(GenerationError, match="traverses symlink"):
        generate_consumer(source_root=source, source_commit=commit, consumer="root-e2e", repo=repo, check=False)


def test_failed_check_does_not_create_consumer_directories(
    committed_source: tuple[Path, str], tmp_path: Path
) -> None:
    source, commit = committed_source
    repo = tmp_path / "repo"; repo.mkdir()
    before = sorted(path.relative_to(repo).as_posix() for path in repo.rglob("*"))
    with pytest.raises(GenerationError, match="consumer output drift"):
        generate_consumer(source_root=source, source_commit=commit, consumer="root-e2e", repo=repo, check=True)
    assert sorted(path.relative_to(repo).as_posix() for path in repo.rglob("*")) == before


def test_check_rejects_symlink_inside_existing_generated_tree(
    committed_source: tuple[Path, str], tmp_path: Path
) -> None:
    source, commit = committed_source
    repo = tmp_path / "repo"; repo.mkdir()
    generate_consumer(source_root=source, source_commit=commit, consumer="root-e2e", repo=repo, check=False)
    generated = repo / "scripts/e2e/generated"
    victim = next(generated.rglob("site_pb2.py"))
    outside = tmp_path / "outside.py"
    outside.write_bytes(victim.read_bytes())
    victim.unlink()
    victim.symlink_to(outside)
    with pytest.raises(GenerationError, match="symlink in generated output"):
        generate_consumer(source_root=source, source_commit=commit, consumer="root-e2e", repo=repo, check=True)


def test_generation_rejects_dirty_toolchain_and_runtime_registry_drift(
    committed_source: tuple[Path, str], tmp_path: Path
) -> None:
    source, commit = committed_source
    repo = tmp_path / "repo"; repo.mkdir()
    pyproject = source / "pyproject.toml"
    pyproject.write_text(pyproject.read_text() + "\n")
    with pytest.raises(GenerationError, match="registered contract source is dirty"):
        generate_consumer(source_root=source, source_commit=commit, consumer="root-e2e", repo=repo, check=False)
    _git(source, "checkout", "--", "pyproject.toml")
    registry = json.loads((source / "contract/consumers.yaml").read_text())
    registry["consumers"]["kokoro-web"]["protoFiles"].append("kokoro/agent/v1/agent_runtime.proto")
    (source / "contract/consumers.yaml").write_text(json.dumps(registry, indent=2) + "\n")
    _git(source, "add", "contract/consumers.yaml")
    _git(source, "commit", "-qm", "drift registry")
    drift_commit = _git(source, "rev-parse", "HEAD")
    with pytest.raises(GenerationError, match="consumer closure differs from machine authority"):
        generate_consumer(source_root=source, source_commit=drift_commit, consumer="kokoro-web", repo=repo, check=False)


def test_generation_requires_source_root_to_be_git_top_level(
    committed_source: tuple[Path, str], tmp_path: Path
) -> None:
    source, commit = committed_source
    repo = tmp_path / "repo"; repo.mkdir()
    manifest = source / "contract/slice-a-contract-manifest.yaml"
    manifest.write_text(manifest.read_text() + "\n")
    with pytest.raises(GenerationError, match="source root must be the Git top-level"):
        generate_consumer(
            source_root=source / "contract", source_commit=commit,
            consumer="root-e2e", repo=repo, check=False,
        )


def test_all_requires_exact_repo_map_before_generation(
    committed_source: tuple[Path, str], tmp_path: Path
) -> None:
    source, commit = committed_source
    partial = tmp_path / "partial.json"
    partial.write_text(json.dumps({"root-e2e": str(tmp_path / "repo")}) + "\n")
    with pytest.raises(GenerationError, match="every declared consumer exactly once"):
        main([
            "--source-root", str(source), "--source-commit", commit,
            "--all", "--repo-map", str(partial), "--check",
        ])
    extra = {name: str(tmp_path / name) for name in CONSUMERS["consumers"]}
    extra["unknown"] = str(tmp_path / "unknown")
    extra_path = tmp_path / "extra.json"
    extra_path.write_text(json.dumps(extra) + "\n")
    with pytest.raises(GenerationError, match="every declared consumer exactly once"):
        main([
            "--source-root", str(source), "--source-commit", commit,
            "--all", "--repo-map", str(extra_path), "--check",
        ])

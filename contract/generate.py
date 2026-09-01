#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parents[1]))
from contract.validate_slice_a_manifest import validate as validate_manifest


ROOT = Path(__file__).parents[1]
REGISTERED_SOURCE_PATHS = (
    ".node-version",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "pyproject.toml",
    "uv.lock",
    "contract/slice-a-contract-manifest.yaml",
    "contract/validate_slice_a_manifest.py",
    "contract/consumers.yaml",
    "contract/buf.gen.yaml",
    "contract/proto",
    "contract/openapi/slice-a-web-v1.yaml",
    "contract/generate.py",
)
RUNTIME_SOURCE_FILES = (
    ".node-version",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "pyproject.toml",
    "uv.lock",
    "contract/validate_slice_a_manifest.py",
    "contract/buf.gen.yaml",
    "contract/generate.py",
)
EXPECTED_CONSUMER_POLICY = {
    "kokoro-system": ("typescript", "src/generated/proto", False),
    "kokoro-iam": ("typescript", "src/generated/proto", False),
    "kokoro-model": ("typescript", "src/generated/proto", False),
    "kokoro-capability": ("typescript", "src/generated/proto", False),
    "kokoro-storage": ("typescript", "src/generated/proto", False),
    "kokoro-bff": ("typescript", "src/generated/proto", False),
    "kokoro-agent": ("python", "src/kokoro_agent/generated", False),
    "kokoro": ("typescript", "src/generated/proto", True),
    "root-e2e": ("python", "scripts/e2e/generated", False),
}


class GenerationError(RuntimeError):
    pass


def _run(command: list[str], *, cwd: Path, capture: bool = False) -> str:
    completed = subprocess.run(command, cwd=cwd, check=False, text=True, capture_output=capture)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "command failed").strip()
        raise GenerationError(f"generator command failed: {' '.join(command)}: {detail}")
    return completed.stdout.strip() if capture else ""


def _git(root: Path, *args: str) -> str:
    return _run(["git", *args], cwd=root, capture=True)


def _read_commit_file(root: Path, commit: str, relative: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode:
        raise GenerationError(f"registered source missing at {commit}: {relative}")
    return completed.stdout


def _load_json_bytes(data: bytes, name: str) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"invalid JSON-compatible YAML: {name}: {exc}") from exc
    if not isinstance(value, dict):
        raise GenerationError(f"source root must be object: {name}")
    return value


def _verify_source(source_root: Path, source_commit: str) -> tuple[str, str]:
    source_root = source_root.resolve()
    git_top_level = Path(_git(source_root, "rev-parse", "--show-toplevel")).resolve()
    if source_root != git_top_level:
        raise GenerationError(
            f"source root must be the Git top-level: expected {git_top_level}, got {source_root}"
        )
    commit = _git(source_root, "rev-parse", "--verify", f"{source_commit}^{{commit}}")
    tree = _git(source_root, "rev-parse", f"{commit}^{{tree}}")
    dirty = _git(source_root, "status", "--porcelain", "--", *REGISTERED_SOURCE_PATHS)
    if dirty:
        raise GenerationError(f"registered contract source is dirty: {dirty.splitlines()[0]}")
    drift = subprocess.run(
        ["git", "diff", "--quiet", commit, "HEAD", "--", *REGISTERED_SOURCE_PATHS],
        cwd=source_root,
        check=False,
    )
    if drift.returncode not in {0, 1}:
        raise GenerationError("failed to compare registered source with the requested commit")
    if drift.returncode == 1:
        raise GenerationError("checked-out registered source differs from requested source commit")
    return commit, tree


def _materialize_sources(source_root: Path, commit: str, target: Path, proto_files: list[str], include_openapi: bool) -> tuple[bytes, bytes]:
    manifest_bytes = _read_commit_file(source_root, commit, "contract/slice-a-contract-manifest.yaml")
    consumers_bytes = _read_commit_file(source_root, commit, "contract/consumers.yaml")
    for relative in proto_files:
        destination = target / "proto" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(_read_commit_file(source_root, commit, f"contract/proto/{relative}"))
    if include_openapi:
        destination = target / "openapi/slice-a-web-v1.yaml"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(_read_commit_file(source_root, commit, "contract/openapi/slice-a-web-v1.yaml"))
    return manifest_bytes, consumers_bytes


def _validate_registry(consumers: dict[str, Any], manifest: dict[str, Any]) -> None:
    if consumers.get("version") != 1 or set(consumers) != {"version", "consumers"}:
        raise GenerationError("consumer registry version or shape drift")
    entries = consumers.get("consumers")
    if not isinstance(entries, dict) or set(entries) != set(EXPECTED_CONSUMER_POLICY):
        raise GenerationError("consumer registry inventory drift")
    if set(entries) != set(manifest.get("consumerFileClosure", {})):
        raise GenerationError("consumer registry differs from machine authority")
    for name, policy in EXPECTED_CONSUMER_POLICY.items():
        entry = entries[name]
        if not isinstance(entry, dict) or set(entry) != {"language", "output", "includeOpenApi", "protoFiles"}:
            raise GenerationError(f"consumer registry shape drift: {name}")
        if (entry["language"], entry["output"], entry["includeOpenApi"]) != policy:
            raise GenerationError(f"consumer runtime policy drift: {name}")
        if entry["protoFiles"] != manifest["consumerFileClosure"][name]:
            raise GenerationError(f"consumer closure differs from machine authority: {name}")
        if any(Path(path).is_absolute() or ".." in Path(path).parts for path in entry["protoFiles"]):
            raise GenerationError(f"unsafe proto path in consumer closure: {name}")


def _registered_source_hashes(source_root: Path, commit: str, manifest: dict[str, Any]) -> dict[str, str]:
    files = [
        *RUNTIME_SOURCE_FILES,
        "contract/slice-a-contract-manifest.yaml",
        "contract/consumers.yaml",
        "contract/buf.gen.yaml",
        "contract/openapi/slice-a-web-v1.yaml",
        *(f"contract/proto/{item['path']}" for item in manifest["protobuf"]["files"]),
    ]
    return {
        relative: hashlib.sha256(_read_commit_file(source_root, commit, relative)).hexdigest()
        for relative in files
    }


def _verify_runtime_sources(source_root: Path, commit: str) -> None:
    validator_path = Path(validate_manifest.__code__.co_filename).resolve()
    running = {
        **{relative: (ROOT / relative).read_bytes() for relative in RUNTIME_SOURCE_FILES},
        "contract/validate_slice_a_manifest.py": validator_path.read_bytes(),
    }
    for relative, actual in running.items():
        if actual != _read_commit_file(source_root, commit, relative):
            raise GenerationError(f"running contract tool differs from requested source commit: {relative}")


def _tool_versions() -> dict[str, str]:
    protobuf = importlib.metadata.version("protobuf")
    grpc_tools = importlib.metadata.version("grpcio-tools")
    plugin = ROOT / "node_modules/.bin/protoc-gen-es"
    if not plugin.is_file():
        raise GenerationError(f"local protoc-gen-es missing: {plugin}")
    plugin_version = _run([str(plugin), "--version"], cwd=ROOT, capture=True).removeprefix("protoc-gen-es v")
    actual = {"protobuf": protobuf, "grpcio-tools": grpc_tools, "protoc-gen-es": plugin_version}
    expected = {"protobuf": "6.33.6", "grpcio-tools": "1.76.0", "protoc-gen-es": "2.14.0"}
    if actual != expected:
        raise GenerationError(f"contract tool version drift: expected {expected}, got {actual}")
    return actual


def _prepend_generated_header(path: Path, source_commit: str, manifest_sha: str) -> None:
    if path.suffix not in {".py", ".ts"}:
        return
    marker = "#" if path.suffix == ".py" else "//"
    header = (
        f"{marker} GENERATED — DO NOT EDIT. Source Root commit: {source_commit}\n"
        f"{marker} Manifest SHA-256: {manifest_sha}\n"
    ).encode()
    path.write_bytes(header + path.read_bytes())


def _normalize_generated_text(path: Path) -> None:
    """Keep protoc output deterministic across generators and platforms."""
    if path.suffix not in {".py", ".ts"}:
        return
    text = path.read_text(encoding="utf-8")
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    normalized = "\n".join(lines) + "\n"
    path.write_text(normalized, encoding="utf-8")


def _ensure_python_packages(output: Path) -> None:
    directories = {path.parent for path in output.rglob("*.py")}
    for directory in sorted(directories):
        current = directory
        while current != output.parent and output in (current, *current.parents):
            directories.add(current)
            if current == output:
                break
            current = current.parent
    for directory in sorted(directories):
        init = directory / "__init__.py"
        if not init.exists():
            init.write_text("")


def _generate_language(language: str, materialized: Path, output: Path, proto_files: list[str]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    proto_root = materialized / "proto"
    if language == "python":
        command = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{proto_root}",
            f"--python_out={output}",
            f"--grpc_python_out={output}",
            *proto_files,
        ]
    elif language == "typescript":
        plugin = ROOT / "node_modules/.bin/protoc-gen-es"
        if not plugin.is_file():
            raise GenerationError(f"local protoc-gen-es missing: {plugin}")
        command = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{proto_root}",
            f"--plugin=protoc-gen-es={plugin}",
            f"--es_out={output}",
            "--es_opt=target=ts,import_extension=js",
            *proto_files,
        ]
    else:
        raise GenerationError(f"unsupported consumer language: {language}")
    _run(command, cwd=proto_root)


def _rewrite_python_imports(output: Path) -> None:
    for path in output.rglob("*.py"):
        lines = []
        for line in path.read_text().splitlines(keepends=True):
            if line.startswith("from kokoro."):
                line = "from ..." + line.removeprefix("from kokoro.")
            lines.append(line)
        path.write_text("".join(lines))


def _hash_outputs(output: Path) -> dict[str, str]:
    return {
        path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "provenance.json"
    }


def _generated_files(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise GenerationError(f"symlink in generated output: {path}")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def _atomic_replace(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{destination.name}.replace-", dir=destination.parent) as temporary:
        backup = Path(temporary) / "previous"
        if destination.exists():
            os.replace(destination, backup)
        try:
            os.replace(source, destination)
        except BaseException:
            if backup.exists():
                os.replace(backup, destination)
            raise


def _require_safe_output(repo: Path, output_relative: Path) -> Path:
    if not repo.is_dir() or repo.is_symlink():
        raise GenerationError(f"consumer repository must be a real directory: {repo}")
    if output_relative in {Path(""), Path(".")} or output_relative.is_absolute() or ".." in output_relative.parts:
        raise GenerationError(f"unsafe consumer output: {output_relative}")
    current = repo
    for part in output_relative.parts:
        current = current / part
        if current.is_symlink():
            raise GenerationError(f"consumer output traverses symlink: {current}")
    if current.exists() and not current.is_dir():
        raise GenerationError(f"consumer output is not a directory: {current}")
    return current


def generate_consumer(
    *,
    source_root: Path,
    source_commit: str,
    consumer: str,
    repo: Path,
    check: bool,
) -> dict[str, Any]:
    commit, tree = _verify_source(source_root, source_commit)
    _verify_runtime_sources(source_root, commit)
    committed_generator = _read_commit_file(source_root, commit, "contract/generate.py")
    manifest_bytes = _read_commit_file(source_root, commit, "contract/slice-a-contract-manifest.yaml")
    consumers_bytes = _read_commit_file(source_root, commit, "contract/consumers.yaml")
    manifest = _load_json_bytes(manifest_bytes, "contract/slice-a-contract-manifest.yaml")
    validate_manifest(manifest)
    consumers = _load_json_bytes(consumers_bytes, "contract/consumers.yaml")
    _validate_registry(consumers, manifest)
    registered_source_hashes = _registered_source_hashes(source_root, commit, manifest)
    entries = consumers.get("consumers", {})
    if consumer not in entries:
        raise GenerationError(f"unknown consumer: {consumer}")
    entry = entries[consumer]
    output_relative = Path(entry["output"])
    repo = repo.absolute()
    destination = _require_safe_output(repo, output_relative)
    temporary_parent = None
    if not check:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_parent = destination.parent
    with tempfile.TemporaryDirectory(prefix=f".kokoro-contract-{consumer}-", dir=temporary_parent) as temporary:
        work = Path(temporary)
        materialized = work / "source"
        generated = work / "generated"
        manifest_bytes, committed_consumers = _materialize_sources(
            source_root,
            commit,
            materialized,
            list(entry["protoFiles"]),
            bool(entry["includeOpenApi"]),
        )
        if committed_consumers != consumers_bytes:
            raise GenerationError("consumer registry source drift")
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        tools = _tool_versions()
        _generate_language(entry["language"], materialized, generated, list(entry["protoFiles"]))
        if entry["language"] == "python":
            _rewrite_python_imports(generated)
            _ensure_python_packages(generated)
        for path in generated.rglob("*"):
            if path.is_file():
                _prepend_generated_header(path, commit, manifest_sha)
                _normalize_generated_text(path)
        if entry["includeOpenApi"]:
            http = generated / "http/slice-a-web-v1.yaml"
            http.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(materialized / "openapi/slice-a-web-v1.yaml", http)
        provenance = {
            "consumer": consumer,
            "sourceRootCommit": commit,
            "sourceRootTree": tree,
            "manifestSha256": manifest_sha,
            "language": entry["language"],
            "protoFiles": entry["protoFiles"],
            "outputs": _hash_outputs(generated),
            "tools": tools,
            "generatorSha256": hashlib.sha256(committed_generator).hexdigest(),
            "registeredSourceSha256": registered_source_hashes,
        }
        (generated / "provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
        if check:
            expected = _generated_files(generated)
            actual = _generated_files(destination) if destination.is_dir() else {}
            if expected != actual:
                raise GenerationError(f"consumer output drift: {consumer}: {output_relative}")
        else:
            staged = work / "staged-output"
            os.replace(generated, staged)
            _atomic_replace(staged, destination)
    return provenance


def _parse_repo_map(path: Path) -> dict[str, Path]:
    value = _load_json_bytes(path.read_bytes(), str(path))
    return {name: Path(repo) for name, repo in value.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--consumer")
    selection.add_argument("--all", action="store_true")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--repo-map", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.consumer:
        if args.repo is None or args.repo_map is not None:
            parser.error("--consumer requires --repo and forbids --repo-map")
        generate_consumer(
            source_root=args.source_root,
            source_commit=args.source_commit,
            consumer=args.consumer,
            repo=args.repo,
            check=args.check,
        )
        print(f"consumer_generated:{args.consumer}")
    else:
        if args.repo_map is None or args.repo is not None:
            parser.error("--all requires --repo-map and forbids --repo")
        if not args.check:
            parser.error("--all is check-only; generate consumers individually to avoid cross-repository partial writes")
        repo_map = _parse_repo_map(args.repo_map)
        if set(repo_map) != set(EXPECTED_CONSUMER_POLICY):
            raise GenerationError("--all repo-map must contain every declared consumer exactly once")
        for consumer, repo in sorted(repo_map.items()):
            generate_consumer(
                source_root=args.source_root,
                source_commit=args.source_commit,
                consumer=consumer,
                repo=repo,
                check=args.check,
            )
        print(f"consumers_generated:{len(repo_map)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

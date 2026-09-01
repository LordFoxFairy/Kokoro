from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import NoReturn


class ManifestError(ValueError):
    """The checked Slice manifest and its SQL source set disagree."""


def _manifest_path(root: Path, slice_name: str) -> Path:
    return root / "database" / "slices" / f"{slice_name}.json"


def _load_manifest(root: Path, slice_name: str) -> dict[str, object]:
    path = _manifest_path(root, slice_name)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError(f"cannot read manifest {path}: {error}") from error
    if not isinstance(raw, dict):
        raise ManifestError("manifest root must be an object")
    if raw.get("slice") != slice_name:
        raise ManifestError(f"manifest slice must be {slice_name!r}")
    segments = raw.get("segments")
    if (
        not isinstance(segments, list)
        or not segments
        or not all(isinstance(segment, str) and segment for segment in segments)
        or len(segments) != len(set(segments))
    ):
        raise ManifestError("manifest segments must be a non-empty unique string list")
    return raw


def _normalize_sql(raw: bytes) -> bytes:
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return normalized.rstrip(b"\n") + b"\n"


def _source_segments(
    root: Path, manifest: dict[str, object]
) -> list[tuple[str, Path, bytes, str]]:
    schema_dir = root / "database" / "schema"
    segments = manifest["segments"]
    assert isinstance(segments, list)
    expected_names = {f"{segment}.sql" for segment in segments}
    # Every SQL file in this directory is part of the active PostgreSQL
    # baseline. Owner-specific migrations live in their child repository.
    actual_names = {
        entry.name for entry in schema_dir.iterdir()
        if entry.name.endswith(".sql")
    } if schema_dir.is_dir() else set()
    missing = sorted(expected_names - actual_names)
    extra = sorted(actual_names - expected_names)
    if missing:
        raise ManifestError(f"missing manifest SQL segments: {', '.join(missing)}")
    if extra:
        raise ManifestError(f"extra SQL segments outside manifest: {', '.join(extra)}")

    sources: list[tuple[str, Path, bytes, str]] = []
    for segment in segments:
        assert isinstance(segment, str)
        path = schema_dir / f"{segment}.sql"
        if path.is_symlink():
            raise ManifestError(f"symlink SQL segment is forbidden: {path}")
        try:
            normalized = _normalize_sql(path.read_bytes())
        except OSError as error:
            raise ManifestError(f"cannot read SQL segment {path}: {error}") from error
        digest = hashlib.sha256(normalized).hexdigest()
        sources.append((segment, path, normalized, digest))
    return sources


def compose_baseline(root: Path, slice_name: str = "slice-a") -> bytes:
    """Compose the complete checked segment set into deterministic SQL bytes."""

    resolved_root = root.resolve()
    manifest = _load_manifest(resolved_root, slice_name)
    chunks: list[bytes] = []
    for segment, _path, source, digest in _source_segments(resolved_root, manifest):
        header = (
            f"-- source: database/schema/{segment}.sql\n"
            f"-- sha256: {digest}\n"
        ).encode("ascii")
        chunks.append(header + source)
    return b"\n".join(chunks)


def _output_manifest(
    root: Path, slice_name: str, baseline: bytes
) -> bytes:
    manifest = _load_manifest(root, slice_name)
    sources = _source_segments(root, manifest)
    output = {
        "version": 1,
        "slice": slice_name,
        "schema": manifest.get("schema"),
        "baselineSha256": hashlib.sha256(baseline).hexdigest(),
        "segments": [
            {
                "name": segment,
                "path": f"database/schema/{segment}.sql",
                "sha256": digest,
            }
            for segment, _path, _source, digest in sources
        ],
    }
    return (json.dumps(output, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary.write(data)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def _git_bytes(root: Path, relative_path: Path) -> bytes:
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative_path.as_posix()}"],
        cwd=root,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ManifestError(f"uncommitted source: {relative_path.as_posix()}")
    return result.stdout


def _require_clean_sources(root: Path, slice_name: str) -> None:
    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignore-submodules=none",
        ],
        cwd=root,
        capture_output=True,
    )
    if status.returncode != 0:
        detail = status.stderr.decode("utf-8", errors="replace").strip()
        raise ManifestError(f"cannot inspect Root worktree: {detail}")
    if status.stdout:
        raise ManifestError(
            "dirty Root worktree: tracked or untracked files differ from HEAD"
        )

    manifest = _load_manifest(root, slice_name)
    paths = [_manifest_path(root, slice_name)]
    paths.extend(path for _segment, path, _source, _digest in _source_segments(root, manifest))
    for path in paths:
        relative = path.relative_to(root)
        committed = _git_bytes(root, relative)
        if committed != path.read_bytes():
            raise ManifestError(f"dirty source: {relative.as_posix()}")


def _fail(message: str) -> NoReturn:
    raise SystemExit(message)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose the Root Slice SQL baseline")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--slice", default="slice-a")
    parser.add_argument("--require-clean", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    try:
        if args.require_clean:
            _require_clean_sources(root, args.slice)
        baseline = compose_baseline(root, args.slice)
        manifest = _output_manifest(root, args.slice, baseline)
    except ManifestError as error:
        _fail(str(error))

    baseline_path = root / "database" / "baseline" / "kokoro.sql"
    output_manifest_path = root / "database" / "baseline" / "manifest.json"
    if args.write:
        _atomic_write(baseline_path, baseline)
        _atomic_write(output_manifest_path, manifest)
        return 0

    mismatches = []
    for path, expected in (
        (baseline_path, baseline),
        (output_manifest_path, manifest),
    ):
        try:
            actual = path.read_bytes()
        except OSError:
            actual = None
        if actual != expected:
            mismatches.append(path.relative_to(root).as_posix())
    if mismatches:
        _fail(f"generated baseline is stale: {', '.join(mismatches)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

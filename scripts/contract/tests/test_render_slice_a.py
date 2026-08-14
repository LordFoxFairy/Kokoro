from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT))
from contract.validate_slice_a_manifest import ManifestError
import scripts.contract.render_slice_a as renderer
from scripts.contract.render_slice_a import check_tree, load_manifest, render_openapi, render_proto


MANIFEST = ROOT / "contract/slice-a-contract-manifest.yaml"


def test_proto_render_is_deterministic_and_buf_valid(tmp_path: Path) -> None:
    manifest = load_manifest(MANIFEST)
    first = tmp_path / "first"
    second = tmp_path / "second"
    paths = render_proto(manifest, first)
    render_proto(manifest, second)
    expected = [item["path"] for item in manifest["protobuf"]["files"]]
    assert [path.relative_to(first).as_posix() for path in paths] == expected
    for relative in expected:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()
        assert (first / relative).read_text().startswith(
            "// GENERATED SOURCE — authority: contract/slice-a-contract-manifest.yaml\n"
        )
    (first / "buf.yaml").write_text(
        "version: v2\nmodules:\n  - path: .\nlint:\n  use:\n    - STANDARD\nbreaking:\n  use:\n    - FILE\n"
    )
    descriptor = tmp_path / "slice-a.binpb"
    subprocess.run(
        ["pnpm", "exec", "buf", "build", str(first), "--as-file-descriptor-set", "-o", str(descriptor)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert descriptor.stat().st_size > 0


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda manifest: manifest["protobuf"]["enums"][1]["values"].__setitem__(
                1, copy.deepcopy(manifest["protobuf"]["enums"][0]["values"][1])
            ),
            "enum value prefix drift|duplicate package symbol",
        ),
        (
            lambda manifest: manifest["protobuf"]["files"][0]["declarations"].pop(),
            "unassigned declaration",
        ),
        (
            lambda manifest: manifest["protobuf"]["messages"][0]["fields"][0].__setitem__("type", ".missing.Type"),
            "unknown protobuf type",
        ),
        (
            lambda manifest: next(
                field
                for message in manifest["protobuf"]["messages"]
                for field in message["fields"]
                if "oneof" in field
            ).__setitem__("label", "optional"),
            "oneof field must be required",
        ),
    ],
)
def test_invalid_manifest_never_renders(tmp_path: Path, mutate, message: str) -> None:
    manifest = json.loads(MANIFEST.read_text())
    mutate(manifest)
    with pytest.raises(ManifestError, match=message):
        render_proto(manifest, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_proto_tree_replacement_is_exact_and_rolls_back_on_failure(tmp_path: Path, monkeypatch) -> None:
    manifest = load_manifest(MANIFEST)
    output = tmp_path / "proto"
    render_proto(manifest, output)
    extra = output / "extra.proto"; extra.write_text('syntax = "proto3";\n')
    render_proto(manifest, output)
    assert not extra.exists()
    first = next(output.rglob("*.proto"))
    first.write_text(first.read_text() + "// locally preserved on failed replacement\n")
    before = {path.relative_to(output).as_posix(): path.read_bytes() for path in output.rglob("*.proto")}
    real_replace = renderer.os.replace
    failed = False
    def fail_new_tree_once(source, destination):
        nonlocal failed
        if not failed and Path(source).name == "tree" and Path(destination) == output.absolute():
            failed = True
            raise OSError("injected replacement failure")
        return real_replace(source, destination)
    monkeypatch.setattr(renderer.os, "replace", fail_new_tree_once)
    with pytest.raises(OSError, match="injected replacement failure"):
        render_proto(manifest, output)
    assert {path.relative_to(output).as_posix(): path.read_bytes() for path in output.rglob("*.proto")} == before


def test_check_rejects_extra_proto_file(tmp_path: Path) -> None:
    manifest = load_manifest(MANIFEST)
    proto = tmp_path / "proto"
    openapi = tmp_path / "slice-a-web-v1.yaml"
    render_proto(manifest, proto)
    render_openapi(manifest, openapi)
    (proto / "extra.proto").write_text('syntax = "proto3";\n')
    with pytest.raises(ManifestError, match="Proto file inventory drift"):
        check_tree(MANIFEST, proto, openapi)

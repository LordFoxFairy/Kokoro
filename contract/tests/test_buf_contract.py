"""Policy tests for the standard Protobuf/Buf contract toolchain."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

CONTRACT = Path(__file__).resolve().parents[1]


def test_buf_contract_toolchain_is_exact_and_local() -> None:
    package = json.loads((CONTRACT / "package.json").read_text())

    assert package["private"] is True
    assert package["packageManager"] == "pnpm@11.2.2"
    assert package["devDependencies"] == {
        "@bufbuild/buf": "1.72.0",
        "@bufbuild/protobuf": "2.13.0",
        "@bufbuild/protoc-gen-es": "2.13.0",
    }
    assert "pnpm" not in package
    workspace = yaml.safe_load((CONTRACT / "pnpm-workspace.yaml").read_text())
    assert workspace["allowBuilds"] == {"@bufbuild/buf": True}


def test_buf_policy_is_standard_and_file_strict() -> None:
    config = yaml.safe_load((CONTRACT / "buf.yaml").read_text())

    assert config["version"] == "v2"
    assert config["modules"] == [{"path": "proto"}]
    assert config["deps"] == ["buf.build/bufbuild/protovalidate"]
    assert config["lint"]["use"] == ["STANDARD"]
    assert config["breaking"]["use"] == ["FILE"]


def test_generation_targets_only_committed_child_mirrors() -> None:
    config = yaml.safe_load((CONTRACT / "buf.gen.yaml").read_text())
    outputs = [plugin["out"] for plugin in config["plugins"]]

    assert outputs == [
        "../kokoro-platform/kokoro-platform-admin/src/generated/contracts",
        "../kokoro-web/apps/admin/lib/generated/contracts",
    ]
    assert all(plugin["local"] == "protoc-gen-es" for plugin in config["plugins"])
    assert all(plugin["opt"] == ["target=ts", "import_extension=js"] for plugin in config["plugins"])

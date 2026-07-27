"""Policy tests for the standard Protobuf/Buf contract toolchain."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

CONTRACT = Path(__file__).resolve().parents[1]
PROTO = CONTRACT / "proto"


def test_buf_contract_toolchain_is_exact_and_local() -> None:
    package = json.loads((CONTRACT / "package.json").read_text())

    assert package["private"] is True
    assert package["packageManager"] == "pnpm@11.2.2"
    assert package["devDependencies"] == {
        "@bufbuild/buf": "1.72.0",
        "@bufbuild/protobuf": "2.13.0",
        "@bufbuild/protoc-gen-es": "2.13.0",
    }
    assert package["scripts"] == {
        "buf:breaking": "buf breaking",
        "buf:format": "buf format -w",
        "buf:format:check": "buf format --diff --exit-code",
        "buf:generate": "node generate.mjs",
        "buf:lint": "buf lint",
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


def _proto(relative_path: str) -> str:
    return (PROTO / relative_path).read_text()


def test_admin_auth_v1_has_the_closed_service_surface() -> None:
    source = _proto("kokoro/platform/admin/v1/admin_auth.proto")

    assert "package kokoro.platform.admin.v1;" in source
    methods = re.findall(r"^\s*rpc\s+(\w+)\(", source, flags=re.MULTILINE)
    assert methods == [
        "GetOperatorByEmail",
        "GetOperator",
        "CreateVerificationToken",
        "ConsumeVerificationToken",
        "RecordAuthEvent",
        "GetCommandReceipt",
    ]


def test_effect_requests_use_common_command_identity_and_timestamps() -> None:
    source = _proto("kokoro/platform/admin/v1/admin_auth.proto")

    for message in (
        "CreateVerificationTokenRequest",
        "ConsumeVerificationTokenRequest",
        "RecordAuthEventRequest",
    ):
        body = re.search(rf"message {message} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL)
        assert body is not None
        assert "kokoro.common.v1.CommandIdentity command = 1" in body.group("body")
    assert "google.protobuf.Timestamp expires" in source
    assert "google.protobuf.Timestamp occurred_at" in source


def test_receipt_contract_never_contains_raw_secret_fields() -> None:
    receipt = _proto("kokoro/common/v1/receipt.proto")
    admin = _proto("kokoro/platform/admin/v1/admin_auth.proto")
    receipt_messages = re.findall(r"message \w*Receipt\w* \{.*?\n\}", receipt + admin, flags=re.DOTALL)

    assert receipt_messages
    assert all(" token " not in message for message in receipt_messages)
    assert "string request_digest" in receipt
    assert "string idempotency_key" in receipt

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
    assert all(
        plugin["opt"] == ["target=ts", "import_extension=js"]
        for plugin in config["plugins"]
    )


def _proto(relative_path: str) -> str:
    return (PROTO / relative_path).read_text()


def _service_methods(source: str, service: str) -> list[str]:
    block = re.search(
        rf"service {service} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL
    )
    assert block is not None
    return re.findall(r"^\s*rpc\s+(\w+)\(", block.group("body"), flags=re.MULTILINE)


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
        body = re.search(
            rf"message {message} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL
        )
        assert body is not None
        assert "kokoro.common.v1.CommandIdentity command = 1" in body.group("body")
    assert "google.protobuf.Timestamp expires" in source
    assert "google.protobuf.Timestamp occurred_at" in source


def test_effect_requests_embed_method_specific_digest_payloads() -> None:
    source = _proto("kokoro/platform/admin/v1/admin_auth.proto")
    expected = {
        "CreateVerificationTokenRequest": "CreateVerificationTokenEffect",
        "ConsumeVerificationTokenRequest": "ConsumeVerificationTokenEffect",
        "RecordAuthEventRequest": "RecordAuthEventEffect",
    }

    for request, effect in expected.items():
        body = re.search(
            rf"message {request} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL
        )
        assert body is not None
        assert (
            f"{effect} effect = 2 [(buf.validate.field).required = true];"
            in body.group("body")
        )

    for effect in expected.values():
        body = re.search(
            rf"message {effect} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL
        )
        assert body is not None
        assert " map<" not in body.group("body")
        assert " repeated " not in body.group("body")


def test_command_digest_algorithm_is_explicit_and_storage_safe() -> None:
    receipt = _proto("kokoro/common/v1/receipt.proto")
    admin = _proto("kokoro/platform/admin/v1/admin_auth.proto")

    assert "COMMAND_DIGEST_ALGORITHM_SHA256_PROTOBUF_V1 = 1;" in receipt
    assert "CommandDigestAlgorithm digest_algorithm" in receipt
    assert "len: 64" in receipt
    assert 'pattern: "^[0-9a-f]{64}$"' in receipt
    assert "CommandDigestAlgorithm digest_algorithm" in admin
    assert "len: 64" in admin
    assert 'pattern: "^[0-9a-f]{64}$"' in admin

    # The owner schema uses MySQL VARCHAR(191) for these indexed/auth fields.
    # Proto-valid requests must therefore never fail later as persistence errors.
    assert "max_len: 256" not in receipt
    for unsupported_bound in ("max_len: 320", "max_len: 512", "max_len: 2048"):
        assert unsupported_bound not in admin


def test_generation_owns_the_node_digest_helper_for_both_mirrors() -> None:
    generator = (CONTRACT / "generate.mjs").read_text()
    helper = re.search(
        r"function adminAuthEffectDigestSource\(\).*?\n\}\n\nfunction singleOutputTemplate",
        generator,
        flags=re.DOTALL,
    )

    assert helper is not None
    assert '"admin-auth-effect-digest.ts"' in generator
    assert "CommandDigestAlgorithm.SHA256_PROTOBUF_V1" in generator
    assert "writeUnknownFields: false" in generator
    assert "JSON.stringify" not in helper.group(0)


def test_receipt_contract_never_contains_raw_secret_fields() -> None:
    receipt = _proto("kokoro/common/v1/receipt.proto")
    admin = _proto("kokoro/platform/admin/v1/admin_auth.proto")
    receipt_messages = re.findall(
        r"message \w*Receipt\w* \{.*?\n\}", receipt + admin, flags=re.DOTALL
    )

    assert receipt_messages
    assert all(" token " not in message for message in receipt_messages)
    assert "string request_digest" in receipt
    assert "string idempotency_key" in receipt


def test_wave1_privileged_services_have_exact_closed_surfaces() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")
    control = _proto("kokoro/platform/admin/v2/admin_control.proto")
    lifecycle = _proto("kokoro/platform/site/v1/site_lifecycle.proto")

    assert _service_methods(identity, "AdminIdentityService") == [
        "BeginOperatorLogin",
        "ExchangeOidcSession",
        "BeginStepUp",
        "CompleteStepUp",
        "SignOut",
    ]
    assert _service_methods(control, "AdminQueryService") == [
        "GetSite",
        "ListSites",
        "GetUserWithinSite",
        "GetAuditWithinScope",
    ]
    assert _service_methods(control, "AdminCommandService") == [
        "PrepareCommand",
        "SubmitForApproval",
        "DecideApproval",
        "ExecuteApproved",
        "GetReceipt",
    ]
    assert _service_methods(lifecycle, "SiteLifecycleService") == [
        "RequestSite",
        "ReconcileProvisioning",
        "CreateRelease",
        "ActivateRelease",
        "SuspendSite",
        "ResumeSite",
        "PlanDecommission",
        "CancelDecommission",
        "ExecuteDecommission",
        "GetDecommissionReceipt",
    ]


def test_wave1_commands_freeze_identity_axes_scope_and_receipts() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")
    control = _proto("kokoro/platform/admin/v2/admin_control.proto")
    lifecycle = _proto("kokoro/platform/site/v1/site_lifecycle.proto")
    blob = "\n".join((identity, control, lifecycle))

    assert "message AdminCommandContext" in control
    for field in (
        "kokoro.common.v1.CommandIdentity command",
        "string environment",
        "string region",
        "string managed_device_ref",
        "SecurityEpochs security_epochs",
        "OperatorScope scope",
    ):
        assert field in control
    assert "oneof kind" in control
    assert "SiteScope site" in control
    assert "GlobalScope global" in control
    assert "BreakGlassScope breakglass" in control
    assert "string incident_id" in control
    assert "repeated string field_allowlist" in control
    assert "kokoro.common.v1.CommandReceipt receipt" in blob
    assert "authorization_code" in identity
    assert "id_token" not in identity


def test_site_lifecycle_is_typed_and_not_a_generic_admin_effect() -> None:
    control = _proto("kokoro/platform/admin/v2/admin_control.proto")
    lifecycle = _proto("kokoro/platform/site/v1/site_lifecycle.proto")

    for forbidden in (
        "REQUEST_SITE",
        "CREATE_RELEASE",
        "ACTIVATE_RELEASE",
        "SUSPEND_SITE",
        "RESUME_SITE",
        "DECOMMISSION",
    ):
        assert forbidden not in control
    assert "bytes payload" not in control
    assert "string operation" not in control
    for effect in (
        "RequestSiteEffect",
        "CreateReleaseEffect",
        "ActivateReleaseEffect",
        "SuspendSiteEffect",
        "ResumeSiteEffect",
        "PlanDecommissionEffect",
        "ExecuteDecommissionEffect",
    ):
        assert f"message {effect}" in lifecycle


def test_platform_admission_v1_surface_remains_frozen() -> None:
    source = _proto("kokoro/platform/admission/v1/admission.proto")
    assert _service_methods(source, "AdmissionService") == [
        "PrepareRun",
        "FinalizeRun",
        "GetCommandReceipt",
    ]
    assert "AuthorizeEffect" not in source
    assert "GetRestrictionEpochs" not in source

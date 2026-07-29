"""Golden-file gate for the contract generator: fixed spec -> byte-stable mirrors."""

from __future__ import annotations

import sys
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

CONTRACT = Path(__file__).resolve().parents[1]
ROOT = CONTRACT.parent
sys.path.insert(0, str(CONTRACT))

from generate import build, emit_platform_runtime_ts, emit_session_events_ts, load  # noqa: E402

OUTPUTS = build()


def _find(suffix: str) -> str:
    return next(c for p, c in OUTPUTS.items() if str(p).endswith(suffix))


def test_deterministic() -> None:
    assert build() == OUTPUTS


def test_mirrors_match_on_disk() -> None:
    stale = [
        str(path.relative_to(ROOT))
        for path, content in OUTPUTS.items()
        if not path.exists() or path.read_text() != content
    ]
    assert not stale, f"stale mirrors (run contract/generate.py): {stale}"


@pytest.mark.parametrize(
    "path,content",
    list(OUTPUTS.items()),
    ids=[str(p.relative_to(ROOT)) for p in OUTPUTS],
)
def test_generated_header(path: Path, content: str) -> None:
    assert content.startswith(
        (
            "# GENERATED — DO NOT EDIT",
            "// GENERATED — DO NOT EDIT",
            "<!-- GENERATED — DO NOT EDIT",
        )
    )


def test_raw_and_browser_kinds() -> None:
    events = load("events.yaml")
    raw = [e["kind"] for e in events["raw_kinds"]]
    browser = list(events["browser_order"])
    assert len(raw) == 22 and "run.started" in raw
    assert "plan.proposed" in raw
    assert len(browser) == 10
    assert "run.started" not in browser
    assert {"message.part.updated", "run.launch.updated"}.issubset(browser)
    assert "stream.draining" not in browser

    wire = _find("kokoro-session/src/contract/wire-events.ts")
    events_py = _find("contract/events.py")
    for kind in raw:
        assert f'z.literal("{kind}")' in wire, kind
        assert f'Literal["{kind}"]' in events_py, kind

    session = _find("kokoro-session/src/contract/session-events.ts")
    web = _find("kokoro-web/packages/session-client/src/generated/session-events.ts")
    for kind in browser:
        assert f'z.literal("{kind}")' in session, kind
        assert f'z.literal("{kind}")' in web, kind
    # run.started is raw-only: never a browser literal.
    assert 'z.literal("run.started")' not in session


def test_completed_owner_milestone_is_private_strict_and_durable_capable() -> None:
    events_py = _find("kokoro-agent/src/kokoro_agent/contract/events.py")
    wire = _find("kokoro-session/src/contract/wire-events.ts")
    browser = _find("kokoro-session/src/contract/session-events.ts")

    assert "class RunOwnerCompletedPayload(StrictModel):" in events_py
    assert "execution_context_anchor: Reference" in events_py
    assert "execution_context_digest: Sha256Str" in events_py
    assert "owner_revision: PositiveInt" in events_py
    assert 'kind: Literal["run.owner.completed"]' in events_py

    assert 'kind: z.literal("run.owner.completed")' in wire
    assert "execution_context_anchor: z.string().min(1).max(256)" in wire
    assert "execution_context_digest: z.string().regex(/^[0-9a-f]{64}$/u)" in wire
    assert "owner_revision: z.number().int().positive()" in wire

    assert 'z.literal("run.owner.completed")' not in browser


def test_plan_proposal_raw_contract_is_typed_and_owner_safe() -> None:
    events_py = _find("kokoro-agent/src/kokoro_agent/contract/events.py")
    wire = _find("kokoro-session/src/contract/wire-events.ts")

    assert "class PlanStep(StrictModel):" in events_py
    assert "class PlanProposal(StrictModel):" in events_py
    assert "class PlanProposedPayload(StrictModel):" in events_py
    assert "owner_version: PositiveInt" in events_py
    assert "proposal: PlanProposal" in events_py
    assert 'PlanAction = Literal["accept", "reject"]' in events_py

    assert "const planStepSchema = z" in wire
    assert "const planProposalSchema = z" in wire
    assert "owner_version: z.number().int().positive()" in wire
    assert "proposal: planProposalSchema" in wire


def test_wave3_browser_contract_is_complete_and_cursor_only() -> None:
    http = load("http.yaml")
    snapshot = next(obj for obj in http["objects"] if obj["name"] == "SessionSnapshot")
    fields = {field["name"]: field for field in snapshot["fields"]}
    assert fields["messages"].get("optional") is not True
    assert fields["branches"].get("optional") is not True
    assert fields["snapshot_watermark"]["type"] == "object:SnapshotWatermark"
    capability = next(
        obj for obj in http["objects"] if obj["name"] == "CapabilityDisplaySnapshot"
    )
    capability_fields = {field["name"]: field for field in capability["fields"]}
    assert capability_fields["agent_label"].get("optional") is True
    assert capability_fields["source"]["type"] == "literal:admission_snapshot"
    assert "availability" not in capability_fields

    snapshot_query = next(
        obj for obj in http["objects"] if obj["name"] == "SnapshotQuery"
    )
    snapshot_query_fields = {
        field["name"]: field for field in snapshot_query["fields"]
    }
    assert snapshot_query_fields == {
        "cursor": {"name": "cursor", "type": "opaque_cursor", "optional": True},
        "limit": {"name": "limit", "type": "page_limit", "optional": True},
    }
    snapshot_endpoint = http["endpoints"]["snapshot"]
    assert snapshot_endpoint["query_object"] == "SnapshotQuery"

    stable_errors = set(http["enums"]["stable_error_code"])
    assert {
        "REQUEST_INVALID",
        "PAYLOAD_TOO_LARGE",
        "METHOD_NOT_ALLOWED",
        "UNSUPPORTED_MEDIA_TYPE",
        "BFF_WORKLOAD_REQUIRED",
        "BFF_WORKLOAD_REVOKED",
    }.issubset(stable_errors)

    generated_events = emit_session_events_ts(load("events.yaml"))
    assert 'from "./http.js"' in generated_events
    assert 'from "./http"' not in generated_events

    endpoint_names = set(http["endpoints"])
    assert {
        "submit_message",
        "edit_message",
        "regenerate_message",
        "fork_branch",
        "activate_branch",
        "cancel_run",
        "decide_action",
        "decide_plan",
        "get_command_receipt",
        "archive_session",
        "restore_session",
        "trash_session",
        "put_preference",
        "list_folders",
        "create_folder",
    }.issubset(endpoint_names)

    generated = _find("kokoro-session/src/contract/http.ts")
    assert "event_watermark" not in generated
    assert "messagePartEnvelopeSchema = z.discriminatedUnion" in generated
    assert "messageInputPartSchema = z.discriminatedUnion" in generated
    submit = next(obj for obj in http["objects"] if obj["name"] == "SubmitMessageRequest")
    submit_fields = {field["name"]: field for field in submit["fields"]}
    assert "content" not in submit_fields
    assert {
        "branch_id",
        "parent_message_id",
        "trusted_locale",
        "parts",
        "attachment_refs",
        "model_option_revision_ref",
    }.issubset(submit_fields)
    assert "SHA256_CANONICAL_JSON_V2" in generated
    assert "canonicalBrowserCommandDigestPreimage" in generated
    assert '"fork_branch": Object.freeze(["session_id", "branch_id"])' in generated
    assert '"create_session": Object.freeze([])' in generated
    assert "BROWSER_COMMAND_TARGETS_INVALID" in generated
    assert http["command_digest"] == {
        "algorithm": "SHA256_CANONICAL_JSON_V2",
        "preimage_fields": ["operation", "targets", "effect"],
    }
    assert 'commandReceiptViewSchema = z.discriminatedUnion("status"' in generated
    assert 'sessionCommandEffectSchema = z.discriminatedUnion("kind"' in generated
    assert "command receipt operation/effect mismatch" in generated
    assert '"create_session": "session-created"' in generated
    assert '"delete_folder": "folder-deleted"' in generated
    assert '"decide_action": "action-decision-recorded"' in generated
    assert '"decide_plan": "plan-decision-recorded"' in generated
    assert (
        http["endpoints"]["decide_action"]["path_template"]
        == "/v1/sessions/{session_id}/runs/{run_id}/actions:decide"
    )
    assert (
        http["endpoints"]["decide_plan"]["path_template"]
        == "/v1/sessions/{session_id}/runs/{run_id}/plans:decide"
    )
    action_decision = next(
        obj for obj in http["objects"] if obj["name"] == "ActionDecision"
    )
    plan_decision = next(
        obj for obj in http["objects"] if obj["name"] == "PlanDecision"
    )
    assert {variant["value"] for variant in action_decision["variants"]} == {
        "approve",
        "reject",
        "edit",
        "respond",
    }
    assert {variant["value"] for variant in plan_decision["variants"]} == {
        "accept",
        "reject",
    }
    action_projection = next(
        obj for obj in http["objects"] if obj["name"] == "ActionPartPayload"
    )
    assert {
        "decision_group_ref",
        "required_owner_refs",
        "safe_request_summary",
        "input_schema_ref",
        "safe_input_schema",
    }.issubset({field["name"] for field in action_projection["fields"]})
    plan_projection = next(
        obj for obj in http["objects"] if obj["name"] == "PlanPartPayload"
    )
    assert {"plan_version", "allowed_actions", "status"}.issubset(
        {field["name"] for field in plan_projection["fields"]}
    )
    receipt_endpoint = http["endpoints"]["get_command_receipt"]
    assert receipt_endpoint["path_template"] == "/v1/session-commands/{command_id}/receipt"
    assert receipt_endpoint["params"] == ["command_id"]
    assert receipt_endpoint["query_object"] == "CommandReceiptLookupQuery"
    assert receipt_endpoint["authorization"] == "subject-site-command-receipt-grant"
    assert http["endpoints"]["list_sessions"]["query_object"] == "ListSessionsQuery"
    assert http["endpoints"]["stream"]["query_object"] == "StreamQuery"
    assert http["endpoints"]["list_folders"]["query_object"] == "FolderListQuery"
    assert "parts: z.array(messageInputPartSchema).min(1).max(64)" in generated
    assert "attachment_refs: z.array(attachmentIntentSchema).max(64)" in generated
    assert "command_id: z.string().min(1).max(128)" in generated
    assert "idempotency_key: z.string().min(1).max(191)" in generated
    assert "limit: z.number().int().min(1).max(100)" in generated

    operations = set(http["enums"]["browser_command_operation"])
    mutation_endpoints = {
        name
        for name, endpoint in http["endpoints"].items()
        if endpoint.get("request_object") not in {None} and name != "get_command_receipt"
    }
    assert operations == mutation_endpoints
    for name in mutation_endpoints:
        assert http["endpoints"][name]["response_object"] == "SessionCommandResponse"
    assert "seq: z.number().int().nonnegative()" not in _find(
        "kokoro-session/src/contract/session-events.ts"
    )
    events_generated = _find("kokoro-session/src/contract/session-events.ts")
    assert "cursor: z.string().min(1)" in events_generated
    assert "durable_seq: z.string()" in events_generated
    assert "streamControlFrameSchema" in events_generated
    assert "sessionStreamFrameSchema" in events_generated
    draining = events_generated.split("const streamDrainingControlFrameSchema", 1)[1]
    assert "last_durable_cursor" in draining
    assert "durable_seq" not in draining


def test_no_legacy_vocabulary() -> None:
    # 注：request_id 曾在禁用列表,但已是合法 control 词汇——HITL submit 决策的幂等锚
    # (contract/spec/control.yaml 定义)。故移出;其余仍为应绝迹的旧词汇。
    blob = "\n".join(OUTPUTS.values())
    for banned in (
        "agui_out_web_extra",
        "conversation_id",
        "execution_style",
        "permission_mode",
        "awaiting_kind",
        'z.literal("text.delta")',
        'z.literal("text.completed")',
        'Literal["text.delta"]',
    ):
        assert banned not in blob, banned
    # the new vocabulary must be present.
    assert 'z.literal("message.delta")' in blob
    assert 'z.literal("session.updated")' in blob
    assert 'z.literal("run.view.updated")' in blob


def test_run_request_shape() -> None:
    control_py = _find("contract/control.py")
    # handbook RunRequest: run_id + thread_id + nested input/runtime/context; no session_id top field.
    assert "thread_id: NonEmptyStr" in control_py
    assert "input: RunInput" in control_py
    assert "runtime: RuntimeConfig" in control_py
    assert "context: RuntimeContext" in control_py
    assert "execution_context: ExecutionContextIntent" in control_py
    assert "class ExecutionContextIntentRoot(StrictModel):" in control_py
    assert "class ExecutionContextIntentContinue(StrictModel):" in control_py
    assert "class ExecutionContextIntentFork(StrictModel):" in control_py
    assert 'Field(discriminator="mode")' in control_py
    assert "parent_anchor: Reference" in control_py
    assert "parent_digest: Sha256Str" in control_py

    control_init = _find("kokoro-agent/src/kokoro_agent/contract/__init__.py")
    assert "ExecutionContextIntentRoot" in control_init
    assert "ExecutionContextIntentContinue" in control_init
    assert "ExecutionContextIntentFork" in control_init

    control_ts = _find("kokoro-session/src/contract/control.ts")
    assert 'executionContextIntentSchema = z.discriminatedUnion("mode"' in control_ts
    assert 'mode: z.literal("root")' in control_ts
    assert 'mode: z.literal("continue")' in control_ts
    assert 'mode: z.literal("fork")' in control_ts
    assert (
        "parent_anchor: z.string().min(1).max(256).refine((value) => "
        "value.trim() === value)"
    ) in control_ts
    assert "parent_digest: z.string().regex(/^[0-9a-f]{64}$/u)" in control_ts

    namespace: dict[str, object] = {}
    exec(control_py, namespace)
    arm = namespace["ExecutionContextIntentContinue"]
    assert callable(arm)
    arm.model_rebuild(_types_namespace=namespace)
    digest = "a" * 64
    arm(mode="continue", parent_anchor="ctx_valid", parent_digest=digest)
    for anchor in (" ctx", "ctx ", "x" * 257, "ctx\n"):
        with pytest.raises(Exception):
            arm(mode="continue", parent_anchor=anchor, parent_digest=digest)


def test_session_client_and_session_share_outbound_bytes() -> None:
    assert _find("kokoro-session/src/contract/session-events.ts") == _find(
        "kokoro-web/packages/session-client/src/generated/session-events.ts"
    )
    assert _find("kokoro-session/src/contract/control.ts") == _find(
        "kokoro-web/packages/session-client/src/generated/control.ts"
    )
    assert _find("kokoro-session/src/contract/http.ts") == _find(
        "kokoro-web/packages/session-client/src/generated/http.ts"
    )


def test_generator_never_targets_retired_user_app() -> None:
    retired = ROOT / "kokoro-web/apps/user"
    assert all(not path.is_relative_to(retired) for path in OUTPUTS)


def test_session_agent_and_platform_draft_producer_share_control_bytes() -> None:
    session = _find("kokoro-session/src/contract/control.ts")
    assert session == _find("kokoro-web/packages/session-client/src/generated/control.ts")
    assert session == _find("kokoro-platform/kokoro-platform-kit/src/contract/control.ts")


def test_platform_and_session_share_runtime_contract_bytes() -> None:
    spec = load("platform-runtime.yaml")
    generated = emit_platform_runtime_ts(spec)
    assert generated == _find(
        "kokoro-platform/kokoro-platform-kit/src/contract/platform-runtime.ts"
    )
    assert generated == _find("kokoro-session/src/contract/platform-runtime.ts")
    for symbol in (
        "usageHoldRequestSchema",
        "usageSettleRequestSchema",
        "releaseCreditRequestSchema",
        "resolveModelBindingsQuerySchema",
        "listModelLabelsQuerySchema",
        "modelTransportKindSchema",
    ):
        assert f"export const {symbol}" in generated


def test_node_generator_declares_boundary_scoped_bundles() -> None:
    generator = (CONTRACT / "generate.mjs").read_text()

    for boundary in (
        "platform-admin-auth@v1",
        "platform-admin-identity@v1",
        "platform-admin-query@v2",
        "platform-admin-command@v2",
        "platform-site-lifecycle@v1",
        "platform-admission@v1",
        "platform-session-authorization@v2",
        "session-dispatch-owner-evidence@v1",
    ):
        assert boundary in generator
    assert "await protoFiles(protoRoot)" not in generator
    assert 'schemaId: "kokoro.platform.admin.v1.AdminAuthService"' not in generator


def test_node_generator_isolates_new_boundary_output() -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "bundle"
        result = subprocess.run(
            [
                "node",
                str(CONTRACT / "generate.mjs"),
                "--boundary",
                "platform-site-lifecycle@v1",
                "--output",
                str(output),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        metadata = (output / "contract-metadata.ts").read_text()
        assert 'schemaId: "kokoro.platform.site.v1.SiteLifecycleService"' in metadata
        assert '"kokoro/platform/site/v1/site_lifecycle.proto"' in metadata
        assert '"kokoro/platform/admission/v1/admission.proto"' not in metadata
        assert (output / "kokoro/platform/site/v1/site_lifecycle_pb.ts").is_file()
        assert not (output / "kokoro/platform/admission/v1/admission_pb.ts").exists()


@pytest.mark.parametrize(
    "boundary,own_file,forbidden_files",
    [
        (
            "platform-admin-identity@v1",
            "kokoro/platform/identity/v1/admin_identity_pb.ts",
            [
                "kokoro/platform/admin/v2/admin_query_pb.ts",
                "kokoro/platform/admin/v2/admin_command_pb.ts",
                "kokoro/platform/admin/v2/admin_control_pb.ts",
                "kokoro/platform/site/v1/site_lifecycle_pb.ts",
            ],
        ),
        (
            "platform-admin-query@v2",
            "kokoro/platform/admin/v2/admin_query_pb.ts",
            [
                "kokoro/platform/admin/v2/admin_command_pb.ts",
                "kokoro/platform/admin/v2/admin_control_pb.ts",
                "kokoro/platform/identity/v1/admin_identity_pb.ts",
                "kokoro/platform/site/v1/site_lifecycle_pb.ts",
            ],
        ),
        (
            "platform-admin-command@v2",
            "kokoro/platform/admin/v2/admin_command_pb.ts",
            [
                "kokoro/platform/admin/v2/admin_query_pb.ts",
                "kokoro/platform/admin/v2/admin_control_pb.ts",
                "kokoro/platform/identity/v1/admin_identity_pb.ts",
                "kokoro/platform/site/v1/site_lifecycle_pb.ts",
            ],
        ),
        (
            "platform-site-lifecycle@v1",
            "kokoro/platform/site/v1/site_lifecycle_pb.ts",
            [
                "kokoro/platform/admin/v2/admin_query_pb.ts",
                "kokoro/platform/admin/v2/admin_command_pb.ts",
                "kokoro/platform/admin/v2/admin_control_pb.ts",
                "kokoro/platform/identity/v1/admin_identity_pb.ts",
            ],
        ),
        (
            "platform-admission@v1",
            "kokoro/platform/admission/v1/admission_pb.ts",
            [
                "kokoro/platform/admin/v2/admin_query_pb.ts",
                "kokoro/platform/admin/v2/admin_command_pb.ts",
                "kokoro/platform/identity/v1/admin_identity_pb.ts",
                "kokoro/platform/site/v1/site_lifecycle_pb.ts",
            ],
        ),
        (
            "platform-session-authorization@v2",
            "kokoro/platform/authorization/v2/scoped_session_authorization_pb.ts",
            [
                "kokoro/platform/authorization/v1/session_authorization_pb.ts",
                "kokoro/platform/admission/v1/admission_pb.ts",
                "kokoro/platform/admin/v2/admin_query_pb.ts",
            ],
        ),
        (
            "session-dispatch-owner-evidence@v1",
            "kokoro/session/dispatch/v1/dispatch_owner_evidence_pb.ts",
            [
                "kokoro/platform/authorization/v2/scoped_session_authorization_pb.ts",
                "kokoro/platform/admission/v1/admission_pb.ts",
                "kokoro/platform/admin/v2/admin_query_pb.ts",
            ],
        ),
    ],
)
def test_node_generator_never_leaks_sibling_services(
    boundary: str, own_file: str, forbidden_files: list[str]
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "bundle"
        result = subprocess.run(
            [
                "node",
                str(CONTRACT / "generate.mjs"),
                "--boundary",
                boundary,
                "--output",
                str(output),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert (output / own_file).is_file()
        assert all(not (output / path).exists() for path in forbidden_files)


def test_command_envelope_v2_is_frozen_in_the_common_proto() -> None:
    legacy_receipt = (CONTRACT / "proto/kokoro/common/v1/receipt.proto").read_text()
    envelope = (
        CONTRACT / "proto/kokoro/common/v2/command_envelope.proto"
    ).read_text()

    assert "CanonicalCommandEnvelopeV2" not in legacy_receipt
    assert "COMMAND_DIGEST_ALGORITHM_V2_SHA256_COMMAND_ENVELOPE = 1;" in envelope
    for message in (
        "CanonicalTypedProtobufV2",
        "CanonicalSecurityEpochV2",
        "CanonicalCommandTrustAxesV2",
        "CanonicalCommandEnvelopeV2",
        "CommandIdentityV2",
        "CommandReceiptV2",
    ):
        assert f"message {message} {{" in envelope
    canonical = _proto_message(envelope, "CanonicalCommandEnvelopeV2")
    assert "CommandIdentityV2" not in canonical
    assert "request_digest" not in canonical

    shared = (
        CONTRACT / "proto/kokoro/platform/admin/v2/admin_shared.proto"
    ).read_text()
    command_context = _proto_message(shared, "AuthenticatedOperatorCommandContext")
    assert "string actor_ref = 8" in command_context

    for relative_path in (
        "kokoro/platform/identity/v1/admin_identity.proto",
        "kokoro/platform/admin/v2/admin_shared.proto",
        "kokoro/platform/admin/v2/admin_command.proto",
        "kokoro/platform/site/v1/site_lifecycle.proto",
    ):
        source = (CONTRACT / "proto" / relative_path).read_text()
        assert "kokoro.common.v2.CommandIdentityV2" in source or (
            "kokoro.common.v2.CommandReceiptV2" in source
        )
        assert "kokoro.common.v1.CommandIdentity" not in source
        assert "kokoro.common.v1.CommandReceipt" not in source


def _proto_message(source: str, message: str) -> str:
    marker = f"message {message} {{"
    start = source.index(marker) + len(marker)
    depth = 1
    for index in range(start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index]
    raise AssertionError(f"unterminated proto message: {message}")


def _typescript_compiler() -> Path:
    version = json.loads((CONTRACT / "package.json").read_text())["devDependencies"][
        "typescript"
    ]
    compiler = (
        CONTRACT
        / "node_modules/.pnpm"
        / f"typescript@{version}"
        / "node_modules/typescript/bin/tsc"
    )
    assert compiler.is_file(), compiler
    return compiler


@pytest.mark.parametrize(
    ("boundary", "expected_wrappers", "runner_source"),
    [
        (
            "platform-admin-identity@v1",
            [
                "beginOperatorLoginRequestDigest",
                "exchangeOidcSessionRequestDigest",
                "beginStepUpRequestDigest",
                "completeStepUpRequestDigest",
                "signOutRequestDigest",
            ],
            r'''
import { create } from "@bufbuild/protobuf";
import {
  beginOperatorLoginRequestDigest,
} from "./bundle/command-envelope-digest.js";
import { CommandDigestAlgorithmV2, CommandIdentityV2Schema } from "./bundle/kokoro/common/v2/command_envelope_pb.js";
import {
  AdminPreLoginWorkloadContextSchema,
  AdminSessionRecoveryProofSchema,
  BeginOperatorLoginEffectSchema,
} from "./bundle/kokoro/platform/identity/v1/admin_identity_pb.js";

const command = create(CommandIdentityV2Schema, {
  commandId: "command:1",
  idempotencyKey: "idempotency:1",
  digestAlgorithm: CommandDigestAlgorithmV2.SHA256_COMMAND_ENVELOPE,
  requestDigest: "0".repeat(64),
});
const context = create(AdminPreLoginWorkloadContextSchema, {
  command,
  workloadIdentityRef: "workload:web-admin",
  environment: "production",
  region: "us-east-1",
  managedDeviceRef: "device:3",
  audience: "platform-admin",
});
const effect = create(BeginOperatorLoginEffectSchema, {
  returnIntentRef: "dashboard",
  recoveryProof: create(AdminSessionRecoveryProofSchema, { recoveryHandle: Uint8Array.from({ length: 32 }, (_, i) => i) }),
});
const verified = {
  workloadIdentityRef: "workload:web-admin",
  environment: "production",
  region: "us-east-1",
  managedDeviceRef: "device:3",
  audience: "platform-admin",
} as const;
const golden = beginOperatorLoginRequestDigest(context, effect, verified);
const changedEffect = beginOperatorLoginRequestDigest(
  context,
  create(BeginOperatorLoginEffectSchema, { ...effect, returnIntentRef: "settings" }),
  verified,
);
let mismatch = "accepted";
try {
  beginOperatorLoginRequestDigest(context, effect, { ...verified, region: "eu-west-1" });
} catch (error) {
  mismatch = error instanceof Error ? error.message : String(error);
}
console.log(JSON.stringify({ golden, changedEffect, mismatch }));
''',
        ),
        (
            "platform-admin-command@v2",
            [
                "prepareCommandRequestDigest",
                "submitForApprovalRequestDigest",
                "decideApprovalRequestDigest",
                "executeApprovedRequestDigest",
            ],
            r'''
import { create } from "@bufbuild/protobuf";
import {
  prepareCommandRequestDigest,
} from "./bundle/command-envelope-digest.js";
import { CommandDigestAlgorithmV2, CommandIdentityV2Schema } from "./bundle/kokoro/common/v2/command_envelope_pb.js";
import {
  AuthenticatedOperatorCommandContextSchema,
  OperatorScopeSchema,
  SecurityEpochsSchema,
  SiteScopeSchema,
} from "./bundle/kokoro/platform/admin/v2/admin_shared_pb.js";
import {
  DisableUserChangeSchema,
  PrepareCommandEffectSchema,
} from "./bundle/kokoro/platform/admin/v2/admin_command_pb.js";

const command = create(CommandIdentityV2Schema, {
  commandId: "command:1",
  idempotencyKey: "idempotency:1",
  digestAlgorithm: CommandDigestAlgorithmV2.SHA256_COMMAND_ENVELOPE,
  requestDigest: "0".repeat(64),
});
const makeContext = (siteIds: string[], actorRef = "operator:7") => create(AuthenticatedOperatorCommandContextSchema, {
  command,
  actorRef,
  operatorSessionRef: "session:9",
  environment: "production",
  region: "us-east-1",
  managedDeviceRef: "device:3",
  securityEpochs: create(SecurityEpochsSchema, {
    operatorSecurityEpoch: 2n,
    sessionEpoch: 11n,
    restrictionEpoch: 3n,
    policyEpoch: 5n,
    siteSecurityEpoch: 7n,
  }),
  scope: create(OperatorScopeSchema, {
    kind: { case: "site", value: create(SiteScopeSchema, { siteIds, environment: "production", region: "us-east-1" }) },
  }),
});
const effect = create(PrepareCommandEffectSchema, {
  change: {
    case: "disableUser",
    value: create(DisableUserChangeSchema, { siteId: "site:alpha", userRef: "user:42", reasonCode: "abuse" }),
  },
  reason: "security response",
});
const verified = {
  workloadIdentityRef: "workload:web-admin",
  audience: "platform-admin",
  actorRef: "operator:7",
  operatorSessionRef: "session:9",
  environment: "production",
  region: "us-east-1",
  managedDeviceRef: "device:3",
} as const;
const golden = prepareCommandRequestDigest(makeContext(["site:beta", "site:alpha"]), effect, verified);
const stable = prepareCommandRequestDigest(makeContext(["site:alpha", "site:beta"]), effect, verified);
const changedActor = prepareCommandRequestDigest(makeContext(["site:beta", "site:alpha"], "operator:8"), effect, { ...verified, actorRef: "operator:8" });
const changedEffect = prepareCommandRequestDigest(
  makeContext(["site:beta", "site:alpha"]),
  create(PrepareCommandEffectSchema, { ...effect, reason: "different" }),
  verified,
);
let mismatch = "accepted";
try {
  prepareCommandRequestDigest(makeContext(["site:beta", "site:alpha"]), effect, { ...verified, region: "eu-west-1" });
} catch (error) {
  mismatch = error instanceof Error ? error.message : String(error);
}
console.log(JSON.stringify({ golden, stable, changedActor, changedEffect, mismatch }));
''',
        ),
        (
            "platform-site-lifecycle@v1",
            [
                "requestSiteRequestDigest",
                "reconcileProvisioningRequestDigest",
                "createReleaseRequestDigest",
                "activateReleaseRequestDigest",
                "suspendSiteRequestDigest",
                "resumeSiteRequestDigest",
                "planDecommissionRequestDigest",
                "cancelDecommissionRequestDigest",
                "executeDecommissionRequestDigest",
            ],
            r'''
import { create } from "@bufbuild/protobuf";
import {
  planDecommissionRequestDigest,
} from "./bundle/command-envelope-digest.js";
import { CommandDigestAlgorithmV2, CommandIdentityV2Schema } from "./bundle/kokoro/common/v2/command_envelope_pb.js";
import {
  AuthenticatedOperatorCommandContextSchema,
  OperatorScopeSchema,
  SecurityEpochsSchema,
  SiteScopeSchema,
} from "./bundle/kokoro/platform/admin/v2/admin_shared_pb.js";
import { PlanDecommissionEffectSchema } from "./bundle/kokoro/platform/site/v1/site_lifecycle_pb.js";
import { timestampFromDate } from "@bufbuild/protobuf/wkt";

const command = create(CommandIdentityV2Schema, {
  commandId: "command:1",
  idempotencyKey: "idempotency:1",
  digestAlgorithm: CommandDigestAlgorithmV2.SHA256_COMMAND_ENVELOPE,
  requestDigest: "0".repeat(64),
});
const context = create(AuthenticatedOperatorCommandContextSchema, {
  command,
  actorRef: "operator:7",
  operatorSessionRef: "session:9",
  environment: "production",
  region: "us-east-1",
  managedDeviceRef: "device:3",
  securityEpochs: create(SecurityEpochsSchema, { operatorSecurityEpoch: 2n, sessionEpoch: 11n, restrictionEpoch: 3n, policyEpoch: 5n, siteSecurityEpoch: 7n }),
  scope: create(OperatorScopeSchema, {
    kind: { case: "site", value: create(SiteScopeSchema, { siteIds: ["site:alpha"], environment: "production", region: "us-east-1" }) },
  }),
});
const makeEffect = (participants: string[]) => create(PlanDecommissionEffectSchema, {
  earliestExecutionAt: timestampFromDate(new Date("2027-01-01T00:00:00Z")),
  requiredParticipantRefs: participants,
  retentionPolicyRef: "retention:standard",
});
const verified = {
  workloadIdentityRef: "workload:web-admin",
  audience: "platform-admin",
  actorRef: "operator:7",
  operatorSessionRef: "session:9",
  environment: "production",
  region: "us-east-1",
  managedDeviceRef: "device:3",
} as const;
const golden = planDecommissionRequestDigest(context, "site:alpha", makeEffect(["billing", "storage"]), verified);
const stable = planDecommissionRequestDigest(context, "site:alpha", makeEffect(["storage", "billing"]), verified);
const changedSite = planDecommissionRequestDigest(context, "site:beta", makeEffect(["billing", "storage"]), verified);
const changedEffect = planDecommissionRequestDigest(context, "site:alpha", makeEffect(["billing", "search"]), verified);
console.log(JSON.stringify({ golden, stable, changedSite, changedEffect }));
''',
        ),
    ],
)
def test_generated_command_envelope_v2_digest_executes_typed_boundary_vectors(
    boundary: str, expected_wrappers: list[str], runner_source: str
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        output = root / "bundle"
        result = subprocess.run(
            [
                "node",
                str(CONTRACT / "generate.mjs"),
                "--boundary",
                boundary,
                "--output",
                str(output),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        helper = output / "command-envelope-digest.ts"
        assert helper.is_file()
        helper_source = helper.read_text()
        for wrapper in expected_wrappers:
            assert f"export function {wrapper}(" in helper_source
        assert "export function commandEnvelopeV2Digest(" not in helper_source
        assert "export function canonicalCommandEnvelopeV2(" not in helper_source
        assert "export type CanonicalCommandEnvelopeV2Input" not in helper_source

        (root / "package.json").write_text('{"type":"module"}\n')
        os.symlink(CONTRACT / "node_modules", root / "node_modules", target_is_directory=True)
        (root / "tsconfig.json").write_text(
            json.dumps(
                {
                    "compilerOptions": {
                        "target": "ES2022",
                        "module": "NodeNext",
                        "moduleResolution": "NodeNext",
                        "strict": True,
                        "skipLibCheck": True,
                        "outDir": "dist",
                        "rootDir": ".",
                    },
                    "include": ["bundle/**/*.ts", "runner.ts", "node-crypto.d.ts"],
                }
            )
        )
        (root / "node-crypto.d.ts").write_text(
            """
declare module "node:crypto" {
  interface Hash {
    update(data: string, encoding: "utf8"): Hash;
    update(data: Uint8Array): Hash;
    digest(encoding: "hex"): string;
  }
  export function createHash(algorithm: "sha256"): Hash;
}
"""
        )
        (root / "runner.ts").write_text(runner_source)
        compile_result = subprocess.run(
            ["node", str(_typescript_compiler()), "--project", "tsconfig.json"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert compile_result.returncode == 0, compile_result.stdout + compile_result.stderr
        runtime = subprocess.run(
            ["node", "dist/runner.js"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert runtime.returncode == 0, runtime.stderr
        evidence = json.loads(runtime.stdout)

        assert len(evidence["golden"]) == 64
        if "stable" in evidence:
            assert evidence["stable"] == evidence["golden"]
        for name, digest in evidence.items():
            if name not in {"golden", "stable", "mismatch"}:
                assert digest != evidence["golden"], name
        if "mismatch" in evidence:
            assert evidence["mismatch"] == "command_envelope_axis_mismatch:region"


def test_admin_auth_v1_frozen_metadata_is_reproducible() -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "bundle"
        result = subprocess.run(
            [
                "node",
                str(CONTRACT / "generate.mjs"),
                "--boundary",
                "platform-admin-auth@v1",
                "--output",
                str(output),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        committed = (
            ROOT
            / "kokoro-platform/kokoro-platform-admin/src/generated/contracts/contract-metadata.ts"
        )
        assert (output / "contract-metadata.ts").read_bytes() == committed.read_bytes()
        committed_helper = committed.with_name("admin-auth-effect-digest.ts")
        assert (
            output / "admin-auth-effect-digest.ts"
        ).read_bytes() == committed_helper.read_bytes()

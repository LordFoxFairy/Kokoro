"""Policy tests for the standard Protobuf/Buf contract toolchain."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

CONTRACT = Path(__file__).resolve().parents[1]
PROTO = CONTRACT / "proto"
PUBLIC_OPENAPI = CONTRACT / "openapi/platform-public-v1.yaml"
ASSET_DATA_PLANE_OPENAPI = CONTRACT / "openapi/asset-data-plane-v1.yaml"


def test_buf_contract_toolchain_is_exact_and_local() -> None:
    package = json.loads((CONTRACT / "package.json").read_text())

    assert package["private"] is True
    assert package["packageManager"] == "pnpm@11.2.2"
    assert package["devDependencies"] == {
        "@bufbuild/buf": "1.72.0",
        "@bufbuild/protobuf": "2.13.0",
        "@bufbuild/protoc-gen-es": "2.13.0",
        "@bufbuild/protovalidate": "1.2.0",
        "@redocly/cli": "2.41.0",
        "@hey-api/openapi-ts": "0.99.0",
        "ajv": "8.20.0",
        "typescript": "5.9.3",
    }
    assert package["scripts"] == {
        "buf:breaking": "buf breaking",
        "buf:format": "buf format -w",
        "buf:format:check": "buf format --diff --exit-code",
        "buf:generate": "node generate.mjs",
        "buf:lint": "buf lint",
            "openapi:lint": (
                "redocly lint --extends=spec openapi/platform-public-v1.yaml "
                "openapi/asset-data-plane-v1.yaml openapi/admin-web-v1.yaml"
            ),
            "openapi:generate:asset-data-plane": (
                "node generate-public-openapi.mjs --schema asset-data-plane-v1"
            ),
            "openapi:generate:public": "node generate-public-openapi.mjs",
            "web-release:check": (
                "node ../scripts/contract/check-web-release-composition.mjs --root .."
            ),
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


def test_default_generation_targets_only_the_current_admin_auth_provider() -> None:
    config = yaml.safe_load((CONTRACT / "buf.gen.yaml").read_text())
    outputs = [plugin["out"] for plugin in config["plugins"]]

    assert outputs == [
        "../kokoro-platform/kokoro-platform-admin/src/generated/contracts",
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


def _message_body(source: str, message: str) -> str:
    block = re.search(
        rf"message {message} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL
    )
    assert block is not None
    return block.group("body")


def _enum_body(source: str, enum: str) -> str:
    block = re.search(rf"enum {enum} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL)
    assert block is not None
    return block.group("body")


def _public_operations() -> dict[str, dict]:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    return {
        operation["operationId"]: operation
        for path in document["paths"].values()
        for method, operation in path.items()
        if method.lower()
        in {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
    }


def test_redemption_preview_credentials_reject_whitespace_without_escaping_the_regex() -> None:
    schemas = yaml.safe_load(PUBLIC_OPENAPI.read_text())["components"]["schemas"]

    for schema_name in ("RedemptionConfirmInput", "RedemptionPreview"):
        pattern = schemas[schema_name]["properties"]["previewCredential"]["pattern"]
        assert pattern == r"^\S+$"
        assert re.fullmatch(pattern, "opaque-preview-credential-1234567890")
        assert re.fullmatch(pattern, "contains whitespace") is None


def _response_schema(document: dict, operation: dict) -> str:
    success = [
        response
        for status, response in operation["responses"].items()
        if str(status).startswith("2")
    ]
    response_refs = {response.get("$ref") for response in success}
    assert len(response_refs) == 1
    response = success[0]
    if "$ref" in response:
        response = document["components"]["responses"][
            response["$ref"].rsplit("/", 1)[1]
        ]
    return response["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[1]


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


def test_admission_binds_a_strict_opaque_execution_context_intent() -> None:
    source = _proto("kokoro/platform/admission/v1/admission.proto")
    prepare = _message_body(source, "PrepareRunEffect")
    intent = _message_body(source, "OpaqueExecutionContextIntent")
    parent = _message_body(source, "ParentExecutionContextAnchor")

    assert (
        "OpaqueExecutionContextIntent execution_context = 12 "
        "[(buf.validate.field).required = true];"
    ) in prepare
    assert "option (buf.validate.oneof).required = true;" in intent
    assert "bool root = 1 [(buf.validate.field).bool.const = true];" in intent
    assert "ParentExecutionContextAnchor continue_from = 2;" in intent
    assert "ParentExecutionContextAnchor fork_from = 3;" in intent
    assert "string anchor = 1" in parent
    assert "max_len: 256" in parent
    assert "string digest = 2" in parent
    assert 'pattern: "^[0-9a-f]{64}$"' in parent


def test_admission_binds_the_session_owned_trigger_content_into_the_effect_digest() -> None:
    source = _proto("kokoro/platform/admission/v1/admission.proto")
    prepare = _message_body(source, "PrepareRunEffect")

    assert "string trigger_message_content = 13" in prepare
    assert "min_len: 1" in prepare
    assert "max_bytes: 524288" in prepare


def test_dispatch_owner_evidence_is_a_closed_session_owned_read_boundary() -> None:
    source = _proto("kokoro/session/dispatch/v1/dispatch_owner_evidence.proto")

    assert "package kokoro.session.dispatch.v1;" in source
    assert _service_methods(source, "DispatchOwnerEvidenceService") == [
        "GetDispatchOwnerEvidence"
    ]
    request = _message_body(source, "GetDispatchOwnerEvidenceRequest")
    assert "string site_id = 1" in request
    assert "string session_id = 2" in request
    assert "string evidence_ref = 3" in request
    for forbidden in ("project_ref", "segment_version", "kind", "payload_sha256"):
        assert forbidden not in request

    evidence = _message_body(source, "DispatchOwnerEvidence")
    assert "uint64 evidence_version = 2" in evidence
    assert "uint64 authorization_segment_version = 10" in evidence
    assert "uint64 lease_generation = 11" in evidence
    assert 'pattern: "^[0-9a-f]{64}$"' in evidence
    response = _message_body(source, "GetDispatchOwnerEvidenceResponse")
    assert "option (buf.validate.oneof).required = true;" in response
    assert "DispatchOwnerEvidence evidence = 1;" in response
    assert "DispatchOwnerEvidenceNotFound not_found = 2;" in response


def test_agent_execution_evidence_is_a_closed_agent_owned_read_boundary() -> None:
    source = _proto("kokoro/agent/execution/v1/agent_execution_evidence.proto")

    assert "package kokoro.agent.execution.v1;" in source
    assert _service_methods(source, "AgentExecutionEvidenceService") == [
        "PullDurableExecutionEvidence",
        "GetDurableExecutionEvidence",
        "GetRunDurableCheckpoint",
        "PullDurableOutputRecords",
    ]

    evidence = _message_body(source, "DurableExecutionEvidence")
    for field in (
        "string evidence_ref = 1",
        "uint64 evidence_version = 2",
        "string run_id = 3",
        "uint64 durable_seq = 4",
        "string event_id = 5",
        "DurableExecutionEvidenceKind kind = 6",
        "bytes canonical_payload = 7",
        "string payload_sha256 = 8",
        "google.protobuf.Timestamp recorded_at = 9",
        "string producer_instance_ref = 10",
        "uint64 producer_generation = 11",
    ):
        assert field in evidence
    assert "max_len: 65536" in evidence
    for forbidden in ("site_id", "project_ref", "user_id", "namespace"):
        assert forbidden not in evidence

    kinds = _enum_body(source, "DurableExecutionEvidenceKind")
    for kind in (
        "RUN_STARTED",
        "ACTION_OWNER",
        "PLAN_OWNER",
        "RUN_OWNER_COMPLETED",
        "RUN_COMPLETED",
        "RUN_FAILED",
    ):
        assert f"DURABLE_EXECUTION_EVIDENCE_KIND_{kind}" in kinds

    pull = _message_body(source, "PullDurableExecutionEvidenceRequest")
    assert "string run_id = 1" in pull
    assert "uint64 after_durable_seq = 2" in pull
    assert "uint32 page_size = 3" in pull
    assert "lte: 256" in pull

    get_request = _message_body(source, "GetDurableExecutionEvidenceRequest")
    assert "string run_id = 1" in get_request
    assert "string evidence_ref = 2" in get_request
    checkpoint = _message_body(source, "GetRunDurableCheckpointResponse")
    assert "DurableExecutionEvidence evidence = 1;" in checkpoint
    assert "DurableExecutionEvidenceNotFound not_found = 2;" in checkpoint

    canonical = _message_body(source, "DurableExecutionCanonicalPayloadV1")
    assert "option (buf.validate.oneof).required = true;" in canonical
    for payload in (
        "RunStartedEvidenceV1 run_started = 1;",
        "ActionOwnerEvidenceV1 action_owner = 2;",
        "PlanOwnerEvidenceV1 plan_owner = 3;",
        "RunOwnerCompletedEvidenceV1 run_owner_completed = 4;",
        "RunCompletedEvidenceV1 run_completed = 5;",
        "RunFailedEvidenceV1 run_failed = 6;",
    ):
        assert payload in canonical

    action_owner = _message_body(source, "ActionOwnerEvidenceV1")
    for field in (
        "ActionAwaitingKindV1 awaiting_kind = 5",
        "string description = 7",
        "repeated ActionDecisionV1 allowed_decisions = 8",
        "repeated string pending_owner_refs = 9",
        "bool editable = 10",
        "optional ActionRiskSummaryV1 risk = 11",
        "optional bytes safe_request_json = 12",
        "optional string input_schema_ref = 13",
        "optional bytes safe_input_schema_json = 14",
        "optional string safe_result_preview = 15",
    ):
        assert field in action_owner
    assert "max_len = 16384" in action_owner

    plan_owner = _message_body(source, "PlanOwnerEvidenceV1")
    for field in (
        "string summary = 5",
        "repeated PlanStepV1 steps = 6",
        "repeated PlanDecisionV1 allowed_decisions = 7",
    ):
        assert field in plan_owner
    for forbidden in ("site_id", "project_ref", "session_id", "dispatch_id", "user_id", "namespace"):
        assert forbidden not in action_owner
        assert forbidden not in plan_owner
    owner = _message_body(source, "RunOwnerCompletedEvidenceV1")
    assert "string execution_context_anchor = 1" in owner
    assert "string execution_context_digest = 2" in owner
    assert "uint64 owner_revision = 3" in owner
    completed = _message_body(source, "RunCompletedEvidenceV1")
    assert "RunCompletedEvidenceStatus status = 1" in completed
    assert "TokenUsageEvidenceV1 token_usage = 2;" in completed
    usage = _message_body(source, "TokenUsageEvidenceV1")
    assert "uint64 input_tokens = 1;" in usage
    assert "uint64 output_tokens = 2;" in usage
    failed = _message_body(source, "RunFailedEvidenceV1")
    assert "string code = 1" in failed
    assert "string error_kind = 2" in failed
    assert "string message = 3" in failed


def test_agent_durable_output_is_independent_bounded_and_digest_chained() -> None:
    source = _proto("kokoro/agent/execution/v1/agent_execution_evidence.proto")

    assert _service_methods(source, "AgentExecutionEvidenceService") == [
        "PullDurableExecutionEvidence",
        "GetDurableExecutionEvidence",
        "GetRunDurableCheckpoint",
        "PullDurableOutputRecords",
    ]
    record = _message_body(source, "DurableOutputRecord")
    for field in (
        "string output_ref = 1",
        "uint64 output_version = 2",
        "string run_id = 3",
        "uint64 output_seq = 4",
        "bytes canonical_payload = 5",
        "string payload_sha256 = 6",
        "google.protobuf.Timestamp recorded_at = 7",
        "string producer_instance_ref = 8",
        "uint64 producer_generation = 9",
    ):
        assert field in record
    assert "max_len: 65536" in record
    assert "durable_seq" not in record

    request = _message_body(source, "PullDurableOutputRecordsRequest")
    response = _message_body(source, "PullDurableOutputRecordsResponse")
    assert "uint64 after_output_seq = 2" in request
    assert "lte: 64" in request
    assert "repeated DurableOutputRecord records = 1" in response
    assert "max_items = 64" in response

    canonical = _message_body(source, "DurableOutputPayloadV1")
    assert "option (buf.validate.oneof).required = true;" in canonical
    for payload in (
        "TextDeltaOutputV1 text_delta",
        "TextSnapshotOutputV1 text_snapshot",
        "SafeReasoningSummaryOutputV1 safe_reasoning_summary",
        "ToolStartedOutputV1 tool_started",
        "ToolFinishedOutputV1 tool_finished",
        "PlanProgressOutputV1 plan_progress",
        "SubagentProgressOutputV1 subagent_progress",
            "MediaOperationReferenceOutputV1 media_operation_reference",
        "NoticeOutputV1 notice",
        "ErrorOutputV1 error",
    ):
        assert payload in canonical
    assert "raw_reasoning" not in source
    assert "reasoning_token" not in source

    snapshot = _message_body(source, "TextSnapshotOutputV1")
    assert "uint64 replaces_through_output_seq = 3;" in snapshot
    media_reference = _message_body(source, "MediaOperationReferenceOutputV1")
    assert "string agent_media_command_ref = 2" in media_reference
    assert "string operation_ref = 3" in media_reference

    subagent = _message_body(source, "SubagentProgressOutputV1")
    notice = _message_body(source, "NoticeOutputV1")
    error = _message_body(source, "ErrorOutputV1")
    assert "SubagentProgressStatusV1 status = 2" in subagent
    assert "string notice_ref = 1" in notice
    assert "NoticeSeverityV1 severity = 4" in notice
    assert "optional OutputRetryClassV1 retry_class = 5" in notice
    assert "string error_ref = 1" in error
    assert "OutputRetryClassV1 retry_class = 4" in error

    started = _message_body(source, "ToolStartedOutputV1")
    finished = _message_body(source, "ToolFinishedOutputV1")
    assert "string tool_call_id = 1" in started
    assert "bytes redacted_input_summary_json = 3" in started
    assert "string tool_call_id = 1" in finished
    assert "string safe_result_preview = 2" in finished
    assert "max_bytes: 16384" in finished

    completed = _message_body(source, "RunCompletedEvidenceV1")
    failed = _message_body(source, "RunFailedEvidenceV1")
    assert "uint64 output_high_watermark = 3" in completed
    assert "string output_digest_sha256 = 4" in completed
    assert "uint64 output_high_watermark = 4" in failed
    assert "string output_digest_sha256 = 5" in failed
    assert "chain0 = SHA256('kokoro-output-chain-v1\\0' || UTF8(run_id))" in source
    assert "chainN = SHA256(prev || UINT64_BE(output_seq) || HEX_DECODE(payload_sha256))" in source

    boundaries = json.loads((CONTRACT / "registry/boundaries.yaml").read_text())["boundaries"]
    boundary = next(item for item in boundaries if item["id"] == "agent-execution-evidence")
    assert "PullDurableOutputRecords" in {operation["id"] for operation in boundary["operations"]}


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
    shared = _proto("kokoro/platform/admin/v2/admin_shared.proto")
    query = _proto("kokoro/platform/admin/v2/admin_query.proto")
    command = _proto("kokoro/platform/admin/v2/admin_command.proto")
    lifecycle = _proto("kokoro/platform/site/v1/site_lifecycle.proto")

    assert _service_methods(identity, "AdminIdentityService") == [
        "BeginOperatorLogin",
        "ExchangeOidcSession",
        "GetOperatorSessionDelivery",
        "BeginStepUp",
        "CompleteStepUp",
        "SignOut",
    ]
    assert _service_methods(query, "AdminQueryService") == [
        "GetSite",
        "ListSites",
        "GetUserWithinSite",
        "GetAuditWithinScope",
        "GetCurrentOperator",
        "GetOperator",
        "ListOperators",
        "ListPendingApprovals",
    ]
    assert _service_methods(command, "AdminCommandService") == [
        "SubmitCommand",
        "DecideApproval",
        "GetReceipt",
    ]
    assert _service_methods(lifecycle, "SiteLifecycleService") == [
        "RequestActivationApproval",
        "ApproveAndActivate",
    ]
    assert "service " not in shared
    assert "AdminCommandService" not in query
    assert "AdminQueryService" not in command
    assert not (PROTO / "kokoro/platform/admin/v2/admin_control.proto").exists()


def test_admin_commerce_has_an_exact_typed_surface_and_never_exposes_persisted_secrets() -> None:
    service = _proto("kokoro/platform/commerce/v1/admin_commerce.proto")
    commerce = "\n".join((
        service,
        _proto("kokoro/platform/commerce/v1/commerce_catalog.proto"),
        _proto("kokoro/platform/commerce/v1/commerce_control.proto"),
    ))

    assert _service_methods(service, "AdminCommerceService") == [
        "PublishPlanRevision", "ListPlanRevisions", "GetPlanRevision",
        "PublishOfferRevision", "ListOfferRevisions", "GetOfferRevision",
        "PublishOfferPriceRevision", "ListOfferPriceRevisions", "GetOfferPriceRevision",
        "PublishFulfillmentProgramRevision", "ListFulfillmentProgramRevisions",
        "GetFulfillmentProgramRevision", "PublishRedemptionProgramRevision",
        "ListRedemptionProgramRevisions", "GetRedemptionProgramRevision",
        "RequestSiteCommerceAssignmentPromotion", "DecideSiteCommerceAssignmentPromotion",
        "ListSiteCommerceAssignments", "GetSiteCommerceAssignment",
        "RequestCodeBatchIssuance", "DecideCodeBatchIssuance",
        "RequestCodeBatchTransition", "DecideCodeBatchTransition",
        "EmergencySuspendCodeBatch", "BeginCodeBatchDelivery",
        "ReadCodeDeliveryRange", "AcknowledgeCodeDeliveryRange",
        "GetCodeDeliverySession", "ListCodeBatches", "GetCodeBatch",
        "RequestSourceCorrection", "DecideSourceCorrection",
        "ListSourceCorrections", "GetSourceCorrection",
        "RequestCommerceReconciliationResolution",
        "DecideCommerceReconciliationResolution",
        "ListCommerceReconciliations", "GetCommerceReconciliation",
        "GetCommerceApproval", "GetCommerceExecution",
        "GetGlobalCommerceCommandReceipt", "GetSiteCommerceCommandReceipt",
    ]
    assert "message CommerceGlobalCommandContext" in commerce
    assert "message CommerceGlobalQueryContext" in commerce
    assert "message CommerceSiteCommandContext" in commerce
    assert "message CommerceSiteQueryContext" in commerce
    assert "AuthenticatedOperatorCommandContext operator" in commerce
    assert "AuthenticatedOperatorQueryContext operator" in commerce
    assert "raw_codes" not in commerce
    assert "EncryptedCodeDelivery" not in commerce
    assert "bytes ciphertext" not in commerce
    assert "CommerceApprovalAnchor" not in commerce
    assert "CreditProgramRevisionBinding" in commerce
    assert "EntitlementTemplateRevisionBinding" in commerce
    assert "google.protobuf.Struct" not in commerce
    assert "rpc Route" not in commerce
    assert "string action" not in commerce


def test_admin_credit_has_safe_reads_and_a_typed_reconciliation_exit() -> None:
    credit = _proto("kokoro/platform/credit/v1/admin_credit.proto")
    credit_catalog = _proto("kokoro/platform/credit/v1/credit_catalog.proto")

    assert _service_methods(credit, "AdminCreditService") == [
        "PublishCreditProgramRevision",
        "ListCreditProgramRevisions",
        "GetCreditProgramRevision",
        "GetCreditGlobalCommandReceipt",
        "GetSiteCreditSummary",
        "ListCreditAccounts",
        "GetCreditAccount",
        "ListCreditGrants",
        "ListCreditHolds",
        "ListCreditHoldAllocations",
        "ListCreditJournalTransactions",
        "ListCreditJournalEntries",
        "ListRatedUsage",
        "ListRatedUsageSourceAllocations",
        "RequestCreditReconciliationResolution",
        "DecideCreditReconciliationResolution",
        "GetCreditReconciliationResolution",
    ]
    assert "CreditSiteQueryContext authority" in credit
    assert "CreditSiteCommandContext authority" in credit
    assert "CreditProgramRevisionView" in credit_catalog
    assert "maximum_program_balance_per_account_minor" in credit_catalog
    assert "maximum_account_balance_minor" not in credit_catalog
    assert "consumption_order" not in credit_catalog
    assert "bucket rank (daily, period, permanent)" in credit_catalog
    assert "effective expiry (NULLS LAST)" in credit_catalog
    assert "CreditReadFreshness freshness" in _message_body(credit, "SiteCreditSummary")
    assert "CREDIT_READ_FRESHNESS_AUTHORITATIVE_DATABASE_OBSERVATION" in credit
    assert "CREDIT_READ_FRESHNESS_AUTHORITATIVE_TRANSACTION_SNAPSHOT" not in credit
    assert "google.protobuf.Timestamp as_of" in _message_body(credit, "SiteCreditSummary")
    for message in (
        "CreditBalanceSummary",
        "CreditGrantSummary",
        "CreditHoldSummary",
        "CreditJournalEntrySummary",
        "RatedUsageSummary",
    ):
        assert "string" in _message_body(credit, message)
    for request in (
        "ListCreditGrantsRequest",
        "ListCreditHoldsRequest",
        "ListCreditJournalTransactionsRequest",
        "ListRatedUsageRequest",
    ):
        body = _message_body(credit, request)
        assert "optional CreditGrantSourceType source_type" in body
        assert "optional string source_ref" in body
    for request in (
        "ListCreditGrantsRequest",
        "ListCreditHoldsRequest",
        "ListRatedUsageRequest",
    ):
        assert "optional string credit_grant_id" in _message_body(credit, request)
    for response in (
        "ListCreditAccountsResponse",
        "ListCreditGrantsResponse",
        "ListCreditHoldsResponse",
        "ListCreditHoldAllocationsResponse",
        "ListCreditJournalTransactionsResponse",
        "ListCreditJournalEntriesResponse",
        "ListRatedUsageResponse",
        "ListRatedUsageSourceAllocationsResponse",
    ):
        body = _message_body(credit, response)
        assert "google.protobuf.Timestamp membership_watermark" in body
        assert "google.protobuf.Timestamp observed_at" in body
        assert "google.protobuf.Timestamp as_of" not in body
    hold_allocation = _message_body(credit, "CreditHoldAllocationSummary")
    for field in (
        "string credit_hold_ref",
        "string credit_grant_id",
        "string allocated_amount",
        "uint32 allocation_ordinal",
    ):
        assert field in hold_allocation
    usage_allocation = _message_body(credit, "RatedUsageSourceAllocationSummary")
    for field in (
        "string rated_usage_ref",
        "string settlement_ref",
        "string credit_grant_id",
        "CreditUsageSourceDirection direction",
        "string amount",
        "uint32 allocation_ordinal",
    ):
        assert field in usage_allocation
    assert "google.protobuf.Struct" not in credit
    assert "bytes raw" not in credit
    assert "provider_payload" not in credit
    assert "evidence_payload" not in credit
    assert "rating_snapshot" not in credit
    assert "liability_merchant_account_ref" not in credit
    assert "CommandReceiptV2 receipt" in _message_body(
        credit, "RequestCreditReconciliationResolutionResponse"
    )


def test_wave1_commands_freeze_identity_axes_scope_and_receipts() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")
    shared = _proto("kokoro/platform/admin/v2/admin_shared.proto")
    query = _proto("kokoro/platform/admin/v2/admin_query.proto")
    command = _proto("kokoro/platform/admin/v2/admin_command.proto")
    lifecycle = _proto("kokoro/platform/site/v1/site_lifecycle.proto")
    blob = "\n".join((identity, shared, query, command, lifecycle))

    assert "message AuthenticatedOperatorCommandContext" in shared
    for field in (
        "kokoro.common.v2.CommandIdentityV2 command",
        "string environment",
        "string region",
        "string managed_device_ref",
        "SecurityEpochs security_epochs",
        "OperatorScope scope",
        "string actor_ref",
        "uint64 operator_generation",
        "kokoro.common.v2.OperatorAssuranceLevel assurance_level",
        "repeated string factor_classes",
        "google.protobuf.Timestamp authenticated_at",
        "google.protobuf.Timestamp step_up_at",
        "string operator_attestation_ref",
        "string operator_attestation_digest",
    ):
        assert field in shared
    assert "oneof kind" in shared
    assert "SiteScope site" in shared
    assert "GlobalScope global" in shared
    assert "BreakGlassScope breakglass" in shared
    assert "string incident_id" in shared
    assert "repeated string field_allowlist" in shared
    assert "kokoro.common.v2.CommandReceiptV2 receipt" in blob
    assert "CommandIdentityV2" not in _message_body(
        shared, "AuthenticatedOperatorQueryContext"
    )
    assert "authorization_code" in identity
    assert "id_token" not in identity


def test_admin_command_v2_is_submit_queue_worker_and_receipt_only() -> None:
    command = _proto("kokoro/platform/admin/v2/admin_command.proto")

    for legacy in (
        "PrepareCommand",
        "SubmitForApproval",
        "ExecuteApproved",
        "prepared_command_ref",
    ):
        assert legacy not in command

    submit = _message_body(command, "SubmitCommandResponse")
    submit_state = _enum_body(command, "SubmitCommandState")
    assert "SUBMIT_COMMAND_STATE_PENDING_APPROVAL" in submit_state
    assert "optional string approval_ref" in submit
    assert "kokoro.common.v2.CommandReceiptV2 receipt" in submit

    approval = _message_body(command, "DecideApprovalResponse")
    approval_state = _enum_body(command, "ApprovalDecisionState")
    for state in (
        "APPROVAL_DECISION_STATE_EXECUTION_QUEUED",
        "APPROVAL_DECISION_STATE_REJECTED",
        "APPROVAL_DECISION_STATE_DENIED",
    ):
        assert state in approval_state
    assert "ApprovalDecisionState state" in approval
    assert "kokoro.common.v2.CommandReceiptV2 receipt" in approval

    assert "DecidePostEffectReview" not in command
    assert "post_effect_review" not in command
    assert "Platform Worker is the sole authority" in command


def test_admin_command_v2_advertises_only_the_real_worker_owned_authority_aggregate() -> None:
    command = _proto("kokoro/platform/admin/v2/admin_command.proto")
    effect = _message_body(command, "SubmitCommandEffect")
    change = _message_body(command, "ChangeOperatorAuthority")

    assert "ChangeOperatorAuthority change" in effect
    assert "oneof change" not in effect
    for unowned in (
        "DisableUserChange",
        "UpdateOperatorScopeChange",
        "UpdatePolicyChange",
        "disable_user",
        "update_policy",
    ):
        assert unowned not in command
    for field in (
        "OperatorAuthorityChangeAction action",
        "string operator_ref",
        "uint64 operator_generation",
        "optional uint64 expected_authorization_epoch",
        "repeated string permissions",
        "repeated string site_ids",
        "repeated string environments",
        "repeated string regions",
        "google.protobuf.Timestamp expires_at",
        "google.protobuf.Timestamp break_glass_expires_at",
    ):
        assert field in change
    for action in ("PROVISION", "REPLACE", "SUSPEND", "REVOKE"):
        assert f"OPERATOR_AUTHORITY_CHANGE_ACTION_{action}" in command


def test_authenticated_operator_axes_are_exactly_canonical_and_attested() -> None:
    shared = _proto("kokoro/platform/admin/v2/admin_shared.proto")
    envelope = _proto("kokoro/common/v2/command_envelope.proto")
    command_context = _message_body(shared, "AuthenticatedOperatorCommandContext")
    query_context = _message_body(shared, "AuthenticatedOperatorQueryContext")
    canonical = _message_body(envelope, "CanonicalCommandTrustAxesV2")

    for context in (command_context, query_context):
        for field in (
            "actor_ref",
            "operator_generation",
            "assurance_level",
            "factor_classes",
            "authenticated_at",
            "step_up_at",
            "operator_attestation_ref",
            "operator_attestation_digest",
        ):
            assert field in context
        assert 'pattern: "^[0-9a-f]{64}$"' in context

    for field in (
        "actor_generation",
        "assurance_level",
        "factor_classes",
        "authenticated_at",
        "step_up_at",
        "operator_attestation_ref",
        "operator_attestation_digest",
    ):
        assert field in canonical
    assurance = _enum_body(envelope, "OperatorAssuranceLevel")
    assert "OPERATOR_ASSURANCE_LEVEL_PASSWORD" in assurance
    assert "OPERATOR_ASSURANCE_LEVEL_MFA" in assurance
    assert "OPERATOR_ASSURANCE_LEVEL_PHISHING_RESISTANT" in assurance


def test_site_lifecycle_is_typed_and_not_a_generic_admin_effect() -> None:
    control = _proto("kokoro/platform/admin/v2/admin_command.proto")
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
    for effect in ("ActivationFacts", "RequestActivationApprovalEffect", "ApproveAndActivateEffect"):
        assert f"message {effect}" in lifecycle


def test_admin_login_contexts_do_not_require_an_operator_before_oidc_exchange() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")
    shared = _proto("kokoro/platform/admin/v2/admin_shared.proto")

    pre_login = _message_body(identity, "AdminPreLoginWorkloadContext")
    transaction = _message_body(identity, "AdminAuthTransactionContext")
    authenticated = _message_body(shared, "AuthenticatedOperatorCommandContext")
    assert "OperatorScope" not in pre_login + transaction
    assert "SecurityEpochs" not in pre_login + transaction
    assert "OperatorScope scope" in authenticated
    assert "SecurityEpochs security_epochs" in authenticated

    begin = _message_body(identity, "BeginOperatorLoginEffect")
    begin_fields = re.findall(r"\bstring\s+(\w+)\s*=", begin)
    assert set(begin_fields).isdisjoint(
        {
            "issuer",
            "audience",
            "redirect_uri",
            "pkce_challenge",
            "pkce_verifier",
            "nonce",
        }
    )
    assert begin_fields == ["return_intent_ref"]
    begin_effect = _message_body(identity, "BeginOperatorLoginEffect")
    assert "^[a-z][a-z0-9_.-]{0,127}$" in begin_effect
    assert "registered allowlist" in begin_effect
    exchange = _message_body(identity, "ExchangeOidcSessionEffect")
    assert re.findall(r"\bstring\s+(\w+)\s*=", exchange) == [
        "transaction_ref",
        "authorization_code",
    ]
    assert "Platform generates" in identity
    assert "PKCE verifier" in identity
    assert "nonce" in identity


def test_public_operations_have_exact_implementable_response_schemas() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    operations = _public_operations()
    expected = {
        "exchangeProductContext": "ProductContextExchangeResponse",
        "issueSessionAccessGrant": "SessionAccessGrantResponse",
        "beginRegistration": "EmailVerificationTransactionResponse",
        "completeEmailVerification": "VerificationActivationResponse",
        "resendEmailVerification": "EmailVerificationTransactionResponse",
        "createIdentitySession": "CreateSessionResponse",
        "completeSessionMfa": "SessionCredentialPairResponse",
        "refreshIdentitySession": "SessionCredentialPairResponse",
        "listIdentitySessions": "IdentitySessionList",
        "revokeIdentitySessions": "CommandReceiptResponse",
        "beginPasswordReset": "PasswordResetTransactionResponse",
        "completePasswordReset": "CommandReceiptResponse",
        "changePassword": "SessionCredentialPairResponse",
        "beginEmailChange": "EmailChangeTransactionResponse",
        "completeEmailChange": "SessionCredentialPairResponse",
        "beginTotpEnrollment": "TotpEnrollmentTransactionResponse",
        "confirmTotpEnrollment": "RecoveryCodeSetResponse",
        "disableTotp": "CommandReceiptResponse",
        "regenerateRecoveryCodes": "RecoveryCodeSetResponse",
        "beginAccountRecovery": "AccountRecoveryTransactionResponse",
        "completeAccountRecovery": "AccountRecoveryCompletionResponse",
        "reauthenticateIdentitySession": "ReauthenticationResponse",
        "getPersonalContext": "PersonalContext",
        "previewRedemption": "RedemptionPreviewResponse",
        "confirmRedemption": "RedemptionCommandResponse",
        "recoverRedemptionCommand": "RedemptionCommandResponse",
        "getRedemptionReceipt": "RedemptionReceiptResponse",
        "listAccountProducts": "AccountProductsResponse",
        "getCreditSummary": "CreditSummaryResponse",
        "getCreditGrant": "CreditGrantResponse",
        "getUsageDetail": "UsageDetailResponse",
        "createAssetUploadIntent": "AssetUploadIntentResponse",
        "completeAssetUpload": "AssetUploadCommandResponse",
        "getAssetUploadStatus": "AssetUploadStatusResponse",
        "recoverAssetUploadCommand": "AssetUploadCommandResponse",
        "getTrustedAssetGrant": "TrustedAssetGrantResponse",
        "listMediaOperationDefinitions": "MediaOperationDefinitionPage",
        "getMediaOperationDefinition": "MediaOperationDefinitionResponse",
        "listMediaOperationModelOptions": "MediaDefinitionModelOptionPage",
        "quoteMediaOperation": "MediaOperationQuoteResponse",
        "submitMediaOperation": "MediaOperationCommandResponse",
        "listMediaOperations": "MediaOperationPage",
        "getMediaOperation": "MediaOperationResponse",
        "cancelMediaOperation": "MediaOperationCommandResponse",
        "recoverMediaOperationCommand": "MediaOperationCommandResponse",
        "listArtifacts": "ArtifactPage",
        "getArtifact": "ArtifactResponse",
        "listArtifactVersions": "ArtifactVersionPage",
        "getArtifactVersion": "ArtifactVersionResponse",
        "issueArtifactDeliveryAuthorization": "ArtifactDeliveryAuthorizationResponse",
        "revokeArtifactDeliveryAuthorization": "ArtifactDeliveryRevocationResponse",
        "getPublicCommandReceipt": "PublicCommandReceiptResponse",
    }

    assert set(operations) == set(expected) | {"redeemArtifactDeliveryAuthorization"}
    assert {
        operation_id: _response_schema(document, operation)
        for operation_id, operation in operations.items()
        if operation_id != "redeemArtifactDeliveryAuthorization"
    } == expected


def test_asset_public_surface_is_owner_scoped_and_non_disclosing() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    operations = _public_operations()
    schemas = document["components"]["schemas"]

    for operation_id in (
        "createAssetUploadIntent",
        "completeAssetUpload",
        "getAssetUploadStatus",
        "recoverAssetUploadCommand",
        "getTrustedAssetGrant",
    ):
        operation = operations[operation_id]
        assert operation["security"] == [{"ProductWorkload": [], "UserSession": []}]
        assert "{projectRef}" in next(
            path
            for path, item in document["paths"].items()
            if operation in item.values()
        )

    create_response = document["components"]["responses"]["AssetUploadIntentResponse"]
    recovery_response = document["components"]["responses"]["AssetUploadCommandResponse"]
    assert create_response["headers"]["Cache-Control"]["schema"]["const"] == "no-store"
    assert recovery_response["headers"]["Cache-Control"]["schema"]["const"] == "no-store"

    receipt = yaml.safe_dump(schemas["AssetUploadOwnerReceipt"]["properties"]).lower()
    status = yaml.safe_dump(schemas["AssetUploadStatus"]["properties"]).lower()
    grant = schemas["TrustedAssetGrant"]
    for forbidden in (
        "credential",
        "presigned",
        "bucket",
        "storagekey",
        "quarantineobject",
        "provideretag",
    ):
        assert forbidden not in receipt
        assert forbidden not in status
    assert set(grant["required"]) >= {
        "assetRef",
        "assetVersionRef",
        "assetGrantRef",
        "projectRef",
        "purpose",
        "subjectGeneration",
        "eligibilityEpoch",
        "state",
    }
    assert "siteRef" not in grant["properties"]
    assert {
        "ASSET_NOT_ACCEPTED",
        "ASSET_UPLOAD_CONFLICT",
        "ASSET_QUOTA_EXCEEDED",
        "ASSET_TEMPORARILY_UNAVAILABLE",
    }.issubset(set(schemas["ErrorCode"]["enum"]))


def test_asset_data_plane_is_capability_scoped_resumable_and_provider_neutral() -> None:
    document = yaml.safe_load(ASSET_DATA_PLANE_OPENAPI.read_text())
    operations = {
        operation["operationId"]: operation
        for item in document["paths"].values()
        for operation in item.values()
        if isinstance(operation, dict) and "operationId" in operation
    }
    authenticated_operation_ids = {
        "initiateAssetMultipartUpload",
        "putAssetMultipartPart",
        "completeAssetMultipartUpload",
        "abortAssetMultipartUpload",
        "getAssetMultipartUploadStatus",
    }
    preflight_operation_ids = {
        "preflightInitiateAssetMultipartUpload",
        "preflightPutAssetMultipartPart",
        "preflightCompleteAssetMultipartUpload",
        "preflightAbortAssetMultipartUpload",
        "preflightGetAssetMultipartUploadStatus",
    }
    assert set(operations) == authenticated_operation_ids | preflight_operation_ids
    assert all(
        operation.get("security", document["security"])
        == [{"AssetUploadCapability": []}]
        for operation_id, operation in operations.items()
        if operation_id in authenticated_operation_ids
    )
    assert all(operations[operation_id]["security"] == [] for operation_id in preflight_operation_ids)
    schemas = document["components"]["schemas"]
    wire = yaml.safe_dump(
        {
            name: schemas[name]
            for name in (
                "MultipartCommandReceipt",
                "MultipartPart",
                "MultipartUploadState",
                "MultipartPartResponse",
                "MultipartUploadStateResponse",
            )
        }
    ).lower()
    for forbidden in (
        "bucket",
        "objectref",
        "objectkey",
        "providerupload",
        "provideretag",
        "presigned",
        "accesskey",
        "secretkey",
    ):
        assert forbidden not in wire
    assert schemas["MultipartUploadState"]["properties"]["parts"]["maxItems"] == 10000
    assert "integrity_rejected" in schemas["MultipartCommandReceipt"]["properties"]["state"]["enum"]
    assert "integrity_rejected" in schemas["MultipartUploadState"]["properties"]["state"]["enum"]
    assert schemas["MultipartUploadState"]["properties"]["safeReasonCode"]["type"] == [
        "string",
        "null",
    ]
    assert schemas["MultipartPartCommit"]["properties"]["partNumber"]["maximum"] == 10000
    assert set(schemas["CompleteMultipartUploadInput"]["required"]) == {
        "expectedVersion",
        "expectedSize",
        "expectedChecksumSha256",
        "parts",
    }
    for response_name in ("MultipartPartResponse", "MultipartUploadStateResponse"):
        headers = document["components"]["responses"][response_name]["headers"]
        assert headers["Cache-Control"]["schema"]["const"] == "no-store"
        origin = headers["Access-Control-Allow-Origin"]["schema"]
        assert origin["pattern"] == (
            r"^https://(?:[A-Za-z0-9.-]+|\[[0-9A-Fa-f:.]+\])"
            r"(?::[1-9][0-9]{0,4})?$"
        )
        assert "const" not in origin
        assert headers["Vary"]["schema"]["const"] == "Origin"

    responses = document["components"]["responses"]
    assert responses["PostPreflightResponse"]["headers"]["Access-Control-Allow-Methods"][
        "schema"
    ]["const"] == "POST, OPTIONS"
    assert responses["PutPreflightResponse"]["headers"]["Access-Control-Allow-Methods"][
        "schema"
    ]["const"] == "PUT, OPTIONS"
    assert responses["GetPreflightResponse"]["headers"]["Access-Control-Allow-Methods"][
        "schema"
    ]["const"] == "GET, OPTIONS"
    assert responses["PostPreflightResponse"]["headers"]["Access-Control-Max-Age"][
        "schema"
    ]["const"] == 300
    put_allowed_headers = responses["PutPreflightResponse"]["headers"][
        "Access-Control-Allow-Headers"
    ]["schema"]["const"]
    assert "x-kokoro-content-length" in put_allowed_headers
    assert "x-kokoro-content-sha256" in put_allowed_headers
    assert document["components"]["parameters"]["ContentLength"]["name"] == (
        "X-Kokoro-Content-Length"
    )
    assert document["components"]["responses"]["ErrorResponse"]["headers"][
        "Access-Control-Allow-Origin"
    ]["required"] is False

    complete_description = operations["completeAssetMultipartUpload"]["description"].lower()
    assert "streaming the completed quarantine object" in complete_description
    assert "multipart etag" in complete_description
    assert "never accepted" in complete_description
    assert "integrity_rejected" in complete_description
    assert "only transport ambiguity" in complete_description


def test_public_auth_and_personal_context_payloads_are_complete() -> None:
    schemas = yaml.safe_load(PUBLIC_OPENAPI.read_text())["components"]["schemas"]

    assert schemas["CommandReceipt"]["properties"]["state"]["const"] == "committed"
    assert "committedAt" in schemas["CommandReceipt"]["required"]
    assert set(schemas["AuthPending"]["required"]) >= {
        "transactionRef",
        "challengeKind",
        "expiresAt",
    }
    assert set(schemas["SessionCredentialPair"]["required"]) >= {
        "sessionCredential",
        "sessionCredentialExpiresAt",
        "refreshCredential",
        "refreshCredentialExpiresAt",
    }
    assert set(schemas["IdentitySessionList"]["required"]) >= {"sessions"}
    assert set(schemas["PersonalContext"]["required"]) >= {
        "productContextRef",
        "personalContextRef",
        "actor",
        "projects",
        "defaultProjectRef",
        "contextRevision",
    }
    for transaction_schema in (
        "EmailVerificationTransaction",
        "EmailChangeTransaction",
        "PasswordResetTransaction",
        "AccountRecoveryTransaction",
        "TotpEnrollmentTransaction",
    ):
        assert {"transactionRef", "expiresAt"}.issubset(
            schemas[transaction_schema]["required"]
        )


def test_one_time_public_payloads_are_no_store_and_never_receipt_replayable() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    operations = _public_operations()
    for operation_id in (
        "beginTotpEnrollment",
        "confirmTotpEnrollment",
        "regenerateRecoveryCodes",
    ):
        response = operations[operation_id]["responses"]["200"]
        if "$ref" in response:
            response = document["components"]["responses"][
                response["$ref"].rsplit("/", 1)[1]
            ]
        assert response["headers"]["Cache-Control"]["schema"]["const"] == "no-store"

    receipt = document["components"]["schemas"]["PublicCommandReceiptResponse"]
    serialized = yaml.safe_dump(receipt).lower()
    for forbidden in ("credential", "secret", "code", "otpauth", "recoverycodes"):
        assert forbidden not in serialized
    assert "oneOf" in receipt


def test_public_secret_delivery_is_separate_and_retry_requires_supersession() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    schemas = document["components"]["schemas"]

    response_alternatives = {}
    for response_schema in (
        "CreateSessionResponse",
        "SessionCredentialPairResponse",
        "TotpEnrollmentTransactionResponse",
        "RecoveryCodeSetResponse",
        "ReauthenticationResponse",
    ):
        alternatives = {
            item["$ref"].rsplit("/", 1)[1]
            for item in schemas[response_schema]["oneOf"]
        }
        response_alternatives[response_schema] = alternatives
        assert "OneTimeDeliveryUnavailable" in alternatives
    assert "AuthPendingResponse" in response_alternatives["CreateSessionResponse"]
    assert "ReauthenticationPendingResponse" in response_alternatives[
        "ReauthenticationResponse"
    ]

    recovery_alternatives = {
        item["$ref"].rsplit("/", 1)[1]
        for item in schemas["AccountRecoveryCompletionResponse"]["oneOf"]
    }
    assert "OneTimeDeliveryUnavailable" in recovery_alternatives
    assert "OneTimeTotpRecoveryEnrollmentDelivery" in recovery_alternatives
    assert "receipt" not in schemas["OneTimeTotpRecoveryEnrollmentDelivery"][
        "properties"
    ]

    for delivery_schema in (
        "OneTimeSessionCredentialDelivery",
        "OneTimeTotpEnrollmentDelivery",
        "OneTimeRecoveryCodeSetDelivery",
        "OneTimeReauthenticationProofDelivery",
    ):
        delivery = schemas[delivery_schema]
        assert {"commandId", "requestDigest"}.issubset(delivery["required"])
        assert "receipt" not in delivery["properties"]

    supersede = schemas["SupersedingCeremony"]
    assert {
        "transactionRef",
        "operationId",
        "bindingDigest",
        "expiresAt",
        "invalidatesPriorDelivery",
    }.issubset(supersede["required"])
    assert "capability" not in supersede["properties"]
    assert supersede["properties"]["invalidatesPriorDelivery"]["const"] is True


def test_public_secret_commands_have_an_executable_lost_response_path() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    operations = _public_operations()
    schemas = document["components"]["schemas"]

    request_unions = {
        "createIdentitySession": (
            "CreateSessionInput",
            "SupersedeSessionCredentialDeliveryInput",
        ),
        "completeSessionMfa": (
            "SessionMfaCompletionInput",
            "SupersedeSessionCredentialDeliveryInput",
        ),
        "refreshIdentitySession": (
            "RefreshSessionInput",
            "SupersedeRefreshCredentialDeliveryInput",
        ),
        "beginTotpEnrollment": (
            "TotpEnrollmentStartInput",
            "SupersedeTotpEnrollmentInput",
        ),
        "regenerateRecoveryCodes": (
            "RecoveryCodeRegenerationInput",
            "SupersedeRecoveryCodeSetInput",
        ),
        "reauthenticateIdentitySession": (
            "ReauthenticationInput",
            "SupersedeReauthenticationProofInput",
        ),
    }
    for operation_id, (union_schema, superseding_schema) in request_unions.items():
        request_ref = operations[operation_id]["requestBody"]["$ref"]
        request_body = document["components"]["requestBodies"][
            request_ref.rsplit("/", 1)[1]
        ]
        assert request_body["content"]["application/json"]["schema"]["$ref"].endswith(
            f"/{union_schema}"
        )
        alternatives = {
            item["$ref"].rsplit("/", 1)[1]
            for item in schemas[union_schema]["oneOf"]
        }
        assert superseding_schema in alternatives
        assert "receiptReadCapability" not in schemas[superseding_schema].get(
            "properties", {}
        )
        parameter_refs = {
            parameter["$ref"].rsplit("/", 1)[1]
            for parameter in operations[operation_id]["parameters"]
        }
        assert "ReceiptRecoveryCapability" not in parameter_refs
        assert "ReceiptRecoveryCapabilityLookup" not in parameter_refs
        assert "SupersedingCeremonyCapability" not in parameter_refs

    for first_claim_input in (
        "PasswordLoginInput",
        "CompleteSessionMfaInput",
        "RefreshCredentialInput",
        "PasswordChangeInput",
        "EmailChangeCompletionInput",
        "BeginTotpEnrollmentInput",
        "TotpConfirmationInput",
        "RegenerateRecoveryCodesInput",
        "PasswordReauthenticationInput",
        "MfaReauthenticationInput",
        "BeginTotpRecoveryReplacementInput",
    ):
        assert "receiptReadCapability" not in schemas[first_claim_input].get(
            "properties", {}
        )

    password_login = schemas["PasswordLoginInput"]
    assert "returnIntentRef" in password_login["properties"]
    assert "returnIntent" not in password_login["properties"]
    assert "registered allowlist" in password_login["properties"]["returnIntentRef"][
        "description"
    ]
    receipt_capability = document["components"]["securitySchemes"][
        "ReceiptRecoveryCapability"
    ]
    assert receipt_capability["type"] == "apiKey"
    assert receipt_capability["name"] == "X-Kokoro-Receipt-Recovery-Capability"
    assert receipt_capability["in"] == "header"
    assert "caller-generated" in receipt_capability["description"]
    assert "does not consume" in receipt_capability["description"]
    assert "atomically consumes" in receipt_capability["description"]

    for operation_id in (
        "completeEmailVerification",
        "createIdentitySession",
        "completeSessionMfa",
        "refreshIdentitySession",
        "completePasswordReset",
        "completeAccountRecovery",
    ):
        assert operations[operation_id]["security"] == [
            {"ProductWorkload": [], "ReceiptRecoveryCapability": []}
        ]

    for operation_id in (
        "changePassword",
        "completeEmailChange",
        "beginTotpEnrollment",
        "confirmTotpEnrollment",
        "regenerateRecoveryCodes",
        "reauthenticateIdentitySession",
    ):
        assert operations[operation_id]["security"] == [
            {
                "ProductWorkload": [],
                "UserSession": [],
                "ReceiptRecoveryCapability": [],
            }
        ]

    for operation_id in (
        "exchangeProductContext",
        "beginRegistration",
        "resendEmailVerification",
        "revokeIdentitySessions",
        "beginPasswordReset",
        "beginEmailChange",
        "disableTotp",
        "beginAccountRecovery",
    ):
        parameter_refs = {
            parameter["$ref"].rsplit("/", 1)[1]
            for parameter in operations[operation_id]["parameters"]
        }
        assert "ReceiptRecoveryCapability" not in parameter_refs


def test_public_anonymous_recovery_receipts_are_capability_and_transaction_bound() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    operation = document["paths"]["/v1/commands/{id}/receipt"]["get"]
    security = operation["security"]
    assert security == [
        {"ProductWorkload": [], "UserSession": []},
        {"ProductWorkload": [], "ReceiptRecoveryCapability": []},
    ]

    parameter_refs = {
        parameter["$ref"].rsplit("/", 1)[1] for parameter in operation["parameters"]
    }
    assert {"CommandId", "ContractVersion"}.issubset(parameter_refs)
    assert "ReceiptRecoveryCapability" not in parameter_refs
    assert "ReceiptRecoveryCapabilityLookup" not in parameter_refs
    assert "RequestDigest" not in parameter_refs
    assert "RecoveryTransactionRef" not in parameter_refs
    assert "RecoveryPurpose" not in parameter_refs
    description = operation["description"]
    for binding in (
        "workload-derived Site",
        "purpose",
        "transaction",
        "command",
        "subject generation",
        "not-found",
        "login",
        "MFA",
        "refresh",
    ):
        assert binding in description
    assert "does not require the caller to know the server-side request digest" in description
    assert "does not consume" in description

    schemas = document["components"]["schemas"]
    assert "receiptReadCapability" not in schemas["PasswordInput"].get(
        "properties", {}
    )
    for recovery_input in (
        "PasswordRecoveryCompletionInput",
        "BeginTotpRecoveryReplacementInput",
        "ConfirmTotpRecoveryReplacementInput",
    ):
        assert "receiptReadCapability" not in schemas[recovery_input].get(
            "properties", {}
        )


def test_account_recovery_binds_password_or_confirmed_totp_replacement() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    schemas = document["components"]["schemas"]
    recovery = schemas["RecoveryInput"]
    alternatives = [item["$ref"].rsplit("/", 1)[1] for item in recovery["oneOf"]]
    assert alternatives == [
        "PasswordRecoveryCompletionInput",
        "BeginTotpRecoveryReplacementInput",
        "ConfirmTotpRecoveryReplacementInput",
        "SupersedeTotpRecoveryReplacementInput",
    ]

    password = schemas["PasswordRecoveryCompletionInput"]
    assert password["properties"]["replacementFactor"]["const"] == "password"
    assert "replacementPassword" in password["required"]

    begin_totp = schemas["BeginTotpRecoveryReplacementInput"]
    assert begin_totp["properties"]["replacementFactor"]["const"] == "totp"
    assert begin_totp["properties"]["ceremonyAction"]["const"] == "begin"
    assert {"transactionSecret", "proofCode"}.issubset(begin_totp["required"])

    confirm_totp = schemas["ConfirmTotpRecoveryReplacementInput"]
    assert confirm_totp["properties"]["replacementFactor"]["const"] == "totp"
    assert confirm_totp["properties"]["ceremonyAction"]["const"] == "confirm"
    assert {
        "factorReplacementCapability",
        "enrollmentTransactionRef",
        "confirmationCode",
    }.issubset(confirm_totp["required"])

    supersede_totp = schemas["SupersedeTotpRecoveryReplacementInput"]
    assert supersede_totp["properties"]["replacementFactor"]["const"] == "totp"
    assert supersede_totp["properties"]["ceremonyAction"]["const"] == "supersede"
    assert {"priorCommandId", "priorEnrollmentTransactionRef"}.issubset(
        supersede_totp["required"]
    )
    assert "receiptReadCapability" not in supersede_totp.get("properties", {})

    operation = _public_operations()["completeAccountRecovery"]
    assert _response_schema(document, operation) == "AccountRecoveryCompletionResponse"
    response_alternatives = {
        item["$ref"].rsplit("/", 1)[1]
        for item in schemas["AccountRecoveryCompletionResponse"]["oneOf"]
    }
    assert response_alternatives == {
        "CommandReceiptResponse",
        "OneTimeTotpRecoveryEnrollmentDelivery",
        "OneTimeDeliveryUnavailable",
    }


def test_email_change_requires_session_recent_reauth_dual_channel_and_mfa() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    operations = _public_operations()
    schemas = document["components"]["schemas"]

    assert operations["beginEmailChange"]["security"] == [
        {"ProductWorkload": [], "UserSession": []}
    ]
    assert operations["completeEmailChange"]["security"] == [
        {
            "ProductWorkload": [],
            "UserSession": [],
            "ReceiptRecoveryCapability": [],
        }
    ]

    begin_request = operations["beginEmailChange"]["requestBody"]["$ref"]
    complete_request = operations["completeEmailChange"]["requestBody"]["$ref"]
    assert begin_request.endswith("/EmailChangeStartRequest")
    assert complete_request.endswith("/EmailChangeCompletionRequest")
    assert {"replacementEmail", "reauthenticationProof"}.issubset(
        schemas["EmailChangeStartInput"]["required"]
    )
    assert {
        "reauthenticationProof",
        "currentAddressChallenge",
        "replacementAddressChallenge",
    }.issubset(schemas["EmailChangeCompletionInput"]["required"])

    transaction = schemas["EmailChangeTransaction"]
    assert {
        "currentAddressChallengeRef",
        "replacementAddressChallengeRef",
    }.issubset(transaction["required"])
    assert "distinct" in transaction["description"]

    reauthentication = schemas["ReauthenticationInput"]
    reauth_inputs = [
        item["$ref"].rsplit("/", 1)[1] for item in reauthentication["oneOf"]
    ]
    assert reauth_inputs == [
        "PasswordReauthenticationInput",
        "MfaReauthenticationInput",
        "SupersedeReauthenticationProofInput",
    ]
    mfa = schemas["MfaReauthenticationInput"]
    assert {"transactionRef", "challengeKind", "proofCode"}.issubset(
        mfa["required"]
    )
    reauth_response = schemas["ReauthenticationResponse"]
    assert {
        item["$ref"].rsplit("/", 1)[1] for item in reauth_response["oneOf"]
    } == {
        "ReauthenticationPendingResponse",
        "OneTimeReauthenticationProofDelivery",
        "OneTimeDeliveryUnavailable",
    }
    proof = schemas["ReauthenticationProof"]
    assert {
        "reauthenticationProof",
        "sessionRef",
        "userSecurityEpoch",
        "sessionEpoch",
        "authStrengthPolicyRevision",
        "issuedAt",
        "expiresAt",
    }.issubset(proof["required"])


def test_reauthentication_proofs_are_bound_to_one_sensitive_identity_mutation() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    schemas = document["components"]["schemas"]

    target = schemas["ReauthenticationTarget"]
    assert target["additionalProperties"] is False
    assert target["properties"]["audience"]["const"] == "platform-public"
    assert target["properties"]["operationId"]["enum"] == [
        "beginTotpEnrollment",
        "disableTotp",
        "regenerateRecoveryCodes",
    ]
    assert target["properties"]["resource"]["$ref"].endswith(
        "/IdentityAccountReauthenticationResource"
    )
    resource = schemas["IdentityAccountReauthenticationResource"]
    assert resource["additionalProperties"] is False
    assert resource["properties"]["kind"]["const"] == "identity_account"
    assert set(resource["properties"]) == {"kind"}

    for schema_name in ("PasswordReauthenticationInput", "MfaReauthenticationInput"):
        assert schemas[schema_name]["properties"]["target"]["$ref"].endswith(
            "/ReauthenticationTarget"
        )
        assert "target" in schemas[schema_name]["required"]

    for schema_name in (
        "BeginTotpEnrollmentInput",
        "OtpInput",
        "RegenerateRecoveryCodesInput",
    ):
        assert schemas[schema_name]["properties"]["reauthenticationProof"]["minLength"] == 32
        assert "reauthenticationProof" in schemas[schema_name]["required"]

    for schema_name in (
        "SupersedeTotpEnrollmentInput",
        "SupersedeRecoveryCodeSetInput",
    ):
        assert "reauthenticationProof" not in schemas[schema_name]["properties"]
        assert "reauthenticationProof" not in schemas[schema_name]["required"]

    proof = schemas["ReauthenticationProof"]
    assert proof["properties"]["audience"]["const"] == "platform-public"
    assert proof["properties"]["operationId"]["enum"] == target["properties"]["operationId"]["enum"]
    assert proof["properties"]["resourceKind"]["const"] == "identity_account"
    assert proof["properties"]["userSecurityEpoch"]["$ref"].endswith(
        "/PositiveUint64String"
    )
    assert proof["properties"]["sessionEpoch"]["$ref"].endswith(
        "/PositiveUint64String"
    )
    assert {"audience", "operationId", "resourceKind"}.issubset(proof["required"])


def test_public_mutations_use_caller_generated_command_ids_for_zero_byte_recovery() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    operations = _public_operations()
    command_identity = document["components"]["parameters"]["CommandIdentity"]
    assert command_identity["name"] == "X-Kokoro-Command-Id"
    assert command_identity["in"] == "header"
    assert command_identity["required"] is True
    expected_pattern = (
        "^(?:[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-"
        "[89ab][0-9a-f]{3}-[0-9a-f]{12})$"
    )
    assert command_identity["schema"]["pattern"] == expected_pattern
    assert document["components"]["parameters"]["CommandId"]["schema"][
        "pattern"
    ] == expected_pattern
    for phrase in (
        "caller-generated",
        "128-bit",
        "must not be derived from Idempotency-Key",
        "same command id with a different payload",
    ):
        assert phrase in command_identity["description"]

    for operation_id, operation in operations.items():
        if operation_id in {
            "issueSessionAccessGrant",
            "listIdentitySessions",
            "getPersonalContext",
            "recoverRedemptionCommand",
            "getRedemptionReceipt",
            "listAccountProducts",
            "getCreditSummary",
            "getCreditGrant",
            "getUsageDetail",
            "getAssetUploadStatus",
            "recoverAssetUploadCommand",
            "getTrustedAssetGrant",
            "listMediaOperationDefinitions",
            "getMediaOperationDefinition",
            "listMediaOperationModelOptions",
            "listMediaOperations",
            "getMediaOperation",
            "recoverMediaOperationCommand",
            "listArtifacts",
            "getArtifact",
            "listArtifactVersions",
            "getArtifactVersion",
                "issueArtifactDeliveryAuthorization",
                "redeemArtifactDeliveryAuthorization",
                "getPublicCommandReceipt",
        }:
            continue
        parameter_refs = {
            parameter["$ref"].rsplit("/", 1)[1]
            for parameter in operation["parameters"]
        }
        assert "CommandIdentity" in parameter_refs

    for delivery_schema in (
        "OneTimeSessionCredentialDelivery",
        "OneTimeTotpEnrollmentDelivery",
        "OneTimeRecoveryCodeSetDelivery",
        "OneTimeTotpRecoveryEnrollmentDelivery",
        "OneTimeReauthenticationProofDelivery",
        "OneTimeDeliveryUnavailable",
    ):
        schema = document["components"]["schemas"][delivery_schema]
        assert "commandId" in schema["required"]
        assert schema["properties"]["commandId"]["pattern"] == expected_pattern
    command_receipt = document["components"]["schemas"]["CommandReceipt"]
    assert "commandId" in command_receipt["required"]
    assert command_receipt["properties"]["commandId"]["pattern"] == expected_pattern
    for superseding_schema in (
        "SupersedeSessionCredentialDeliveryInput",
        "SupersedeRefreshCredentialDeliveryInput",
        "SupersedeTotpRecoveryReplacementInput",
        "SupersedeTotpEnrollmentInput",
        "SupersedeRecoveryCodeSetInput",
        "SupersedeReauthenticationProofInput",
    ):
        assert document["components"]["schemas"][superseding_schema]["properties"][
            "priorCommandId"
        ]["pattern"] == expected_pattern


def test_public_safe_pending_results_include_the_committed_command_receipt() -> None:
    schemas = yaml.safe_load(PUBLIC_OPENAPI.read_text())["components"]["schemas"]
    expected = {
        "AuthPendingResponse": "AuthPending",
        "ReauthenticationPendingResponse": "ReauthenticationPending",
    }
    for wrapper_name, result_name in expected.items():
        wrapper = schemas[wrapper_name]
        assert set(wrapper["required"]) == {"receipt", "pending"}
        assert wrapper["properties"]["receipt"]["$ref"].endswith("/CommandReceipt")
        assert wrapper["properties"]["pending"]["$ref"].endswith(f"/{result_name}")


def test_public_receipt_state_and_reconciliation_combinations_are_closed() -> None:
    schemas = yaml.safe_load(PUBLIC_OPENAPI.read_text())["components"]["schemas"]
    response = schemas["PublicCommandReceiptResponse"]
    alternatives = [item["$ref"].rsplit("/", 1)[1] for item in response["oneOf"]]
    expected = {
        "AcceptedPublicCommandReceiptResponse": (
            "AcceptedPublicCommandReceipt",
            "PendingCommandReconciliation",
            "accepted",
            "not_applicable",
        ),
        "OutcomeUnknownPublicCommandReceiptResponse": (
            "OutcomeUnknownPublicCommandReceipt",
            "PendingCommandReconciliation",
            "outcome_unknown",
            "not_applicable",
        ),
        "CommittedTerminalPublicCommandReceiptResponse": (
            "CommittedPublicCommandReceipt",
            "CommittedCommandReconciliation",
            "committed",
            "not_applicable",
        ),
        "RejectedTerminalPublicCommandReceiptResponse": (
            "RejectedPublicCommandReceipt",
            "RejectedCommandReconciliation",
            "rejected",
            "not_applicable",
        ),
        "CommittedSupersedingPublicCommandReceiptResponse": (
            "CommittedDeliveryConsumedPublicCommandReceipt",
            "SupersedingCeremonyReconciliation",
            "committed",
            "first_claim_consumed",
        ),
        "CommittedSupersededPublicCommandReceiptResponse": (
            "CommittedDeliverySupersededPublicCommandReceipt",
            "CommittedCommandReconciliation",
            "committed",
            "superseded",
        ),
    }
    assert alternatives == list(expected)
    for wrapper_name, (receipt_name, reconciliation_name, state, delivery) in expected.items():
        wrapper = schemas[wrapper_name]
        assert set(wrapper["required"]) == {"receipt", "reconciliation"}
        assert wrapper["properties"]["receipt"]["$ref"].endswith(f"/{receipt_name}")
        assert wrapper["properties"]["reconciliation"]["$ref"].endswith(
            f"/{reconciliation_name}"
        )
        receipt = schemas[receipt_name]
        assert receipt["properties"]["state"]["const"] == state
        assert receipt["properties"]["deliveryState"]["const"] == delivery


def test_public_receipt_lookup_is_non_enumerable_and_caller_recoverable() -> None:
    document = yaml.safe_load(PUBLIC_OPENAPI.read_text())
    operation = document["paths"]["/v1/commands/{id}/receipt"]["get"]
    parameter_refs = {
        parameter["$ref"].rsplit("/", 1)[1] for parameter in operation["parameters"]
    }
    assert {"CommandId", "ContractVersion"}.issubset(parameter_refs)
    assert "ReceiptRecoveryCapability" not in parameter_refs
    assert "ReceiptRecoveryCapabilityLookup" not in parameter_refs
    assert "RequestDigest" not in parameter_refs
    assert operation["security"] == [
        {"ProductWorkload": [], "UserSession": []},
        {"ProductWorkload": [], "ReceiptRecoveryCapability": []},
    ]
    description = operation["description"]
    assert "workload-derived Site" in description
    assert "same caller" in description
    assert "not-found" in description
    assert "caller-generated command id" in description
    assert "zero response bytes" in description


def test_public_error_codes_are_a_frozen_enum() -> None:
    error_codes = yaml.safe_load(PUBLIC_OPENAPI.read_text())["components"]["schemas"][
        "ErrorCode"
    ]["enum"]
    assert error_codes == [
        "INVALID_REQUEST",
        "CONTRACT_VERSION_UNSUPPORTED",
        "AUTHENTICATION_REQUIRED",
        "AUTHENTICATION_FAILED",
        "AUTH_TRANSACTION_EXPIRED",
        "MFA_REQUIRED",
        "FORBIDDEN",
        "NOT_FOUND",
        "CONFLICT",
        "RATE_LIMITED",
        "RISK_UNAVAILABLE",
        "SITE_UNAVAILABLE",
        "OUTCOME_UNKNOWN",
        "INTERNAL_UNAVAILABLE",
        "REDEEM_NOT_ACCEPTED",
        "REDEEM_TEMPORARILY_UNAVAILABLE",
        "IDEMPOTENCY_CONFLICT",
        "ACQUISITION_CHANNEL_DISABLED",
        "ASSET_NOT_ACCEPTED",
        "ASSET_UPLOAD_CONFLICT",
        "ASSET_QUOTA_EXCEEDED",
        "ASSET_TEMPORARILY_UNAVAILABLE",
        "MEDIA_INPUT_REJECTED",
        "MEDIA_CALLER_FINGERPRINT_MISMATCH",
        "MEDIA_DEFINITION_UNAVAILABLE",
        "MEDIA_MODEL_OPTION_UNAVAILABLE",
        "MEDIA_CREDIT_INSUFFICIENT",
        "MEDIA_POLICY_REJECTED",
        "MEDIA_OPERATION_VERSION_CONFLICT",
        "MEDIA_CANCEL_NOT_ACCEPTED",
        "MEDIA_TEMPORARILY_UNAVAILABLE",
        "PAGE_CURSOR_INVALID",
        "ARTIFACT_NOT_AVAILABLE",
        "ARTIFACT_DELIVERY_NOT_ALLOWED",
        "ARTIFACT_DELIVERY_AUTHORIZATION_REJECTED",
        "ARTIFACT_TEMPORARILY_UNAVAILABLE",
        "ARTIFACT_RANGE_NOT_SATISFIABLE",
    ]


def test_platform_admission_v1_surface_remains_frozen() -> None:
    source = _proto("kokoro/platform/admission/v1/admission.proto")
    assert _service_methods(source, "AdmissionService") == [
        "PrepareRun",
        "FinalizeRunAuthorization",
        "ReleaseRunAuthorization",
        "ReconcileRunAuthorization",
        "GetCommandReceipt",
    ]
    prepare = _message_body(source, "PrepareRunEffect")
    for required in (
        "session_access_grant",
        "project_ref",
        "session_id",
        "launch_id",
        "proposed_run_id",
        "trigger_message_id",
        "trigger_message_content",
        "model_option_revision_ref",
        "session_projection_authorization_handle",
    ):
        assert required in prepare
    for owner_fact in (
        "namespace",
        "capability_snapshot_ref",
        "runtime_config",
        "root_hold_ref",
        "authorization_segment_ref",
    ):
        assert owner_fact not in prepare
    for response in (
        "PrepareRunResponse",
        "FinalizeRunAuthorizationResponse",
        "ReleaseRunAuthorizationResponse",
        "ReconcileRunAuthorizationResponse",
        "GetCommandReceiptResponse",
    ):
        body = _message_body(source, response)
        assert "oneof result" in body
        assert "option (buf.validate.oneof).required = true;" in body


def test_platform_session_authorization_v1_surface_is_pull_snapshot_and_key_only() -> None:
    source = _proto("kokoro/platform/authorization/v1/session_authorization.proto")
    assert _service_methods(source, "SessionAuthorizationService") == [
        "PullAuthorizationEvents",
        "GetAuthorizationSnapshotPage",
        "GetAuthorizationVerificationKeys",
    ]
    event = _message_body(source, "AuthorizationEventSigningPayload")
    assert "uint64 stream_sequence" in event
    assert "uint64 aggregate_sequence" in event
    assert "DeliveredGrantFact grant_delivered" in event
    assert "RevocationEpochChanged revocation_epoch_changed" in event
    assert "key_rotated" not in event
    assert "grant_prepared" not in event
    delivered = _message_body(source, "DeliveredGrantFact")
    assert "string site_ref" in delivered
    snapshot = _message_body(source, "AuthorizationSnapshotPage")
    assert "uint64 high_watermark_stream_sequence" in snapshot
    assert "string key_set_revision" in snapshot
    assert "pattern: \"^[0-9a-f]{64}$\"" in snapshot
    assert "repeated AuthorizationSnapshotRecord records" in snapshot
    assert "optional string next_page_cursor" in snapshot
    site_snapshot = _message_body(source, "AuthorizationSiteSnapshot")
    assert "uint64 aggregate_sequence = 2;" in site_snapshot
    assert "AUTHORIZATION_SITE_STATE_DECOMMISSIONING" in source
    keys = _message_body(source, "GetAuthorizationVerificationKeysResponse")
    assert "oneof outcome" in keys
    assert "AuthorizationVerificationKeys key_set" in keys
    assert "AuthorizationVerificationKeysNotModified not_modified" in keys
    assert "option (buf.validate.oneof).required = true;" in keys
    verification_key = _message_body(source, "AuthorizationVerificationKey")
    assert "AuthorizationVerificationKeyPurpose purpose" in verification_key
    assert "AUTHORIZATION_VERIFICATION_KEY_PURPOSE_EVENT_SIGNING" in source
    assert "AUTHORIZATION_VERIFICATION_KEY_PURPOSE_SESSION_ACCESS_GRANT" in source
    registry_invariants = (CONTRACT / "registry/platform-session-authorization-v1.yaml").read_text()
    assert "jwt-fact-nine-axis-equality" in registry_invariants
    assert "universal-site-revocation-fence" in registry_invariants
    assert "revoke an identity session, revoke a membership, and suspend a Site" in registry_invariants


def test_platform_session_authorization_v2_projects_all_nine_axes_without_site_wide_owner_revocation() -> None:
    source = _proto("kokoro/platform/authorization/v2/scoped_session_authorization.proto")
    assert _service_methods(source, "ScopedSessionAuthorizationService") == [
        "PullAuthorizationEvents",
        "GetAuthorizationSnapshotPage",
        "GetAuthorizationVerificationKeys",
    ]

    site = _message_body(source, "SiteCurrent")
    for field in ("site_ref", "state", "site_security_epoch", "policy_epoch", "site_revocation_epoch"):
        assert field in site
    subject = _message_body(source, "SubjectCurrent")
    for field in ("site_ref", "subject_ref", "state", "subject_generation", "restriction_epoch"):
        assert field in subject
    identity = _message_body(source, "IdentitySessionCurrent")
    for field in (
        "site_ref", "subject_ref", "identity_session_ref", "state",
        "identity_session_epoch", "credential_epoch", "expires_at",
    ):
        assert field in identity
    membership = _message_body(source, "ProjectMembershipCurrent")
    for field in (
        "site_ref", "subject_ref", "project_ref", "state", "membership_epoch", "authorization_epoch",
    ):
        assert field in membership
    assert "membership_ref" not in membership

    vector = _message_body(source, "AuthorizationEpochVector")
    assert [
        field for field in (
            "site_security_epoch", "subject_generation", "identity_session_epoch",
            "membership_epoch", "authorization_epoch", "restriction_epoch",
            "credential_epoch", "policy_epoch", "site_revocation_epoch",
        ) if field in vector
    ] == [
        "site_security_epoch", "subject_generation", "identity_session_epoch",
        "membership_epoch", "authorization_epoch", "restriction_epoch",
        "credential_epoch", "policy_epoch", "site_revocation_epoch",
    ]
    event = _message_body(source, "AuthorizationEventSigningPayload")
    for fact in (
        "SiteCurrent site_current_changed",
        "SubjectCurrent subject_current_changed",
        "IdentitySessionCurrent identity_session_current_changed",
        "ProjectMembershipCurrent project_membership_current_changed",
        "DeliveredGrantFact grant_delivered",
    ):
        assert fact in event
    snapshot = _message_body(source, "AuthorizationSnapshotRecord")
    for fact in (
        "SiteCurrentSnapshot site_current",
        "SubjectCurrent subject_current",
        "IdentitySessionCurrent identity_session_current",
        "ProjectMembershipCurrent project_membership_current",
        "DeliveredGrantFact delivered_grant",
        "AuthorizationVerificationKey verification_key",
    ):
        assert fact in snapshot
    site_snapshot = _message_body(source, "SiteCurrentSnapshot")
    assert "SiteCurrent current" in site_snapshot
    assert "uint64 aggregate_sequence" in site_snapshot
    for state in (
        "AUTHORIZATION_SUBJECT_STATE_REMOVED",
        "AUTHORIZATION_IDENTITY_SESSION_STATE_REVOKED",
        "AUTHORIZATION_IDENTITY_SESSION_STATE_REMOVED",
        "AUTHORIZATION_PROJECT_MEMBERSHIP_STATE_REVOKED",
        "AUTHORIZATION_PROJECT_MEMBERSHIP_STATE_REMOVED",
    ):
        assert state in source
    assert source.count("google.protobuf.Timestamp retain_until") == 4

    registry = (CONTRACT / "registry/platform-session-authorization-v2.yaml").read_text()
    for invariant in (
        "nine-axis-current-fact-equality",
        "global-site-owner-lock-order",
        "owner-binding-integrity",
        "owner-epoch-monotonicity",
        "delivered-grant-is-not-current-state",
        "owner-scoped-revocation-only",
        "tombstone-retention",
        "missing-current-fact-fail-closed",
        "target-subject-invalid-neighbor-valid",
        "target-identity-session-invalid-neighbor-valid",
        "target-membership-invalid-neighbor-valid",
        "site-suspend-invalidates-all-site-grants",
    ):
        assert invariant in registry
    assert "lifecycle: contract-only" in registry
    assert "activation: inactive" in registry
    assert "universal-site-revocation-fence" not in registry
    boundaries = json.loads((CONTRACT / "registry/boundaries.yaml").read_text())["boundaries"]
    boundary = next(item for item in boundaries if item["id"] == "platform-session-authorization")
    assert boundary["version"] == 2
    assert boundary["lifecycle"] == "contract-only"
    assert boundary["sources"][0]["path"].endswith(
        "/authorization/v2/scoped_session_authorization.proto"
    )
    assert all("authorization/v1" not in item["path"] for item in boundary["sources"])


def test_safe_admission_capabilities_are_typed_for_browser_projection() -> None:
    source = _proto("kokoro/platform/admission/v1/admission.proto")
    snapshot = _message_body(source, "SafeAdmissionSnapshot")
    display = _message_body(source, "SafeCapabilityDisplay")

    assert "enum SafeCapabilityKind" in source
    assert "SAFE_CAPABILITY_KIND_SKILL" in source
    assert "SAFE_CAPABILITY_KIND_MCP" in source
    assert "repeated SafeCapabilityDisplay capabilities" in snapshot
    assert "SafeCapabilityKind kind" in display
    assert "string label" in display
    assert "deprecated = true" in snapshot


def test_admin_oidc_session_delivery_recovers_without_redeeming_the_code_again() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")

    recovery = _message_body(identity, "AdminSessionRecoveryProof")
    begin_effect = _message_body(identity, "BeginOperatorLoginEffect")
    begin_response = _message_body(identity, "BeginOperatorLoginResponse")
    exchange = _message_body(identity, "ExchangeOidcSessionEffect")
    exchange_response = _message_body(identity, "ExchangeOidcSessionResponse")

    assert "bytes recovery_handle" in recovery
    assert "len: 32" in recovery
    assert "AdminSessionRecoveryProof recovery_proof" in begin_effect
    assert "AdminSessionRecoveryProof recovery_proof" not in begin_response
    assert "AdminSessionRecoveryProof recovery_proof" in exchange
    assert "string session_delivery_envelope" in exchange_response
    assert "google.protobuf.Timestamp delivery_expires_at" in exchange_response
    assert "opaque_session_handle" not in exchange_response
    assert "RFC 7516 compact JWE" in identity
    assert "registered delivery key" in identity
    assert "workload_identity_ref, transaction_ref, and request_digest" in identity
    assert "must not redeem the authorization code again" in identity
    assert "before the first response" in identity
    assert "Generic CommandReceipt never contains" in identity


def test_admin_session_recovery_is_workload_bound_short_lived_and_non_enumerable() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")

    pre_login = _message_body(identity, "AdminPreLoginWorkloadContext")
    transaction = _message_body(identity, "AdminAuthTransactionContext")
    begin_response = _message_body(identity, "BeginOperatorLoginResponse")
    exchange = _message_body(identity, "ExchangeOidcSessionEffect")

    for context in (pre_login, transaction):
        for axis in (
            "workload_identity_ref",
            "environment",
            "region",
            "managed_device_ref",
            "audience",
        ):
            assert axis in context
    assert "google.protobuf.Timestamp recovery_expires_at" in begin_response
    assert "recovery_proof" in exchange
    assert "single-purpose" in identity
    assert "constant-time" in identity
    assert "indistinguishable not-found" in identity
    assert "never disclose whether the transaction or session exists" in identity


def test_admin_oidc_callbacks_and_return_targets_are_registered_opaque_refs() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")

    begin_login = _message_body(identity, "BeginOperatorLoginEffect")
    begin_step_up = _message_body(identity, "BeginStepUpEffect")
    complete_step_up = _message_body(identity, "CompleteStepUpEffect")

    assert re.findall(r"\bstring\s+(\w+)\s*=", begin_login) == ["return_intent_ref"]
    assert "^[a-z][a-z0-9_.-]{0,127}$" in begin_login
    assert "callback_uri" not in begin_step_up
    assert "string callback_ref" in begin_step_up
    assert "^[a-z][a-z0-9_.-]{0,127}$" in begin_step_up
    assert "callback_uri" not in complete_step_up
    assert "callback_ref" not in complete_step_up
    exchange = _message_body(identity, "ExchangeOidcSessionEffect")
    assert "callback_uri" not in exchange
    assert "registered workload allowlist" in identity
    assert "Unknown callback or return refs fail closed" in identity


def test_admin_session_delivery_has_a_non_effect_recovery_read() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")

    assert _service_methods(identity, "AdminIdentityService") == [
        "BeginOperatorLogin",
        "ExchangeOidcSession",
        "GetOperatorSessionDelivery",
        "BeginStepUp",
        "CompleteStepUp",
        "SignOut",
    ]
    read_context = _message_body(identity, "AdminVerifiedWorkloadReadContext")
    assert "CommandIdentity" not in read_context
    for field in (
        "request_id",
        "workload_identity_ref",
        "environment",
        "region",
        "managed_device_ref",
        "audience",
    ):
        assert f"string {field}" in read_context
    request = _message_body(identity, "GetOperatorSessionDeliveryRequest")
    assert "AdminVerifiedWorkloadReadContext context" in request
    assert "string transaction_ref" in request
    assert "AdminSessionRecoveryProof recovery_proof" in request
    assert "CommandIdentity" not in request
    assert "authorization_code" not in request
    assert "Effect" not in request

    exchange_response = _message_body(identity, "ExchangeOidcSessionResponse")
    read_response = _message_body(identity, "GetOperatorSessionDeliveryResponse")
    assert "AdminSessionDelivery delivery" in exchange_response
    assert "kokoro.common.v2.CommandReceiptV2 receipt" in exchange_response
    assert re.findall(r"^\s*\S+\s+(\w+)\s*=", exchange_response, re.MULTILINE) == [
        "delivery",
        "receipt",
    ]
    assert "AdminSessionDelivery delivery" in read_response
    assert "kokoro.common.v2.CommandReceiptV2 original_exchange_receipt" in read_response
    assert "oneof" not in exchange_response
    assert "oneof" not in read_response


def test_admin_session_delivery_read_is_committed_exact_and_never_redeems() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")
    policy = re.sub(r"\s*//\s*", " ", identity)

    for phrase in (
        "atomically committed the OperatorSession and exact delivery envelope",
        "byte-for-byte identical",
        "never re-encrypt after key rotation",
        "never call the identity provider",
        "provider_outcome_unknown",
        "stable restart-login failure",
        "new BeginOperatorLogin",
        "must never redeem the authorization code again",
    ):
        assert phrase in policy
    assert "unknown, expired, revoked, or mismatched" in policy
    assert "same public NOT_FOUND" in policy


def test_admin_session_delivery_freezes_authenticated_jose_profile() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")
    policy = re.sub(r"\s*//\s*", " ", identity)
    delivery = _message_body(identity, "AdminSessionDelivery")

    assert "string operator_session_ref" in delivery
    assert "string session_delivery_envelope" in delivery
    assert "google.protobuf.Timestamp expires_at" in delivery
    assert "google.protobuf.Timestamp delivery_expires_at" in delivery
    for phrase in (
        "signed-then-encrypted",
        "inner compact JWS",
        "ES256",
        "P-256",
        "kokoro-admin-session-delivery+jwt",
        "outer compact JWE",
        "RSA-OAEP-256",
        "A256GCM",
        "RSA key of at least 3072 bits",
        "kokoro-admin-session-delivery+jwe",
        "cty=JWT",
        "delivery_expires_at equals the signed exp claim",
        "freezes both signing and encryption key revisions",
        "retained through the delivery TTL",
    ):
        assert phrase in policy
    for claim in (
        "iss",
        "aud",
        "jti",
        "iat",
        "nbf",
        "exp",
        "workload_identity_ref",
        "environment",
        "region",
        "managed_device_ref",
        "transaction_ref",
        "exchange_request_digest",
        "operator_session_ref",
        "opaque_session_credential",
    ):
        assert claim in policy
    for forbidden in (
        "none",
        "dir",
        "RSA1_5",
        "CBC",
        "zip",
        "crit",
        "jku",
        "x5u",
        "jwk",
        "unprotected headers",
        "unknown kid",
        "key-type mismatch",
    ):
        assert forbidden in policy


def test_admin_recovery_proof_lifecycle_is_unique_secret_and_non_enumerable() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")
    policy = re.sub(r"\s*//\s*", " ", identity)
    recovery_proof = _message_body(identity, "AdminSessionRecoveryProof")
    assert re.search(r"bytes recovery_handle.*?len: 32", recovery_proof, re.DOTALL)
    assert "min_len" not in recovery_proof
    assert "max_len" not in recovery_proof

    for phrase in (
        "exactly 32 bytes",
        "OS CSPRNG",
        "unique among active recovery digests",
        "must never bind one proof to more than one transaction",
        "domain-separated SHA-256",
        "kokoro.admin-session-recovery.v1",
        "raw proof is never persisted",
        "logs, traces, metrics, receipts, outbox events, or audit payloads",
        "constant-time",
        "valid only until delivery_expires_at",
        "same public NOT_FOUND status and domain error",
        "no receipt reference or delivery payload",
        "true reason is available only to security audit",
    ):
        assert phrase in policy


def test_admin_identity_success_responses_require_valid_refs_uris_and_times() -> None:
    identity = _proto("kokoro/platform/identity/v1/admin_identity.proto")

    begin = _message_body(identity, "BeginOperatorLoginResponse")
    begin_step_up = _message_body(identity, "BeginStepUpResponse")
    complete_step_up = _message_body(identity, "CompleteStepUpResponse")
    delivery = _message_body(identity, "AdminSessionDelivery")
    for body in (begin, begin_step_up):
        assert re.search(r"string transaction_ref.*?min_len: 1", body, re.DOTALL)
        assert re.search(
            r"string authorization_uri.*?min_len: 1.*?uri: true", body, re.DOTALL
        )
        assert re.search(
            r"google\.protobuf\.Timestamp expires_at.*?required = true", body
        )
    assert re.search(
        r"string operator_session_ref.*?min_len: 1", delivery, re.DOTALL
    )
    for field in ("expires_at", "delivery_expires_at"):
        assert re.search(
            rf"google\.protobuf\.Timestamp {field}.*?required = true", delivery
        )
    assert re.search(
        r"string operator_session_ref.*?min_len: 1", complete_step_up, re.DOTALL
    )
    assert re.search(
        r"google\.protobuf\.Timestamp step_up_at.*?required = true",
        complete_step_up,
    )


def test_wave1_required_reference_fields_reject_empty_values() -> None:
    command = _proto("kokoro/platform/admin/v2/admin_command.proto")
    query = _proto("kokoro/platform/admin/v2/admin_query.proto")
    lifecycle = _proto("kokoro/platform/site/v1/site_lifecycle.proto")

    required_refs = {
        (command, "SubmitCommandResponse"): ("approval_ref",),
        (query, "SiteSummary"): ("site_ref",),
        (query, "UserSummary"): ("user_ref",),
        (query, "AuditRecord"): ("audit_ref",),
        (lifecycle, "RequestActivationApprovalResponse"): ("approval_ref",),
        (lifecycle, "ApproveAndActivateResponse"): ("activation_attempt_ref",),
    }
    for (source, message), fields in required_refs.items():
        body = _message_body(source, message)
        for field in fields:
            assert re.search(rf"string {field}.*?min_len: [1-9]", body, re.DOTALL)


def test_wave1_query_and_lifecycle_outputs_reject_empty_sentinels() -> None:
    query = _proto("kokoro/platform/admin/v2/admin_query.proto")
    lifecycle = _proto("kokoro/platform/site/v1/site_lifecycle.proto")

    for message, field in (
        ("SiteSummary", "status"),
        ("UserSummary", "status"),
        ("AuditRecord", "action_code"),
    ):
        assert re.search(
            rf"string {field}.*?min_len: 1", _message_body(query, message), re.DOTALL
        )
    assert re.search(
        r"google\.protobuf\.Timestamp occurred_at.*?required = true",
        _message_body(query, "AuditRecord"),
    )
    for message in ("ListSitesRequest", "ListSitesResponse", "GetAuditWithinScopeRequest", "GetAuditWithinScopeResponse"):
        body = _message_body(query, message)
        if "page_token" in body:
            assert re.search(r"optional string .*page_token.*?min_len: 1", body, re.DOTALL)

    activate = _message_body(lifecycle, "ActivationFacts")
    assert "ActivePointerCasPrecondition active_pointer" in activate
    assert "ImmutableContractRevisionBinding target_release" in activate
    assert re.search(r"string reason.*?min_len: 3", activate, re.DOTALL)


def test_site_lifecycle_activation_approval_preserves_owner_facts() -> None:
    lifecycle = _proto("kokoro/platform/site/v1/site_lifecycle.proto")
    facts = _message_body(lifecycle, "ActivationFacts")
    for field in ("candidate", "target_release", "active_pointer", "audience", "session_contract_revision", "reason"):
        assert field in facts
    assert not re.search(r"\b(?:optional\s+)?string\s+candidate_release_ref\b", facts)
    assert not re.search(r"\b(?:optional\s+)?string\s+expected_active_release_ref\b", facts)
    assert 'reserved "candidate_release_ref", "expected_active_release_ref"' in facts
    publication_common = _proto("kokoro/platform/publication/v1/publication_common.proto")
    candidate = _message_body(publication_common, "CandidateAuthorityBinding")
    for field in ("candidate_ref", "candidate_version", "candidate_authorization_epoch"):
        assert field in candidate
    pointer = _message_body(lifecycle, "ActivePointerCasPrecondition")
    for field in ("expected_generation", "cas_precondition_digest", "fence"):
        assert field in pointer
    assert "has(this.first_activation) && this.expected_generation == 0u" in pointer
    assert "has(this.existing) && this.expected_generation == this.existing.current_generation" in pointer
    assert "this.existing.current_generation >= 1u" in pointer
    existing = _message_body(lifecycle, "ExistingActivePointer")
    assert "ImmutableContractRevisionBinding current_release" in existing
    evidence = _message_body(lifecycle, "ActivationEligibilityEvidenceRefs")
    for field in (
        "begin_authority_snapshot",
        "immediate_before_pointer_cas_authority_snapshot",
        "eligibility_evidence",
    ):
        assert field in evidence
    for message in ("RequestActivationApprovalEffect", "ApproveAndActivateEffect"):
        body = _message_body(lifecycle, message)
        assert "string approval_ref" in body
        assert "ActivationFacts activation" in body
    assert "string activation_attempt_ref" in _message_body(
        lifecycle, "ApproveAndActivateEffect"
    )
    response = _message_body(lifecycle, "ApproveAndActivateResponse")
    assert "SITE_ACTIVATION_STATE_SUCCEEDED || this.replayed" in response
    assert "has(this.committed_active_pointer_generation)" in response
    assert "this.committed_active_pointer_generation > 0u" in response
    assert "has(this.activation_evidence)" in response


def test_site_release_publication_accepts_only_candidate_command_identity() -> None:
    provisioning = _proto("kokoro/platform/site/v1/site_publication.proto")
    effect = _message_body(provisioning, "PublishSiteReleaseEffect")
    assert "CandidateAuthorityBinding candidate = 16" in effect
    assert "string reason = 18" in effect
    assert "reserved 17;" in effect
    assert 'reserved "site_release_candidate_ref", "expected_candidate_version"' in effect
    for legacy in (
        "release_ref", "web_artifact_digest", "release_manifest_digest",
        "certification_digest", "launch_profile_ref", "model_option_catalog_ref",
        "enabled_surface_ids",
    ):
        assert not re.search(rf"\b{legacy}\s*=", effect)
    for legacy_type in ("SiteReleaseCertificationProof", "SiteLocalePolicy"):
        assert legacy_type not in provisioning
    assert "reserved 1 to 15;" in effect


def test_site_publication_authority_has_typed_contract_document_operations() -> None:
    provisioning = _proto("kokoro/platform/site/v1/site_provisioning.proto")
    catalog = _proto("kokoro/platform/product/v1/product_catalog_publication.proto")
    publication = _proto("kokoro/platform/site/v1/site_publication.proto")
    assert _service_methods(provisioning, "SiteProvisioningService") == ["RegisterSite"]
    assert _service_methods(catalog, "ProductCatalogPublicationService") == [
        "PublishProductSurfaceCatalog",
        "PublishLaunchProductProfile",
    ]
    assert _service_methods(publication, "SitePublicationService") == [
        "AuthorizeSiteReleaseCandidate",
        "RevokeSiteReleaseCandidate",
        "PublishSurfaceInventory",
        "PublishWebBuildMaterialBundle",
        "IssueWebBuildIntent",
        "PublishReleaseCertification",
        "PublishSiteRelease",
    ]
    assert _service_methods(publication, "SiteEvidenceAdmissionService") == [
        "RecordReleaseEvidence",
    ]
    expected_effects = {
        "AuthorizeSiteReleaseCandidateEffect": (
            "candidate_ref", "expected_candidate_version", "candidate_authorization_epoch",
        ),
        "RevokeSiteReleaseCandidateEffect": ("candidate", "expected_authorization_epoch"),
        "PublishSurfaceInventoryEffect": ("candidate", "surface_inventory"),
        "PublishWebBuildMaterialBundleEffect": ("candidate", "web_build_material_bundle"),
        "IssueWebBuildIntentEffect": (
            "candidate", "expected_surface_inventory", "expected_web_build_material_bundle",
        ),
        "RecordReleaseEvidenceEffect": (
            "candidate", "compiled_web_manifest", "web_artifact_provenance",
        ),
        "PublishReleaseCertificationEffect": ("candidate", "release_certification"),
    }
    for message, fields in expected_effects.items():
        body = _message_body(publication, message)
        for field in fields:
            assert field in body
        assert "bytes payload" not in body
        assert "string operation" not in body
    intent_effect = _message_body(publication, "IssueWebBuildIntentEffect")
    assert "web_build_intent =" not in intent_effect
    assert "issued_at =" not in intent_effect
    revoke_response = _message_body(publication, "RevokeSiteReleaseCandidateResponse")
    assert "SiteReleaseCandidateAuthorizationState state" in revoke_response
    assert "previous_authorization_epoch" in revoke_response
    assert "authorization_epoch" in revoke_response
    assert "CommandReceiptV2 receipt" in revoke_response
    assert "SITE_RELEASE_CANDIDATE_AUTHORIZATION_STATE_REVOKED" in publication
    revoke_effect = _message_body(publication, "RevokeSiteReleaseCandidateEffect")
    assert "candidate.candidate_authorization_epoch == this.expected_authorization_epoch" in revoke_effect
    revoke_request = _message_body(publication, "RevokeSiteReleaseCandidateRequest")
    assert "has(this.context.step_up_at)" in revoke_request
    assert "this.site_id in this.context.scope.site.site_ids" in revoke_request
    assert "this.authorization_epoch == this.previous_authorization_epoch + 1u" in revoke_response
    assert "COMMAND_RECEIPT_STATE_V2_COMMITTED" in revoke_response
    assert "SitePublicationService/RevokeSiteReleaseCandidate" in revoke_response
    for invariant in (
        "one transaction-local compare-and-swap",
        "current AUTHORIZED state",
        "same command identity and request digest",
        "without advancing the epoch again",
        "cross-Site/binding mismatch",
        "REVOKED is permanent",
        "AuthorizeSiteReleaseCandidate cannot",
        "revive it",
        "requires a new Candidate",
    ):
        assert invariant in publication
    generator = (CONTRACT / "generate.mjs").read_text()
    assert "revokeSiteReleaseCandidateRequestDigest" in generator
    assert 'sitePublicationDigest("RevokeSiteReleaseCandidate"' in generator
    issue_digest = generator[generator.index("export function issueWebBuildIntentRequestDigest"):]
    issue_digest = issue_digest[:issue_digest.index("export function publishReleaseCertificationRequestDigest")]
    assert "effect.webBuildIntent" not in issue_digest
    assert "effect.expectedSurfaceInventory?.ref" in issue_digest
    assert "effect.expectedWebBuildMaterialBundle?.ref" in issue_digest
    evidence_request = _message_body(publication, "RecordReleaseEvidenceRequest")
    assert "AttestedReleaseEvidenceContext context" in evidence_request
    assert "AuthenticatedOperatorCommandContext context" not in evidence_request
    workload_context = _message_body(publication, "AttestedReleaseEvidenceContext")
    for field in (
        "command", "workload_identity_ref", "audience", "environment", "region",
        "producer_identity_ref", "producer_registration", "producer_role", "workload_attestation",
        "workload_authorization_epoch", "workload_revocation_epoch", "workload_authorization_state",
        "workload_authorization_live_read", "workload_authorization_observed_at",
        "workload_authorization_valid_until",
    ):
        assert field in workload_context
    assert "kokoro.site-release-evidence-admission.v1" in workload_context
    assert "WORKLOAD_AUTHORIZATION_STATE_ACTIVE" in publication
    assert "this.workload_revocation_epoch == 0" in workload_context
    assert "this.workload_authorization_observed_at < this.workload_authorization_valid_until" in workload_context
    assert "operator_session" not in workload_context
    assert "assurance_level" not in workload_context
    assert "factor_classes" not in workload_context
    assert "managed_device" not in workload_context
    for operation in (
        "AuthorizeSiteReleaseCandidateRequest", "RevokeSiteReleaseCandidateRequest", "PublishWebBuildMaterialBundleRequest",
        "IssueWebBuildIntentRequest", "PublishReleaseCertificationRequest", "PublishSiteReleaseRequest",
    ):
        assert "AuthenticatedOperatorCommandContext context" in _message_body(publication, operation)
    for message, fields in {
        "PublishProductSurfaceCatalogEffect": ("catalog_revision",),
        "PublishLaunchProductProfileEffect": ("profile_revision", "product_surface_catalog"),
    }.items():
        body = _message_body(catalog, message)
        for field in fields:
            assert field in body
        assert "bytes payload" not in body
        assert "string operation" not in body

    registry = json.loads((CONTRACT / "registry/boundaries.yaml").read_text())
    by_id = {item["id"]: item for item in registry["boundaries"]}
    assert by_id["platform-site-provisioning"]["lifecycle"] == "contract-only"
    assert [operation["id"] for operation in by_id["platform-site-provisioning"]["operations"]] == ["RegisterSite"]
    assert [operation["id"] for operation in by_id["platform-product-catalog-publication"]["operations"]] == [
        "PublishProductSurfaceCatalog", "PublishLaunchProductProfile",
    ]
    assert [operation["id"] for operation in by_id["platform-site-publication"]["operations"]] == [
        "AuthorizeSiteReleaseCandidate",
        "RevokeSiteReleaseCandidate",
        "PublishSurfaceInventory",
        "PublishWebBuildMaterialBundle",
        "IssueWebBuildIntent",
        "PublishReleaseCertification",
        "PublishSiteRelease",
    ]
    assert [operation["id"] for operation in by_id["platform-site-evidence-admission"]["operations"]] == [
        "RecordReleaseEvidence",
    ]
    assert by_id["platform-site-evidence-admission"]["audience"] == "kokoro.site-release-evidence-admission.v1"
    assert by_id["platform-site-evidence-admission"]["trustPlane"] == "internal-control"
    assert by_id["platform-site-evidence-admission"]["consumers"] == [
        {"boundary": "web.release-attestor", "repository": "kokoro-web"},
    ]
    architecture = json.loads((CONTRACT.parent / "config/architecture/index-roots.yaml").read_text())
    architecture_by_id = {item["id"]: item for item in architecture["roots"]}
    release_attestor = architecture_by_id["web.release-attestor"]
    assert release_attestor["kind"] == "boundary"
    assert release_attestor["boundary"] == "web.release-attestor"
    assert release_attestor["path"].startswith("kokoro-web/")
    assert release_attestor["id"] not in {"web.user", "web.admin"}
    federation = json.loads((CONTRACT.parent / "config/repository/federated-repositories.json").read_text())
    protocol_roles = {
        (repository["id"], protocol["id"], protocol["role"], protocol["lifecycle"])
        for repository in federation["repositories"]
        for protocol in repository["protocols"]
    }
    assert (
        "kokoro-platform", "platform-site-evidence-admission", "provider", "contract-only",
    ) in protocol_roles
    assert (
        "kokoro-web", "platform-site-evidence-admission", "consumer", "contract-only",
    ) in protocol_roles
    compatibility = json.loads((CONTRACT.parent / "config/repository/compatibility-matrix.json").read_text())
    assert "platform-site-evidence-admission" not in {
        contract["id"] for contract in compatibility["contracts"]
    }
    assert by_id["platform-product-catalog-publication"]["provider"] == by_id["platform-site-publication"]["provider"]
    assert by_id["platform-product-catalog-publication"]["id"] != by_id["platform-site-publication"]["id"]


def test_site_release_publication_compatibility_corpus_freezes_latest_only_shape() -> None:
    path = CONTRACT / "corpus" / "site-release-publication-command-v1.json"
    assert path.exists()
    corpus = json.loads(path.read_text())
    assert corpus["schema"] == "kokoro.site-release-publication-command.corpus.v1"
    assert corpus["boundary"] == "platform-site-publication@v1"
    assert corpus["service"] == "kokoro.platform.site.v1.SitePublicationService"
    assert corpus["operation"] == "PublishSiteRelease"
    assert corpus["acceptedEffectFields"] == ["candidate", "reason"]
    assert corpus["positiveEffect"]["candidate"] == {
        "candidate_ref": "site-release-candidate.alpha.7",
        "candidate_version": "7",
        "candidate_authorization_epoch": "3",
        "candidate_digest": "a" * 64,
    }
    assert set(corpus["forbiddenLegacyEffectFields"]) >= {
        "site_release_candidate_ref", "expected_candidate_version", "enabled_surface_ids",
        "model_option_catalog_ref", "release_manifest_digest",
    }

    registry = json.loads((CONTRACT / "registry/boundaries.yaml").read_text())
    boundary = next(item for item in registry["boundaries"] if item["id"] == corpus["boundary"].removesuffix("@v1"))
    assert boundary["sources"] == [{
        "kind": "proto",
        "path": "contract/proto/kokoro/platform/site/v1/site_publication.proto",
        "select": {"service": "SitePublicationService"},
    }]
    assert corpus["operation"] in {item["id"] for item in boundary["operations"]}


def test_site_publication_r0b_checklists_cover_every_contract_only_boundary() -> None:
    handbook = (CONTRACT.parent / "docs/kokoro-handbook/technical/24-federated-product-platform-architecture.md").read_text()
    for boundary in (
        "platform-product-catalog-publication@v1",
        "platform-site-publication@v1",
        "platform-site-evidence-admission@v1",
        "platform-site-lifecycle@v1",
    ):
        assert f"#### `{boundary}`" in handbook
    for item in (
        "runtime/provider", "persistence", "authorization", "CAS", "live evidence",
        "generated mirror", "compatibility promotion",
    ):
        assert item in handbook


def test_admin_commerce_cursor_and_integer_limits_match_the_provider_storage() -> None:
    source = "\n".join((
        _proto("kokoro/platform/commerce/v1/commerce_catalog.proto"),
        _proto("kokoro/platform/commerce/v1/commerce_control.proto"),
    ))

    cursor_rules = re.findall(
        r"optional string (?:next_)?page_token = \d+ \[\(buf\.validate\.field\)\.string = \{(.*?)\}\];",
        source,
        re.DOTALL,
    )
    assert len(cursor_rules) == 2
    assert all("max_len: 2048" in rule for rule in cursor_rules)
    page = _message_body(source, "CommercePageRequest")
    assert "gte: 1" in page
    assert "max_len: 2048" in page
    assert "snapshot_digest" in page


def test_admin_commerce_fulfillment_lines_and_delivery_are_executable_contracts() -> None:
    source = "\n".join((
        _proto("kokoro/platform/commerce/v1/commerce_catalog.proto"),
        _proto("kokoro/platform/commerce/v1/commerce_control.proto"),
    ))

    program = _message_body(source, "PublishFulfillmentProgramRevisionEffect")
    assert "commerce.fulfillment.unique_lines" in program
    assert "repeated FulfillmentProgramOutputLine output_lines" in program
    assert "commerce.fulfillment.cardinality" in program
    session = _message_body(source, "SecretDeliverySessionView")
    assert "next_offset" in session
    assert "active_range" in session
    activation = _message_body(source, "CodeBatchActivationEvidence")
    assert "delivered_session" in activation
    assert "disposal_receipt" in activation


def test_model_gateway_publishes_one_resumable_server_stream() -> None:
    source = _proto("kokoro/platform/model/v1/model_gateway.proto")

    assert _service_methods(source, "ModelGatewayService") == [
        "InvokeModel",
        "StreamModel",
    ]
    assert re.search(
        r"rpc StreamModel\(StreamModelRequest\) returns \(stream StreamModelResponse\)",
        source,
    )
    request = _message_body(source, "StreamModelRequest")
    assert (
        "InvokeModelRequest invocation = 1 [(buf.validate.field).required = true];"
        in request
    )
    assert "uint64 after_sequence = 2;" in request


def test_model_gateway_stream_frame_is_closed_chained_and_bounded() -> None:
    source = _proto("kokoro/platform/model/v1/model_gateway.proto")
    frame = _message_body(source, "StreamModelResponse")

    assert "uint64 sequence = 3" in frame
    assert re.search(r"sequence.*?gte: 1", frame, re.DOTALL)
    for field in ("previous_frame_digest", "frame_digest"):
        assert re.search(
            rf"string {field}.*?len: 64.*?\^\[0-9a-f\]\{{64\}}\$",
            frame,
            re.DOTALL,
        )
    assert "option (buf.validate.oneof).required = true;" in frame
    for payload in (
        "ModelAccepted accepted",
        "ModelContentDelta content_delta",
        "ModelReasoningDelta reasoning_delta",
        "ModelToolCallDelta tool_call_delta",
        "ModelCompleted completed",
        "ModelFailed failed",
        "ModelOutcomeUnknown outcome_unknown",
    ):
        assert payload in frame

    content = _message_body(source, "ModelContentDelta")
    reasoning = _message_body(source, "ModelReasoningDelta")
    tool = _message_body(source, "ModelToolCallDelta")
    assert re.search(r"string content.*?max_bytes: 16384", content, re.DOTALL)
    assert re.search(r"string content.*?max_bytes: 16384", reasoning, re.DOTALL)
    assert re.search(
        r"bytes arguments_json_fragment.*?max_len: 16384", tool, re.DOTALL
    )
    assert re.search(r"uint32 tool_index.*?lte = 127", tool, re.DOTALL)

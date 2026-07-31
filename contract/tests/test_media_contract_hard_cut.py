"""Executable review gates for the ADR-015 Media contract hard cut."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
PROTO = ROOT / "contract/proto"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text()


def _message(source: str, name: str) -> str:
    match = re.search(rf"message {name} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert match is not None, name
    return match.group("body")


def _typescript_object(source: str, name: str) -> str:
    match = re.search(rf"export type {name} = \{{(?P<body>.*?)\n\}};", source, re.DOTALL)
    assert match is not None, name
    return match.group("body")


def _openapi() -> dict:
    return yaml.safe_load(_read("contract/openapi/platform-public-v1.yaml"))


def test_canonical_contract_is_byte_explicit_and_rejects_ambiguous_inputs(
    tmp_path: Path,
) -> None:
    spec = yaml.safe_load(_read("contract/spec/media-canonicalization.yaml"))
    assert set(spec) == {
        "schema_version",
        "algorithm",
        "domain_separator_hex",
        "message",
        "unknown_fields",
        "unicode_normalization",
        "kind",
        "input_errors",
    }
    separator = bytes.fromhex(spec["domain_separator_hex"])
    assert separator == b"kokoro.media.caller-request-fingerprint.v1\0"
    canonical_proto = _read(
        "contract/proto/kokoro/platform/media/v1/media_canonical.proto"
    )
    assert 'pattern: "^[A-Za-z0-9][A-Za-z0-9._:@-]{0,255}$"' in canonical_proto

    corpus = json.loads(_read("contract/corpus/media-canonicalization-v1.json"))
    ids = {case["id"] for case in corpus["cases"]}
    assert {
        "prototype-key-rejected",
        "constructor-key-rejected",
        "astral-definition-ref-rejected",
        "lone-surrogate-prompt-rejected",
        "nfc-preserved",
        "nfd-preserved",
        "prompt-utf8-limit",
        "prompt-utf8-over-limit-rejected",
    }.issubset(ids)

    generated_ts = tmp_path / "media-canonical.ts"
    result = subprocess.run(
        [
            "node",
            "contract/generate-media-canonical.mjs",
            "--validate-corpus",
            "--output",
            str(generated_ts),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    source = generated_ts.read_text()
    assert "input: unknown" in source
    assert "Object.hasOwn" in source
    assert "mediaCallerRequestFingerprintSha256" in source
    assert "mediaCallerRequestFingerprintHeaders" in source
    assert '"X-Kokoro-Caller-Request-Fingerprint"' in source
    assert "Object.getOwnPropertyDescriptors(input)" in source
    assert "new TextEncoder().encode(value).length" in source

    generated_py = tmp_path / "media_canonical.py"
    result = subprocess.run(
        [
            "python3",
            "contract/generate_media_canonical.py",
            "--validate-corpus",
            "--output",
            str(generated_py),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "def canonical_media_operation_input_v1_bytes(input_value: object)" in generated_py.read_text()

    generated_client = tmp_path / "platform-public-client"
    result = subprocess.run(
        [
            "node",
            "contract/generate-public-openapi.mjs",
            "--output",
            str(generated_client),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (generated_client / "media-canonical.ts").read_text() == source
    assert "export * from './media-canonical.js';" in (generated_client / "index.ts").read_text()
    generated_types = (generated_client / "types.gen.ts").read_text()
    assert "'X-Kokoro-Caller-Request-Fingerprint': string" in generated_types
    completed = _typescript_object(generated_types, "MediaOperationCompletedView")
    failed = _typescript_object(generated_types, "MediaOperationFailedView")
    active = _typescript_object(generated_types, "MediaOperationActiveView")
    assert "outcomeClass:" in completed
    assert "outcomeClass:" in failed and "safeFailure:" in failed
    assert "outcomeClass" not in active and "safeFailure" not in active


def test_ga_runtime_keeps_product_revisions_platform_owned_and_closed_receipts() -> None:
    source = _read("contract/proto/kokoro/platform/media/v1/media_runtime.proto")
    assert 'import "kokoro/platform/media/v1/media_canonical.proto";' in source
    assert "message ImageCreateRequest" not in source
    assert "enum ImageAspectRatio" not in source
    create = _message(source, "CreateAgentImageOperationRequest")
    assert "AgentImageIntentV1 image_intent" in create
    assert "CanonicalMediaOperationInputV1 canonical_input" not in create
    intent = _message(source, "AgentImageIntentV1")
    assert "prompt_intent" in intent
    assert "aspect_ratio" in intent
    assert "candidate_count" in intent
    assert "output_format" in intent
    assert "definition_revision_ref" not in intent
    assert "model_option_revision_ref" not in intent
    fingerprint = _message(source, "AgentImageSubmissionFingerprintInputV1")
    assert "stable_output_slot_ref" in fingerprint
    assert "AgentImageIntentV1 image_intent" in fingerprint
    assert "Platform resolves the exact published" in source
    assert "same MediaOperation owner" in source
    assert "caller_request_fingerprint" in create
    cancel = _message(source, "CancelAgentMediaOperationRequest")
    assert "caller_request_fingerprint" not in cancel

    receipt = _message(source, "MediaCommandReceipt")
    assert "oneof outcome" in receipt
    for arm in (
        "submit_accepted",
        "submit_rejected",
        "submit_outcome_unknown",
        "cancel_accepted",
        "cancel_rejected",
        "cancel_outcome_unknown",
    ):
        assert arm in receipt
    assert "MediaCommandReceiptKind kind" not in receipt
    for message in (
        "SubmitMediaCommandAccepted",
        "SubmitMediaCommandOutcomeUnknown",
        "CancelMediaCommandAccepted",
        "CancelMediaCommandOutcomeUnknown",
    ):
        assert "recovery_action" in _message(source, message)
    assert "caller_request_fingerprint" in _message(source, "SubmitMediaCommandAccepted")
    assert "caller_request_fingerprint" not in _message(source, "CancelMediaCommandAccepted")


def test_public_owner_states_and_artifact_display_are_closed_unions() -> None:
    schemas = _openapi()["components"]["schemas"]
    operation = schemas["MediaOperationView"]
    candidate = schemas["MediaCandidateView"]
    artifact = schemas["ArtifactVersion"]
    cost = schemas["MediaCostProjectionView"]
    for schema, discriminator in (
        (operation, "state"),
        (candidate, "state"),
        (artifact, "availability"),
        (cost, "state"),
    ):
        assert schema["discriminator"]["propertyName"] == discriminator
        assert len(schema["oneOf"]) >= 3
    operation_wire = yaml.safe_dump(operation) + yaml.safe_dump(schemas)
    assert "awaiting_credit" not in operation_wire
    assert "accepted" not in schemas["MediaOperationState"]["enum"]

    ready_candidate = schemas["MediaCandidateReadyView"]
    assert {"artifactRef", "artifactVersionRef"}.issubset(ready_candidate["required"])
    for name in (
        "MediaCandidateProducingView",
        "MediaCandidateValidatingView",
        "MediaCandidateRestrictedView",
        "MediaCandidateFailedView",
        "MediaCandidateUnknownView",
        "MediaCandidateCanceledView",
    ):
        fields = schemas[name].get("properties", {})
        assert "artifactRef" not in fields
        assert "artifactVersionRef" not in fields

    assert "display" in schemas["ImageArtifactVersionReady"]["required"]
    for name in (
        "ImageArtifactVersionProcessing",
        "ImageArtifactVersionRestricted",
        "ImageArtifactVersionUnavailable",
        "ImageArtifactVersionDeleted",
    ):
        assert "display" not in schemas[name].get("properties", {})


def test_credit_cost_is_credit_owned_integer_decimal_union_everywhere() -> None:
    credit = _read("contract/proto/kokoro/platform/credit/v1/cost_projection.proto")
    assert "message CreditAmount" in credit
    amount = _message(credit, "CreditAmount")
    assert "credit_unit" in amount
    assert "amount" in amount
    assert "amount_micros" not in credit
    assert "currency_code" not in credit
    event = _message(credit, "CreditCostProjectionEventRecord")
    assert "oneof projection" in event
    for arm in ("pending", "estimated", "final", "corrected", "unavailable"):
        assert arm in event

    schemas = _openapi()["components"]["schemas"]
    assert schemas["CreditAmount"]["properties"]["amount"]["pattern"] == r"^(0|[1-9][0-9]{0,39})$"
    for name in ("CreditCostEstimated", "CreditCostFinal", "CreditCostCorrected"):
        assert "amount" in schemas[name]["required"]
    for name in ("CreditCostPending", "CreditCostUnavailable"):
        assert "amount" not in schemas[name].get("properties", {})

    http = yaml.safe_load(_read("contract/spec/http.yaml"))
    objects = {obj["name"]: obj for obj in http["objects"]}
    link_fields = {field["name"]: field for field in objects["CostProjectionLink"]["fields"]}
    assert link_fields["owner_version"]["type"] == "uint64_string"
    media_fields = {
        field["name"]: field
        for field in objects["MediaOperationPartPayload"]["common_fields"]
    }
    assert media_fields["owner_version"]["type"] == "uint64_string"
    assert media_fields["cost_projection"]["type"] == "object:CostProjectionLink"
    assert media_fields["cost_projection"]["optional"] is True


def test_durable_media_facts_can_build_chat_parts_without_agent_display_authority() -> None:
    media = _read("contract/proto/kokoro/platform/media/v1/media_projection.proto")
    activation = _message(media, "MediaProjectionBindingCommittedRecord")
    assert "definition_ref" in activation
    assert "definition_revision_ref" in activation
    candidate = _message(media, "MediaCandidateProjectionChanged")
    assert "ordinal" in candidate
    assert "oneof candidate_state" in candidate
    assert "MediaCandidateFailureFact restricted" in candidate
    assert "MediaCandidateFailureFact failed" in candidate
    artifact = _message(media, "MediaArtifactProjectionChanged")
    for field in ("media_class", "oneof artifact_state", "MediaArtifactReadyFact ready"):
        assert field in artifact

    agent = _read("contract/proto/kokoro/agent/execution/v1/agent_execution_evidence.proto")
    output = _message(agent, "DurableOutputPayloadV1")
    assert "MediaOperationReferenceOutputV1 media_operation_reference" in output
    narrative = _message(agent, "MediaOperationReferenceOutputV1")
    assert "stable_output_slot_ref" in narrative
    assert "agent_media_command_ref" in narrative
    assert "operation_ref" in narrative
    assert "safe_metadata_json" not in agent
    assert "ArtifactReferenceOutputV1" not in agent


def test_projection_records_have_public_verifiable_integrity_and_heads_are_immutable(
    tmp_path: Path,
) -> None:
    signing = _read("contract/proto/kokoro/common/v1/projection_integrity.proto")
    assert "PROJECTION_SIGNATURE_ALGORITHM_ED25519" in signing
    assert "key_revision" in _message(signing, "ProjectionSignature")
    spec = yaml.safe_load(_read("contract/spec/projection-integrity.yaml"))
    assert spec["signature_algorithm"] == "ED25519"
    assert spec["canonical_encoding"] == "DETERMINISTIC_PROTOBUF"
    assert spec["forbidden_signed_field_fragments"] == [
        "credential",
        "grant",
        "recovery_handle",
        "authorization_token",
    ]
    corpus = json.loads(_read("contract/corpus/projection-integrity-v1.json"))
    assert {case["messageType"] for case in corpus["cases"]} == {
        surface["message_type"] for surface in spec["surfaces"]
    }
    assert len(corpus["negativeCases"]) >= 4
    result = subprocess.run(
        ["node", "contract/validate-projection-integrity.mjs", "--validate-corpus"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    for relative, head_name in (
        ("contract/proto/kokoro/platform/media/v1/media_projection_recovery.proto", "MediaProjectionHead"),
        ("contract/proto/kokoro/platform/credit/v1/cost_projection_recovery.proto", "CreditCostProjectionHead"),
    ):
        source = _read(relative)
        head = _message(source, head_name)
        assert "head_digest" in head
        assert "ProjectionSignature signature" in head
        assert "refreshed_owner_recovery_handle" not in head


def test_session_projection_commands_are_recoverable_without_replaying_bearers() -> None:
    source = _read("contract/proto/kokoro/session/media/v1/media_projection.proto")
    service = re.search(r"service SessionMediaProjectionService \{(.*?)\n\}", source, re.DOTALL)
    assert service is not None
    assert "RecoverProjectionCommand" in service.group(1)
    for request in (
        "IssueMediaProjectionReservationRequest",
        "BindMediaProjectionTargetRequest",
        "CreateReplacementMediaProjectionBindingRequest",
        "RefreshMediaProjectionAccessRequest",
        "RefreshCreditCostProjectionAccessRequest",
    ):
        body = _message(source, request)
        assert "projection_command_ref" in body
        assert "projection_command_recovery_capability" in body
    recovery = _message(source, "RecoverProjectionCommandRequest")
    assert "projection_command_ref" in recovery
    assert "projection_command_recovery_capability" in recovery
    response = _message(source, "RecoverProjectionCommandResponse")
    assert "ProjectionCommandResolution resolution" in response
    resolution = _message(source, "ProjectionCommandResolution")
    assert "ProjectionCommandReceipt receipt" in resolution
    assert "oneof result" in resolution
    for arm in ("issue_result", "bind_result", "replacement_result", "refresh_media_result", "refresh_credit_result"):
        assert arm in resolution
    rotation = _message(source, "ProjectionCredentialRotation")
    for field in ("envelope_generation", "previous_credentials_valid_until", "previous_credentials_invalidated"):
        assert field in rotation
    binding = _message(source, "MediaProjectionBinding")
    assert "binding_lineage_ref" in binding
    assert "lineage_generation" in binding
    replacement = _message(source, "CreateReplacementMediaProjectionBindingRequest")
    assert "expected_lineage_generation" in replacement

    registry = json.loads(_read("contract/registry/boundaries.yaml"))
    boundary = next(item for item in registry["boundaries"] if item["id"] == "session-media-projection")
    operations = {item["id"]: item for item in boundary["operations"]}
    for operation in (
        "IssueMediaProjectionReservation",
        "BindMediaProjectionTarget",
        "CreateReplacementMediaProjectionBinding",
        "RefreshMediaProjectionAccess",
        "RefreshCreditCostProjectionAccess",
    ):
        assert operations[operation]["retryClass"] == "reconcile_receipt"
        assert operations[operation]["receipt"]["recoveryOperation"] == "RecoverProjectionCommand"


def test_artifact_delivery_has_authoritative_redemption_and_safe_filename() -> None:
    document = _openapi()
    operations = {
        operation["operationId"]: (method, path, operation)
        for path, item in document["paths"].items()
        for method, operation in item.items()
        if isinstance(operation, dict) and "operationId" in operation
    }
    method, path, redemption = operations["redeemArtifactDeliveryAuthorization"]
    assert method == "get"
    assert path == "/v1/artifact-delivery-authorizations/{authorizationRef}/content"
    assert redemption["security"] == [
        {"ProductWorkload": [], "ArtifactDeliveryCapability": []}
    ]
    response = redemption["responses"]["200"]
    if "$ref" in response:
        response = document["components"]["responses"][response["$ref"].rsplit("/", 1)[-1]]
    assert response["content"]["application/octet-stream"]["schema"]["format"] == "binary"
    assert "Content-Disposition" in response["headers"]

    filename = document["components"]["schemas"]["ArtifactDownloadDeliveryInput"]["properties"]["suggestedFileName"]
    assert filename["pattern"] == r"^[^\x00-\x1F\x7F/\\]{1,255}$"
    assert "RFC 6266" in filename["description"]
    assert "RFC 8187" in filename["description"]

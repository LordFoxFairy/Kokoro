"""Image-first authority contracts frozen by ADR-015."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROTO = ROOT / "contract/proto"


def _read(relative_path: str) -> str:
    return (PROTO / relative_path).read_text()


def _service_methods(source: str, service: str) -> list[str]:
    match = re.search(rf"service {service} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert match is not None
    return re.findall(r"^\s*rpc\s+(\w+)\(", match.group("body"), re.MULTILINE)


def _message_body(source: str, message: str) -> str:
    match = re.search(rf"message {message} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert match is not None
    return match.group("body")


def test_agent_media_runtime_is_opaque_recoverable_and_closed() -> None:
    source = _read("kokoro/platform/media/v1/media_runtime.proto")

    assert _service_methods(source, "MediaRuntimeService") == [
        "CreateAgentImageOperation",
        "CancelAgentMediaOperation",
        "RecoverMediaOperationByCommand",
        "GetAgentMediaOperation",
    ]
    create = _message_body(source, "CreateAgentImageOperationRequest")
    for field in (
        "media_access_handle",
        "media_projection_reservation_handle",
        "stable_output_slot_ref",
        "agent_media_command_ref",
        "caller_request_fingerprint",
    ):
        assert field in create
    for forbidden in ("site_id", "account_ref", "provider", "owner_keyed", "owner_digest"):
        assert forbidden not in create

    recover = _message_body(source, "RecoverMediaOperationByCommandRequest")
    assert "media_access_handle" in recover
    assert "media_command_ref" in recover
    for forbidden in ("caller_request_fingerprint", "image_request", "prompt", "owner_digest"):
        assert forbidden not in recover

    assert "enum MediaOperationState" in source
    assert "MEDIA_OPERATION_STATE_RECONCILING" in source
    assert "MEDIA_OPERATION_OUTCOME_CLASS_IRRECONCILABLE" in source
    assert "enum MediaRuntimeErrorCode" in source
    assert "MEDIA_RUNTIME_ERROR_CODE_IDEMPOTENCY_CONFLICT" in source
    assert "enum MediaCommandReceiptKind" in source
    assert "MEDIA_COMMAND_RECEIPT_KIND_CANCEL_INTENT_COMMITTED" in source
    assert "provider_canceled" not in source.lower()
    assert re.search(r"\bGeneration\b|\bJob\b", source) is None


def test_image_effect_has_preallocated_identity_and_safe_attempt_attachment() -> None:
    source = _read("kokoro/platform/model/image/v1/image_effect.proto")

    assert _service_methods(source, "ImageEffectV1Service") == [
        "CreateImageEffect",
        "RecoverImageEffectByCommand",
        "GetImageEffectByCommand",
        "RequestCancelImageEffect",
        "AttachNextAttemptAuthorization",
    ]
    create = _message_body(source, "CreateImageEffectRequest")
    for field in (
        "model_invocation_command_ref",
        "logical_output_slots",
        "effect_budget_commit_ref",
        "effect_budget_commit_digest",
        "attempt_ordinal",
    ):
        assert field in create
    assert "uint32 attempt_ordinal" in create
    assert "const = 1" in create

    attach = _message_body(source, "AttachNextAttemptAuthorizationRequest")
    for field in (
        "attempt_authorization_command_ref",
        "model_invocation_command_ref",
        "logical_invocation_ref",
        "definitely_not_submitted_receipt_ref",
        "definitely_not_submitted_receipt_digest",
        "next_attempt_ordinal",
        "effect_budget_commit_ref",
        "effect_budget_commit_digest",
    ):
        assert field in attach
    assert "does not dispatch" in source

    recover = _message_body(source, "RecoverImageEffectByCommandRequest")
    assert "caller_access_handle" in recover
    assert "caller_command_ref" in recover
    for forbidden in ("request_digest", "effect_budget_commit", "input_revision"):
        assert forbidden not in recover
    assert "IMAGE_EFFECT_STATE_SUBMISSION_UNKNOWN" in source
    assert "IMAGE_EFFECT_STATE_OUTCOME_UNKNOWN" in source
    assert "IMAGE_EFFECT_RECEIPT_KIND_DEFINITELY_NOT_SUBMITTED" in source
    assert "IMAGE_EFFECT_ERROR_CODE_IDEMPOTENCY_CONFLICT" in source
    assert re.search(r"\bGeneration\b|\bJob\b", source) is None


def test_session_projection_activates_first_and_keeps_credit_owner_facts_separate() -> None:
    source = _read("kokoro/session/media/v1/media_projection.proto")
    media_owner = _read("kokoro/platform/media/v1/media_projection.proto")
    credit_owner = _read("kokoro/platform/credit/v1/cost_projection.proto")

    assert _service_methods(source, "SessionMediaProjectionService") == [
        "IssueMediaProjectionReservation",
        "BindMediaProjectionTarget",
        "RecoverMediaProjectionActivation",
        "CreateReplacementMediaProjectionBinding",
        "RefreshMediaProjectionAccess",
        "GetMediaProjectionBinding",
        "RefreshCreditCostProjectionAccess",
        "GetCreditCostProjectionBinding",
    ]
    binding = _message_body(source, "MediaProjectionBinding")
    bound = _message_body(source, "BoundMediaProjectionTarget")
    assert "MEDIA_PROJECTION_BINDING_STATE_PENDING" in source
    assert "MEDIA_PROJECTION_BINDING_STATE_ACTIVE" in source
    assert "MEDIA_PROJECTION_BINDING_STATE_REJECTED" in source
    assert "MEDIA_PROJECTION_BINDING_STATE_EXPIRED" in source
    assert "MEDIA_PROJECTION_BINDING_STATE_REVOKED" in source
    assert "media_projection_handle" in bound
    assert "cost_projection_handle" in bound
    assert "media_projection_recovery_grant" in bound
    assert "media_projection_refresh_grant" in bound
    assert "credit_cost_projection_refresh_grant" in bound
    assert "cost_projection_handle" not in binding

    activation = _message_body(media_owner, "MediaProjectionBindingCommittedRecord")
    for field in (
        "event_digest",
        "command_commit_receipt_ref",
        "command_commit_receipt_digest",
        "binding_ref",
        "operation_ref",
        "producer_generation",
        "source_sequence",
        "predecessor_event_ref",
        "predecessor_event_digest",
    ):
        assert field in activation
    assert "media_projection_handle" not in activation
    assert "owner_recovery_handle" not in activation
    assert re.search(r"command_commit_receipt_digest\s*=\s*6\b", activation)
    assert re.search(r"event_digest\s*=\s*13\b", activation)
    activation_delivery = _message_body(source, "MediaProjectionBindingCommittedDeliveryEnvelope")
    assert "pending_media_projection_handle" in activation_delivery
    assert "owner_recovery_handle" in activation_delivery
    assert "MediaProjectionBindingCommittedRecord record" in activation_delivery
    assert "first event" in source

    media_event = _message_body(media_owner, "MediaProjectionEventRecord")
    assert "media_projection_handle" not in media_event
    assert "owner_recovery_handle" not in media_event
    assert "cost_projection_ref" in media_event
    assert "cost_projection_owner_version" in media_event
    for field in ("source_sequence", "predecessor_event_ref", "predecessor_event_digest", "owner_signature"):
        assert field in media_event
    for forbidden in ("cost_state", "amount_micros", "currency", "estimated_cost"):
        assert forbidden not in media_event

    media_delivery = _message_body(source, "MediaProjectionDeliveryEnvelope")
    assert "media_projection_handle" in media_delivery
    assert "owner_recovery_handle" in media_delivery
    assert "MediaProjectionEventRecord record" in media_delivery

    cost_event = _message_body(credit_owner, "CreditCostProjectionEventRecord")
    assert "cost_projection_handle" not in cost_event
    assert "owner_recovery_handle" not in cost_event
    assert "cost_projection_ref" in cost_event
    assert "owner_version" in cost_event
    assert "producer_generation" in cost_event
    for field in ("source_sequence", "predecessor_event_ref", "predecessor_event_digest", "owner_signature"):
        assert field in cost_event
    assert "cost_state" in cost_event
    assert "amount_micros" in cost_event
    cost_delivery = _message_body(source, "CreditCostProjectionDeliveryEnvelope")
    assert "cost_projection_handle" in cost_delivery
    assert "owner_recovery_handle" in cost_delivery
    assert "CreditCostProjectionEventRecord record" in cost_delivery

    media_refresh = _message_body(source, "RefreshMediaProjectionAccessResponse")
    credit_refresh = _message_body(source, "RefreshCreditCostProjectionAccessResponse")
    assert "media_projection_refresh_grant" in media_refresh
    assert "credit_cost_projection_refresh_grant" in credit_refresh
    assert "media_projection_refresh_grant" in _message_body(source, "RefreshMediaProjectionAccessRequest")
    assert "credit_cost_projection_refresh_grant" in _message_body(source, "RefreshCreditCostProjectionAccessRequest")
    for response in (media_refresh, credit_refresh):
        for immutable in ("event_ref", "event_digest", "owner_signature", "source_sequence"):
            assert immutable not in response


def test_projection_owner_chain_rules_reject_missing_or_illegal_predecessors() -> None:
    media = _read("kokoro/platform/media/v1/media_projection.proto")
    credit = _read("kokoro/platform/credit/v1/cost_projection.proto")

    assert 'id: "media_projection.activation_predecessor_absent"' in media
    assert (
        'expression: "this.source_sequence == 1u && '
        '!has(this.predecessor_event_ref) && !has(this.predecessor_event_digest)"'
    ) in media
    assert 'id: "media_projection.event_predecessor_required"' in media
    assert (
        'expression: "this.source_sequence >= 2u && '
        'has(this.predecessor_event_ref) && has(this.predecessor_event_digest)"'
    ) in media
    assert 'id: "credit_cost_projection.predecessor_by_sequence"' in credit
    assert (
        'expression: "(this.source_sequence == 1u && '
        '!has(this.predecessor_event_ref) && !has(this.predecessor_event_digest)) || '
        '(this.source_sequence > 1u && has(this.predecessor_event_ref) && '
        'has(this.predecessor_event_digest))"'
    ) in credit

    media_activation_cases = {
        (1, False, False): True,
        (1, True, False): False,
        (1, False, True): False,
        (1, True, True): False,
        (2, False, False): False,
    }
    for (sequence, has_ref, has_digest), expected in media_activation_cases.items():
        assert (sequence == 1 and not has_ref and not has_digest) is expected

    media_event_cases = {
        (1, True, True): False,
        (2, False, False): False,
        (2, True, False): False,
        (2, False, True): False,
        (2, True, True): True,
    }
    for (sequence, has_ref, has_digest), expected in media_event_cases.items():
        assert (sequence >= 2 and has_ref and has_digest) is expected

    credit_cases = {
        (0, False, False): False,
        (1, False, False): True,
        (1, True, False): False,
        (1, False, True): False,
        (1, True, True): False,
        (2, False, False): False,
        (2, True, False): False,
        (2, False, True): False,
        (2, True, True): True,
    }
    for (sequence, has_ref, has_digest), expected in credit_cases.items():
        valid = (sequence == 1 and not has_ref and not has_digest) or (
            sequence > 1 and has_ref and has_digest
        )
        assert valid is expected


def test_projection_recovery_has_separate_authenticated_owner_chains() -> None:
    media = _read("kokoro/platform/media/v1/media_projection_recovery.proto")
    credit = _read("kokoro/platform/credit/v1/cost_projection_recovery.proto")

    assert _service_methods(media, "MediaProjectionRecoveryService") == [
        "GetProjectionHead",
        "PullProjectionEvents",
    ]
    media_pull = _message_body(media, "PullProjectionEventsRequest")
    assert "owner_recovery_handle" in media_pull
    assert "after_sequence" in media_pull
    assert "limit" in media_pull
    assert "lte: 256" in media_pull
    media_head = _message_body(media, "MediaProjectionHead")
    for field in ("producer_generation", "high_watermark", "head_event_ref", "head_event_digest", "owner_signature"):
        assert field in media_head
    assert "CreditCostProjectionEvent" not in media
    media_response = _message_body(media, "PullProjectionEventsResponse")
    assert "replay_delivery_authorization" in media_response
    assert "MediaProjectionRecoveryRecord events" in media_response
    assert "min_items" not in media_response
    assert "max_items: 256" in media_response

    assert _service_methods(credit, "CreditCostProjectionRecoveryService") == [
        "GetProjectionHead",
        "PullProjectionEvents",
    ]
    credit_pull = _message_body(credit, "PullProjectionEventsRequest")
    assert "owner_recovery_handle" in credit_pull
    assert "after_sequence" in credit_pull
    assert "limit" in credit_pull
    assert "lte: 256" in credit_pull
    credit_head = _message_body(credit, "CreditCostProjectionHead")
    for field in ("producer_generation", "high_watermark", "head_event_ref", "head_event_digest", "owner_signature"):
        assert field in credit_head
    assert "MediaProjectionEvent" not in credit
    credit_response = _message_body(credit, "PullProjectionEventsResponse")
    assert "replay_delivery_authorization" in credit_response
    assert "CreditCostProjectionEventRecord events" in credit_response
    assert "min_items" not in credit_response
    assert "max_items: 256" in credit_response
    assert "only after the first cost record" in credit


def test_media_boundaries_are_contract_only_and_have_no_runtime_claim() -> None:
    boundaries = json.loads((ROOT / "contract/registry/boundaries.yaml").read_text())["boundaries"]
    by_id = {boundary["id"]: boundary for boundary in boundaries}
    expected = {
        "platform-media-runtime": ("kokoro-platform", ["kokoro-agent"]),
        "model-image-effect": ("kokoro-platform", ["kokoro-platform"]),
        "session-media-projection": ("kokoro-session", ["kokoro-platform"]),
        "media-session-projection-events": ("kokoro-platform", ["kokoro-session"]),
        "credit-session-cost-projection-events": ("kokoro-platform", ["kokoro-session"]),
        "platform-media-projection-recovery": ("kokoro-platform", ["kokoro-session"]),
        "platform-credit-cost-projection-recovery": ("kokoro-platform", ["kokoro-session"]),
    }
    for boundary_id, (provider, consumers) in expected.items():
        boundary = by_id[boundary_id]
        assert boundary["lifecycle"] == "contract-only"
        assert boundary["sourceStatus"] == "machine-readable"
        assert boundary["provider"]["repository"] == provider
        assert [item["repository"] for item in boundary["consumers"]] == consumers

    matrix = json.loads((ROOT / "config/repository/compatibility-matrix.json").read_text())
    runtime_ids = {contract["id"] for contract in matrix["contracts"]}
    assert runtime_ids.isdisjoint(expected)
    scenario_protocols = {
        protocol["id"]
        for scenario in matrix["runtimeGate"]["scenarios"]
        for protocol in scenario["protocols"]
    }
    assert scenario_protocols.isdisjoint(expected)

    manifest = json.loads((ROOT / "config/repository/federated-repositories.json").read_text())
    roles = {
        (repo["id"], protocol["id"], protocol["role"], protocol["lifecycle"])
        for repo in manifest["repositories"]
        for protocol in repo["protocols"]
    }
    assert ("kokoro-agent", "platform-media-runtime", "consumer", "contract-only") in roles
    assert ("kokoro-platform", "platform-media-runtime", "provider", "contract-only") in roles
    assert ("kokoro-platform", "model-image-effect", "provider", "contract-only") in roles
    assert ("kokoro-platform", "model-image-effect", "consumer", "contract-only") in roles
    assert ("kokoro-session", "session-media-projection", "provider", "contract-only") in roles
    assert ("kokoro-platform", "session-media-projection", "consumer", "contract-only") in roles
    assert ("kokoro-platform", "media-session-projection-events", "provider", "contract-only") in roles
    assert ("kokoro-session", "media-session-projection-events", "consumer", "contract-only") in roles
    assert ("kokoro-platform", "credit-session-cost-projection-events", "provider", "contract-only") in roles
    assert ("kokoro-session", "credit-session-cost-projection-events", "consumer", "contract-only") in roles
    assert ("kokoro-platform", "platform-media-projection-recovery", "provider", "contract-only") in roles
    assert ("kokoro-session", "platform-media-projection-recovery", "consumer", "contract-only") in roles
    assert ("kokoro-platform", "platform-credit-cost-projection-recovery", "provider", "contract-only") in roles
    assert ("kokoro-session", "platform-credit-cost-projection-recovery", "consumer", "contract-only") in roles

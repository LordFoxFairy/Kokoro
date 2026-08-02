"""Contract-only foundation for ADR-014 Interaction protocol V2."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contract"
EVIDENCE = CONTRACT / "proto/kokoro/agent/execution/v2/agent_execution_evidence.proto"
CONTROL = CONTRACT / "proto/kokoro/agent/control/v2/session_agent_control.proto"
CONTROL_SPEC = CONTRACT / "spec/session-agent-control-v2.yaml"
CORPUS = CONTRACT / "corpus/interaction-identity-v2.json"


def test_browser_hitl_versions_preserve_the_full_uint64_wire_domain() -> None:
    """JS clients must never narrow durable owner revisions to IEEE-754 numbers."""
    spec = yaml.safe_load((CONTRACT / "spec/http.yaml").read_text())
    objects = {item["name"]: item for item in spec["objects"]}

    expected = {
        "ActionDecisionCommandResult": "owner_version",
        "PlanDecisionCommandResult": "plan_version",
        "ActionDecisionRequest": "expected_owner_version",
        "PlanDecisionRequest": "expected_plan_version",
    }
    for object_name, field_name in expected.items():
        fields = {field["name"]: field for field in objects[object_name]["fields"]}
        assert fields[field_name]["type"] == "uint64_string"


def _message_body(source: str, message: str) -> str:
    block = re.search(
        rf"message {message} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL
    )
    assert block is not None, message
    return block.group("body")


def _service_methods(source: str, service: str) -> list[str]:
    block = re.search(
        rf"service {service} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL
    )
    assert block is not None, service
    return re.findall(r"^\s*rpc\s+(\w+)\(", block.group("body"), re.MULTILINE)


def _enum_values(source: str, enum: str) -> list[str]:
    block = re.search(rf"enum {enum} \{{(?P<body>.*?)\n\}}", source, flags=re.DOTALL)
    assert block is not None, enum
    return re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*=", block.group("body"), re.MULTILINE)


def _buf_validate(
    proto: Path, type_name: str, payload: dict[str, object]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(CONTRACT / "node_modules/.bin/buf"),
            "convert",
            str(proto.relative_to(CONTRACT)),
            "--type",
            type_name,
            "--from=-#format=json",
            "--to=-#format=json",
            "--validate",
        ],
        cwd=CONTRACT,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def _member(owner_ref: str, ordinal: int) -> dict[str, object]:
    digest = "a" * 64
    return {
        "interactionOwnerRef": owner_ref,
        "ownerRevision": "1",
        "projectionEventRef": f"ipev_{owner_ref}",
        "projectionPayloadSha256": digest,
        "interactionKind": "INTERACTION_KIND_V2_APPROVAL",
        "applicationRequestRef": f"areq_{owner_ref}",
        "decisionGroupRef": "igrp_fixture",
        "decisionGroupRevision": "1",
        "groupMemberOrdinal": ordinal,
        "requiredOwnerRevisionRefs": [
            {"interactionOwnerRef": owner_ref, "ownerRevision": "1"}
        ],
        "pendingFrameDigest": digest,
        "presentation": {
            "approval": {
                "prompt": {"title": "Approve this operation"},
                "allowedDecisions": ["INTERACTION_DECISION_KIND_V2_APPROVE"],
            }
        },
        "state": "INTERACTION_REVISION_STATE_V2_PENDING",
    }


def _valid_group() -> dict[str, object]:
    members = [_member("iown_one", 1), _member("iown_two", 2)]
    required = [
        {"interactionOwnerRef": "iown_one", "ownerRevision": "1"},
        {"interactionOwnerRef": "iown_two", "ownerRevision": "1"},
    ]
    for member in members:
        member["requiredOwnerRevisionRefs"] = deepcopy(required)
    return {
        "decisionGroupRef": "igrp_fixture",
        "decisionGroupRevision": "1",
        "groupProjectionRef": "igpev_fixture",
        "pendingFrameDigest": "a" * 64,
        "memberVectorSha256": "b" * 64,
        "members": members,
    }


def _valid_receipt() -> dict[str, object]:
    return {
        "runId": "run_fixture",
        "resumeRef": "rsm_fixture",
        "resumeReceiptRef": "rrcpt_fixture",
        "resumeReceiptEventRef": "rrcev_fixture",
        "resumeReceiptRevision": "1",
        "requestDigest": "c" * 64,
        "receiptEventSha256": "d" * 64,
        "status": "RUN_RESUME_RECEIPT_STATUS_V2_PERSISTED",
        "recordedAt": "2026-07-31T00:00:00Z",
        "producerInstanceRef": "agent_fixture",
        "producerGeneration": "1",
        "interactionProtocolReleaseEpoch": "interaction-epoch-fixture",
    }


def _resume_decision(owner_ref: str, ordinal: int) -> dict[str, object]:
    return {
        "interactionOwnerRef": owner_ref,
        "ownerRevision": "1",
        "projectionEventRef": f"ipev_{owner_ref}",
        "applicationRequestRef": f"areq_{owner_ref}",
        "groupMemberOrdinal": ordinal,
        "decisionReceiptRef": f"drcpt_{owner_ref}",
        "decisionPayloadSha256": "e" * 64,
        "kind": "INTERACTION_DECISION_KIND_V2_APPROVE",
        "decision": {"approve": {}},
    }


def _valid_resume() -> dict[str, object]:
    return {
        "payload": {
            "runId": "run_fixture",
            "resumeRef": "rsm_fixture",
            "pendingFrameDigest": "a" * 64,
            "decisionGroupRef": "igrp_fixture",
            "decisionGroupRevision": "1",
            "decisions": [
                _resume_decision("iown_one", 1),
                _resume_decision("iown_two", 2),
            ],
        },
        "requestDigest": "f" * 64,
        "interactionProtocolReleaseEpoch": "interaction-epoch-fixture",
    }


def test_v2_evidence_is_a_clean_whole_frame_successor() -> None:
    source = EVIDENCE.read_text()

    assert _service_methods(source, "AgentExecutionEvidenceService") == [
        "PullDurableExecutionEvidence",
        "GetDurableExecutionEvidence",
        "GetRunDurableCheckpoint",
        "PullDurableOutputRecords",
    ]
    canonical = _message_body(source, "DurableExecutionCanonicalPayloadV2")
    assert "InteractionGroupRevisionEvidenceV2 interaction_group_revision" in canonical
    assert "ActionOwnerEvidence" not in canonical
    assert "PlanOwnerEvidence" not in canonical

    envelope = _message_body(source, "DurableExecutionEvidenceV2")
    for authenticated_fence in (
        "string run_id",
        "string dispatch_id",
        "string assistant_message_id",
        "uint64 durable_seq",
        "uint64 producer_generation",
        "string evidence_sha256",
        "string interaction_protocol_release_epoch",
    ):
        assert authenticated_fence in envelope

    group = _message_body(source, "InteractionGroupRevisionEvidenceV2")
    for field in (
        "string decision_group_ref",
        "uint64 decision_group_revision",
        "string group_projection_ref",
        "string pending_frame_digest",
        "string member_vector_sha256",
        "repeated InteractionOwnerRevisionEvidenceV2 members",
    ):
        assert field in group
    assert "min_items: 1" in group
    assert "max_items: 64" in group
    assert "interaction_group.member_ordinals" in group
    assert "interaction_group.required_vector" in group

    member = _message_body(source, "InteractionOwnerRevisionEvidenceV2")
    for field in (
        "string interaction_owner_ref",
        "uint64 owner_revision",
        "string projection_event_ref",
        "optional string predecessor_projection_event_ref",
        "optional string predecessor_evidence_sha256",
        "string projection_payload_sha256",
        "InteractionKindV2 interaction_kind",
        "string application_request_ref",
        "uint32 group_member_ordinal",
        "repeated InteractionOwnerRevisionRefV2 required_owner_revision_refs",
        "InteractionPresentationV2 presentation",
    ):
        assert field in member
    assert "interaction_owner.predecessor_pair" in member
    assert "interaction_owner.predecessor_revision" in member
    assert "interaction_owner.group_identity" in member
    assert "interaction_owner.presentation_kind" in member
    assert _enum_values(source, "InteractionDecisionKindV2") == [
        "INTERACTION_DECISION_KIND_V2_UNSPECIFIED",
        "INTERACTION_DECISION_KIND_V2_APPROVE",
        "INTERACTION_DECISION_KIND_V2_EDIT",
        "INTERACTION_DECISION_KIND_V2_REJECT",
        "INTERACTION_DECISION_KIND_V2_RESPOND",
        "INTERACTION_DECISION_KIND_V2_SUBMIT",
    ]

    forbidden = (
        "site_id",
        "user_id",
        "owner_id",
        "workspace_id",
        "namespace",
        "langgraph",
        "interrupt_ref",
        "task_path",
    )
    assert all(field not in source.lower() for field in forbidden)


def test_v2_control_separates_durable_control_from_authenticated_gap_pull() -> None:
    source = CONTROL.read_text()
    spec = CONTROL_SPEC.read_text()

    assert _service_methods(source, "SessionAgentControlRecoveryService") == [
        "GetRunResumeReceiptEvents"
    ]
    resume = _message_body(source, "RunResumeV2")
    for field in (
        "RunResumePayloadV2 payload",
        "string request_digest",
        "string interaction_protocol_release_epoch",
    ):
        assert field in resume
    payload = _message_body(source, "RunResumePayloadV2")
    for field in (
        "string run_id",
        "string resume_ref",
        "string pending_frame_digest",
        "string decision_group_ref",
        "uint64 decision_group_revision",
        "repeated RunResumeDecisionV2 decisions",
    ):
        assert field in payload
    for forbidden_field in (
        "thread_id",
        "decision_id",
        "tool_id",
        "checkpoint_id",
        "checkpoint_namespace",
        "resume_target",
        "interrupt_ref",
        "task_path",
        "site_id",
        "user_id",
        "namespace",
    ):
        assert not re.search(rf"\b{forbidden_field}\b", source.lower())
    assert "langgraph" not in source.lower()
    assert "authenticated_context: workload-identity" in spec
    assert "strict_unknown_fields: reject" in spec

    decision = _message_body(source, "RunResumeDecisionV2")
    for field in (
        "string interaction_owner_ref",
        "uint64 owner_revision",
        "string projection_event_ref",
        "string application_request_ref",
        "string decision_receipt_ref",
        "string decision_payload_sha256",
        "InteractionDecisionPayloadV2 decision",
    ):
        assert field in decision

    receipt = _message_body(source, "RunResumeReceiptEventV2")
    for field in (
        "string run_id",
        "string resume_ref",
        "string resume_receipt_ref",
        "string resume_receipt_event_ref",
        "uint64 resume_receipt_revision",
        "optional string predecessor_receipt_event_ref",
        "optional string predecessor_receipt_event_sha256",
        "string request_digest",
        "string receipt_event_sha256",
        "RunResumeReceiptStatusV2 status",
        "string interaction_protocol_release_epoch",
    ):
        assert field in receipt
    for rule in (
        "resume_receipt.predecessor_pair",
        "resume_receipt.predecessor_revision",
        "resume_receipt.proof_requirements",
    ):
        assert rule in receipt
    assert _enum_values(source, "RunResumeReceiptStatusV2") == [
        "RUN_RESUME_RECEIPT_STATUS_V2_UNSPECIFIED",
        "RUN_RESUME_RECEIPT_STATUS_V2_PERSISTED",
        "RUN_RESUME_RECEIPT_STATUS_V2_APPLYING",
        "RUN_RESUME_RECEIPT_STATUS_V2_APPLIED",
        "RUN_RESUME_RECEIPT_STATUS_V2_SUPERSEDED",
        "RUN_RESUME_RECEIPT_STATUS_V2_REJECTED",
        "RUN_RESUME_RECEIPT_STATUS_V2_OUTCOME_UNKNOWN",
        "RUN_RESUME_RECEIPT_STATUS_V2_CLOSED_BY_TERMINAL",
    ]

    request = _message_body(source, "GetRunResumeReceiptEventsRequest")
    response = _message_body(source, "GetRunResumeReceiptEventsResponse")
    assert "uint64 after_receipt_revision" in request
    assert "uint32 page_size" in request and "lte: 64" in request
    assert "repeated RunResumeReceiptEventV2 events" in response
    for field in (
        "string run_id",
        "string resume_ref",
        "string resume_receipt_ref",
        "uint64 current_head_revision",
        "string current_head_event_ref",
        "string current_head_event_sha256",
    ):
        assert field in response


def test_v2_registry_and_generator_are_contract_only_and_not_active() -> None:
    registry = json.loads((CONTRACT / "registry/boundaries.yaml").read_text())
    by_id = {boundary["id"]: boundary for boundary in registry["boundaries"]}
    evidence = by_id["agent-execution-evidence"]
    control = by_id["session-agent-control"]

    assert evidence["version"] == 2
    assert evidence["lifecycle"] == "contract-only"
    assert evidence["sourceStatus"] == "machine-readable"
    assert evidence["sources"] == [
        {
            "kind": "proto",
            "path": "contract/proto/kokoro/agent/execution/v2/agent_execution_evidence.proto",
            "select": {"service": "AgentExecutionEvidenceService"},
        }
    ]
    assert {operation["id"] for operation in evidence["operations"]} == {
        "PullDurableExecutionEvidence",
        "GetDurableExecutionEvidence",
        "GetRunDurableCheckpoint",
        "PullDurableOutputRecords",
    }

    assert control["version"] == 2
    assert control["lifecycle"] == "contract-only"
    assert control["sourceStatus"] == "machine-readable"
    assert set(control["transports"]) == {
        "run-control-v2",
        "run-control-receipts-v2",
        "connect-rpc",
    }
    assert {operation["id"] for operation in control["operations"]} == {
        "RunResumeV2",
        "RunResumeReceiptEventV2",
        "GetRunResumeReceiptEvents",
    }
    control_operations = {
        operation["id"]: operation for operation in control["operations"]
    }
    assert control_operations["RunResumeV2"]["receipt"] == {
        "kind": "durable-event",
        "recoveryOperation": "GetRunResumeReceiptEvents",
        "ref": "kokoro.agent.control.v2.RunResumeReceiptEventV2",
    }
    assert control_operations["GetRunResumeReceiptEvents"]["trustedCallers"] == [
        {
            "audience": "agent.run-resume-recovery",
            "role": "session-control-reconciler",
        }
    ]

    matrix = json.loads(
        (ROOT / "config/repository/compatibility-matrix.json").read_text()
    )
    active = {(item["id"], item["version"]) for item in matrix["contracts"]}
    assert ("agent-execution-evidence", 2) not in active
    assert ("session-agent-control", 2) not in active

    generator = (CONTRACT / "generate.mjs").read_text()
    assert '"agent-execution-evidence@v2"' in generator
    assert '"session-agent-control@v2"' in generator


def test_identity_vectors_freeze_all_nine_adr_identity_planes() -> None:
    corpus = json.loads(CORPUS.read_text())
    assert corpus["schema"] == "kokoro.interaction-identity.v2"
    assert corpus["algorithm"] == "sha256-domain-nul-rfc8785-json-v1"
    assert corpus["canonical_profile"] == {
        "allowed_json_values": ["array", "object", "string"],
        "fixture_keys": "ascii-only",
        "integer_encoding": "decimal-string",
        "object_keys": "rfc8785-utf16-code-unit-lexicographic",
        "string_encoding": "rfc8785",
    }
    vectors = corpus["vectors"]
    assert {vector["kind"] for vector in vectors} == {
        "application_request",
        "interaction_owner",
        "projection_event",
        "group_projection",
        "human_decision",
        "decision_receipt",
        "run_resume",
        "resume_receipt",
        "resume_receipt_event",
    }
    assert len(vectors) == 9

    def assert_restricted_profile(value: object) -> None:
        if isinstance(value, str):
            return
        if isinstance(value, list):
            for member in value:
                assert_restricted_profile(member)
            return
        assert isinstance(value, dict)
        for key, member in value.items():
            assert key.isascii()
            assert_restricted_profile(member)

    for vector in vectors:
        assert_restricted_profile(vector["material"])
        canonical = json.dumps(
            vector["material"],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        assert canonical == vector["canonical_json"]
        digest = hashlib.sha256(
            vector["domain"].encode() + b"\0" + canonical.encode()
        ).hexdigest()
        assert vector["expected_ref"] == vector["prefix"] + digest
        assert re.fullmatch(
            rf"{re.escape(vector['prefix'])}[0-9a-f]{{64}}",
            vector["expected_ref"],
        )

    resume = next(vector for vector in vectors if vector["kind"] == "run_resume")
    assert [member["member_ordinal"] for member in resume["material"]["members"]] == [
        "1",
        "2",
    ]
    by_kind = {vector["kind"]: vector for vector in vectors}
    assert (
        by_kind["interaction_owner"]["material"]["application_request_ref"]
        == by_kind["application_request"]["expected_ref"]
    )
    assert (
        by_kind["decision_receipt"]["material"]["decision_id"]
        == by_kind["human_decision"]["expected_ref"]
    )
    assert (
        by_kind["resume_receipt"]["material"]["resume_ref"]
        == by_kind["run_resume"]["expected_ref"]
    )
    assert (
        by_kind["resume_receipt_event"]["material"]["resume_ref"]
        == by_kind["run_resume"]["expected_ref"]
    )


def test_v2_protovalidate_enforces_atomic_group_and_predecessor_rules() -> None:
    type_name = "kokoro.agent.execution.v2.InteractionGroupRevisionEvidenceV2"
    valid = _buf_validate(EVIDENCE, type_name, _valid_group())
    assert valid.returncode == 0, valid.stderr

    duplicate_ordinal = _valid_group()
    duplicate_ordinal["members"][1]["groupMemberOrdinal"] = 1  # type: ignore[index]
    invalid = _buf_validate(EVIDENCE, type_name, duplicate_ordinal)
    assert invalid.returncode != 0
    assert "member ordinals are unique" in invalid.stderr

    successor_without_predecessor = _valid_group()
    successor_without_predecessor["members"][0]["ownerRevision"] = "2"  # type: ignore[index]
    successor_without_predecessor["members"][0]["requiredOwnerRevisionRefs"][0][  # type: ignore[index]
        "ownerRevision"
    ] = "2"
    invalid = _buf_validate(EVIDENCE, type_name, successor_without_predecessor)
    assert invalid.returncode != 0
    assert "revision one has no predecessor" in invalid.stderr

    first_revision_with_predecessor = _valid_group()
    first_revision_with_predecessor["members"][0][  # type: ignore[index]
        "predecessorProjectionEventRef"
    ] = "ipev_previous"
    first_revision_with_predecessor["members"][0][  # type: ignore[index]
        "predecessorEvidenceSha256"
    ] = "c" * 64
    invalid = _buf_validate(EVIDENCE, type_name, first_revision_with_predecessor)
    assert invalid.returncode != 0
    assert "revision one has no predecessor" in invalid.stderr

    group_mismatch = _valid_group()
    group_mismatch["members"][1]["decisionGroupRevision"] = "2"  # type: ignore[index]
    invalid = _buf_validate(EVIDENCE, type_name, group_mismatch)
    assert invalid.returncode != 0
    assert "every member is bound to this exact group revision" in invalid.stderr

    invalid_approval_action = _valid_group()
    invalid_approval_action["members"][0]["presentation"]["approval"][  # type: ignore[index]
        "allowedDecisions"
    ] = ["INTERACTION_DECISION_KIND_V2_RESPOND"]
    invalid = _buf_validate(EVIDENCE, type_name, invalid_approval_action)
    assert invalid.returncode != 0
    assert "approval actions" in invalid.stderr

    mismatched_required_vector = _valid_group()
    mismatched_required_vector["members"][0]["requiredOwnerRevisionRefs"].reverse()  # type: ignore[index,union-attr]
    invalid = _buf_validate(EVIDENCE, type_name, mismatched_required_vector)
    assert invalid.returncode != 0
    assert "exact ordered group member vector" in invalid.stderr


def test_v2_protovalidate_enforces_receipt_chain_and_disposition_proofs() -> None:
    type_name = "kokoro.agent.control.v2.RunResumeReceiptEventV2"
    valid = _buf_validate(CONTROL, type_name, _valid_receipt())
    assert valid.returncode == 0, valid.stderr

    successor_without_predecessor = _valid_receipt()
    successor_without_predecessor["resumeReceiptRevision"] = "2"
    invalid = _buf_validate(CONTROL, type_name, successor_without_predecessor)
    assert invalid.returncode != 0
    assert "revision one has no predecessor" in invalid.stderr

    for status in (
        "RUN_RESUME_RECEIPT_STATUS_V2_APPLIED",
        "RUN_RESUME_RECEIPT_STATUS_V2_SUPERSEDED",
        "RUN_RESUME_RECEIPT_STATUS_V2_CLOSED_BY_TERMINAL",
    ):
        missing_proof = _valid_receipt()
        missing_proof["status"] = status
        invalid = _buf_validate(CONTROL, type_name, missing_proof)
        assert invalid.returncode != 0
        assert "carry their exact durable proof" in invalid.stderr


def test_v2_protovalidate_rejects_partial_resume_and_receipt_gaps() -> None:
    resume_type = "kokoro.agent.control.v2.RunResumeV2"
    valid_resume = _buf_validate(CONTROL, resume_type, _valid_resume())
    assert valid_resume.returncode == 0, valid_resume.stderr

    duplicate_member = _valid_resume()
    duplicate_member["payload"]["decisions"][1][  # type: ignore[index]
        "groupMemberOrdinal"
    ] = 1
    invalid = _buf_validate(CONTROL, resume_type, duplicate_member)
    assert invalid.returncode != 0
    assert "decision ordinals are unique" in invalid.stderr

    receipt_one = _valid_receipt()
    receipt_two = _valid_receipt()
    receipt_two.update(
        {
            "resumeReceiptEventRef": "rrcev_second",
            "resumeReceiptRevision": "2",
            "predecessorReceiptEventRef": "rrcev_fixture",
            "predecessorReceiptEventSha256": "d" * 64,
        }
    )
    pull_type = "kokoro.agent.control.v2.GetRunResumeReceiptEventsResponse"
    valid_pull = {
        "runId": "run_fixture",
        "resumeRef": "rsm_fixture",
        "resumeReceiptRef": "rrcpt_fixture",
        "currentHeadRevision": "2",
        "currentHeadEventRef": "rrcev_second",
        "currentHeadEventSha256": "d" * 64,
        "events": [receipt_one, receipt_two],
        "returnedAfterReceiptRevision": "0",
        "hasMore": False,
    }
    valid = _buf_validate(CONTROL, pull_type, valid_pull)
    assert valid.returncode == 0, valid.stderr

    gapped_pull = deepcopy(valid_pull)
    gapped_pull["events"][1]["resumeReceiptRevision"] = "3"  # type: ignore[index]
    invalid = _buf_validate(CONTROL, pull_type, gapped_pull)
    assert invalid.returncode != 0
    assert "exact range after the echoed cursor" in invalid.stderr

    substituted_aggregate = deepcopy(valid_pull)
    substituted_aggregate["events"][1]["resumeRef"] = "rsm_other"  # type: ignore[index]
    invalid = _buf_validate(CONTROL, pull_type, substituted_aggregate)
    assert invalid.returncode != 0
    assert "belongs to the stable receipt aggregate" in invalid.stderr


def test_v2_generator_outputs_are_boundary_isolated() -> None:
    fixtures = (
        (
            "agent-execution-evidence@v2",
            "kokoro.agent.execution.v2.AgentExecutionEvidenceService",
            "kokoro/agent/execution/v2/agent_execution_evidence_pb.ts",
            "kokoro/agent/control/v2/session_agent_control_pb.ts",
        ),
        (
            "session-agent-control@v2",
            "kokoro.agent.control.v2.SessionAgentControlRecoveryService",
            "kokoro/agent/control/v2/session_agent_control_pb.ts",
            "kokoro/agent/execution/v2/agent_execution_evidence_pb.ts",
        ),
    )
    with tempfile.TemporaryDirectory() as directory:
        for boundary, schema, own_file, forbidden_file in fixtures:
            output = Path(directory) / boundary
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
            metadata = (output / "contract-metadata.ts").read_text()
            assert f'schemaId: "{schema}"' in metadata
            assert "schemaVersion: 2" in metadata
            assert (output / own_file).is_file()
            assert not (output / forbidden_file).exists()

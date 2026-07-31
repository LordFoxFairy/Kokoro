from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _message(source: str, name: str) -> str:
    match = re.search(rf"message {name} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert match is not None, name
    return match.group("body")


def _service_methods(source: str, name: str) -> list[str]:
    match = re.search(rf"service {name} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert match is not None, name
    return re.findall(r"^\s*rpc\s+(\w+)\(", match.group("body"), re.MULTILINE)


def test_common_owner_recovery_credential_separates_read_access_from_refresh_authority() -> None:
    source = _read("contract/proto/kokoro/common/v1/projection_integrity.proto")

    access = _message(source, "ProjectionRecoveryAccessCredential")
    assert "string handle = 1" in access
    assert "uint64 generation = 2" in access
    assert "refresh" not in access

    envelope = _message(source, "OwnerProjectionRecoveryCredentialEnvelope")
    assert "ProjectionRecoveryAccessCredential access = 1" in envelope
    assert "google.protobuf.Timestamp access_expires_at = 2" in envelope
    assert "string refresh_grant = 3" in envelope
    assert "google.protobuf.Timestamp refresh_grant_expires_at = 4" in envelope
    assert "ProjectionRecoveryCredentialTransition transition = 5" in envelope
    assert "google.protobuf.Timestamp issued_at = 6" in envelope
    assert "projection_recovery_credential.transition" in source
    assert "projection_recovery_credential.expiry_order" in source


def test_media_and_credit_recovery_services_use_pure_reads_and_explicit_idempotent_refresh() -> None:
    cases = (
        (
            "contract/proto/kokoro/platform/media/v1/media_projection_recovery.proto",
            "MediaProjectionRecoveryService",
            "RefreshMediaProjectionRecoveryAccessEffect",
            "operation_ref",
        ),
        (
            "contract/proto/kokoro/platform/credit/v1/cost_projection_recovery.proto",
            "CreditCostProjectionRecoveryService",
            "RefreshCreditCostProjectionRecoveryAccessEffect",
            "cost_projection_ref",
        ),
    )

    for path, service, effect_name, projection_ref in cases:
        source = _read(path)
        assert _service_methods(source, service) == [
            "GetProjectionHead",
            "PullProjectionEvents",
            "RefreshProjectionRecoveryAccess",
        ]

        for request_name in ("GetProjectionHeadRequest", "PullProjectionEventsRequest"):
            request = _message(source, request_name)
            assert "ProjectionRecoveryAccessCredential owner_recovery_access = 1" in request
            assert "refresh_grant" not in request

        head_response = _message(source, "GetProjectionHeadResponse")
        pull_response = _message(source, "PullProjectionEventsResponse")
        for forbidden in (
            "refreshed_owner_recovery_handle",
            "replay_delivery_authorization",
            "replay_authorization_expires_at",
            "refresh_grant",
        ):
            assert forbidden not in head_response
            assert forbidden not in pull_response

        request = _message(source, "RefreshProjectionRecoveryAccessRequest")
        assert "kokoro.common.v2.CommandIdentityV2 command = 1" in request
        assert f"{effect_name} effect = 2" in request
        effect = _message(source, effect_name)
        assert "string owner_recovery_refresh_grant = 1" in effect
        assert "uint64 expected_generation = 2" in effect
        assert "string binding_ref = 3" in effect
        assert f"string {projection_ref} = 4" in effect
        assert "uint64 producer_generation = 5" in effect
        response = _message(source, "RefreshProjectionRecoveryAccessResponse")
        assert "kokoro.common.v2.CommandReceiptV2 receipt = 1" in response
        assert "uint64 expected_generation = 2" in response
        assert "OwnerProjectionRecoveryCredentialEnvelope owner_recovery_credential = 3" in response
        assert "projection_recovery_refresh.receipt_operation" in source
        assert "projection_recovery_refresh.committed_result" in source


def test_session_delivery_envelopes_carry_the_complete_owner_recovery_credential() -> None:
    source = _read("contract/proto/kokoro/session/media/v1/media_projection.proto")

    for envelope_name in (
        "MediaProjectionBindingCommittedDeliveryEnvelope",
        "MediaProjectionDeliveryEnvelope",
        "CreditCostProjectionDeliveryEnvelope",
    ):
        envelope = _message(source, envelope_name)
        assert (
            "kokoro.common.v1.OwnerProjectionRecoveryCredentialEnvelope "
            "owner_recovery_credential = 2"
        ) in envelope
        assert "string owner_recovery_handle" not in envelope


def test_registry_declares_projection_recovery_refresh_as_same_identity_effect() -> None:
    registry = json.loads(_read("contract/registry/boundaries.yaml"))
    boundaries = {boundary["id"]: boundary for boundary in registry["boundaries"]}

    for boundary_id in (
        "platform-media-projection-recovery",
        "platform-credit-cost-projection-recovery",
    ):
        operations = {operation["id"]: operation for operation in boundaries[boundary_id]["operations"]}
        assert list(operations) == [
            "GetProjectionHead",
            "PullProjectionEvents",
            "RefreshProjectionRecoveryAccess",
        ]
        assert operations["GetProjectionHead"]["effect"] is False
        assert operations["PullProjectionEvents"]["effect"] is False
        assert operations["RefreshProjectionRecoveryAccess"] == {
            "effect": True,
            "id": "RefreshProjectionRecoveryAccess",
            "receipt": {
                "kind": "command-receipt",
                "ref": "kokoro.common.v2.CommandReceiptV2",
            },
            "retryClass": "same_identity",
            "scope": "site",
            "siteBinding": "capability-binding",
            "transport": "connect-rpc",
        }


def test_projection_recovery_generation_and_transition_rules_execute() -> None:
    runner = r'''
import {execFileSync} from "node:child_process";
import {createFileRegistry,fromBinary,fromJson} from "@bufbuild/protobuf";
import {FileDescriptorSetSchema} from "@bufbuild/protobuf/wkt";
import {createValidator} from "@bufbuild/protovalidate";
const registry=createFileRegistry(fromBinary(FileDescriptorSetSchema,execFileSync("./node_modules/.bin/buf",["build","proto","--as-file-descriptor-set","-o","-"],{encoding:"buffer"})));
const validator=createValidator({registry,failFast:false});
function validate(typeName,value){
  const descriptor=registry.getMessage(typeName);
  return validator.validate(descriptor,fromJson(descriptor,value)).kind;
}
const initial={
  access:{handle:"a".repeat(32),generation:"1"},
  accessExpiresAt:"2026-01-01T00:05:00Z",
  refreshGrant:"r".repeat(32),
  refreshGrantExpiresAt:"2026-01-01T00:30:00Z",
  transition:{previousAccessState:"PROJECTION_RECOVERY_PREVIOUS_ACCESS_STATE_INITIAL"},
  issuedAt:"2026-01-01T00:00:00Z",
};
const rotated={
  ...initial,
  access:{handle:"b".repeat(32),generation:"2"},
  transition:{previousAccessState:"PROJECTION_RECOVERY_PREVIOUS_ACCESS_STATE_INVALIDATED"},
};
const overlap={
  ...rotated,
  transition:{
    previousAccessState:"PROJECTION_RECOVERY_PREVIOUS_ACCESS_STATE_OVERLAP",
    previousAccessValidUntil:"2026-01-01T00:04:00Z",
  },
};
const command={
  identity:{
    commandId:"command-1",
    idempotencyKey:"refresh-1",
    digestAlgorithm:"COMMAND_DIGEST_ALGORITHM_V2_SHA256_COMMAND_ENVELOPE",
    requestDigest:"c".repeat(64),
  },
  operation:"RefreshProjectionRecoveryAccess",
  state:"COMMAND_RECEIPT_STATE_V2_COMMITTED",
  recordedAt:"2026-01-01T00:00:00Z",
};
const observed={
  initial:validate("kokoro.common.v1.OwnerProjectionRecoveryCredentialEnvelope",initial),
  initialMarkedInvalidated:validate("kokoro.common.v1.OwnerProjectionRecoveryCredentialEnvelope",{
    ...initial,
    transition:{previousAccessState:"PROJECTION_RECOVERY_PREVIOUS_ACCESS_STATE_INVALIDATED"},
  }),
  rotated:validate("kokoro.common.v1.OwnerProjectionRecoveryCredentialEnvelope",rotated),
  overlap:validate("kokoro.common.v1.OwnerProjectionRecoveryCredentialEnvelope",overlap),
  overlapAfterCurrent:validate("kokoro.common.v1.OwnerProjectionRecoveryCredentialEnvelope",{
    ...overlap,
    transition:{...overlap.transition,previousAccessValidUntil:"2026-01-01T00:06:00Z"},
  }),
  overlapAtIssuance:validate("kokoro.common.v1.OwnerProjectionRecoveryCredentialEnvelope",{
    ...overlap,
    transition:{...overlap.transition,previousAccessValidUntil:overlap.issuedAt},
  }),
  accessExpiresAtIssuance:validate("kokoro.common.v1.OwnerProjectionRecoveryCredentialEnvelope",{
    ...initial,
    accessExpiresAt:initial.issuedAt,
  }),
  refreshDoesNotOutliveAccess:validate("kokoro.common.v1.OwnerProjectionRecoveryCredentialEnvelope",{
    ...initial,
    refreshGrantExpiresAt:initial.accessExpiresAt,
  }),
  committedNext:validate("kokoro.platform.media.v1.RefreshProjectionRecoveryAccessResponse",{
    receipt:command,
    expectedGeneration:"1",
    ownerRecoveryCredential:rotated,
  }),
  committedWrongGeneration:validate("kokoro.platform.media.v1.RefreshProjectionRecoveryAccessResponse",{
    receipt:command,
    expectedGeneration:"2",
    ownerRecoveryCredential:rotated,
  }),
  rejectedWithoutCredential:validate("kokoro.platform.media.v1.RefreshProjectionRecoveryAccessResponse",{
    receipt:{...command,state:"COMMAND_RECEIPT_STATE_V2_REJECTED"},
    expectedGeneration:"1",
  }),
  rejectedWithCredential:validate("kokoro.platform.media.v1.RefreshProjectionRecoveryAccessResponse",{
    receipt:{...command,state:"COMMAND_RECEIPT_STATE_V2_REJECTED"},
    expectedGeneration:"1",
    ownerRecoveryCredential:rotated,
  }),
  acceptedWithoutCredential:validate("kokoro.platform.media.v1.RefreshProjectionRecoveryAccessResponse",{
    receipt:{...command,state:"COMMAND_RECEIPT_STATE_V2_ACCEPTED"},
    expectedGeneration:"1",
  }),
};
process.stdout.write(JSON.stringify(observed));
'''
    result = subprocess.run(
        ["node", "--input-type=module", "-"],
        cwd=ROOT / "contract",
        input=runner,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "initial": "valid",
        "initialMarkedInvalidated": "invalid",
        "rotated": "valid",
        "overlap": "valid",
        "overlapAfterCurrent": "invalid",
        "overlapAtIssuance": "invalid",
        "accessExpiresAtIssuance": "invalid",
        "refreshDoesNotOutliveAccess": "invalid",
        "committedNext": "valid",
        "committedWrongGeneration": "invalid",
        "rejectedWithoutCredential": "valid",
        "rejectedWithCredential": "invalid",
        "acceptedWithoutCredential": "invalid",
    }


def test_projection_recovery_generation_tracks_common_sources_and_emits_digest_helpers() -> None:
    source = _read("contract/generate.mjs")

    assert 'commandEnvelopeDigest: "media-projection-recovery"' in source
    assert 'commandEnvelopeDigest: "credit-cost-projection-recovery"' in source
    assert "function mediaProjectionRecoveryDigestSource(kind)" in source
    for dependency in (
        '"kokoro/common/v1/error.proto"',
        '"kokoro/common/v1/projection_integrity.proto"',
        '"kokoro/common/v2/command_envelope.proto"',
    ):
        assert source.count(dependency) >= 2

    assert "mediaProjectionRecoveryRefreshRequestDigest" in source
    assert "creditCostProjectionRecoveryRefreshRequestDigest" in source
    assert "effect.producerGeneration.toString()" not in source

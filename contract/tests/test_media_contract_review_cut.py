from __future__ import annotations

import json
import importlib.util
import re
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _message(source: str, name: str) -> str:
    match = re.search(rf"message {name} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert match is not None, name
    return match.group("body")


def test_canonicalizers_take_one_immutable_data_descriptor_snapshot() -> None:
    source = _read("contract/generate-media-canonical.mjs")
    assert "Object.getOwnPropertyDescriptors(input)" in source
    manifest = json.loads(_read("contract/spec/media-canonicalization.yaml"))
    assert manifest["input_errors"]["$accessor"] == "MEDIA_CANONICAL_DATA_PROPERTY_REQUIRED"
    assert "Object.freeze(snapshot)" in source
    assert "const value = Object.freeze(dict(input_value))" not in source
    launcher = _read("contract/generate_media_canonical.py")
    assert "generate-media-canonical.mjs" in launcher
    assert "canonical_media_operation_input_v1_bytes" not in launcher


def test_projection_failure_state_and_terminal_taxonomies_are_closed() -> None:
    durable = _read("contract/proto/kokoro/platform/media/v1/media_projection.proto")
    session = _read("contract/proto/kokoro/session/media/v1/media_projection.proto")
    assert "enum MediaProjectionFailureCode" in durable
    assert "oneof operation_state" in durable
    assert "oneof candidate_state" in durable
    assert "oneof artifact_state" in durable
    assert "MEDIA_PROJECTION_TERMINAL_OUTCOME_CLASS_CANONICAL" in durable
    assert "enum MediaProjectionFailureCode" in session


def test_admission_carries_only_the_session_owner_issued_projection_authorization() -> None:
    admission = _read("contract/proto/kokoro/platform/admission/v1/admission.proto")
    prepare = _message(admission, "PrepareRunEffect")
    assert "string session_projection_authorization_handle" in prepare
    assert "min_len: 32" in prepare
    assert "max_len: 8192" in prepare

    for browser_safe_message in ("SafeAdmissionSnapshot", "PreparedRunAuthorization"):
        assert "session_projection_authorization_handle" not in _message(
            admission, browser_safe_message
        )
    assert "session_projection_authorization_handle" not in _read(
        "contract/openapi/platform-public-v1.yaml"
    )


def test_projection_ingest_is_a_separate_typed_connect_delivery_entry() -> None:
    source = _read(
        "contract/proto/kokoro/session/media/v1/media_projection_ingest.proto"
    )
    service = re.search(
        r"service SessionMediaProjectionIngestService \{(.*?)\n\}", source, re.DOTALL
    )
    assert service is not None
    methods = re.findall(r"rpc (\w+)\(", service.group(1))
    assert methods == [
        "ApplyMediaProjectionEvent",
        "ApplyCreditCostProjectionEvent",
    ]

    media_request = _message(source, "ApplyMediaProjectionEventRequest")
    assert "MediaProjectionDeliveryEnvelope delivery" in media_request
    assert "oneof delivery" not in media_request
    assert "MediaProjectionBindingCommittedDeliveryEnvelope" not in media_request
    assert "caller_role" not in media_request
    assert "caller_audience" not in media_request
    assert "spiffe" not in media_request.lower()

    credit_request = _message(source, "ApplyCreditCostProjectionEventRequest")
    assert "CreditCostProjectionDeliveryEnvelope delivery" in credit_request
    assert "caller_role" not in credit_request
    assert "caller_audience" not in credit_request
    assert "spiffe" not in credit_request.lower()

    receipt = _message(source, "ProjectionIngestReceipt")
    for field in (
        "event_ref",
        "record_digest",
        "binding_ref",
        "source_sequence",
        "outcome",
        "recovery_action",
        "accepted_high_watermark",
        "recorded_at",
    ):
        assert field in receipt
    for outcome in (
        "PROJECTION_INGEST_OUTCOME_APPLIED",
        "PROJECTION_INGEST_OUTCOME_REPLAYED",
        "PROJECTION_INGEST_OUTCOME_PENDING_GAP",
        "PROJECTION_INGEST_OUTCOME_REJECTED",
        "PROJECTION_INGEST_OUTCOME_SUPPRESSED",
    ):
        assert outcome in source
    for action in (
        "PROJECTION_INGEST_RECOVERY_ACTION_NONE",
        "PROJECTION_INGEST_RECOVERY_ACTION_RECOVER_MISSING_PREDECESSOR",
        "PROJECTION_INGEST_RECOVERY_ACTION_RECONCILE_OWNER",
        "PROJECTION_INGEST_RECOVERY_ACTION_CONTACT_SUPPORT",
    ):
        assert action in source
    for rejection in (
        "PROJECTION_INGEST_REJECTION_CODE_RECORD_INTEGRITY_CONFLICT",
        "PROJECTION_INGEST_REJECTION_CODE_OWNER_FENCE_CONFLICT",
    ):
        assert rejection in source
    assert "projection_ingest.outcome_recovery_contract" in source


def test_projection_ingest_outcome_and_recovery_contract_executes() -> None:
    runner = r'''
import {execFileSync} from "node:child_process";
import {createFileRegistry,fromBinary,fromJson} from "@bufbuild/protobuf";
import {FileDescriptorSetSchema} from "@bufbuild/protobuf/wkt";
import {createValidator} from "@bufbuild/protovalidate";
const registry=createFileRegistry(fromBinary(FileDescriptorSetSchema,execFileSync("./node_modules/.bin/buf",["build","proto","--as-file-descriptor-set","-o","-"],{encoding:"buffer"})));
const descriptor=registry.getMessage("kokoro.session.media.v1.ProjectionIngestReceipt");
const validator=createValidator({registry,failFast:false});
const base={eventRef:"event-1",recordDigest:"a".repeat(64),bindingRef:"binding-1",sourceSequence:"2",acceptedHighWatermark:"1",recordedAt:"1970-01-01T00:00:00Z"};
function validate(value){return validator.validate(descriptor,fromJson(descriptor,{...base,...value})).kind;}
const observed={
  applied:validate({outcome:"PROJECTION_INGEST_OUTCOME_APPLIED",recoveryAction:"PROJECTION_INGEST_RECOVERY_ACTION_NONE",acceptedHighWatermark:"2"}),
  gap:validate({outcome:"PROJECTION_INGEST_OUTCOME_PENDING_GAP",recoveryAction:"PROJECTION_INGEST_RECOVERY_ACTION_RECOVER_MISSING_PREDECESSOR",expectedNextSequence:"2"}),
  integrity:validate({outcome:"PROJECTION_INGEST_OUTCOME_REJECTED",recoveryAction:"PROJECTION_INGEST_RECOVERY_ACTION_CONTACT_SUPPORT",rejectionCode:"PROJECTION_INGEST_REJECTION_CODE_RECORD_INTEGRITY_CONFLICT"}),
  fence:validate({outcome:"PROJECTION_INGEST_OUTCOME_REJECTED",recoveryAction:"PROJECTION_INGEST_RECOVERY_ACTION_RECONCILE_OWNER",rejectionCode:"PROJECTION_INGEST_REJECTION_CODE_OWNER_FENCE_CONFLICT"}),
  missingGap:validate({outcome:"PROJECTION_INGEST_OUTCOME_PENDING_GAP",recoveryAction:"PROJECTION_INGEST_RECOVERY_ACTION_RECOVER_MISSING_PREDECESSOR"}),
  wrongApplied:validate({outcome:"PROJECTION_INGEST_OUTCOME_APPLIED",recoveryAction:"PROJECTION_INGEST_RECOVERY_ACTION_RECONCILE_OWNER"}),
  wrongRejected:validate({outcome:"PROJECTION_INGEST_OUTCOME_REJECTED",recoveryAction:"PROJECTION_INGEST_RECOVERY_ACTION_RECONCILE_OWNER",rejectionCode:"PROJECTION_INGEST_REJECTION_CODE_RECORD_INTEGRITY_CONFLICT"}),
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
        "applied": "valid",
        "gap": "valid",
        "integrity": "valid",
        "fence": "valid",
        "missingGap": "invalid",
        "wrongApplied": "invalid",
        "wrongRejected": "invalid",
    }


def test_projection_boundaries_freeze_method_level_trusted_callers() -> None:
    registry = json.loads(_read("contract/registry/boundaries.yaml"))
    boundaries = {boundary["id"]: boundary for boundary in registry["boundaries"]}

    def callers(boundary: str, operation: str) -> list[dict[str, str]]:
        item = next(
            candidate
            for candidate in boundaries[boundary]["operations"]
            if candidate["id"] == operation
        )
        return item["trustedCallers"]

    admission = [
        {
            "role": "platform-admission",
            "audience": "session.media-projection.reservation",
        }
    ]
    media = [
        {
            "role": "platform-media",
            "audience": "session.media-projection.media",
        }
    ]
    credit = [
        {
            "role": "platform-credit",
            "audience": "session.media-projection.credit",
        }
    ]

    assert callers("session-media-projection", "IssueMediaProjectionReservation") == admission
    for operation in (
        "BindMediaProjectionTarget",
        "RecoverMediaProjectionActivation",
        "CreateReplacementMediaProjectionBinding",
        "RefreshMediaProjectionAccess",
        "GetMediaProjectionBinding",
    ):
        assert callers("session-media-projection", operation) == media
    for operation in (
        "RefreshCreditCostProjectionAccess",
        "GetCreditCostProjectionBinding",
    ):
        assert callers("session-media-projection", operation) == credit
    assert callers("session-media-projection", "RecoverProjectionCommand") == [
        *admission,
        *media,
        *credit,
    ]
    assert callers("session-media-projection-ingest", "ApplyMediaProjectionEvent") == media
    assert callers(
        "session-media-projection-ingest", "ApplyCreditCostProjectionEvent"
    ) == credit
    for operation in ("VerifyPrepareOwner", "VerifyFinalizeOwner"):
        assert callers("session-admission-owner", operation) == [
            {
                "role": "platform-admission",
                "audience": "session.admission-owner",
            }
        ]
    assert callers(
        "session-dispatch-owner-evidence", "GetDispatchOwnerEvidence"
    ) == [
        {
            "role": "platform-admission",
            "audience": "session.dispatch-owner-evidence",
        }
    ]

    media_events = boundaries["media-session-projection-events"]["operations"]
    activation = next(
        item
        for item in media_events
        if item["id"] == "MediaProjectionBindingCommitted"
    )
    assert activation["receipt"]["ref"] == (
        "kokoro.session.media.v1.MediaProjectionActivationReceipt"
    )


def test_projection_ingest_federation_and_generation_stay_contract_only() -> None:
    manifest = json.loads(_read("config/repository/federated-repositories.json"))
    repositories = {repository["id"]: repository for repository in manifest["repositories"]}

    def protocol(repository: str) -> dict[str, object]:
        return next(
            item
            for item in repositories[repository]["protocols"]
            if item["id"] == "session-media-projection-ingest"
        )

    assert protocol("kokoro-platform") == {
        "id": "session-media-projection-ingest",
        "version": 1,
        "role": "consumer",
        "lifecycle": "contract-only",
    }
    assert protocol("kokoro-session") == {
        "id": "session-media-projection-ingest",
        "version": 1,
        "role": "provider",
        "lifecycle": "contract-only",
    }
    generator = _read("contract/generate.mjs")
    assert '"session-media-projection-ingest@v1"' in generator
    generated_gate = _read("scripts/repository/check-generated-contracts.mjs")
    assert '"session-media-projection-ingest@v1"' in generated_gate


def test_browser_media_parts_preserve_the_signed_producer_union() -> None:
    spec = yaml.safe_load(_read("contract/spec/http.yaml"))
    enums = spec["enums"]
    assert enums["media_safe_failure_code"] == [
        "input_rejected",
        "policy_rejected",
        "credit_rejected",
        "generation_failed",
        "validation_failed",
        "temporarily_unavailable",
        "outcome_unknown",
        "artifact_restricted",
        "artifact_unavailable",
    ]
    assert "immediate" not in enums["retry_class"]
    assert enums["media_terminal_outcome_class"] == ["canonical", "irreconcilable"]
    objects = {item["name"]: item for item in spec["objects"]}
    operation = objects["MediaOperationPartPayload"]
    assert operation["discriminator"] == "state"
    operation_variants = {item["value"]: item for item in operation["variants"]}
    for state in ("completed", "partial", "canceled"):
        assert {field["name"] for field in operation_variants[state]["fields"]} == {"outcome_class"}
    assert {field["name"] for field in operation_variants["failed"]["fields"]} == {
        "outcome_class",
        "safe_failure",
    }
    candidate = objects["MediaCandidatePart"]
    unknown = next(item for item in candidate["variants"] if item["value"] == "unknown")
    assert "fields" not in unknown


def test_projection_integrity_uses_descriptors_and_reencode_equality() -> None:
    validator = _read("contract/validate-projection-integrity.mjs")
    for symbol in ("createFileRegistry", "FileDescriptorSetSchema", "fromBinary", "toBinary"):
        assert symbol in validator
    assert "readVarint" not in validator
    assert "createValidator" in validator
    assert "fieldName" not in validator
    corpus = json.loads(_read("contract/corpus/projection-integrity-v1.json"))
    negative_ids = {item["id"] for item in corpus["negativeCases"]}
    assert {
        "non-minimal-varint-rejected",
        "explicit-default-rejected",
        "invalid-utf8-rejected",
        "required-field-missing-rejected",
    }.issubset(negative_ids)
    authenticated_constraints = {
        item["messageType"]
        for item in corpus["negativeCases"]
        if item.get("authenticated") is True
    }
    assert authenticated_constraints == {
        item["messageType"] for item in corpus["cases"]
    }


def test_projection_integrity_corpus_is_reproducible_and_resource_bounded(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        ["node", "contract/generate-projection-integrity-corpus.mjs", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "projection_integrity_corpus_reproducible\n"

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b"{" + b" " * 1_048_576 + b"}")
    result = subprocess.run(
        [
            "node",
            "contract/validate-projection-integrity.mjs",
            "--validate-corpus-file",
            str(oversized),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert result.stderr == "PROJECTION_INTEGRITY_CORPUS_TOO_LARGE\n"

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    result = subprocess.run(
        [
            "node",
            "contract/validate-projection-integrity.mjs",
            "--validate-corpus-file",
            str(malformed),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert result.stderr == "PROJECTION_INTEGRITY_CORPUS_INVALID\n"

    symlink = tmp_path / "corpus-link.json"
    symlink.symlink_to(malformed)
    result = subprocess.run(
        [
            "node",
            "contract/validate-projection-integrity.mjs",
            "--validate-corpus-file",
            str(symlink),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert result.stderr == "PROJECTION_INTEGRITY_CORPUS_UNREADABLE\n"


def test_recovery_uses_the_same_closed_result_messages_as_direct_commands() -> None:
    session = _read("contract/proto/kokoro/session/media/v1/media_projection.proto")
    for result in (
        "IssueMediaProjectionReservationAcceptedResult",
        "BindMediaProjectionTargetAcceptedResult",
        "CreateReplacementMediaProjectionBindingAcceptedResult",
        "RefreshMediaProjectionAccessAcceptedResult",
        "RefreshCreditProjectionAccessAcceptedResult",
    ):
        assert session.count(result) == 2
    assert "enum ProjectionCommandKind" in session
    assert session.count("message ProjectionCommandResolution") == 1
    assert "projection_command_resolution.accepted_result_matches_command_kind" in session
    assert "command_kind == 1" not in session


def test_projection_command_symbolic_enum_mapping_executes_in_protovalidate() -> None:
    runner = r'''
import {execFileSync} from "node:child_process";
import {createFileRegistry,fromBinary,fromJson} from "@bufbuild/protobuf";
import {FileDescriptorSetSchema} from "@bufbuild/protobuf/wkt";
import {createValidator} from "@bufbuild/protovalidate";
const registry=createFileRegistry(fromBinary(FileDescriptorSetSchema,execFileSync("./node_modules/.bin/buf",["build","proto","--as-file-descriptor-set","-o","-"],{encoding:"buffer"})));
const descriptor=registry.getMessage("kokoro.session.media.v1.ProjectionCommandResolution");
const issueResponse=registry.getMessage("kokoro.session.media.v1.IssueMediaProjectionReservationResponse");
const validator=createValidator({registry,failFast:false});
const accepted={projectionCommandRef:"cmd",receiptVersion:"1",recoveryAction:"PROJECTION_COMMAND_RECOVERY_ACTION_NONE",recordedAt:"1970-01-01T00:00:00Z",commandKind:"PROJECTION_COMMAND_KIND_ISSUE_MEDIA_PROJECTION_RESERVATION"};
const issueResult={reservation:{mediaProjectionReservationHandle:"x".repeat(32),expiresAt:"1970-01-01T00:00:00Z",credentialRotation:{envelopeGeneration:"1",previousCredentialsInvalidated:false}}};
const valid=validator.validate(descriptor,fromJson(descriptor,{receipt:{accepted},issueResult}));
const invalid=validator.validate(descriptor,fromJson(descriptor,{receipt:{accepted:{...accepted,commandKind:"PROJECTION_COMMAND_KIND_BIND_MEDIA_PROJECTION_TARGET"}},issueResult}));
const rejected={projectionCommandRef:"cmd",safeErrorCode:"REJECTED",receiptVersion:"1",recordedAt:"1970-01-01T00:00:00Z",commandKind:"PROJECTION_COMMAND_KIND_ISSUE_MEDIA_PROJECTION_RESERVATION"};
const directValid=validator.validate(issueResponse,fromJson(issueResponse,{resolution:{receipt:{rejected}}}));
const directInvalid=validator.validate(issueResponse,fromJson(issueResponse,{resolution:{receipt:{rejected:{...rejected,commandKind:"PROJECTION_COMMAND_KIND_BIND_MEDIA_PROJECTION_TARGET"}}}}));
process.stdout.write(JSON.stringify({valid:valid.kind,invalid:invalid.kind,rule:invalid.kind==="invalid"?invalid.violations[0].ruleId:null,directValid:directValid.kind,directInvalid:directInvalid.kind,directRule:directInvalid.kind==="invalid"?directInvalid.violations[0].ruleId:null}));
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
        "valid": "valid",
        "invalid": "invalid",
        "rule": "projection_command_resolution.accepted_result_matches_command_kind",
        "directValid": "valid",
        "directInvalid": "invalid",
        "directRule": "projection_command.issue_receipt_kind",
    }


def test_integrity_corpus_covers_every_signed_surface_and_negative_field_classes() -> None:
    corpus = json.loads(_read("contract/corpus/projection-integrity-v1.json"))
    messages = {case["messageType"] for case in corpus["cases"]}
    assert messages == {
        "kokoro.platform.media.v1.MediaProjectionBindingCommittedRecord",
        "kokoro.platform.media.v1.MediaProjectionEventRecord",
        "kokoro.platform.credit.v1.CreditCostProjectionEventRecord",
        "kokoro.platform.media.v1.MediaProjectionHead",
        "kokoro.platform.credit.v1.CreditCostProjectionHead",
    }
    assert {case["expectedErrorCode"] for case in corpus["negativeCases"]} >= {
        "PROJECTION_INTEGRITY_UNKNOWN_FIELD",
        "PROJECTION_INTEGRITY_EXCLUDED_FIELD",
        "PROJECTION_INTEGRITY_SIGNATURE_FIELD",
    }


def test_artifact_delivery_has_bounded_single_range_and_deadline_contract() -> None:
    document = yaml.safe_load(_read("contract/openapi/platform-public-v1.yaml"))
    operation = document["paths"]["/v1/artifact-delivery-authorizations/{authorizationRef}/content"]["get"]
    parameters = {item["$ref"].split("/")[-1] for item in operation["parameters"]}
    assert {"ArtifactByteRange", "RequestDeadline"}.issubset(parameters)
    assert {"200", "206", "416"}.issubset(operation["responses"])
    assert operation["x-kokoro-max-range-bytes"] == 8_388_608
    generator = _read("contract/generate-public-openapi.mjs")
    assert "ArtifactDeliveryCallOptions" in generator
    assert "AbortSignal" in generator


def test_generated_artifact_delivery_helper_rejects_ambiguous_or_unsafe_inputs(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "platform-public-client"
    result = subprocess.run(
        ["node", "contract/generate-public-openapi.mjs", "--output", str(generated)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    compiled = tmp_path / "dist"
    result = subprocess.run(
        [
            str(ROOT / "contract/node_modules/.bin/tsc"),
            "--target",
            "ES2022",
            "--module",
            "ES2022",
            "--moduleResolution",
            "Bundler",
            "--lib",
            "ES2022,DOM",
            "--outDir",
            str(compiled),
            str(generated / "artifact-delivery.ts"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    (tmp_path / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    runner = tmp_path / "artifact-runner.mjs"
    runner.write_text(
        """
import { artifactDeliveryCall } from "./dist/artifact-delivery.js";
const signal = new AbortController().signal;
const cases = [];
function observe(id, input) {
  try { const value = artifactDeliveryCall(input); cases.push({id, range:value.headers.Range ?? null, deadline:value.headers["X-Kokoro-Request-Deadline-Ms"]}); }
  catch (error) { cases.push({id, code:error.code ?? error.message}); }
}
observe("valid-full", {signal, deadlineMs:30_000, range:{start:0n,endInclusive:8_388_607n}});
observe("valid-suffix", {signal, deadlineMs:1, range:{suffixLength:8_388_608n}});
observe("null", null);
observe("incomplete", {signal});
observe("extra-option", {signal, deadlineMs:1, surprise:true});
observe("null-range", {signal, deadlineMs:1, range:null});
observe("incomplete-range", {signal, deadlineMs:1, range:{start:0n}});
observe("mixed-range", {signal, deadlineMs:1, range:{start:0n,endInclusive:1n,suffixLength:1n}});
observe("extra-range", {signal, deadlineMs:1, range:{suffixLength:1n,surprise:true}});
observe("number-range", {signal, deadlineMs:1, range:{start:0,endInclusive:1}});
observe("negative", {signal, deadlineMs:1, range:{start:-1n,endInclusive:1n}});
observe("reversed", {signal, deadlineMs:1, range:{start:2n,endInclusive:1n}});
observe("span", {signal, deadlineMs:1, range:{start:0n,endInclusive:8_388_608n}});
observe("absolute", {signal, deadlineMs:1, range:{start:18_446_744_073_709_551_616n,endInclusive:18_446_744_073_709_551_616n}});
observe("suffix-zero", {signal, deadlineMs:1, range:{suffixLength:0n}});
observe("deadline", {signal, deadlineMs:30_001});
const aborted = new AbortController(); aborted.abort();
observe("aborted", {signal:aborted.signal, deadlineMs:1});
let optionGetterCalls = 0;
const optionAccessor = {deadlineMs:1}; Object.defineProperty(optionAccessor,"signal",{enumerable:true,get(){ optionGetterCalls += 1; return signal; }});
observe("option-accessor", optionAccessor);
let rangeGetterCalls = 0;
const rangeAccessor = {endInclusive:1n}; Object.defineProperty(rangeAccessor,"start",{enumerable:true,get(){ rangeGetterCalls += 1; return 0n; }});
observe("range-accessor", {signal, deadlineMs:1, range:rangeAccessor});
observe("option-prototype", Object.assign(Object.create({}), {signal, deadlineMs:1}));
observe("range-prototype", {signal, deadlineMs:1, range:Object.assign(Object.create({}), {suffixLength:1n})});
process.stdout.write(JSON.stringify({cases,optionGetterCalls,rangeGetterCalls}));
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["node", str(runner)], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert observed["optionGetterCalls"] == 0
    assert observed["rangeGetterCalls"] == 0
    by_id = {item["id"]: item for item in observed["cases"]}
    assert by_id["valid-full"]["range"] == "bytes=0-8388607"
    assert by_id["valid-suffix"]["range"] == "bytes=-8388608"
    assert all(
        item.get("range") is None or len(item["range"]) <= 64
        for item in observed["cases"]
    )
    assert {item["code"] for item in observed["cases"] if "code" in item} <= {
        "ARTIFACT_DELIVERY_OPTIONS_REQUIRED",
        "ARTIFACT_DELIVERY_OPTIONS_SHAPE_INVALID",
        "ARTIFACT_DELIVERY_DATA_PROPERTY_REQUIRED",
        "ARTIFACT_DELIVERY_ABORT_SIGNAL_REQUIRED",
        "ARTIFACT_DELIVERY_DEADLINE_INVALID",
        "ARTIFACT_DELIVERY_RANGE_INVALID",
    }
    for rejected in (
        "null",
        "incomplete",
        "extra-option",
        "null-range",
        "incomplete-range",
        "mixed-range",
        "extra-range",
        "number-range",
        "negative",
        "reversed",
        "span",
        "absolute",
        "suffix-zero",
        "deadline",
        "aborted",
        "option-accessor",
        "range-accessor",
        "option-prototype",
        "range-prototype",
    ):
        assert "code" in by_id[rejected], rejected


def test_emitted_typescript_executes_the_canonical_corpus_and_rejects_accessors(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "media-canonical.ts"
    result = subprocess.run(
        [
            "node",
            "contract/generate-media-canonical.mjs",
            "--validate-corpus",
            "--output",
            str(generated),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    compiled = tmp_path / "dist"
    result = subprocess.run(
        [
            str(ROOT / "contract/node_modules/.bin/tsc"),
            "--target",
            "ES2022",
            "--module",
            "ES2022",
            "--moduleResolution",
            "Bundler",
            "--lib",
            "ES2022,DOM",
            "--outDir",
            str(compiled),
            str(generated),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    (tmp_path / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    runner = tmp_path / "runner.mjs"
    runner.write_text(
        """
import fs from "node:fs";
import * as emitted from "./dist/media-canonical.js";
import * as source from SOURCE_URL;
const corpus = JSON.parse(fs.readFileSync(CORPUS_PATH, "utf8"));
const materialize = (item) => item.promptRepeat ? {...item.input, promptIntent: item.promptRepeat.scalar.repeat(item.promptRepeat.count)} : item.input;
async function run(api, asyncDigest) {
  const results = [];
  for (const item of corpus.cases) {
    try {
      const input = materialize(item);
      const canonicalHex = Buffer.from(api.canonicalMediaOperationInputV1Bytes(input)).toString("hex");
      const fingerprintSha256 = asyncDigest ? await api.mediaCallerRequestFingerprintSha256(input) : api.mediaCallerRequestFingerprintSha256(input);
      results.push({id:item.id, canonicalHex, fingerprintSha256});
    } catch (error) { results.push({id:item.id, errorCode:error.message}); }
  }
  let getterCalls = 0;
  const accessor = {...corpus.cases[0].input};
  Object.defineProperty(accessor, "aspectRatio", {enumerable:true, get() { getterCalls += 1; accessor.candidateCount = 4; return getterCalls === 1 ? "square_1_1" : "portrait_9_16"; }});
  let accessorError = "";
  try { api.canonicalMediaOperationInputV1Bytes(accessor); } catch (error) { accessorError = error.message; }
  const wrongPrototype = {...corpus.cases[0].input};
  Object.setPrototypeOf(wrongPrototype, {polluted:true});
  let prototypeError = "";
  try { api.canonicalMediaOperationInputV1Bytes(wrongPrototype); } catch (error) { prototypeError = error.message; }
  return {results, getterCalls, accessorError, prototypeError};
}
process.stdout.write(JSON.stringify({source:await run(source,false), emitted:await run(emitted,true)}));
""".replace("SOURCE_URL", json.dumps((ROOT / "contract/generate-media-canonical.mjs").as_uri()))
        .replace("CORPUS_PATH", json.dumps(str(ROOT / "contract/corpus/media-canonicalization-v1.json"))),
        encoding="utf-8",
    )
    result = subprocess.run(
        ["node", str(runner)], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert observed["source"] == observed["emitted"]
    assert observed["emitted"]["getterCalls"] == 0
    assert observed["emitted"]["accessorError"] == "MEDIA_CANONICAL_DATA_PROPERTY_REQUIRED"
    assert observed["emitted"]["prototypeError"] == "MEDIA_CANONICAL_INPUT_REQUIRED"

    generated_py = tmp_path / "media_canonical.py"
    result = subprocess.run(
        ["python3", "contract/generate_media_canonical.py", "--output", str(generated_py)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    spec = importlib.util.spec_from_file_location("generated_media_canonical", generated_py)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    corpus = json.loads(_read("contract/corpus/media-canonicalization-v1.json"))
    python_results = []
    for item in corpus["cases"]:
      value = item["input"]
      if "promptRepeat" in item:
          repeat = item["promptRepeat"]
          value = {**value, "promptIntent": repeat["scalar"] * repeat["count"]}
      try:
          python_results.append({
              "id": item["id"],
              "canonicalHex": module.canonical_media_operation_input_v1_bytes(value).hex(),
              "fingerprintSha256": module.media_caller_request_fingerprint_sha256(value),
          })
      except module.MediaCanonicalError as error:
          python_results.append({"id": item["id"], "errorCode": error.code})
    assert python_results == observed["emitted"]["results"]

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory


ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from contract.validate_slice_a_manifest import (
    ManifestError,
    projection_nack_echo_matches,
    validate_projection_nack_values,
)


def _classes(tmp_path: Path) -> tuple[type, type, type]:
    output = tmp_path / "slice-a.binpb"
    subprocess.run(
        ["pnpm", "exec", "buf", "build", "contract", "-o", str(output)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    descriptor = descriptor_pb2.FileDescriptorSet.FromString(output.read_bytes())
    pool = descriptor_pool.DescriptorPool()
    pending = list(descriptor.file)
    while pending:
        for file in list(pending):
            try:
                pool.AddSerializedFile(file.SerializeToString())
            except TypeError:
                continue
            pending.remove(file)
            break
        else:
            raise AssertionError("descriptor dependency closure is incomplete")
    request = message_factory.GetMessageClass(
        pool.FindMessageTypeByName("kokoro.agent.v1.AckProjectionRequest")
    )
    response = message_factory.GetMessageClass(
        pool.FindMessageTypeByName("kokoro.agent.v1.AckProjectionResponse")
    )

    legacy_file = descriptor_pb2.FileDescriptorProto(
        name="legacy_ack.proto", package="legacy", syntax="proto3"
    )
    legacy_request = legacy_file.message_type.add(name="AckProjectionRequest")
    for number, name, type_ in (
        (1, "request_id", descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
        (2, "agent_run_id", descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
        (3, "consumer_key", descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
        (4, "epoch", descriptor_pb2.FieldDescriptorProto.TYPE_UINT64),
        (5, "projected_seq", descriptor_pb2.FieldDescriptorProto.TYPE_UINT64),
    ):
        legacy_request.field.add(
            number=number,
            name=name,
            type=type_,
            label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
        )
    legacy_pool = descriptor_pool.DescriptorPool()
    legacy_pool.Add(legacy_file)
    legacy = message_factory.GetMessageClass(
        legacy_pool.FindMessageTypeByName("legacy.AckProjectionRequest")
    )
    return request, response, legacy


def _validate_request(request: object) -> None:
    validate_projection_nack_values(
        projected_seq=request.projected_seq,
        rejected_seq=request.rejected_seq if request.HasField("rejected_seq") else None,
        rejection_code=request.rejection_code if request.HasField("rejection_code") else None,
    )


def _response_matches(response: object, rejected_seq: int, rejection_code: str) -> bool:
    return projection_nack_echo_matches(
        requested_seq=rejected_seq,
        requested_code=rejection_code,
        stored_seq=(
            response.stored_rejected_seq
            if response.HasField("stored_rejected_seq") else None
        ),
        stored_code=(
            response.stored_rejection_code
            if response.HasField("stored_rejection_code") else None
        ),
    )


def test_positive_ack_bytes_are_unchanged_and_new_presence_is_absent(tmp_path: Path) -> None:
    request, response, _legacy = _classes(tmp_path)
    positive = request(
        request_id="r", agent_run_id="u", consumer_key="chat", epoch=1, projected_seq=5
    )
    assert positive.SerializeToString(deterministic=True) == bytes.fromhex(
        "0a01721201751a046368617420012805"
    )
    assert not positive.HasField("rejected_seq")
    assert not positive.HasField("rejection_code")
    positive_response = response(stored_epoch=1, stored_projected_seq=5)
    assert positive_response.SerializeToString(deterministic=True) == bytes.fromhex("08011005")
    assert not positive_response.HasField("stored_rejected_seq")
    assert not positive_response.HasField("stored_rejection_code")


def test_nack_presence_pair_next_seq_and_utf8_byte_bound(tmp_path: Path) -> None:
    request, _response, _legacy = _classes(tmp_path)
    base = dict(request_id="r", agent_run_id="u", consumer_key="chat", epoch=1, projected_seq=5)
    _validate_request(request(**base))
    _validate_request(request(**base, rejected_seq=6, rejection_code="PROTO_DECODE"))
    _validate_request(request(**base, rejected_seq=6, rejection_code="é" * 64))
    for invalid in (
        request(**base, rejected_seq=6),
        request(**base, rejection_code="PROTO_DECODE"),
        request(**base, rejected_seq=0, rejection_code="PROTO_DECODE"),
        request(**base, rejected_seq=7, rejection_code="PROTO_DECODE"),
        request(**base, rejected_seq=6, rejection_code="  "),
        request(**base, rejected_seq=6, rejection_code="é" * 65),
    ):
        with pytest.raises(ManifestError):
            _validate_request(invalid)


def test_old_server_ignores_nack_fields_and_absent_echo_is_fail_safe(tmp_path: Path) -> None:
    request, response, legacy = _classes(tmp_path)
    nack = request(
        request_id="r",
        agent_run_id="u",
        consumer_key="chat",
        epoch=1,
        projected_seq=5,
        rejected_seq=6,
        rejection_code="PROTO_DECODE",
    )
    old_server_request = legacy.FromString(nack.SerializeToString())
    assert old_server_request.projected_seq == 5
    assert old_server_request.epoch == 1
    old_server_request.DiscardUnknownFields()
    assert old_server_request.SerializeToString(deterministic=True) == bytes.fromhex(
        "0a01721201751a046368617420012805"
    )

    old_response = response.FromString(bytes.fromhex("08011005"))
    assert not _response_matches(old_response, 6, "PROTO_DECODE")
    exact = response(
        stored_epoch=1,
        stored_projected_seq=5,
        stored_rejected_seq=6,
        stored_rejection_code="PROTO_DECODE",
    )
    assert _response_matches(exact, 6, "PROTO_DECODE")
    mismatch = response(
        stored_epoch=1,
        stored_projected_seq=5,
        stored_rejected_seq=6,
        stored_rejection_code="SCHEMA_UNSUPPORTED",
    )
    assert not _response_matches(mismatch, 6, "PROTO_DECODE")

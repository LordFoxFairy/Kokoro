from __future__ import annotations

import json
import subprocess
from pathlib import Path

from google.protobuf import descriptor_pb2


ROOT = Path(__file__).parents[2]
MANIFEST = json.loads((ROOT / "contract/slice-a-contract-manifest.yaml").read_text())


SCALAR_TYPES = {
    "double": descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE,
    "float": descriptor_pb2.FieldDescriptorProto.TYPE_FLOAT,
    "int64": descriptor_pb2.FieldDescriptorProto.TYPE_INT64,
    "uint64": descriptor_pb2.FieldDescriptorProto.TYPE_UINT64,
    "int32": descriptor_pb2.FieldDescriptorProto.TYPE_INT32,
    "fixed64": descriptor_pb2.FieldDescriptorProto.TYPE_FIXED64,
    "fixed32": descriptor_pb2.FieldDescriptorProto.TYPE_FIXED32,
    "bool": descriptor_pb2.FieldDescriptorProto.TYPE_BOOL,
    "string": descriptor_pb2.FieldDescriptorProto.TYPE_STRING,
    "bytes": descriptor_pb2.FieldDescriptorProto.TYPE_BYTES,
    "uint32": descriptor_pb2.FieldDescriptorProto.TYPE_UINT32,
    "sfixed32": descriptor_pb2.FieldDescriptorProto.TYPE_SFIXED32,
    "sfixed64": descriptor_pb2.FieldDescriptorProto.TYPE_SFIXED64,
    "sint32": descriptor_pb2.FieldDescriptorProto.TYPE_SINT32,
    "sint64": descriptor_pb2.FieldDescriptorProto.TYPE_SINT64,
}


def _descriptor(tmp_path: Path) -> descriptor_pb2.FileDescriptorSet:
    output = tmp_path / "slice-a.binpb"
    subprocess.run(
        ["pnpm", "exec", "buf", "build", "contract", "-o", str(output)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    descriptor = descriptor_pb2.FileDescriptorSet()
    descriptor.ParseFromString(output.read_bytes())
    return descriptor


def test_descriptor_exactly_matches_machine_authority(tmp_path: Path) -> None:
    descriptor = _descriptor(tmp_path)
    expected_files = {item["path"]: item for item in MANIFEST["protobuf"]["files"]}
    actual_files = {item.name: item for item in descriptor.file if not item.name.startswith("google/")}
    assert set(actual_files) == set(expected_files)
    enums = {(item["package"], item["name"]): item for item in MANIFEST["protobuf"]["enums"]}
    messages = {(item["package"], item["name"]): item for item in MANIFEST["protobuf"]["messages"]}
    services = {(item["package"], item["name"]): item for item in MANIFEST["protobuf"]["services"]}
    enum_type_names = {f".{package}.{name}" for package, name in enums}

    for path, expected_file in expected_files.items():
        actual = actual_files[path]
        assert actual.package == expected_file["package"]
        assert list(actual.dependency) == sorted(expected_file["imports"])
        assert {("enum", item.name) for item in actual.enum_type} | {
            ("message", item.name) for item in actual.message_type
        } | {("service", item.name) for item in actual.service} == {
            (item["kind"], item["name"]) for item in expected_file["declarations"]
        }
        for actual_enum in actual.enum_type:
            expected = enums[(actual.package, actual_enum.name)]
            assert [(item.name, item.number) for item in actual_enum.value] == [
                (item["name"], item["number"]) for item in expected["values"]
            ]
        for actual_message in actual.message_type:
            expected = messages[(actual.package, actual_message.name)]
            expected_oneofs = []
            for field in expected["fields"]:
                if "oneof" in field and field["oneof"] not in expected_oneofs:
                    expected_oneofs.append(field["oneof"])
            actual_oneofs = [item.name for item in actual_message.oneof_decl if not item.name.startswith("_")]
            assert actual_oneofs == expected_oneofs
            assert len(actual_message.field) == len(expected["fields"])
            for actual_field, expected_field in zip(actual_message.field, expected["fields"], strict=True):
                assert (actual_field.number, actual_field.name) == (expected_field["number"], expected_field["name"])
                if expected_field["type"] in SCALAR_TYPES:
                    assert actual_field.type == SCALAR_TYPES[expected_field["type"]]
                    assert actual_field.type_name == ""
                else:
                    assert actual_field.type == (
                        descriptor_pb2.FieldDescriptorProto.TYPE_ENUM
                        if expected_field["type"] in enum_type_names
                        else descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
                    )
                    assert actual_field.type_name == expected_field["type"]
                if expected_field["label"] == "repeated":
                    assert actual_field.label == descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
                else:
                    assert actual_field.label == descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
                assert actual_field.proto3_optional is (expected_field["label"] == "optional")
                if "oneof" in expected_field:
                    assert actual_message.oneof_decl[actual_field.oneof_index].name == expected_field["oneof"]
        for actual_service in actual.service:
            expected = services[(actual.package, actual_service.name)]
            assert len(actual_service.method) == len(expected["methods"])
            for actual_method, expected_method in zip(actual_service.method, expected["methods"], strict=True):
                assert actual_method.name == expected_method["name"]
                assert actual_method.input_type == expected_method["input"]
                assert actual_method.output_type == expected_method["output"]
                assert actual_method.server_streaming is expected_method.get("serverStreaming", False)
                assert actual_method.client_streaming is False


def test_ack_projection_additive_nack_fields_preserve_frozen_wire(tmp_path: Path) -> None:
    descriptor = _descriptor(tmp_path)
    runtime = next(
        file for file in descriptor.file
        if file.name == "kokoro/agent/v1/agent_runtime.proto"
    )
    messages = {message.name: message for message in runtime.message_type}
    request = messages["AckProjectionRequest"]
    response = messages["AckProjectionResponse"]
    assert [(field.number, field.name, field.type, field.proto3_optional) for field in request.field] == [
        (1, "request_id", descriptor_pb2.FieldDescriptorProto.TYPE_STRING, False),
        (2, "agent_run_id", descriptor_pb2.FieldDescriptorProto.TYPE_STRING, False),
        (3, "consumer_key", descriptor_pb2.FieldDescriptorProto.TYPE_STRING, False),
        (4, "epoch", descriptor_pb2.FieldDescriptorProto.TYPE_UINT64, False),
        (5, "projected_seq", descriptor_pb2.FieldDescriptorProto.TYPE_UINT64, False),
        (6, "rejected_seq", descriptor_pb2.FieldDescriptorProto.TYPE_UINT64, True),
        (7, "rejection_code", descriptor_pb2.FieldDescriptorProto.TYPE_STRING, True),
    ]
    assert [(field.number, field.name, field.type, field.proto3_optional) for field in response.field] == [
        (1, "stored_epoch", descriptor_pb2.FieldDescriptorProto.TYPE_UINT64, False),
        (2, "stored_projected_seq", descriptor_pb2.FieldDescriptorProto.TYPE_UINT64, False),
        (3, "stored_rejected_seq", descriptor_pb2.FieldDescriptorProto.TYPE_UINT64, True),
        (4, "stored_rejection_code", descriptor_pb2.FieldDescriptorProto.TYPE_STRING, True),
    ]
    service = next(service for service in runtime.service if service.name == "AgentRuntimeService")
    method = next(method for method in service.method if method.name == "AckProjection")
    assert method.input_type == ".kokoro.agent.v1.AckProjectionRequest"
    assert method.output_type == ".kokoro.agent.v1.AckProjectionResponse"

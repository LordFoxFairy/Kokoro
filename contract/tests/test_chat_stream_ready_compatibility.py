from __future__ import annotations

import subprocess
from pathlib import Path

from google.protobuf import descriptor_pb2, descriptor_pool, message_factory


ROOT = Path(__file__).parents[2]


def _descriptor(tmp_path: Path) -> descriptor_pb2.FileDescriptorSet:
    output = tmp_path / "slice-a.binpb"
    subprocess.run(
        ["pnpm", "exec", "buf", "build", "contract", "-o", str(output)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return descriptor_pb2.FileDescriptorSet.FromString(output.read_bytes())


def _classes(tmp_path: Path) -> tuple[type, type, type, type]:
    descriptor = _descriptor(tmp_path)
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

    legacy_file = descriptor_pb2.FileDescriptorProto(
        name="legacy_chat_stream.proto",
        package="legacy.chat.v1",
        syntax="proto3",
        dependency=["kokoro/chat/v1/chat.proto"],
    )
    legacy_response = legacy_file.message_type.add(name="StreamConversationEventsResponse")
    legacy_response.field.add(
        number=1,
        name="event",
        type=descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        type_name=".kokoro.chat.v1.BrowserSessionEvent",
        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    pool.Add(legacy_file)
    return tuple(
        message_factory.GetMessageClass(pool.FindMessageTypeByName(name))
        for name in (
            "kokoro.chat.v1.BrowserSessionEvent",
            "kokoro.chat.v1.StreamConversationEventsReady",
            "kokoro.chat.v1.StreamConversationEventsResponse",
            "legacy.chat.v1.StreamConversationEventsResponse",
        )
    )


def test_event_field_one_bytes_are_unchanged_for_old_and_new_readers(tmp_path: Path) -> None:
    event_class, _ready_class, response_class, legacy_class = _classes(tmp_path)
    event = event_class(
        event_id="event-1",
        seq=7,
        session_id="conversation-1",
        run_id="launch-1",
        kind="message.delta",
        payload_json=b'{"delta":"ok"}',
    )
    legacy = legacy_class(event=event)
    modern = response_class(event=event)
    legacy_bytes = legacy.SerializeToString(deterministic=True)
    assert modern.SerializeToString(deterministic=True) == legacy_bytes
    assert modern.WhichOneof("payload") == "event"
    reparsed_modern = response_class.FromString(legacy_bytes)
    assert reparsed_modern.WhichOneof("payload") == "event"
    assert reparsed_modern.event == event


def test_additive_ready_is_ignored_fail_closed_by_old_reader(tmp_path: Path) -> None:
    _event_class, ready_class, response_class, legacy_class = _classes(tmp_path)
    modern = response_class(ready=ready_class(accepted_after_seq=7, watermark=9))
    assert modern.WhichOneof("payload") == "ready"
    legacy = legacy_class.FromString(modern.SerializeToString(deterministic=True))
    assert not legacy.HasField("event")
    legacy.DiscardUnknownFields()
    assert legacy.SerializeToString(deterministic=True) == b""


def test_v1_baseline_keeps_stream_event_wire_shape() -> None:
    baseline = descriptor_pb2.FileDescriptorSet.FromString(
        (ROOT / "contract/breaking/slice-a-v1.binpb").read_bytes()
    )
    chat = next(file for file in baseline.file if file.name == "kokoro/chat/v1/chat.proto")
    response = next(
        message for message in chat.message_type if message.name == "StreamConversationEventsResponse"
    )
    assert [oneof.name for oneof in response.oneof_decl] == ["payload"]
    assert [(field.number, field.name, field.type_name, field.oneof_index) for field in response.field] == [
        (1, "event", ".kokoro.chat.v1.BrowserSessionEvent", 0),
        (2, "ready", ".kokoro.chat.v1.StreamConversationEventsReady", 0),
    ]

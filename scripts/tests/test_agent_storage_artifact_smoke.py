"""Infrastructure-free admission checks for the Agent → Storage vertical smoke."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "e2e/run_agent_storage_artifact_smoke.py"
spec = importlib.util.spec_from_file_location("agent_storage_smoke", SCRIPT)
assert spec and spec.loader
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def fixture_env() -> dict[str, str]:
    return {
        "KOKORO_W2_POSTGRES_ADMIN_URL": "postgresql://test:secret@127.0.0.1:5432/postgres",
        "KOKORO_W2_REDIS_URL": "redis://127.0.0.1:6379/6",
        "KOKORO_W2_TEST_BUCKET": "w2-agent-exclusive",
        "KOKORO_W2_EXCLUSIVE_BUCKET": "w2-agent-exclusive",
        "KOKORO_W2_STORAGE_NODE_BIN": "/opt/node24/bin/node",
        "KOKORO_OBJECT_STORE_ENDPOINT": "http://127.0.0.1:39190",
        "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": "http://127.0.0.1:39190",
        "KOKORO_OBJECT_STORE_REGION": "us-east-1",
        "KOKORO_OBJECT_STORE_PROFILE": "custom",
        "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "true",
        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": "fixture-access",
        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY": "fixture-secret",
        "KOKORO_SCANNER_HOST": "127.0.0.1",
        "KOKORO_SCANNER_PORT": "43310",
    }


def test_valid_shape_does_not_contact_provider() -> None:
    config = smoke.check_configuration(fixture_env())
    assert config["bucket"] == "w2-agent-exclusive"
    assert config["admin_url"].startswith("postgresql://")


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({"KOKORO_W2_EXCLUSIVE_BUCKET": "other"}, "exclusive bucket"),
        ({"KOKORO_W2_TEST_BUCKET": ""}, "TEST_BUCKET"),
        (
            {"KOKORO_W2_POSTGRES_ADMIN_URL": "postgresql://u:p@remote:5432/postgres"},
            "local PostgreSQL",
        ),
        (
            {
                "KOKORO_W2_POSTGRES_ADMIN_URL": "postgresql://u:p@127.0.0.1/db?options=-csearch_path%3Dpublic"
            },
            "search-path",
        ),
        (
            {"KOKORO_W2_POSTGRES_ADMIN_URL": "postgresql://127.0.0.1/postgres"},
            "local PostgreSQL",
        ),
        (
            {"KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": "http://u:p@127.0.0.1:39190"},
            "object store origin",
        ),
        ({"KOKORO_OBJECT_STORE_PROFILE": "aws"}, "custom S3"),
        ({"KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "false"}, "path-style"),
        ({"KOKORO_SCANNER_PORT": "3310"}, "3310"),
        ({"KOKORO_W2_STORAGE_NODE_BIN": "node"}, "absolute"),
        ({"AWS_SESSION_TOKEN": "temp"}, "session token"),
    ],
)
def test_unsafe_configuration_rejected(change: dict[str, str], fragment: str) -> None:
    env = fixture_env()
    env.update(change)
    with pytest.raises(smoke.SmokeError, match=fragment):
        smoke.check_configuration(env)


def test_database_url_removes_admin_database_and_sets_owner_schema() -> None:
    url = smoke.database_url(
        fixture_env()["KOKORO_W2_POSTGRES_ADMIN_URL"], "w2_agent_0123", "kokoro_agent"
    )
    assert url.endswith("/w2_agent_0123?options=-csearch_path%3Dkokoro_agent")


def test_cleanup_refuses_unrecognized_or_unversioned_object() -> None:
    for items in (
        [{"Key": "other/final/a", "VersionId": "v1", "ETag": '"a"'}],
        [{"Key": "w2-agent/final/a", "VersionId": "null", "ETag": '"a"'}],
        [{"Key": "w2-agent/mystery/a", "VersionId": "v1", "ETag": '"a"'}],
    ):
        with pytest.raises(smoke.SmokeError):
            smoke.validate_owned_versions(items, "w2-agent/")


def test_cleanup_accepts_only_exact_versioned_upload_or_final_keys() -> None:
    items = [{"Key": "w2-agent/final/a", "VersionId": "v1", "ETag": '"a"'}]
    assert smoke.validate_owned_versions(items, "w2-agent/") == items


def test_preflight_refuses_existing_prefix_without_deleting_anything() -> None:
    class Existing:
        writes = 0

        def head_bucket(self, **_kwargs: object) -> None:
            pass

        def get_bucket_versioning(self, **_kwargs: object) -> dict[str, str]:
            return {"Status": "Enabled"}

        def get_object_lock_configuration(self, **_kwargs: object) -> dict[str, object]:
            return {"ObjectLockConfiguration": {"ObjectLockEnabled": "Enabled"}}

        def list_object_versions(self, **_kwargs: object) -> dict[str, object]:
            return {
                "Versions": [
                    {"Key": "w2-agent/final/a", "VersionId": "v1", "ETag": '"a"'}
                ]
            }

        def delete_object(self, **_kwargs: object) -> None:
            self.writes += 1

    provider = Existing()
    with pytest.raises(smoke.SmokeError, match="not empty"):
        smoke.preflight_bucket(provider, "exclusive-test", "w2-agent/")
    assert provider.writes == 0


def test_cleanup_deletes_only_exact_version_and_verifies_absence() -> None:
    class NotFound(Exception):
        response = {"ResponseMetadata": {"HTTPStatusCode": 404}}

    class Versioned:
        def __init__(self) -> None:
            self.deleted: list[dict[str, str]] = []

        def list_object_versions(self, **_kwargs: object) -> dict[str, object]:
            if self.deleted:
                return {"Versions": []}
            return {
                "Versions": [
                    {"Key": "w2-agent/final/a", "VersionId": "v1", "ETag": '"a"'}
                ]
            }

        def delete_object(self, **kwargs: str) -> None:
            self.deleted.append(kwargs)

        def head_object(self, **_kwargs: str) -> None:
            raise NotFound()

    provider = Versioned()
    smoke.cleanup_objects(provider, "exclusive-test", "w2-agent/")
    assert provider.deleted == [
        {
            "Bucket": "exclusive-test",
            "Key": "w2-agent/final/a",
            "VersionId": "v1",
            "IfMatch": '"a"',
        }
    ]


def test_stop_owned_targets_only_own_process_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, int]] = []

    class Owned:
        pid = 42123

        def __init__(self) -> None:
            self.stopped = False

        def poll(self) -> int | None:
            return 0 if self.stopped else None

        def wait(self, *, timeout: int) -> int:
            assert timeout == 15
            self.stopped = True
            return 0

    monkeypatch.setattr(smoke.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    smoke._stop_owned(Owned())
    assert calls == [(42123, smoke.signal.SIGTERM)]


def test_success_journal_has_production_deliver_result_shape() -> None:
    receipt = SimpleNamespace(
        artifact_id="artifact-1",
        asset_id="asset-1",
        artifact_kind="document",
        mime_type="text/plain",
        size_bytes=5,
        content_sha256="a" * 64,
    )
    assert smoke.deliver_result(receipt, "/report.txt", "Report", "note") == {
        "status": "delivered",
        "artifact_id": "artifact-1",
        "asset_id": "asset-1",
        "artifact_kind": "document",
        "path": "/report.txt",
        "title": "Report",
        "mime": "text/plain",
        "size": 5,
        "content_hash": "a" * 64,
        "note": "note",
    }


def test_event_chain_rejects_missing_delivery_or_wrong_terminal_order() -> None:
    outbox = [
        {
            "kind": "run.started",
            "durable_seq": 1,
            "index": 0,
            "event_id": "start",
            "payload_json": "{}",
        },
        {
            "kind": "run.completed",
            "durable_seq": 2,
            "index": 1,
            "event_id": "end",
            "payload_json": '{"status":"completed"}',
        },
    ]
    chat = [
        {"event_type": "run.started", "source_index": 0, "payload_json": "{}"},
        {
            "event_type": "run.completed",
            "source_index": 1,
            "payload_json": '{"status":"completed"}',
        },
    ]
    wire = [
        {
            "kind": "run.started",
            "durable_seq": 1,
            "index": 0,
            "event_id": "start",
            "payload": {},
        },
        {
            "kind": "run.completed",
            "durable_seq": 2,
            "index": 1,
            "event_id": "end",
            "payload": {"status": "completed"},
        },
    ]
    with pytest.raises(smoke.SmokeError, match="delivery"):
        smoke.verify_event_chain(outbox, chat, wire, "artifact-1", "tool-1", "document")


def test_chat_event_selection_keeps_only_current_run_in_same_session() -> None:
    prior = [
        {"run_id": "run_first", "source_index": index, "event_type": kind}
        for index, kind in enumerate(
            ("run.started", "delivery", "interaction.state", "run.completed")
        )
    ]
    current = [
        {"run_id": "run_second", "source_index": index, "event_type": kind}
        for index, kind in enumerate(
            ("run.started", "delivery", "interaction.state", "run.completed")
        )
    ]
    assert smoke.select_run_chat_events([*prior, *current], "run_second") == current


def test_chat_event_selection_rejects_cross_run_delivery_mix() -> None:
    mixed = [
        {"run_id": "run_second", "source_index": 0, "event_type": "run.started"},
        {"run_id": "run_first", "source_index": 1, "event_type": "delivery"},
        {"run_id": "run_second", "source_index": 2, "event_type": "interaction.state"},
        {"run_id": "run_second", "source_index": 3, "event_type": "run.completed"},
    ]
    with pytest.raises(smoke.SmokeError, match="run event cardinality"):
        smoke.select_run_chat_events(mixed, "run_second")


def test_event_chain_accepts_one_ordered_durable_delivery() -> None:
    outbox = [
        {
            "kind": "run.started",
            "durable_seq": 1,
            "index": 0,
            "event_id": "start",
            "payload_json": "{}",
        },
        {
            "kind": "delivery.created",
            "durable_seq": 2,
            "index": 1,
            "event_id": "delivery",
            "payload_json": '{"artifact_id":"artifact-1","tool_call_id":"tool-1","artifact_kind":"document"}',
        },
        {
            "kind": "run.completed",
            "durable_seq": 3,
            "index": 3,
            "event_id": "end",
            "payload_json": '{"status":"completed"}',
        },
    ]
    chat = [
        {"event_type": "run.started", "source_index": 0, "payload_json": "{}"},
        {
            "event_type": "delivery",
            "source_index": 1,
            "payload_json": '{"artifact_id":"artifact-1","tool_call_id":"tool-1","artifact_kind":"document"}',
        },
        {
            "event_type": "interaction.state",
            "source_index": 2,
            "payload_json": '{"interaction_revision":1,"pause_revision":0,"pause_ref":null,"phase":"terminal","groups":[],"action_result":null}',
        },
        {
            "event_type": "run.completed",
            "source_index": 3,
            "payload_json": '{"status":"completed"}',
        },
    ]
    wire = [
        {
            "kind": "run.started",
            "durable_seq": 1,
            "index": 0,
            "event_id": "start",
            "payload": {},
        },
        {
            "kind": "delivery.created",
            "durable_seq": 2,
            "index": 1,
            "event_id": "delivery",
            "payload": {
                "artifact_id": "artifact-1",
                "tool_call_id": "tool-1",
                "artifact_kind": "document",
            },
        },
        {
            "kind": "run.completed",
            "durable_seq": 3,
            "index": 3,
            "event_id": "end",
            "payload": {"status": "completed"},
        },
    ]
    smoke.verify_event_chain(outbox, chat, wire, "artifact-1", "tool-1", "document")
    previous_run = [{**record, "run_id": "run_previous"} for record in chat]
    current_run = [{**record, "run_id": "run_current"} for record in chat]
    selected = smoke.select_run_chat_events(
        [*previous_run, *current_run], "run_current"
    )
    smoke.verify_event_chain(outbox, selected, wire, "artifact-1", "tool-1", "document")
    missing_kind = [dict(item) for item in outbox]
    missing_kind[1]["payload_json"] = (
        '{"artifact_id":"artifact-1","tool_call_id":"tool-1"}'
    )
    with pytest.raises(smoke.SmokeError, match="payload drift"):
        smoke.verify_event_chain(
            missing_kind, chat, wire, "artifact-1", "tool-1", "document"
        )
    with pytest.raises(smoke.SmokeError, match="duplicate"):
        smoke.verify_event_chain(
            outbox, chat, wire + [wire[1]], "artifact-1", "tool-1", "document"
        )

    with pytest.raises(smoke.SmokeError, match="Chat projection"):
        smoke.verify_event_chain(
            outbox,
            [chat[0], chat[1], chat[3]],
            wire,
            "artifact-1",
            "tool-1",
            "document",
        )
    wrong_state = [dict(item) for item in chat]
    wrong_state[2]["payload_json"] = wrong_state[2]["payload_json"].replace(
        '"terminal"', '"active"'
    )
    with pytest.raises(smoke.SmokeError, match="interaction"):
        smoke.verify_event_chain(
            outbox, wrong_state, wire, "artifact-1", "tool-1", "document"
        )
    drifted = [dict(item) for item in wire]
    drifted[-1]["index"] = 2
    with pytest.raises(smoke.SmokeError, match="index"):
        smoke.verify_event_chain(
            outbox, chat, drifted, "artifact-1", "tool-1", "document"
        )


def test_final_artifact_read_uses_the_current_storage_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    calls = []

    class Client:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def post(self, url, **kwargs):
            calls.append((url, kwargs))
            return SimpleNamespace(
                status_code=200, json=lambda: {"downloadReference": {}}
            )

    monkeypatch.setitem(sys.modules, "httpx", SimpleNamespace(Client=Client))
    assert (
        smoke._storage_read(
            "http://storage.fixture", "fixture", "tenant", "user", "session", "artifact"
        )[0]
        == 200
    )
    assert (
        calls[0][0]
        == "http://storage.fixture/kokoro.storage.v3.StorageService/GetFinalArtifactDownloadReference"
    )
    assert calls[0][1]["json"]["artifactId"] == "artifact"


def test_counting_transport_preserves_the_exact_uploaded_source_version() -> None:
    import asyncio

    class Transport:
        async def put(self, reference, content):
            assert reference == "original-reference" and content == b"original-bytes"
            return "opaque-source-version"

        async def call(self, method, request, headers):
            return (method, request, headers)

    async def exercise():
        counted = smoke._CountingStorageTransport(Transport())
        assert (
            await counted.put("original-reference", b"original-bytes")
            == "opaque-source-version"
        )
        assert await counted.call(
            "complete_upload", "original-command", {"scope": "owned"}
        ) == (
            "complete_upload",
            "original-command",
            {"scope": "owned"},
        )
        assert counted.operations == ["signed_put", "complete_upload"]

    asyncio.run(exercise())


@pytest.mark.parametrize("queue_count", [0, 1, 2])
def test_projection_observer_requires_one_independent_queued_fact(
    queue_count: int,
) -> None:
    import asyncio

    frozen = {
        "run_id": "owned-run",
        "durable_seq": 2,
        "event_id": "original-id",
        "payload_json": '{"artifact_id":"persisted-not-wire"}',
    }
    frame = SimpleNamespace(**frozen, model_dump=lambda: dict(frozen))
    event = {
        "run_id": "owned-run",
        "durable_seq": 2,
        "event_id": "original-id",
        "payload": {"artifact_id": "wire-only"},
    }
    published = []

    class Repository:
        async def list_unpublished_outbox(self):
            return [frame] * queue_count

    class Bus:
        async def read_all(self, stream):
            return [stream]

        async def publish(self, stream, value, *, maxlen):
            published.append((stream, value, maxlen))
            return "original-cursor"

    async def exercise():
        observer = smoke._ProjectionStream(Bus(), Repository(), "owned-run")
        assert await observer.read_all("original-stream") == ["original-stream"]
        if queue_count == 1:
            assert (
                await observer.publish("original-stream", event, maxlen=3)
                == "original-cursor"
            )
            assert observer.frames == [frozen]
            assert published == [("original-stream", event, 3)]
        else:
            with pytest.raises(smoke.SmokeError, match="queued"):
                await observer.publish("original-stream", event, maxlen=3)
            assert published == []
            assert observer.frames == []

    asyncio.run(exercise())

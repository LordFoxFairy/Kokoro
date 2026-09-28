"""Provider-free boundaries for the three-owner artifact composition runner."""

from __future__ import annotations

import pytest

from scripts.e2e import run_agent_bff_storage_artifact_smoke as smoke


def fixture_env() -> dict[str, str]:
    return {
        "KOKORO_W2_POSTGRES_ADMIN_URL": "postgresql://tester:secret@127.0.0.1:5432/postgres",
        "KOKORO_W2_REDIS_URL": "redis://127.0.0.1:6379/6",
        "KOKORO_W2_BFF_NODE_BIN": "/opt/node22/bin/node",
        "KOKORO_W2_STORAGE_NODE_BIN": "/opt/node24/bin/node",
        "KOKORO_W2_TEST_BUCKET": "exclusive-artifact-smoke",
        "KOKORO_W2_EXCLUSIVE_BUCKET": "exclusive-artifact-smoke",
        "KOKORO_OBJECT_STORE_ENDPOINT": "http://127.0.0.1:39190",
        "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": "http://127.0.0.1:39190",
        "KOKORO_OBJECT_STORE_REGION": "us-east-1",
        "KOKORO_OBJECT_STORE_PROFILE": "custom",
        "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "true",
        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": "test-access",
        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY": "test-secret",
        "KOKORO_SCANNER_HOST": "127.0.0.1",
        "KOKORO_SCANNER_PORT": "43310",
    }


def test_check_config_is_shape_only_and_selects_three_owned_redis_dbs() -> None:
    config = smoke.check_configuration(fixture_env())
    assert config["bucket"] == "exclusive-artifact-smoke"
    assert tuple(smoke.redis_url(config["redis_url"], db) for db in (6, 7, 8)) == (
        "redis://127.0.0.1:6379/6",
        "redis://127.0.0.1:6379/7",
        "redis://127.0.0.1:6379/8",
    )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"KOKORO_W2_EXCLUSIVE_BUCKET": "other"}, "exclusive bucket"),
        (
            {"KOKORO_W2_POSTGRES_ADMIN_URL": "postgresql://u:p@remote/db"},
            "local PostgreSQL",
        ),
        ({"KOKORO_W2_REDIS_URL": "redis://127.0.0.1:6379/0"}, "DB 6"),
        ({"KOKORO_OBJECT_STORE_ENDPOINT": "http://127.0.0.1:3310"}, "3310"),
        ({"KOKORO_SCANNER_PORT": "3310"}, "3310"),
        ({"KOKORO_W2_BFF_NODE_BIN": "node"}, "absolute"),
        ({"AWS_SESSION_TOKEN": "temporary"}, "session token"),
    ],
)
def test_unsafe_config_rejected(change: dict[str, str], message: str) -> None:
    env = fixture_env()
    env.update(change)
    with pytest.raises(smoke.SmokeError, match=message):
        smoke.check_configuration(env)


def test_db_urls_are_distinct_schema_boundaries_in_one_database() -> None:
    config = smoke.check_configuration(fixture_env())
    urls = smoke.owner_database_urls(config["admin_url"], "artifact_012345")
    assert set(urls) == {"bff", "agent", "storage"}
    assert all("/artifact_012345?" in url for url in urls.values())
    assert len(set(urls.values())) == 3


def test_cleanup_rejects_foreign_or_unversioned_object() -> None:
    for value in (
        {"Key": "another/final/a", "VersionId": "v1", "ETag": '"x"'},
        {"Key": "owned/final/a", "VersionId": "null", "ETag": '"x"'},
        {"Key": "owned/other/a", "VersionId": "v1", "ETag": '"x"'},
    ):
        with pytest.raises(smoke.SmokeError):
            smoke.validate_owned_versions([value], "owned/")


def test_public_artifact_requires_stable_ids_and_exact_bytes() -> None:
    artifact = {
        "artifact_id": "artifact-1",
        "conversation_id": "conversation-1",
        "content_sha256": smoke.sha256(b"original"),
        "size_bytes": 8,
    }
    smoke.verify_artifact_bytes(artifact, b"original", "artifact-1", "conversation-1")
    with pytest.raises(smoke.SmokeError):
        smoke.verify_artifact_bytes(
            artifact, b"tampered", "artifact-1", "conversation-1"
        )
    with pytest.raises(smoke.SmokeError):
        smoke.verify_artifact_bytes(artifact, b"original", "other", "conversation-1")


def test_check_config_cli_does_not_touch_provider(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        smoke, "run_smoke", lambda *_args: pytest.fail("provider contacted")
    )
    assert smoke.main(["--check-config"], fixture_env()) == 0
    assert "shape valid" in capsys.readouterr().out

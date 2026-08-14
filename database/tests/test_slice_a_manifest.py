from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
MANIFEST_PATH = ROOT / "database/slices/slice-a.json"

EXPECTED_SEGMENTS = [
    "00-foundation",
    "10-site",
    "20-iam",
    "30-chat",
    "40-agent",
    "45-langgraph-checkpointer",
    "50-capability",
    "60-model",
    "99-cross-capability-relations",
]
EXPECTED_TABLES = {
    "site": ["site_site", "site_domain"],
    "iam": [
        "iam_principal",
        "iam_user",
        "iam_identity",
        "iam_contact",
        "iam_magic_link",
        "iam_auth_session",
        "iam_command_receipt",
        "iam_organization",
        "iam_membership",
        "iam_role",
        "iam_permission",
        "iam_role_permission",
        "iam_membership_role",
        "iam_security_event",
    ],
    "chat": [
        "chat_conversation",
        "chat_message",
        "chat_message_part",
        "chat_command_receipt",
        "chat_run_launch",
        "chat_active_run",
        "chat_run_view",
        "chat_interaction",
        "chat_control_command",
        "chat_control_outbox",
        "chat_launch_outbox",
        "chat_projection_inbox",
        "chat_projection_dlq",
        "chat_stream_event",
    ],
    "agent": [
        "agent_run",
        "agent_execution_manifest",
        "agent_run_lease",
        "agent_control_inbox",
        "agent_event_outbox",
        "agent_dispatch_outbox",
        "agent_projection_ack",
        "agent_tool_effect",
        "agent_run_usage",
        "agent_run_usage_line",
        "agent_sandbox_binding",
        "agent_memory",
        "agent_dispatch_dlq",
    ],
    "capability": [
        "capability_runtime_snapshot",
        "capability_command_receipt",
    ],
    "model": [
        "model_provider",
        "model_definition",
        "model_revision",
        "model_routing_policy",
        "model_provider_health_state",
    ],
    "langgraph": [
        "checkpoints",
        "checkpoint_blobs",
        "checkpoint_writes",
        "checkpoint_migrations",
    ],
}


def test_slice_a_manifest_is_exact() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest == {
        "version": 1,
        "slice": "slice-a",
        "schema": "kokoro",
        "segments": EXPECTED_SEGMENTS,
        "ownerTableCount": 50,
        "checkpointerTableCount": 4,
        "tables": EXPECTED_TABLES,
    }
    owner_count = sum(
        len(names) for owner, names in EXPECTED_TABLES.items() if owner != "langgraph"
    )
    assert owner_count == 50
    assert len(EXPECTED_TABLES["langgraph"]) == 4
    encoded = json.dumps(manifest)
    assert "chat_share" not in encoded
    assert "capability_runtime_snapshot_item" not in encoded


def _write_complete_fixture(root: Path) -> dict[str, bytes]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    slices = root / "database/slices"
    schema = root / "database/schema"
    slices.mkdir(parents=True)
    schema.mkdir(parents=True)
    (slices / "slice-a.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    sources: dict[str, bytes] = {}
    for index, segment in enumerate(EXPECTED_SEGMENTS):
        data = f"-- segment {index}\r\nSELECT {index};\r\n".encode()
        (schema / f"{segment}.sql").write_bytes(data)
        sources[segment] = data.replace(b"\r\n", b"\n")
    return sources


def _commit_fixture(root: Path) -> None:
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "fixture@example.com"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "--message", "fixture"], cwd=root, check=True
    )


def test_composition_is_deterministic_and_normalizes_source_bytes(
    tmp_path: Path,
) -> None:
    from scripts.database.compose_baseline import compose_baseline

    sources = _write_complete_fixture(tmp_path)
    first = compose_baseline(tmp_path)
    second = compose_baseline(tmp_path)

    assert first == second
    assert b"\r" not in first
    cursor = 0
    for index, segment in enumerate(EXPECTED_SEGMENTS):
        source = sources[segment]
        digest = hashlib.sha256(source).hexdigest().encode()
        header = (
            b"-- source: database/schema/"
            + segment.encode()
            + b".sql\n-- sha256: "
            + digest
            + b"\n"
        )
        expected = header + source
        assert first[cursor : cursor + len(expected)] == expected
        cursor += len(expected)
        if index < len(EXPECTED_SEGMENTS) - 1:
            cursor += 1
    assert cursor == len(first)


@pytest.mark.parametrize("bad_kind", ["missing", "extra", "symlink"])
def test_composition_rejects_non_manifest_segment_sets(
    tmp_path: Path, bad_kind: str
) -> None:
    from scripts.database.compose_baseline import ManifestError, compose_baseline

    _write_complete_fixture(tmp_path)
    schema = tmp_path / "database/schema"
    if bad_kind == "missing":
        (schema / "10-site.sql").unlink()
    elif bad_kind == "extra":
        (schema / "70-storage.sql").write_text("SELECT 1;\n", encoding="utf-8")
    else:
        source = schema / "00-foundation.sql"
        source.unlink()
        source.symlink_to(schema / "10-site.sql")

    with pytest.raises(ManifestError, match=bad_kind):
        compose_baseline(tmp_path)


def test_root_manifest_composes_the_complete_slice_a_segment_set() -> None:
    from scripts.database.compose_baseline import compose_baseline

    baseline = compose_baseline(ROOT)
    for segment in EXPECTED_SEGMENTS:
        assert f"-- source: database/schema/{segment}.sql\n".encode() in baseline
    assert baseline.count(b"-- source: database/schema/") == len(EXPECTED_SEGMENTS)
    assert baseline.endswith(b"\n")
    assert not baseline.endswith(b"\n\n")


@pytest.mark.parametrize("dirty_kind", ["tracked", "untracked"])
def test_require_clean_rejects_any_root_worktree_dirt(
    tmp_path: Path, dirty_kind: str
) -> None:
    from scripts.database.compose_baseline import ManifestError, _require_clean_sources

    _write_complete_fixture(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("clean\n", encoding="utf-8")
    _commit_fixture(tmp_path)
    if dirty_kind == "tracked":
        readme.write_text("dirty\n", encoding="utf-8")
    else:
        (tmp_path / "UNTRACKED.md").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(ManifestError, match="dirty Root worktree"):
        _require_clean_sources(tmp_path, "slice-a")


def test_require_clean_allows_only_committed_database_ignore_policy(
    tmp_path: Path,
) -> None:
    from scripts.database.compose_baseline import _require_clean_sources

    _write_complete_fixture(tmp_path)
    (tmp_path / "database/.gitignore").write_bytes(
        (ROOT / "database/.gitignore").read_bytes()
    )
    _commit_fixture(tmp_path)
    for relative in (
        "database/.venv/state",
        "database/node_modules/tool/index.js",
        "database/.pytest_cache/state",
        "database/tests/__pycache__/test.pyc",
        "database/baseline/kokoro.sql",
        "database/baseline/manifest.json",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ignored\n", encoding="utf-8")

    _require_clean_sources(tmp_path, "slice-a")

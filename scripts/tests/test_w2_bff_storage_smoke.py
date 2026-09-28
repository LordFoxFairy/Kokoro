"""Static, no-infrastructure admission tests for the W2 owner smoke."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/e2e/run_w2_bff_storage_smoke.mjs"


def fixture_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        KOKORO_W2_POSTGRES_ADMIN_URL="postgresql://test:secret@127.0.0.1:5432/postgres",
        KOKORO_W2_REDIS_URL="redis://127.0.0.1:6379/6",
        KOKORO_W2_BFF_NODE_BIN="/tmp/node22/bin/node",
        KOKORO_W2_TEST_BUCKET="w2-exclusive-test",
        KOKORO_W2_EXCLUSIVE_BUCKET="w2-exclusive-test",
        KOKORO_OBJECT_STORE_ENDPOINT="http://127.0.0.1:39190",
        KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT="http://127.0.0.1:39190",
        KOKORO_OBJECT_STORE_REGION="us-east-1",
        KOKORO_OBJECT_STORE_PROFILE="custom",
        KOKORO_OBJECT_STORE_FORCE_PATH_STYLE="true",
        KOKORO_OBJECT_STORE_ACCESS_KEY_ID="fixture-access",
        KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY="fixture-secret",
        KOKORO_SCANNER_HOST="127.0.0.1",
        KOKORO_SCANNER_PORT="43310",
    )
    env.pop("AWS_SESSION_TOKEN", None)
    env.pop("KOKORO_OBJECT_STORE_SESSION_TOKEN", None)
    return env


def check(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is not available for static W2 fixture validation")
    return subprocess.run(
        [node, str(SCRIPT), "--check-config"],
        env=env,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


def test_shape_validates_without_contacting_dependencies() -> None:
    result = check(fixture_env())
    assert result.returncode == 0, result.stderr
    assert "provider not contacted" in result.stdout


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"KOKORO_W2_EXCLUSIVE_BUCKET": "another-bucket"}, "exclusive bucket"),
        ({"KOKORO_OBJECT_STORE_PROFILE": "minio"}, "custom S3 profile"),
        ({"KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": "http://u:p@127.0.0.1:39190"}, "HTTP(S) origin"),
        ({"KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "false"}, "path-style"),
        ({"AWS_SESSION_TOKEN": "temporary"}, "session token"),
    ],
)
def test_rejects_unsafe_or_ambiguous_configuration(change: dict[str, str], message: str) -> None:
    env = fixture_env()
    env.update(change)
    result = check(env)
    assert result.returncode != 0
    assert message in result.stderr


def test_missing_bucket_cannot_touch_provider() -> None:
    env = fixture_env()
    del env["KOKORO_W2_TEST_BUCKET"]
    result = check(env)
    assert result.returncode != 0
    assert "KOKORO_W2_TEST_BUCKET is required" in result.stderr


def test_exact_object_cleanup_and_database_nonadoption() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is not available for isolated W2 resource validation")
    source = f"""
      import assert from 'node:assert/strict';
      import {{ cleanupObjects, createDatabase }} from '{SCRIPT.as_uri()}';
      const prefix = 'w2-run/';
      let listed = 0;
      const calls = [];
      const s3 = {{ async send(command) {{
        const type = command.constructor.name;
        calls.push([type, command.input]);
        if (type === 'ListObjectVersionsCommand') return listed++ === 0
          ? {{ Versions: [{{ Key: prefix + 'final/a', VersionId: 'v1', ETag: '"etag"' }}], DeleteMarkers: [], IsTruncated: false }}
          : {{ Versions: [], DeleteMarkers: [], IsTruncated: false }};
        if (type === 'HeadObjectCommand') throw Object.assign(new Error('absent'), {{ $metadata: {{ httpStatusCode: 404 }} }});
        return {{}};
      }} }};
      await cleanupObjects(s3, 'exclusive-test', prefix);
      const deleted = calls.find(([kind]) => kind === 'DeleteObjectCommand')[1];
      assert.deepEqual({{ Key: deleted.Key, VersionId: deleted.VersionId, IfMatch: deleted.IfMatch }},
        {{ Key: prefix + 'final/a', VersionId: 'v1', IfMatch: '"etag"' }});
      let writes = 0;
      await assert.rejects(createDatabase({{ async query() {{ writes++; return {{ rowCount: 1 }} }} }}, 'w2_owned'), /refusing adoption/);
      assert.equal(writes, 1);
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr

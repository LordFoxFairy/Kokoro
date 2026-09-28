"""Admission and evidence guards for the live W2 Chromium composition."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.e2e import run_web_project_resource_chromium_smoke as smoke


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/e2e/run_web_project_resource_chromium_smoke.py"
DRIVER = ROOT / "scripts/e2e/web_project_resource_chromium.mjs"


def fixture_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        KOKORO_W2_POSTGRES_ADMIN_URL="postgresql://test:secret@127.0.0.1:5432/postgres",
        KOKORO_W2_REDIS_URL="redis://127.0.0.1:6379/6",
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
    return subprocess.run(
        [sys.executable, str(RUNNER), "--check-config"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


def test_valid_shape_checks_without_contacting_provider() -> None:
    result = check(fixture_env())
    assert result.returncode == 0, result.stderr
    assert "provider not contacted" in result.stdout


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"KOKORO_W2_EXCLUSIVE_BUCKET": "another-bucket"}, "exclusive bucket"),
        ({"KOKORO_OBJECT_STORE_PROFILE": "minio"}, "custom S3 profile"),
        ({"KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "false"}, "path-style"),
        (
            {
                "KOKORO_W2_POSTGRES_ADMIN_URL": "postgresql://test:secret@127.0.0.1:5432/postgres?schema=public"
            },
            "owner schema",
        ),
        ({"KOKORO_SCANNER_PORT": "3310"}, "scanner port 3310"),
        ({"AWS_SESSION_TOKEN": "temporary"}, "session token"),
        (
            {"KOKORO_W2_REDIS_URL": "redis://127.0.0.1:6379/6?protocol=3"},
            "Redis URL without options",
        ),
        (
            {"KOKORO_OBJECT_STORE_ENDPOINT": "https://remote.example.test"},
            "local object store",
        ),
        ({"KOKORO_SCANNER_HOST": "remote.example.test"}, "local scanner"),
        (
            {
                "KOKORO_W2_POSTGRES_ADMIN_URL": "postgresql://test:secret@remote.example.test:5432/postgres"
            },
            "local PostgreSQL",
        ),
        ({"KOKORO_W2_REDIS_URL": "redis://remote.example.test:6379/6"}, "local Redis"),
        ({"KOKORO_W2_REDIS_URL": "redis://127.0.0.1:6379/2"}, "Redis DB 6"),
    ],
)
def test_unsafe_or_ambiguous_config_fails_closed(
    change: dict[str, str], message: str
) -> None:
    env = fixture_env()
    env.update(change)
    result = check(env)
    assert result.returncode != 0
    assert message in result.stderr


def test_missing_exclusive_bucket_cannot_touch_provider() -> None:
    env = fixture_env()
    del env["KOKORO_W2_EXCLUSIVE_BUCKET"]
    result = check(env)
    assert result.returncode != 0
    assert "KOKORO_W2_EXCLUSIVE_BUCKET" in result.stderr


def test_browser_driver_rejects_missing_or_untrusted_input_before_launch() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable")
    result = subprocess.run(
        [node, str(DRIVER)],
        cwd=ROOT,
        input="{}",
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert result.returncode != 0
    assert "invalid Chromium milestone input" in result.stderr


def test_owner_source_sha_must_be_full_before_git_admission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        smoke.product.session,
        "verify_source",
        lambda *_: pytest.fail("git source gate called"),
    )
    with pytest.raises(smoke.SmokeError, match="full commit"):
        smoke._verify_source(smoke.WEB, "a" * 8, "apps/kokoro-app")


def test_s3_operation_rejects_unknown_action_before_provider() -> None:
    with pytest.raises(smoke.SmokeError, match="owned S3 operation invalid"):
        smoke._s3_operation(
            Path("/missing/node"), "delete-bucket", "test-bucket", "run/", {}
        )


def test_isolated_owner_copy_never_writes_live_checkout(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "scratch"
    source.mkdir()
    destination.mkdir()
    (source / "node_modules").mkdir()
    (source / "node_modules" / "dependency").write_text("dependency")
    (source / "src").mkdir()
    (source / "src" / "main.ts").write_text("original")
    isolated = smoke._isolated_owner(source, destination, "owner")
    (isolated / "src" / "main.ts").write_text("changed")
    assert (source / "src" / "main.ts").read_text() == "original"
    assert (isolated / "node_modules").is_symlink()
    assert (isolated / "node_modules").resolve() == source / "node_modules"

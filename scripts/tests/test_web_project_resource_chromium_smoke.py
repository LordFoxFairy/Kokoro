"""Admission and evidence guards for the live W2 Chromium composition."""

from __future__ import annotations

import os
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

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
    assert result.stderr == "FAILURE_PHASE:parse-input\n"


def test_browser_driver_accepts_two_distinct_artifact_fixtures_before_launch(
    tmp_path: Path,
) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable")
    public_certificate, _private_key = smoke.product.certificate(
        tmp_path, "web.example.test"
    )
    artifacts = []
    for index in (1, 2):
        content = f"artifact {index}\n"
        artifacts.append(
            {
                "conversation_id": f"conv_{index}",
                "artifact_id": f"artifact:{index:064x}",
                "filename": "delivered-work.txt",
                "content": content,
                "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
            }
        )
    value = {
        "web_origin": "https://web.example.test:4443",
        "web_host": "web.example.test",
        "web_root": "/missing-browser-root",
        "screenshot": str(tmp_path / "project-resource.png"),
        "web_certificate": str(public_certificate),
        "owner_email": "owner@example.test",
        "owner_password": "fixture",
        "member_email": "member@example.test",
        "member_password": "fixture",
        "filename": "w2-" + "a" * 24 + ".txt",
        "file_content": "file bytes",
        "timeout_ms": 20_000,
        "artifacts": artifacts,
    }

    def phase() -> str:
        result = subprocess.run(
            [node, str(DRIVER)],
            cwd=ROOT,
            input=json.dumps(value),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        assert result.returncode != 0
        return result.stderr

    assert phase() == "FAILURE_PHASE:launch-browser\n"
    smoke.product.certificate(tmp_path, "other.example.test")
    assert phase() == "FAILURE_PHASE:certificate-pin\n"
    public_certificate.write_text("not a public certificate")
    assert phase() == "FAILURE_PHASE:certificate-pin\n"
    artifacts[1]["conversation_id"] = artifacts[0]["conversation_id"]
    assert phase() == "FAILURE_PHASE:parse-input\n"


def test_artifact_browser_failure_phase_reports_only_bounded_safe_identifier(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    public_certificate = tmp_path / "web.crt"
    public_certificate.write_text("public test fixture")

    def failed_driver(*_args: object, **kwargs: object) -> SimpleNamespace:
        payload = json.loads(str(kwargs["input"]))
        assert payload["web_certificate"] == str(public_certificate)
        assert "web.key" not in kwargs["input"]
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="MILESTONE:personal-mobile-layout\nFAILURE_PHASE:artifact-1-saved-download\n",
        )

    monkeypatch.setattr(
        smoke.subprocess,
        "run",
        failed_driver,
    )
    ready = SimpleNamespace(
        redirect_uri="https://web.example.test/api/auth/callback/kokoro-iam",
        email="owner@example.test",
        password="fixture",
    )
    with pytest.raises(
        smoke.SmokeError,
        match="phase=artifact-1-saved-download",
    ):
        smoke._driver_result(
            Path("/missing/node"),
            "https://web.example.test",
            ready,
            SimpleNamespace(email="member@example.test", password="fixture"),
            20,
            tmp_path / "project-resource.png",
            public_certificate,
            "a" * 24,
            [],
        )


def test_agent_redis_claim_registers_only_two_binary_source_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = smoke.AgentRedisOwnership("redis://127.0.0.1:6379/6", "a" * 24)
    calls: list[tuple[str, ...]] = []

    def fake_call(*args: str) -> str:
        calls.append(args)
        return "OK"

    monkeypatch.setattr(owner, "_call", fake_call)
    assert owner.url == "redis://127.0.0.1:6379/10"
    with pytest.raises(smoke.SmokeError, match="run identity invalid"):
        owner.register_run("conv_one", "run_one")
    owner.claim()
    owner.register_run("conv_one", "run_one")
    owner.register_run("conv_two", "run_two")
    with pytest.raises(smoke.SmokeError, match="run identity invalid"):
        owner.register_run("conv/other", "run_three")
    owner.cleanup()
    assert owner.claimed is False
    assert len(calls) == 2
    assert calls[0][0] == calls[1][0] == "EVAL"
    assert calls[0][3] == owner.marker
    assert set(calls[1][3:-1]) == {
        owner.marker,
        "kokoro:runs:requests",
        "kokoro:run:run_one:events",
        "kokoro:run:run_one:control",
        "kokoro:session:conv_one:live",
        "kokoro:agent:lease:run_one",
        "kokoro:run:run_two:events",
        "kokoro:run:run_two:control",
        "kokoro:session:conv_two:live",
        "kokoro:agent:lease:run_two",
    }


def test_agent_and_storage_use_distinct_owner_schemas() -> None:
    bff = "postgresql://localhost/root?schema=kokoro_bff"
    assert parse_qsl(
        urlsplit(smoke._owner_schema_database_url(bff, "kokoro_agent")).query
    ) == [("options", "-csearch_path=kokoro_agent")]
    assert parse_qsl(urlsplit(smoke._storage_database_url(bff)).query) == [
        ("schema", "kokoro_storage")
    ]
    with pytest.raises(smoke.SmokeError, match="PostgreSQL URL invalid"):
        smoke._owner_schema_database_url(bff, "public")


def test_agent_http_readiness_uses_healthz_capable_s6_helper() -> None:
    source = RUNNER.read_text()
    assert (
        'artifact_combo.bff_agent._wait_ready(agent_base, agent, path="/healthz")'
        in source
    )
    assert (
        'product.runtime.wait_ready(agent_base, agent, path="/healthz")' not in source
    )


def test_artifact_action_has_safe_per_delivery_diagnostic_stages() -> None:
    source = RUNNER.read_text()
    assert "def seed_artifacts(request: product.AuthenticatedRequest) -> str:" in source
    assert "nonlocal stage" in source
    for milestone in (
        "Web POST",
        "Web receipt",
        "Agent pending",
        "Agent delivery",
        "Product projection",
    ):
        assert f'stage = f"Artifact {{index + 1}} {milestone}"' in source
    assert 'stage = "real IAM Product post-action session verification"' in source
    assert "authenticated_action=seed_artifacts" in source


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


def test_durable_owner_fact_accepts_storage_asset_digest_id_only() -> None:
    commands: list[list[str]] = []

    class FakeResources:
        def command(self, command: list[str]) -> str:
            commands.append(command)
            return "1,1,1,1,1,1,0,1,1,3,1"

    ready = SimpleNamespace(tenant_id="tenant-a")
    browser = {
        "owner_subject": "user-a",
        "project_id": "project_a",
        "asset_id": "asset:" + "a" * 64,
        "personal": {
            "asset_id": "asset:" + "b" * 64,
            "visible_asset_id": "asset:" + "c" * 64,
        },
        "member_subject": "user-b",
    }
    smoke._durable_owner_facts(
        FakeResources(), "postgresql://localhost/test", ready, browser
    )
    assert len(commands) == 1
    assert "asset:" + "a" * 64 in commands[0][-1]
    assert "asset:" + "b" * 64 in commands[0][-1]
    assert "asset:" + "c" * 64 in commands[0][-1]

    browser["asset_id"] = "asset:';DROP TABLE storage_asset;--"
    with pytest.raises(smoke.SmokeError, match="asset identifier invalid"):
        smoke._durable_owner_facts(
            FakeResources(), "postgresql://localhost/test", ready, browser
        )
    assert len(commands) == 1

    browser["asset_id"] = "asset:" + "a" * 64
    browser["personal"]["asset_id"] = "asset:';DROP TABLE storage_asset;--"
    with pytest.raises(smoke.SmokeError, match="personal_asset identifier invalid"):
        smoke._durable_owner_facts(
            FakeResources(), "postgresql://localhost/test", ready, browser
        )
    assert len(commands) == 1

    browser["personal"]["asset_id"] = "asset:" + "b" * 64
    browser["personal"]["visible_asset_id"] = "asset:';DROP TABLE storage_asset;--"
    with pytest.raises(smoke.SmokeError, match="visible_asset identifier invalid"):
        smoke._durable_owner_facts(
            FakeResources(), "postgresql://localhost/test", ready, browser
        )
    assert len(commands) == 1

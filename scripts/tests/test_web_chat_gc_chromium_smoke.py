"""Fail-closed protocol tests for the real Chromium owner-GC recovery gate."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from scripts.e2e import run_web_chat_gc_chromium_smoke as smoke
from scripts.tests.test_web_project_resource_chromium_smoke import fixture_env


ROOT = Path(__file__).resolve().parents[2]


def test_config_reuses_w2_admission() -> None:
    result = subprocess.run(
        [sys.executable, str(Path(smoke.__file__)), "--check-config"],
        cwd=ROOT,
        env=fixture_env(),
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    env = fixture_env()
    env["KOKORO_SCANNER_PORT"] = "3310"
    rejected = subprocess.run(
        [sys.executable, str(Path(smoke.__file__)), "--check-config"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert rejected.returncode != 0
    assert "scanner port 3310" in rejected.stderr


def test_browser_rejects_input_before_launch() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node unavailable")
    result = subprocess.run(
        [node, str(smoke.DRIVER)],
        cwd=ROOT,
        input="{}\n",
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode != 0
    assert json.loads(result.stdout) == {
        "milestone": "failed",
        "phase": "parse-input",
        "diagnostic": None,
    }


def test_gc_source_uses_owner_api_and_never_fabricates_410() -> None:
    python = Path(smoke.__file__).read_text()
    browser = smoke.DRIVER.read_text()
    assert "agUiConsumers.collectGarbage" in python
    assert "agUi.replay" in python
    assert "agUi.status" in python
    assert "Last-Event-ID" in browser or "last-event-id" in browser
    assert "route.continue()" in browser
    assert "Math.min(30_000, input.timeout_ms / 3)" in browser
    assert 'milestone: "gc_ack"' in browser
    for milestone in (
        "recovered",
        "cards_ready",
        "first_canvas_done",
        "second_canvas_done",
    ):
        assert f'milestone: "{milestone}"' in browser
    for phase in (
        "card-click",
        "canvas-visible",
        "download-event",
        "download-bytes",
        "canvas-close",
    ):
        assert f"`${{label}}-{phase}`" in browser
    assert (
        'await page.locator(\'[data-slot="context-panel"]\').waitFor({ state: "detached"'
        in browser
    )
    assert "route.fulfill(" not in browser
    assert "time.sleep(" not in python
    assert "new Response(" not in browser
    assert "body?.active_run == null" in browser
    assert "body.active_run == null" in browser
    assert "body?.active_run === null" not in browser


def test_gc_login_boundary_is_true_owner_only_and_legacy_is_two_actor() -> None:
    sources = {name: {"sha": name} for name in ("web", "bff", "iam", "agent")}
    owner = {"subject": "owner", "form_status": 200}
    member = {"subject": "member", "form_status": 200}
    assert smoke.stack._login_boundary(
        {"login": {"owner": owner}}, sources, owner_only=True
    ) == {"source_tuple": {"web": "web", "bff": "bff", "iam": "iam"}, "owner": owner}
    assert smoke.stack._login_boundary(
        {"login": {"owner": owner, "member": member}}, sources, owner_only=False
    ) == {
        "source_tuple": {"web": "web", "bff": "bff", "iam": "iam"},
        "owner": owner,
        "member": member,
    }
    with pytest.raises(KeyError):
        smoke.stack._login_boundary(
            {"login": {"owner": owner}}, sources, owner_only=False
        )


def test_fail_only_diagnostic_redacts_unapproved_browser_fields() -> None:
    value = {
        "milestone": "failed",
        "phase": "first-owner-snapshot",
        "diagnostic": {
            "snapshot_count": 1,
            "card_count": 1,
            "original_410_response": True,
            "old_fetch_410": False,
            "new_snapshot_two_deliveries": True,
            "canvas_visible": True,
            "canvas_heading_match": False,
            "card_visible_count": 2,
            "context_panel_count": 1,
            "context_panel_state": "closed",
            "first_card_index": 1,
            "second_card_index": 0,
            "download_digest_match": False,
            "download_filename_match": True,
            "download_completed": True,
            "secret": "PRIVATE_MARKER",
            "snapshots": [
                {
                    "status": 200,
                    "delivery_count": 1,
                    "artifact_match": True,
                    "active_run_kind": "absent",
                    "watermark_present": True,
                    "probe": True,
                    "raw_url": "PRIVATE_MARKER",
                }
            ],
        },
    }
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.write(sys.argv[1]+'\\n')",
            json.dumps(value),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        with pytest.raises(smoke.SmokeError) as caught:
            smoke._read_protocol(process, time.monotonic() + 5)
        assert "active_run_kind" in str(caught.value)
        assert '"original_410_response": true' in str(caught.value)
        assert '"canvas_visible": true' in str(caught.value)
        assert '"card_visible_count": 2' in str(caught.value)
        assert '"context_panel_state": "closed"' in str(caught.value)
        assert '"second_card_index": 0' in str(caught.value)
        assert '"download_digest_match": false' in str(caught.value)
        assert "PRIVATE_MARKER" not in str(caught.value)
    finally:
        process.wait(timeout=5)


def test_browser_phase_wraps_untrusted_exception_without_payload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    certificate = tmp_path / "web.crt"
    certificate.write_text("fixture")

    def fail_launch(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("PRIVATE_MARKER")

    monkeypatch.setattr(smoke.subprocess, "Popen", fail_launch)
    with pytest.raises(smoke.SmokeError) as caught:
        smoke.live_scenario(
            node=Path(sys.executable),
            origin="https://web.example.test:4443",
            ready=SimpleNamespace(
                email="owner@example.test", password="PRIVATE_MARKER"
            ),
            member=object(),
            timeout=20,
            screenshot=tmp_path / "chat-gc.png",
            certificate=certificate,
            run_id="fixture",
            agent_db_url="fixture",
            agent_redis=object(),
            storage_base="fixture",
            object_origin="fixture",
            agent_secret="PRIVATE_MARKER",
            bff_root=tmp_path,
            bff_db_url="PRIVATE_MARKER",
            bff_redis_url="PRIVATE_MARKER",
            tenant_id="fixture",
        )
    assert str(caught.value) == "GC phase browser_launch: RuntimeError"
    assert "PRIVATE_MARKER" not in str(caught.value)


def test_agent_owner_errors_use_fixed_diagnostic_codes() -> None:
    assert (
        smoke._artifact_error_code(
            smoke.artifact_combo.SmokeError(
                "BFF dispatch did not create an Agent pending Run"
            )
        )
        == "pending_run_absent"
    )
    assert (
        smoke._artifact_error_code(smoke.artifact_combo.SmokeError("PRIVATE_MARKER"))
        == "artifact_owner_error"
    )
    assert (
        smoke._owner_error_code(
            smoke.artifact_combo.agent_storage.SmokeError(
                "delivery Chat projection order or cardinality drift"
            )
        )
        == "session_history_cardinality"
    )
    assert (
        smoke._owner_error_code(
            smoke.artifact_combo.agent_storage.SmokeError("PRIVATE_MARKER")
        )
        == "agent_storage_error"
    )


def test_delivery_failure_is_separate_from_pending_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def pending(_url: str, _run: str) -> SimpleNamespace:
        return SimpleNamespace(
            session_id="conv_fixture",
            run_id="run_fixture",
            execution_identity=SimpleNamespace(tenant_ref="tenant_fixture"),
        )

    async def fail_delivery(*_args: object) -> None:
        raise smoke.artifact_combo.agent_storage.SmokeError(
            "delivery Chat projection order or cardinality drift"
        )

    monkeypatch.setattr(smoke.artifact_combo, "_pending_run", pending)
    monkeypatch.setattr(smoke.artifact_combo, "_deliver_pending", fail_delivery)
    redis = SimpleNamespace(
        register_run=lambda *_args: None, url="redis://localhost:6379/10"
    )
    with pytest.raises(smoke.AgentOwnerFailure) as caught:
        smoke._deliver(
            agent_db_url="fixture",
            agent_redis=redis,
            storage_base="fixture",
            object_origin="fixture",
            agent_secret="fixture",
            conversation="conv_fixture",
            run="run_fixture",
            tenant="tenant_fixture",
            content=b"fixture",
            deadline=time.monotonic() + 10,
        )
    assert (caught.value.step, caught.value.code) == (
        "delivery",
        "session_history_cardinality",
    )


def test_fail_only_outbox_diagnostic_redacts_non_codes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "first": {"status": "succeeded", "attempts": 1, "error_code": None},
                    "second": {
                        "status": "retryable",
                        "attempts": 2,
                        "error_code": "PRIVATE_MARKER/secret",
                    },
                }
            ),
        )

    monkeypatch.setattr(smoke.subprocess, "run", fake_run)
    proof = smoke._outbox_failure_diagnostic(
        node=Path(sys.executable),
        root=tmp_path,
        db="PRIVATE_MARKER",
        tenant="tenant",
        conversation="conv_fixture",
        first_run="run_first",
        second_run="run_second",
        deadline=time.monotonic() + 10,
    )
    assert proof == {
        "first": {"status": "succeeded", "attempts": 1, "error_code": None},
        "second": {"status": "retryable", "attempts": 2, "error_code": None},
    }
    assert "PRIVATE_MARKER" not in json.dumps(proof)


def test_owner_gc_precondition_failure_reports_only_bounded_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=2,
            stdout=json.dumps(
                {
                    "kind": "not_ready",
                    "phase": "precondition",
                    "flags": {
                        "replay_kind": "page",
                        "run_started_count": 2,
                        "latest_run_match": True,
                        "terminal_run_match": False,
                        "snapshot_delivery_count": 2,
                        "watermark_changed": True,
                        "delivery_keys_match": True,
                        "secret": "PRIVATE_MARKER",
                    },
                }
            ),
        )

    monkeypatch.setattr(smoke.subprocess, "run", fake_run)
    with pytest.raises(smoke.SmokeError) as caught:
        smoke._collect_owner_gc(
            node=Path(sys.executable),
            root=tmp_path,
            db="PRIVATE_MARKER",
            redis="PRIVATE_MARKER",
            tenant="tenant",
            subject="owner",
            conversation="conv_fixture",
            first_artifact="artifact:first",
            second_artifact="artifact:second",
            second_run="run_second",
            old="opaque-old",
            deadline=time.monotonic() + 10,
        )
    assert "owner GC not_ready at precondition" in str(caught.value)
    assert '"terminal_run_match": false' in str(caught.value)
    assert "PRIVATE_MARKER" not in str(caught.value)


@pytest.mark.parametrize(
    "change",
    [
        {"milestone": "complete"},
        {"original_route_held": False},
        {"old_cursor_gated": False},
    ],
)
def test_gc_ack_requires_original_route_still_held(change: dict[str, object]) -> None:
    value = {
        "milestone": "gc_ack",
        "original_route_held": True,
        "old_cursor_gated": True,
    }
    smoke._check_gc_ack(value)
    value.update(change)
    with pytest.raises(smoke.SmokeError):
        smoke._check_gc_ack(value)


def test_intermediate_browser_milestones_are_strict() -> None:
    recovered = {
        "milestone": "recovered",
        "expired_status": 410,
        "expired_code": "event_cursor_expired",
        "snapshot_delivery_count": 2,
        "resume_status": 200,
        "old_cursor_matched": True,
        "new_watermark_matched": True,
    }
    smoke._check_recovered_stage(recovered)
    with pytest.raises(smoke.SmokeError):
        smoke._check_recovered_stage({**recovered, "resume_status": 410})
    cards = {
        "milestone": "cards_ready",
        "dom_card_count": 2,
        "first_key_count": 1,
        "second_key_count": 1,
    }
    smoke._check_cards_stage(cards)
    with pytest.raises(smoke.SmokeError):
        smoke._check_cards_stage({**cards, "second_key_count": 0})
    smoke._check_canvas_stage(
        {"milestone": "first_canvas_done", "first_canvas_sha256": "a" * 64},
        label="first",
        digest="a" * 64,
    )
    with pytest.raises(smoke.SmokeError):
        smoke._check_canvas_stage(
            {"milestone": "first_canvas_done", "first_canvas_sha256": "b" * 64},
            label="first",
            digest="a" * 64,
        )


@pytest.mark.parametrize(
    "change",
    [
        {"milestone": "complete"},
        {"old_watermark": None},
        {"gated_last_event_id": "different"},
        {"gated_before_network": False},
        {"first_delivery_count": 0},
        {"first_card_count": 0},
    ],
)
def test_first_milestone_rejects_missing_original_gate(
    change: dict[str, object],
) -> None:
    proof = {
        "milestone": "first_gated",
        "conversation_id": "conv_fixture",
        "first_run_id": "run_fixture",
        "first_artifact_id": "artifact:" + "a" * 64,
        "first_delivery_count": 1,
        "first_card_count": 1,
        "old_watermark": "opaque-old",
        "gated_last_event_id": "opaque-old",
        "gated_before_network": True,
        "owner_subject": "owner_fixture",
        "first_snapshot_status": 200,
        "first_sse_status": 200,
    }
    smoke._check_first_gated(proof)
    proof.update(change)
    with pytest.raises(smoke.SmokeError):
        smoke._check_first_gated(proof)


@pytest.mark.parametrize(
    "change",
    [
        {"streamsScanned": 0},
        {"framesDeleted": 0},
        {"tombstonesInserted": 0},
        {"tombstonesDeleted": 1},
        {"retention_floor": 0},
        {"replay_kind": "page"},
        {"new_watermark": "opaque-old"},
        {"second_delivery_count": 1},
        {"latest_run_id": "run_first"},
        {"terminal_run_id": None},
        {"retained_run_starts": 0},
        {"retained_at_head": False},
    ],
)
def test_owner_gc_rejects_missing_expiration(change: dict[str, object]) -> None:
    proof = {
        "kind": "complete",
        "streamsScanned": 1,
        "framesDeleted": 2,
        "tombstonesInserted": 2,
        "tombstonesDeleted": 0,
        "retention_floor": 2,
        "replay_kind": "expired_cursor",
        "new_watermark": "opaque-new",
        "second_delivery_count": 2,
        "latest_run_id": "run_second",
        "terminal_run_id": "run_second",
        "retained_run_starts": 1,
        "retained_at_head": True,
    }
    smoke._check_gc_proof(proof, old="opaque-old", second_run="run_second")
    proof.update(change)
    with pytest.raises(smoke.SmokeError):
        smoke._check_gc_proof(proof, old="opaque-old", second_run="run_second")


@pytest.mark.parametrize("missing", ["retained_run_starts", "retained_at_head"])
def test_owner_gc_requires_explicit_retained_window(missing: str) -> None:
    proof = {
        "kind": "complete",
        "streamsScanned": 1,
        "framesDeleted": 2,
        "tombstonesInserted": 2,
        "tombstonesDeleted": 0,
        "retention_floor": 2,
        "replay_kind": "expired_cursor",
        "new_watermark": "opaque-new",
        "second_delivery_count": 2,
        "latest_run_id": "run_second",
        "terminal_run_id": "run_second",
        "retained_run_starts": 1,
        "retained_at_head": True,
    }
    del proof[missing]
    with pytest.raises(smoke.SmokeError):
        smoke._check_gc_proof(proof, old="opaque-old", second_run="run_second")


@pytest.mark.parametrize(
    "change",
    [
        {"expired_status": 200},
        {"expired_code": "invalid_event_cursor"},
        {"expired_last_event_id": "opaque-new"},
        {"snapshot_after_410_status": 0},
        {"snapshot_after_410_count": 1},
        {"resume_last_event_id": "opaque-old"},
        {"resume_status": 410},
        {"first_card_count": 2},
        {"second_card_count": 0},
        {"first_canvas_sha256": "0" * 64},
        {"canvas_sha256": "0" * 64},
        {"gated_original_released": False},
        {"login": {}},
        {"owner_subject": "different"},
    ],
)
def test_final_rejects_missing_real_410_or_rehydration(
    change: dict[str, object],
) -> None:
    proof = {
        "milestone": "complete",
        "owner_subject": "owner_fixture",
        "login": {
            "owner": {
                "subject": "owner_fixture",
                "form_status": 200,
                "callback_status": 303,
                "session_status": 200,
                "product_cookie": "HttpOnly+Secure+Lax",
            }
        },
        "gated_original_released": True,
        "expired_status": 410,
        "expired_code": "event_cursor_expired",
        "expired_last_event_id": "opaque-old",
        "snapshot_after_410_status": 200,
        "snapshot_after_410_count": 2,
        "snapshot_after_410_watermark": "opaque-new",
        "resume_last_event_id": "opaque-new",
        "resume_status": 200,
        "first_card_count": 1,
        "second_card_count": 1,
        "first_canvas_sha256": "b" * 64,
        "canvas_sha256": "a" * 64,
    }
    smoke._check_complete(
        proof,
        old="opaque-old",
        new="opaque-new",
        first_digest="b" * 64,
        digest="a" * 64,
        owner_subject="owner_fixture",
    )
    proof.update(change)
    with pytest.raises(smoke.SmokeError):
        smoke._check_complete(
            proof,
            old="opaque-old",
            new="opaque-new",
            first_digest="b" * 64,
            digest="a" * 64,
            owner_subject="owner_fixture",
        )

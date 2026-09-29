"""Fail-closed protocol and source guards for the live Chat Delivery browser gate."""

from __future__ import annotations

import asyncio
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts.e2e import run_web_chat_delivery_chromium_smoke as smoke
from scripts.tests.test_web_project_resource_chromium_smoke import fixture_env


ROOT = Path(__file__).resolve().parents[2]


def test_check_config_reuses_owned_w2_admission_without_provider() -> None:
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
    assert "provider not contacted" in result.stdout


def test_check_config_rejects_shared_scanner_port() -> None:
    env = fixture_env()
    env["KOKORO_SCANNER_PORT"] = "3310"
    result = subprocess.run(
        [sys.executable, str(Path(smoke.__file__)), "--check-config"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode != 0
    assert "scanner port 3310" in result.stderr


@pytest.mark.parametrize(
    "change",
    [
        {"post_status": 200},
        {"sse_status": 0},
        {"snapshot_before_delivery_count": 1},
        {"milestone": "complete"},
        {"conversation_id": "not-a-conversation"},
        {"run_id": "bad run"},
        {"initial_sse_attempt_id": 0},
        {"initial_sse_last_event_id": "cursor"},
        {"initial_sse_open_at_handshake": False},
        {"initial_sse_ended_at_handshake": True},
        {"pending_snapshot_gets_at_handshake": 1},
    ],
)
def test_delivery_requires_post_then_real_subscribed_sse(
    change: dict[str, object],
) -> None:
    proof = {
        "milestone": "subscribed",
        "conversation_id": "conv_fixture",
        "run_id": "run_fixture",
        "post_status": 202,
        "sse_status": 200,
        "snapshot_before_delivery_count": 0,
        "initial_sse_attempt_id": 1,
        "initial_sse_last_event_id": None,
        "initial_sse_open_at_handshake": True,
        "initial_sse_ended_at_handshake": False,
        "snapshot_get_count_at_handshake": 1,
        "pending_snapshot_gets_at_handshake": 0,
    }
    proof.update(change)
    with pytest.raises(smoke.SmokeError, match="POST202 then subscribed SSE200"):
        smoke._check_subscribed(proof)


def test_subscribed_protocol_accepts_exact_boundaries() -> None:
    assert smoke._check_subscribed(
        {
            "milestone": "subscribed",
            "conversation_id": "conv_fixture",
            "run_id": "run_fixture",
            "post_status": 202,
            "sse_status": 200,
            "snapshot_before_delivery_count": 0,
            "initial_sse_attempt_id": 1,
            "initial_sse_last_event_id": None,
            "initial_sse_open_at_handshake": True,
            "initial_sse_ended_at_handshake": False,
            "snapshot_get_count_at_handshake": 1,
            "pending_snapshot_gets_at_handshake": 0,
        }
    ) == ("conv_fixture", "run_fixture")


@pytest.mark.parametrize(
    "change",
    [
        {"live_event_count": 0},
        {"card_count_before_reload": 0},
        {"card_count_after_reload": 2},
        {"canvas_native_download_sha256": "0" * 64},
        {"member_chat_status": 200},
        {"member_detail_status": 200},
        {"member_content_status": 200},
        {"delivery_sse_attempt_id": 2},
        {"delivery_sse_open_at_event": False},
        {"delivery_sse_attempt_ended_at_event": True},
        {"delivery_sse_last_event_id": "cursor"},
        {"snapshot_get_count_at_first_card": 2},
        {"terminal_held_until_first_card": False},
        {"terminal_released_after_first_card": False},
    ],
)
def test_final_browser_proof_rejects_missing_live_or_privacy(
    tmp_path: Path,
    change: dict[str, object],
) -> None:
    screenshot = tmp_path / "chat-delivery.png"
    screenshot.write_bytes(b"fixture screenshot")
    digest = "a" * 64
    artifact_id = "artifact:" + "f" * 64
    value = {
        "milestone": "complete",
        "browser": "chromium",
        "entry_url": "https://web.example.test:4443/login",
        "screenshot": str(screenshot),
        "conversation_id": "conv_fixture",
        "artifact_id": artifact_id,
        "content_sha256": digest,
        "live_event_name": "kokoro.delivery.created",
        "live_event_count": 1,
        "initial_sse_attempt_id": 1,
        "initial_sse_last_event_id": None,
        "delivery_sse_attempt_id": 1,
        "delivery_sse_last_event_id": None,
        "delivery_sse_open_at_event": True,
        "delivery_sse_attempt_ended_at_event": False,
        "snapshot_get_count_at_handshake": 1,
        "snapshot_get_count_at_first_card": 1,
        "terminal_held_until_first_card": True,
        "terminal_released_after_first_card": True,
        "card_count_before_reload": 1,
        "card_count_after_reload": 1,
        "canvas_native_download_sha256": digest,
        "member_chat_status": 404,
        "member_detail_status": 404,
        "member_content_status": 404,
        "owner_subject": "owner",
        "member_subject": "member",
        "login": {
            name: {
                "form_status": 200,
                "callback_status": 303,
                "session_status": 200,
                "product_cookie": "HttpOnly+Secure+Lax",
            }
            for name in ("owner", "member")
        },
    }
    smoke._check_evidence(
        value,
        origin="https://web.example.test:4443",
        screenshot=screenshot,
        member_id="member",
        conversation="conv_fixture",
        artifact_id=artifact_id,
        digest=digest,
    )
    value.update(change)
    with pytest.raises(smoke.SmokeError, match="evidence drift"):
        smoke._check_evidence(
            value,
            origin="https://web.example.test:4443",
            screenshot=screenshot,
            member_id="member",
            conversation="conv_fixture",
            artifact_id=artifact_id,
            digest=digest,
        )


def test_browser_input_rejected_before_launch() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable")
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
    assert (
        result.stdout
        == '{"milestone":"failed","phase":"parse-input","diagnostic":null}\n'
    )
    assert result.stderr == "FAILURE_PHASE:parse-input\n"


def test_live_hook_keeps_existing_stack_admission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_stack(
        args: object, config: dict[str, str], *, live_scenario: object
    ) -> dict[str, object]:
        seen.update(config=config, scenario=live_scenario)
        return {"status": "PASS"}

    monkeypatch.setattr(smoke.stack, "_run_smoke", fake_stack)
    monkeypatch.setattr(
        smoke.stack, "parse_args", lambda _argv: SimpleNamespace(check_config=False)
    )
    monkeypatch.setattr(smoke.os, "environ", fixture_env())
    assert smoke.main([]) == 0
    assert seen["scenario"] is smoke.live_scenario
    assert isinstance(seen["config"], dict)


@pytest.mark.parametrize("stall", ["pending", "delivery"])
def test_owner_timeout_stops_only_owned_browser_child(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    stall: str,
) -> None:
    class Child:
        def __init__(self) -> None:
            self.stdin = io.BytesIO()
            self.alive = True

        def poll(self) -> int | None:
            return None if self.alive else 0

    child = Child()
    stopped: list[Child] = []
    monkeypatch.setattr(smoke.subprocess, "Popen", lambda *_args, **_kwargs: child)
    monkeypatch.setattr(smoke, "_remaining", lambda _deadline: 0.01)
    monkeypatch.setattr(
        smoke,
        "_read_protocol",
        lambda _child, _deadline: {
            "milestone": "subscribed",
            "conversation_id": "conv_fixture",
            "run_id": "run_fixture",
            "post_status": 202,
            "sse_status": 200,
            "snapshot_before_delivery_count": 0,
            "initial_sse_attempt_id": 1,
            "initial_sse_last_event_id": None,
            "initial_sse_open_at_handshake": True,
            "initial_sse_ended_at_handshake": False,
            "snapshot_get_count_at_handshake": 1,
            "pending_snapshot_gets_at_handshake": 0,
        },
    )

    async def blocked(*_args: object) -> object:
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    async def pending(*_args: object) -> SimpleNamespace:
        return SimpleNamespace(
            run_id="run_fixture",
            session_id="conv_fixture",
            execution_identity=SimpleNamespace(tenant_ref="tenant_fixture"),
        )

    monkeypatch.setattr(
        smoke.artifact_combo,
        "_pending_run",
        blocked if stall == "pending" else pending,
    )
    monkeypatch.setattr(smoke.artifact_combo, "_deliver_pending", blocked)

    def stop(process: Child) -> None:
        stopped.append(process)
        process.alive = False

    monkeypatch.setattr(smoke.stack.product.runtime, "stop_owned_process", stop)
    certificate = tmp_path / "web.crt"
    certificate.write_text("fixture")
    redis = SimpleNamespace(
        url="redis://127.0.0.1:6379/10", register_run=lambda *_args: None
    )
    with pytest.raises(smoke.SmokeError, match="exceeded owned deadline"):
        smoke.live_scenario(
            node=Path("/node"),
            origin="https://web.example.test:4443",
            ready=SimpleNamespace(
                email="owner@example.test",
                password="fixture",
                tenant_id="tenant_fixture",
            ),
            member=SimpleNamespace(
                email="member@example.test", password="fixture", user_id="member"
            ),
            timeout=20,
            screenshot=tmp_path / "chat-delivery.png",
            certificate=certificate,
            run_id="fixture",
            agent_db_url="postgresql://fixture",
            agent_redis=redis,
            storage_base="http://127.0.0.1:9",
            object_origin="http://127.0.0.1:9",
            agent_secret="fixture",
        )
    assert stopped == [child]


def test_no_pre_delivery_shortcut_in_bounded_handshake() -> None:
    source = Path(smoke.__file__).read_text()
    browser = smoke.DRIVER.read_text()
    assert source.index("_check_subscribed(subscribed)") < source.index(
        "_deliver_pending("
    )
    assert browser.index('protocol({ milestone: "subscribed"') < browser.index(
        "const command = await boundedLine"
    )
    assert "window.__liveDeliveryFrames" in browser
    assert "response.clone().body.getReader()" in browser
    assert "_deliver_pending" in source


def test_failure_diagnostic_strips_credential_and_url_like_text() -> None:
    safe = smoke._safe_diagnostic(
        {
            "attempts": [
                {
                    "id": 1,
                    "status": 200,
                    "last_event_id_present": False,
                    "ended": True,
                    "ended_reason": "stream-error",
                    "frame_count": 2,
                    "parse_errors": 0,
                    "secret": "TOKEN",
                }
            ],
            "frames": [
                {
                    "attempt_id": 1,
                    "type": "CUSTOM",
                    "name": "kokoro.delivery.created",
                    "open_at_frame": True,
                    "url": "https://user:password@example.test",
                },
                {
                    "attempt_id": 2,
                    "type": "https://user:password@example.test",
                    "name": "TOKEN",
                    "open_at_frame": False,
                },
            ],
            "snapshot_get_count": 2,
            "pending_snapshot_gets": 0,
            "first_card_snapshot_get_count": 1,
            "first_card_seen": True,
            "card_count": 1,
            "credential": "TOKEN",
        }
    )
    serialized = json.dumps(safe)
    assert "TOKEN" not in serialized
    assert "password" not in serialized
    assert "https://" not in serialized
    assert safe["attempts"][0]["id"] == 1
    assert safe["frames"][0]["name"] == "kokoro.delivery.created"

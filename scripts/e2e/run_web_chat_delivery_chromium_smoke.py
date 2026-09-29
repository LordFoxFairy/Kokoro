#!/usr/bin/env python3
"""Run-owned live Chromium Chat Delivery composition using the W2 owner stack."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import time
from urllib.parse import urlsplit

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_agent_bff_storage_artifact_smoke as artifact_combo
import run_web_project_resource_chromium_smoke as stack


DRIVER = Path(__file__).with_name("web_chat_delivery_chromium.mjs")
SmokeError = stack.SmokeError


def _safe_diagnostic(value: object) -> dict[str, object]:
    """Keep only bounded, non-secret browser counters and protocol labels."""
    if not isinstance(value, dict):
        return {}

    def number(raw: object) -> int | None:
        return raw if type(raw) is int and 0 <= raw <= 1_000_000 else None

    def event_type(raw: object) -> str | None:
        allowed = {
            "CUSTOM",
            "RUN_STARTED",
            "RUN_FINISHED",
            "RUN_ERROR",
            "TEXT_MESSAGE_START",
            "TEXT_MESSAGE_CONTENT",
            "TEXT_MESSAGE_END",
            "TOOL_CALL_START",
            "TOOL_CALL_ARGS",
            "TOOL_CALL_END",
            "STATE_SNAPSHOT",
            "STATE_DELTA",
            "MESSAGES_SNAPSHOT",
        }
        return raw if isinstance(raw, str) and raw in allowed else None

    def event_name(raw: object) -> str | None:
        return (
            raw
            if isinstance(raw, str) and re.fullmatch(r"kokoro\.[a-z0-9_.-]{1,53}", raw)
            else None
        )

    def reason(raw: object) -> str | None:
        return (
            raw
            if isinstance(raw, str)
            and raw
            in {"complete", "stream-error", "network-error", "non-stream-response"}
            else None
        )

    attempts = value.get("attempts")
    frames = value.get("frames")
    delivery_frames = value.get("delivery_frames")
    return {
        "attempts": [
            {
                "id": number(item.get("id")),
                "status": number(item.get("status")),
                "last_event_id_present": item.get("last_event_id_present") is True,
                "ended": item.get("ended") is True,
                "ended_reason": reason(item.get("ended_reason")),
                "frame_count": number(item.get("frame_count")),
                "parse_errors": number(item.get("parse_errors")),
            }
            for item in attempts[:8]
            if isinstance(item, dict)
        ]
        if isinstance(attempts, list)
        else [],
        "frames": [
            {
                "attempt_id": number(item.get("attempt_id")),
                "type": event_type(item.get("type")),
                "name": event_name(item.get("name")),
                "open_at_frame": item.get("open_at_frame") is True,
            }
            for item in frames[:16]
            if isinstance(item, dict)
        ]
        if isinstance(frames, list)
        else [],
        "delivery_frames": [
            {
                "attempt_id": number(item.get("attempt_id")),
                "artifact_present": item.get("artifact_present") is True,
                "conversation_present": item.get("conversation_present") is True,
                "artifact_match": item.get("artifact_match") is True,
                "conversation_match": item.get("conversation_match") is True,
                "open_at_event": item.get("open_at_event") is True,
            }
            for item in delivery_frames[:8]
            if isinstance(item, dict)
        ]
        if isinstance(delivery_frames, list)
        else [],
        "audit_initial_attempt_id": number(value.get("audit_initial_attempt_id")),
        "snapshot_get_count": number(value.get("snapshot_get_count")),
        "pending_snapshot_gets": number(value.get("pending_snapshot_gets")),
        "first_card_snapshot_get_count": number(
            value.get("first_card_snapshot_get_count")
        ),
        "first_card_seen": value.get("first_card_seen") is True,
        "card_count": number(value.get("card_count")),
        "terminal_held": value.get("terminal_held") is True,
        "terminal_released": value.get("terminal_released") is True,
    }


def _read_protocol(
    process: subprocess.Popen[bytes], deadline: float
) -> dict[str, object]:
    """Read exactly one bounded JSON line; no child stderr or secrets in errors."""
    if process.stdout is None:
        raise SmokeError("live browser protocol pipe absent")
    data = bytearray()
    while time.monotonic() < deadline:
        if process.poll() is not None and not data:
            raise SmokeError("live browser exited before protocol milestone")
        readable, _, _ = select.select(
            [process.stdout], [], [], min(0.2, max(0.0, deadline - time.monotonic()))
        )
        if not readable:
            continue
        chunk = os.read(process.stdout.fileno(), 1)
        if not chunk:
            raise SmokeError("live browser protocol ended prematurely")
        if chunk == b"\n":
            break
        data.extend(chunk)
        if len(data) > 16_384:
            raise SmokeError("live browser protocol line too large")
    else:
        raise SmokeError("live browser protocol milestone timed out")
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError):
        raise SmokeError("live browser protocol milestone malformed") from None
    if not isinstance(value, dict):
        raise SmokeError("live browser protocol milestone malformed")
    if value.get("milestone") == "failed":
        phase = value.get("phase")
        if (
            not isinstance(phase, str)
            or re.fullmatch(r"[a-z0-9-]{1,48}", phase) is None
        ):
            raise SmokeError("live browser failed in unknown phase")
        diagnostic = json.dumps(
            _safe_diagnostic(value.get("diagnostic")),
            sort_keys=True,
            separators=(",", ":"),
        )
        raise SmokeError(
            f"live browser failed in phase {phase}; diagnostic={diagnostic}"
        )
    return value


def _check_subscribed(value: dict[str, object]) -> tuple[str, str]:
    conversation = value.get("conversation_id")
    run = value.get("run_id")
    attempt = value.get("initial_sse_attempt_id")
    snapshots = value.get("snapshot_get_count_at_handshake")
    if (
        value.get("milestone") != "subscribed"
        or value.get("post_status") != 202
        or value.get("sse_status") != 200
        or value.get("snapshot_before_delivery_count") != 0
        or type(attempt) is not int
        or attempt < 1
        or value.get("initial_sse_last_event_id") is not None
        or value.get("initial_sse_open_at_handshake") is not True
        or value.get("initial_sse_ended_at_handshake") is not False
        or type(snapshots) is not int
        or snapshots < 1
        or value.get("pending_snapshot_gets_at_handshake") != 0
        or not isinstance(conversation, str)
        or re.fullmatch(r"conv_[A-Za-z0-9_-]{1,180}", conversation) is None
        or not isinstance(run, str)
        or re.fullmatch(r"[A-Za-z0-9_.:-]{1,190}", run) is None
    ):
        raise SmokeError("live browser did not prove POST202 then subscribed SSE200")
    return conversation, run


def _check_evidence(
    value: dict[str, object],
    *,
    origin: str,
    screenshot: Path,
    member_id: str,
    conversation: str,
    artifact_id: str,
    digest: str,
) -> None:
    login = value.get("login")
    initial_attempt = value.get("initial_sse_attempt_id")
    snapshot_count = value.get("snapshot_get_count_at_handshake")
    if (
        value.get("milestone") != "complete"
        or value.get("browser") != "chromium"
        or value.get("entry_url") != origin + "/login"
        or value.get("screenshot") != str(screenshot)
        or not screenshot.is_file()
        or screenshot.stat().st_size == 0
        or value.get("conversation_id") != conversation
        or value.get("artifact_id") != artifact_id
        or value.get("content_sha256") != digest
        or value.get("live_event_name") != "kokoro.delivery.created"
        or value.get("live_event_count") != 1
        or type(initial_attempt) is not int
        or initial_attempt < 1
        or value.get("initial_sse_last_event_id") is not None
        or value.get("delivery_sse_attempt_id") != initial_attempt
        or value.get("delivery_sse_last_event_id") is not None
        or value.get("delivery_sse_open_at_event") is not True
        or value.get("delivery_sse_attempt_ended_at_event") is not False
        or type(snapshot_count) is not int
        or snapshot_count < 1
        or value.get("snapshot_get_count_at_first_card") != snapshot_count
        or value.get("terminal_held_until_first_card") is not True
        or value.get("terminal_released_after_first_card") is not True
        or value.get("card_count_before_reload") != 1
        or value.get("card_count_after_reload") != 1
        or value.get("canvas_native_download_sha256") != digest
        or value.get("member_chat_status") != 404
        or value.get("member_detail_status") != 404
        or value.get("member_content_status") != 404
        or value.get("member_subject") != member_id
        or not isinstance(value.get("owner_subject"), str)
        or value.get("owner_subject") == member_id
        or not isinstance(login, dict)
        or set(login) != {"owner", "member"}
    ):
        raise SmokeError("live Chromium Chat Delivery evidence drift")
    for actor in ("owner", "member"):
        proof = login[actor]
        if not isinstance(proof, dict) or (
            proof.get("form_status"),
            proof.get("callback_status"),
            proof.get("session_status"),
            proof.get("product_cookie"),
        ) != (200, 303, 200, "HttpOnly+Secure+Lax"):
            raise SmokeError("live Chromium real IAM login evidence drift")


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise SmokeError("live browser owned deadline exhausted")
    return max(1.0, remaining)


def live_scenario(
    *,
    node: Path,
    origin: str,
    ready: object,
    member: object,
    timeout: float,
    screenshot: Path,
    certificate: Path,
    run_id: str,
    agent_db_url: str,
    agent_redis: stack.AgentRedisOwnership,
    storage_base: str,
    object_origin: str,
    agent_secret: str,
) -> dict[str, object]:
    if urlsplit(origin).hostname is None or not certificate.is_file():
        raise SmokeError("live browser origin or certificate invalid")
    content = f"S9 live Agent Artifact {run_id}\n".encode()
    digest = hashlib.sha256(content).hexdigest()
    input_value = {
        "web_origin": origin,
        "web_host": urlsplit(origin).hostname,
        "web_root": str(stack.WEB),
        "web_certificate": str(certificate),
        "screenshot": str(screenshot),
        "owner_email": ready.email,
        "owner_password": ready.password,
        "member_email": member.email,
        "member_password": member.password,
        "content_sha256": digest,
        "timeout_ms": int(timeout * 1000),
    }
    process = subprocess.Popen(
        [str(node), str(DRIVER)],
        cwd=stack.ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        if process.stdin is None:
            raise SmokeError("live browser command pipe absent")
        process.stdin.write(json.dumps(input_value).encode() + b"\n")
        process.stdin.flush()
        deadline = time.monotonic() + timeout
        subscribed = _read_protocol(process, deadline)
        conversation, agent_run = _check_subscribed(subscribed)
        agent_redis.register_run(conversation, agent_run)
        try:
            pending = asyncio.run(
                asyncio.wait_for(
                    artifact_combo._pending_run(agent_db_url, agent_run),
                    timeout=_remaining(deadline),
                )
            )
        except TimeoutError:
            raise SmokeError("pending Agent Run exceeded owned deadline") from None
        if (
            pending.session_id != conversation
            or pending.execution_identity.tenant_ref != ready.tenant_id
            or pending.run_id != agent_run
        ):
            raise SmokeError(
                "pending Agent Run differs from subscribed real IAM dispatch"
            )
        try:
            delivered = asyncio.run(
                asyncio.wait_for(
                    artifact_combo._deliver_pending(
                        agent_db_url,
                        agent_redis.url,
                        storage_base,
                        object_origin,
                        agent_secret,
                        pending,
                        content,
                    ),
                    timeout=_remaining(deadline),
                )
            )
        except TimeoutError:
            raise SmokeError("Agent Storage delivery exceeded owned deadline") from None
        _remaining(deadline)
        process.stdin.write(
            json.dumps(
                {
                    "command": "delivered",
                    "conversation_id": conversation,
                    "artifact_id": delivered.artifact_id,
                }
            ).encode()
            + b"\n"
        )
        process.stdin.flush()
        evidence = _read_protocol(process, deadline)
        _check_evidence(
            evidence,
            origin=origin,
            screenshot=screenshot,
            member_id=member.user_id,
            conversation=conversation,
            artifact_id=delivered.artifact_id,
            digest=digest,
        )
        process.stdin.close()
        try:
            process.wait(timeout=max(1.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            raise SmokeError(
                "live browser did not exit within owned deadline"
            ) from None
        if process.returncode != 0:
            raise SmokeError("live browser exited with failed status")
        return evidence
    finally:
        if process.poll() is None:
            stack.product.runtime.stop_owned_process(process)


def main(argv: list[str] | None = None) -> int:
    args = stack.parse_args(argv)
    config = stack.check_configuration(dict(os.environ))
    if args.check_config:
        print("S9 live browser configuration shape valid; provider not contacted")
        return 0
    print(
        json.dumps(
            stack._run_smoke(args, config, live_scenario=live_scenario), sort_keys=True
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeError as error:
        print(f"S9 live Chromium smoke failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None

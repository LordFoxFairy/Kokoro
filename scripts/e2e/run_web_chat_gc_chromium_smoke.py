#!/usr/bin/env python3
"""Real IAM Chromium two-run owner GC and expired-cursor rehydration gate."""

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
import run_web_chat_delivery_chromium_smoke as live
import run_web_project_resource_chromium_smoke as stack


DRIVER = Path(__file__).with_name("web_chat_gc_chromium.mjs")
SmokeError = stack.SmokeError
# The isolated BFF's compiled owner repository is the only GC writer. No Root SQL.
_OWNER_GC = r"""
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { readFileSync } from 'node:fs';
const input = JSON.parse(readFileSync(0, 'utf8'));
const module = await import(pathToFileURL(resolve(input.root, 'dist/infrastructure/postgres/repositories.js')));
const owner = new module.PostgresBffRepositories(input.db, input.redis);
let phase = 'ready';
let flags = {};
try {
  await owner.ready();
  phase = 'precondition';
  const deadline = Date.now() + input.wait_ms;
  let latest = null;
  for (;;) {
    const before = await owner.agUi.replay(input.tenant, input.conversation, null, 1000);
    const snapshot = await owner.services.chat.snapshot(input.tenant, input.subject, input.conversation, undefined);
    const starts = before.kind === 'page' ? before.frames.filter(frame => frame.eventType === 'RUN_STARTED') : [];
    latest = starts.at(-1)?.payload?.runId ?? null;
    const terminal = before.kind === 'page' &&
      before.frames.some(frame => frame.eventType === 'RUN_FINISHED' && frame.payload?.runId === input.second_run);
    const keys = snapshot.deliveries.map(item => JSON.stringify([item.conversation_id, item.artifact_id]));
    flags = { replay_kind: before.kind, run_started_count: starts.length,
      latest_run_match: latest === input.second_run,
      terminal_run_match: terminal && before.terminalRunId === input.second_run,
      snapshot_delivery_count: snapshot.deliveries.length,
      delivery_keys_match: keys.length === 2 &&
        keys.includes(JSON.stringify([input.conversation, input.first_artifact])) &&
        keys.includes(JSON.stringify([input.conversation, input.second_artifact])) &&
        new Set(keys).size === 2,
      watermark_changed: typeof snapshot.event_watermark === 'string' && snapshot.event_watermark !== input.old };
    if (before.kind === 'page' && starts.length >= 2 && flags.latest_run_match &&
        flags.terminal_run_match && flags.delivery_keys_match && flags.watermark_changed) break;
    if (Date.now() >= deadline) {
      console.log(JSON.stringify({ kind: 'not_ready', phase, flags }));
      process.exitCode = 2;
      break;
    }
    await new Promise(resolve => setTimeout(resolve, 75));
  }
  if (process.exitCode === 2) {
    // No GC write occurred; retain the original browser route for cleanup.
  } else {
  phase = 'collect';
  const result = await owner.agUiConsumers.collectGarbage({
    now: new Date(Date.now() + 8 * 24 * 60 * 60 * 1000).toISOString(),
    retentionMs: 7 * 24 * 60 * 60 * 1000,
    tombstoneRetentionMs: 30 * 24 * 60 * 60 * 1000,
    batchSize: 1000,
  });
  phase = 'postcondition';
  const replay = await owner.agUi.replay(input.tenant, input.conversation, input.old, 1000);
  const after = await owner.agUi.replay(input.tenant, input.conversation, null, 1000);
  const status = await owner.agUi.status(input.tenant, input.conversation);
  const refreshed = await owner.services.chat.snapshot(input.tenant, input.subject, input.conversation, undefined);
  console.log(JSON.stringify({ kind: 'complete', ...result, replay_kind: replay.kind,
    retention_floor: status.retentionFloorSequence, new_watermark: refreshed.event_watermark,
    second_delivery_count: refreshed.deliveries.length, latest_run_id: latest,
    terminal_run_id: after.kind === 'page' ? after.terminalRunId : null,
    retained_run_starts: after.kind === 'page' ? after.frames.filter(frame => frame.eventType === 'RUN_STARTED').length : 0,
    retained_at_head: after.kind === 'page' && after.atHead,
  }));
  }
} catch {
  console.log(JSON.stringify({ kind: 'owner_error', phase, flags }));
  process.exitCode = 1;
} finally { await owner.close(); }
"""

_OUTBOX_DIAGNOSTIC = r"""
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { readFileSync } from 'node:fs';
const input = JSON.parse(readFileSync(0, 'utf8'));
const require = createRequire(pathToFileURL(resolve(input.root, 'package.json')));
const { Pool } = require('pg');
const pool = new Pool({ connectionString: input.db, max: 1,
  options: '-c search_path=kokoro_bff -c timezone=UTC' });
try {
  const rows = await pool.query(
    `SELECT run_id, status, attempt_count, last_error_code
       FROM bff_agent_dispatch_outbox
      WHERE tenant_id = $1 AND conversation_id = $2 AND run_id = ANY($3::text[])`,
    [input.tenant, input.conversation, [input.first_run, input.second_run]],
  );
  const byRun = new Map(rows.rows.map(row => [row.run_id, row]));
  const safe = run => {
    const row = byRun.get(run);
    return row ? { status: row.status, attempts: row.attempt_count,
      error_code: row.last_error_code } : { status: 'absent', attempts: 0, error_code: null };
  };
  console.log(JSON.stringify({ first: safe(input.first_run), second: safe(input.second_run) }));
} finally { await pool.end(); }
"""

_ARTIFACT_ERROR_CODES = {
    "BFF dispatch did not create an Agent pending Run": "pending_run_absent",
    "Agent production Run lease was not claimed": "lease_unclaimed",
    "Agent production tool journal did not start": "journal_start_failed",
    "Agent production delivery journal did not finish": "journal_finish_failed",
}
_AGENT_STORAGE_ERROR_CODES = {
    "delivery Chat projection order or cardinality drift": "session_history_cardinality",
    "delivery Chat projection source index drift": "chat_source_index_drift",
    "delivery Chat projection payload drift": "chat_payload_drift",
    "delivery critical outbox order or cardinality drift": "critical_outbox_cardinality",
    "delivery live stream order or duplicate frame": "live_stream_cardinality",
    "Agent Run terminal CAS failed": "terminal_cas_failed",
    "Agent retained unpublished critical outbox": "critical_outbox_unpublished",
}


class AgentOwnerFailure(SmokeError):
    def __init__(self, step: str, code: str) -> None:
        self.step = step
        self.code = code
        super().__init__(f"{step}_{code}")


def _artifact_error_code(error: artifact_combo.SmokeError) -> str:
    return _ARTIFACT_ERROR_CODES.get(str(error), "artifact_owner_error")


def _owner_error_code(error: Exception) -> str:
    if isinstance(error, TimeoutError):
        return "deadline"
    if isinstance(error, artifact_combo.SmokeError):
        return _artifact_error_code(error)
    if isinstance(error, artifact_combo.agent_storage.SmokeError):
        return _AGENT_STORAGE_ERROR_CODES.get(str(error), "agent_storage_error")
    return "owner_exception"


def _outbox_failure_diagnostic(
    *,
    node: Path,
    root: Path,
    db: str,
    tenant: str,
    conversation: str,
    first_run: str,
    second_run: str,
    deadline: float,
) -> dict[str, object]:
    """Read only two run-owned BFF outbox rows after failed second admission."""
    input_value = {
        "root": str(root),
        "db": db,
        "tenant": tenant,
        "conversation": conversation,
        "first_run": first_run,
        "second_run": second_run,
    }
    try:
        result = subprocess.run(
            [str(node), "--input-type=module", "-e", _OUTBOX_DIAGNOSTIC],
            cwd=root,
            input=json.dumps(input_value),
            text=True,
            capture_output=True,
            timeout=min(5.0, live._remaining(deadline)),
            check=False,
        )
        if result.returncode != 0:
            return {"state": "unavailable"}
        raw = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, ValueError, UnicodeError, SmokeError):
        return {"state": "unavailable"}
    if not isinstance(raw, dict):
        return {"state": "unavailable"}
    safe: dict[str, object] = {}
    for label in ("first", "second"):
        row = raw.get(label)
        if not isinstance(row, dict):
            return {"state": "unavailable"}
        status = row.get("status")
        attempts = row.get("attempts")
        error_code = row.get("error_code")
        safe[label] = {
            "status": status
            if status
            in {"absent", "pending", "leased", "retryable", "succeeded", "failed"}
            else "unknown",
            "attempts": attempts
            if type(attempts) is int and 0 <= attempts <= 100
            else None,
            "error_code": error_code
            if isinstance(error_code, str)
            and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", error_code)
            else None,
        }
    return safe


def _read_protocol(
    process: subprocess.Popen[bytes], deadline: float
) -> dict[str, object]:
    """Read one bounded browser milestone; expose only approved failure counters."""
    if process.stdout is None:
        raise SmokeError("GC browser protocol pipe absent")
    data = bytearray()
    while time.monotonic() < deadline:
        if process.poll() is not None and not data:
            raise SmokeError("GC browser exited before protocol milestone")
        readable, _, _ = select.select(
            [process.stdout], [], [], min(0.2, max(0.0, deadline - time.monotonic()))
        )
        if not readable:
            continue
        chunk = os.read(process.stdout.fileno(), 1)
        if not chunk:
            raise SmokeError("GC browser protocol ended prematurely")
        if chunk == b"\n":
            break
        data.extend(chunk)
        if len(data) > 16_384:
            raise SmokeError("GC browser protocol line too large")
    else:
        raise SmokeError("GC browser protocol milestone timed out")
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError):
        raise SmokeError("GC browser protocol milestone malformed") from None
    if not isinstance(value, dict):
        raise SmokeError("GC browser protocol milestone malformed")
    if value.get("milestone") == "failed":
        phase = value.get("phase")
        if (
            not isinstance(phase, str)
            or re.fullmatch(r"[a-z0-9-]{1,48}", phase) is None
        ):
            phase = "unknown"
        diagnostic = value.get("diagnostic")
        safe: dict[str, object] = {}
        if isinstance(diagnostic, dict):
            for key in (
                "snapshot_count",
                "sse_200_count",
                "card_count",
                "card_visible_count",
                "context_panel_count",
            ):
                count = diagnostic.get(key)
                if type(count) is int and 0 <= count <= 1_000_000:
                    safe[key] = count
            for key in ("first_card_index", "second_card_index"):
                index = diagnostic.get(key)
                safe[key] = index if type(index) is int and 0 <= index <= 2 else None
            panel_state = diagnostic.get("context_panel_state")
            safe["context_panel_state"] = (
                panel_state
                if isinstance(panel_state, str)
                and panel_state in {"absent", "open", "closed"}
                else "unknown"
            )
            for key in (
                "original_410_response",
                "old_fetch_410",
                "old_fetch_code_match",
                "old_cursor_200",
                "new_snapshot_200",
                "new_snapshot_two_deliveries",
                "new_sse_200",
                "canvas_visible",
                "canvas_heading_match",
            ):
                safe[key] = diagnostic.get(key) is True
            for key in (
                "download_digest_match",
                "download_filename_match",
                "download_completed",
            ):
                observed = diagnostic.get(key)
                safe[key] = observed if type(observed) is bool else None
            snapshots = diagnostic.get("snapshots")
            if isinstance(snapshots, list):
                safe["snapshots"] = [
                    {
                        "status": item.get("status")
                        if type(item.get("status")) is int
                        else None,
                        "delivery_count": item.get("delivery_count")
                        if type(item.get("delivery_count")) is int
                        else None,
                        "artifact_match": item.get("artifact_match") is True,
                        "active_run_kind": item.get("active_run_kind")
                        if item.get("active_run_kind")
                        in {"null", "absent", "object", "other"}
                        else None,
                        "watermark_present": item.get("watermark_present") is True,
                        "probe": item.get("probe") is True,
                    }
                    for item in snapshots[:5]
                    if isinstance(item, dict)
                ]
        raise SmokeError(
            f"GC browser failed in phase {phase}; diagnostic={json.dumps(safe, sort_keys=True)}"
        )
    return value


def _check_first_gated(value: dict[str, object]) -> tuple[str, str, str, str]:
    conversation = value.get("conversation_id")
    run = value.get("first_run_id")
    artifact = value.get("first_artifact_id")
    old = value.get("old_watermark")
    if (
        value.get("milestone") != "first_gated"
        or value.get("first_sse_status") != 200
        or value.get("first_snapshot_status") != 200
        or value.get("first_delivery_count") != 1
        or value.get("first_card_count") != 1
        or value.get("gated_before_network") is not True
        or not isinstance(old, str)
        or not old
        or value.get("gated_last_event_id") != old
        or not isinstance(value.get("owner_subject"), str)
        or not value["owner_subject"]
        or not isinstance(conversation, str)
        or re.fullmatch(r"conv_[A-Za-z0-9_-]+", conversation) is None
        or not isinstance(run, str)
        or re.fullmatch(r"[A-Za-z0-9_.:-]+", run) is None
        or not isinstance(artifact, str)
        or re.fullmatch(r"artifact:[a-f0-9]{64}", artifact) is None
    ):
        raise SmokeError("first real delivery, snapshot, or original SSE gate missing")
    return conversation, run, artifact, old


def _check_gc_proof(value: dict[str, object], *, old: str, second_run: str) -> str:
    new = value.get("new_watermark")
    if (
        value.get("kind") != "complete"
        or type(value.get("streamsScanned")) is not int
        or value["streamsScanned"] < 1
        or type(value.get("framesDeleted")) is not int
        or value["framesDeleted"] < 1
        or value.get("tombstonesInserted") != value["framesDeleted"]
        or value.get("tombstonesDeleted") != 0
        or type(value.get("retention_floor")) is not int
        or value["retention_floor"] < 1
        or value.get("replay_kind") != "expired_cursor"
        or value.get("second_delivery_count") != 2
        or value.get("latest_run_id") != second_run
        or value.get("terminal_run_id") != second_run
        or value.get("retained_run_starts") != 1
        or value.get("retained_at_head") is not True
        or not isinstance(new, str)
        or not new
        or new == old
    ):
        raise SmokeError(
            "production owner GC did not expire old cursor and retain second run"
        )
    return new


def _check_complete(
    value: dict[str, object],
    *,
    old: str,
    new: str,
    first_digest: str,
    digest: str,
    owner_subject: str,
) -> None:
    login = value.get("login")
    owner = login.get("owner") if isinstance(login, dict) else None
    if (
        value.get("milestone") != "complete"
        or not isinstance(login, dict)
        or set(login) != {"owner"}
        or not isinstance(owner, dict)
        or owner.get("subject") != owner_subject
        or value.get("owner_subject") != owner_subject
        or owner.get("form_status") != 200
        or owner.get("callback_status") != 303
        or owner.get("session_status") != 200
        or owner.get("product_cookie") != "HttpOnly+Secure+Lax"
        or value.get("gated_original_released") is not True
        or value.get("expired_status") != 410
        or value.get("expired_code") != "event_cursor_expired"
        or value.get("expired_last_event_id") != old
        or value.get("snapshot_after_410_status") != 200
        or value.get("snapshot_after_410_count") != 2
        or value.get("snapshot_after_410_watermark") != new
        or value.get("resume_last_event_id") != new
        or value.get("resume_status") != 200
        or value.get("first_card_count") != 1
        or value.get("second_card_count") != 1
        or value.get("first_canvas_sha256") != first_digest
        or value.get("canvas_sha256") != digest
    ):
        raise SmokeError("real Chromium 410 recovery evidence drift")


def _check_gc_ack(value: dict[str, object]) -> None:
    if (
        value.get("milestone") != "gc_ack"
        or value.get("original_route_held") is not True
        or value.get("old_cursor_gated") is not True
    ):
        raise SmokeError("browser did not acknowledge owner GC before route release")


def _check_recovered_stage(value: dict[str, object]) -> None:
    if (
        value.get("milestone") != "recovered"
        or value.get("expired_status") != 410
        or value.get("expired_code") != "event_cursor_expired"
        or value.get("snapshot_delivery_count") != 2
        or value.get("resume_status") != 200
        or value.get("old_cursor_matched") is not True
        or value.get("new_watermark_matched") is not True
    ):
        raise SmokeError("browser real 410/re-snapshot/new SSE milestone drift")


def _check_cards_stage(value: dict[str, object]) -> None:
    if (
        value.get("milestone") != "cards_ready"
        or value.get("dom_card_count") != 2
        or value.get("first_key_count") != 1
        or value.get("second_key_count") != 1
    ):
        raise SmokeError("browser two binary Delivery cards milestone drift")


def _check_canvas_stage(value: dict[str, object], *, label: str, digest: str) -> None:
    if (
        value.get("milestone") != f"{label}_canvas_done"
        or value.get(f"{label}_canvas_sha256") != digest
    ):
        raise SmokeError(f"browser {label} native Canvas bytes milestone drift")


def _deliver(
    *,
    agent_db_url: str,
    agent_redis: stack.AgentRedisOwnership,
    storage_base: str,
    object_origin: str,
    agent_secret: str,
    conversation: str,
    run: str,
    tenant: str,
    content: bytes,
    deadline: float,
) -> str:
    agent_redis.register_run(conversation, run)
    try:
        pending = asyncio.run(
            asyncio.wait_for(
                artifact_combo._pending_run(agent_db_url, run),
                timeout=live._remaining(deadline),
            )
        )
    except Exception as error:
        raise AgentOwnerFailure("pending", _owner_error_code(error)) from None
    if (
        pending.session_id != conversation
        or pending.run_id != run
        or pending.execution_identity.tenant_ref != tenant
    ):
        raise SmokeError("Agent pending run identity drift")
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
                timeout=live._remaining(deadline),
            )
        )
    except Exception as error:
        raise AgentOwnerFailure("delivery", _owner_error_code(error)) from None
    return delivered.artifact_id


def _collect_owner_gc(
    *,
    node: Path,
    root: Path,
    db: str,
    redis: str,
    tenant: str,
    subject: str,
    conversation: str,
    first_artifact: str,
    second_artifact: str,
    second_run: str,
    old: str,
    deadline: float,
) -> dict[str, object]:
    input_value = {
        "root": str(root),
        "db": db,
        "redis": redis,
        "tenant": tenant,
        "subject": subject,
        "conversation": conversation,
        "first_artifact": first_artifact,
        "second_artifact": second_artifact,
        "second_run": second_run,
        "old": old,
        "wait_ms": min(
            25_000, max(1_000, int(live._remaining(deadline) * 1000) - 5_000)
        ),
    }
    try:
        result = subprocess.run(
            [
                str(node),
                "--input-type=module",
                "-e",
                _OWNER_GC,
            ],
            cwd=root,
            env={**os.environ, "NODE_ENV": "development"},
            input=json.dumps(input_value),
            text=True,
            capture_output=True,
            timeout=live._remaining(deadline),
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise SmokeError("owner GC exceeded owned deadline") from None
    try:
        proof = json.loads(result.stdout)
    except (ValueError, UnicodeError):
        raise SmokeError("owner GC proof malformed") from None
    if not isinstance(proof, dict):
        raise SmokeError("owner GC proof malformed")
    if result.returncode != 0:
        kind = proof.get("kind")
        phase = proof.get("phase")
        if kind not in {"not_ready", "owner_error"} or phase not in {
            "ready",
            "precondition",
            "collect",
            "postcondition",
        }:
            raise SmokeError("owner GC process failed before bounded proof")
        raw_flags = proof.get("flags")
        flags: dict[str, object] = {}
        if isinstance(raw_flags, dict):
            replay_kind = raw_flags.get("replay_kind")
            flags["replay_kind"] = (
                replay_kind
                if replay_kind in {"page", "invalid_cursor", "expired_cursor"}
                else "unknown"
            )
            for key in ("run_started_count", "snapshot_delivery_count"):
                raw_count = raw_flags.get(key)
                flags[key] = (
                    raw_count
                    if type(raw_count) is int and 0 <= raw_count <= 1000
                    else None
                )
            for key in (
                "latest_run_match",
                "terminal_run_match",
                "delivery_keys_match",
                "watermark_changed",
            ):
                flags[key] = raw_flags.get(key) is True
        raise SmokeError(
            f"owner GC {kind} at {phase}; flags={json.dumps(flags, sort_keys=True)}"
        )
    return proof


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
    bff_root: Path,
    bff_db_url: str,
    bff_redis_url: str,
    tenant_id: str,
) -> dict[str, object]:
    if urlsplit(origin).hostname is None or not certificate.is_file():
        raise SmokeError("GC browser origin or certificate invalid")
    first_content = f"S9 GC first Agent Artifact {run_id}\n".encode()
    second_content = f"S9 GC second Agent Artifact {run_id}\n".encode()
    first_digest = hashlib.sha256(first_content).hexdigest()
    second_digest = hashlib.sha256(second_content).hexdigest()
    input_value = {
        "web_origin": origin,
        "web_host": urlsplit(origin).hostname,
        "web_root": str(stack.WEB),
        "web_certificate": str(certificate),
        "screenshot": str(screenshot),
        "owner_email": ready.email,
        "owner_password": ready.password,
        "first_sha256": first_digest,
        "second_sha256": second_digest,
        "timeout_ms": int(timeout * 1000),
    }
    phase = "browser_launch"
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            [str(node), str(DRIVER)],
            cwd=stack.ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        if process.stdin is None:
            raise SmokeError("GC browser command pipe absent")
        process.stdin.write(json.dumps(input_value).encode() + b"\n")
        process.stdin.flush()
        deadline = time.monotonic() + timeout
        phase = "first_subscribed"
        first = _read_protocol(process, deadline)
        if (
            first.get("milestone") != "first_subscribed"
            or first.get("post_status") != 202
            or first.get("sse_status") != 200
        ):
            raise SmokeError("first Product POST202/SSE200 absent")
        conversation = first.get("conversation_id")
        first_run = first.get("run_id")
        if not isinstance(conversation, str) or not isinstance(first_run, str):
            raise SmokeError("first Product receipt invalid")
        phase = "first_deliver"
        first_artifact = _deliver(
            agent_db_url=agent_db_url,
            agent_redis=agent_redis,
            storage_base=storage_base,
            object_origin=object_origin,
            agent_secret=agent_secret,
            conversation=conversation,
            run=first_run,
            tenant=tenant_id,
            content=first_content,
            deadline=deadline,
        )
        process.stdin.write(
            json.dumps(
                {"command": "first_delivered", "artifact_id": first_artifact}
            ).encode()
            + b"\n"
        )
        process.stdin.flush()
        phase = "first_gated"
        gated = _read_protocol(process, deadline)
        checked_conversation, checked_run, checked_artifact, old = _check_first_gated(
            gated
        )
        if (checked_conversation, checked_run, checked_artifact) != (
            conversation,
            first_run,
            first_artifact,
        ):
            raise SmokeError("first browser gate identity drift")
        phase = "second_submitted"
        second = _read_protocol(process, deadline)
        if (
            second.get("milestone") != "second_submitted"
            or second.get("conversation_id") != conversation
            or second.get("post_status") != 202
        ):
            raise SmokeError("second same-browser Product POST202 absent")
        second_run = second.get("run_id")
        if not isinstance(second_run, str) or second_run == first_run:
            raise SmokeError("second Product run identity drift")
        phase = "second_deliver"
        try:
            second_artifact = _deliver(
                agent_db_url=agent_db_url,
                agent_redis=agent_redis,
                storage_base=storage_base,
                object_origin=object_origin,
                agent_secret=agent_secret,
                conversation=conversation,
                run=second_run,
                tenant=tenant_id,
                content=second_content,
                deadline=deadline,
            )
        except AgentOwnerFailure as error:
            if error.step != "pending":
                raise SmokeError(
                    f"second Agent owner {error.step}_{error.code}"
                ) from None
            diagnostic = _outbox_failure_diagnostic(
                node=node,
                root=bff_root,
                db=bff_db_url,
                tenant=tenant_id,
                conversation=conversation,
                first_run=first_run,
                second_run=second_run,
                deadline=deadline,
            )
            raise SmokeError(
                f"second Agent owner {error.step}_{error.code}; "
                f"outbox={json.dumps(diagnostic, sort_keys=True)}"
            ) from None
        process.stdin.write(
            json.dumps(
                {"command": "second_delivered", "artifact_id": second_artifact}
            ).encode()
            + b"\n"
        )
        process.stdin.flush()
        phase = "second_projected"
        projected = _read_protocol(process, deadline)
        if (
            projected.get("milestone") != "second_projected"
            or projected.get("second_artifact_id") != second_artifact
            or projected.get("snapshot_delivery_count") != 2
        ):
            raise SmokeError("second owner Delivery projection absent")
        phase = "owner_gc"
        gc = _collect_owner_gc(
            node=node,
            root=bff_root,
            db=bff_db_url,
            redis=bff_redis_url,
            tenant=tenant_id,
            subject=gated["owner_subject"],
            conversation=conversation,
            first_artifact=first_artifact,
            second_artifact=second_artifact,
            second_run=second_run,
            old=old,
            deadline=deadline,
        )
        new = _check_gc_proof(gc, old=old, second_run=second_run)
        process.stdin.write(
            json.dumps({"command": "gc_complete", "new_watermark": new}).encode()
            + b"\n"
        )
        process.stdin.flush()
        phase = "gc_ack"
        ack = _read_protocol(process, min(deadline, time.monotonic() + 35))
        _check_gc_ack(ack)
        phase = "browser_recovery"
        recovered = _read_protocol(process, min(deadline, time.monotonic() + 35))
        _check_recovered_stage(recovered)
        phase = "cards_ready"
        cards = _read_protocol(process, min(deadline, time.monotonic() + 35))
        _check_cards_stage(cards)
        phase = "first_canvas"
        first_canvas = _read_protocol(process, min(deadline, time.monotonic() + 35))
        _check_canvas_stage(first_canvas, label="first", digest=first_digest)
        phase = "second_canvas"
        second_canvas = _read_protocol(process, min(deadline, time.monotonic() + 35))
        _check_canvas_stage(second_canvas, label="second", digest=second_digest)
        phase = "browser_complete"
        complete = _read_protocol(process, min(deadline, time.monotonic() + 35))
        _check_complete(
            complete,
            old=old,
            new=new,
            first_digest=first_digest,
            digest=second_digest,
            owner_subject=gated["owner_subject"],
        )
        if (
            complete.get("first_artifact_id") != first_artifact
            or complete.get("second_artifact_id") != second_artifact
        ):
            raise SmokeError("GC browser binary artifact identity drift")
        if (
            complete.get("screenshot") != str(screenshot)
            or not screenshot.is_file()
            or screenshot.stat().st_size == 0
        ):
            raise SmokeError("GC browser screenshot missing")
        phase = "browser_exit"
        process.stdin.close()
        try:
            process.wait(timeout=live._remaining(deadline))
        except subprocess.TimeoutExpired:
            raise SmokeError("GC browser did not exit") from None
        if process.returncode != 0:
            raise SmokeError("GC browser failed")
        return {**complete, "owner_gc": gc}
    except Exception as error:
        if isinstance(error, SmokeError):
            raise SmokeError(f"GC phase {phase}: {error}") from None
        if isinstance(error, artifact_combo.SmokeError):
            raise SmokeError(
                f"GC phase {phase}: {_artifact_error_code(error)}"
            ) from None
        raise SmokeError(f"GC phase {phase}: {type(error).__name__}") from None
    finally:
        if process is not None and process.poll() is None:
            stack.product.runtime.stop_owned_process(process)


def main(argv: list[str] | None = None) -> int:
    args = stack.parse_args(argv)
    config = stack.check_configuration(dict(os.environ))
    if args.check_config:
        print("S9 GC browser configuration shape valid; provider not contacted")
        return 0
    print(
        json.dumps(
            stack._run_smoke(args, config, gc_scenario=live_scenario), sort_keys=True
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeError as error:
        print(f"S9 GC Chromium smoke failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None

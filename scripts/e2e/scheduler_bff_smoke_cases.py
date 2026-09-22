#!/usr/bin/env python3
"""Exercise Scheduler/BFF acceptance behavior and observe private owner facts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
from http.client import RemoteDisconnected
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

if __package__:
    from . import scheduler_bff_smoke_runtime as _runtime
    from .scheduler_bff_smoke_http import (
        MAX_HTTP_BYTES,
        AgentCall,
        AgentReceiptState,
        ProxyCall,
        ResponseDropState,
    )
else:
    import scheduler_bff_smoke_runtime as _runtime
    from scheduler_bff_smoke_http import (
        MAX_HTTP_BYTES,
        AgentCall,
        AgentReceiptState,
        ProxyCall,
        ResponseDropState,
    )

SmokeError = _runtime.SmokeError
command_output = _runtime.command_output


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_: object) -> None:
        return None


@dataclass(frozen=True)
class HTTPResult:
    status: int
    body: dict[str, object]
    headers: dict[str, str]


def http_json(
    base: str,
    path: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, object] | None = None,
    expected: int = 200,
) -> HTTPResult:
    raw_body = (
        None if body is None else json.dumps(body, separators=(",", ":")).encode()
    )
    request_headers = dict(headers or {})
    if raw_body is not None:
        request_headers["content-type"] = "application/json"
    request = Request(
        base + path, data=raw_body, method=method, headers=request_headers
    )
    try:
        response = build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=8)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, OSError):
        raise SmokeError("HTTP request did not complete") from None
    with response:
        raw = response.read(MAX_HTTP_BYTES + 1)
        status = response.status
        response_headers = {
            key.lower(): value for key, value in response.headers.items()
        }
    if status != expected:
        raise SmokeError(
            f"{method} {path.split('?')[0]} returned {status}, expected {expected}"
        )
    if len(raw) > MAX_HTTP_BYTES:
        raise SmokeError("HTTP response exceeded smoke limit")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SmokeError("HTTP response was not valid JSON") from None
    if not isinstance(value, dict):
        raise SmokeError("HTTP object response required")
    return HTTPResult(status, value, response_headers)


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql(url: str, query: str) -> str:
    return command_output(
        ["psql", url, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-Atc", query]
    ).strip()


def wait_sql(url: str, query: str, expected: str, timeout: float = 30) -> str:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        last = sql(url, query)
        if last == expected:
            return last
        time.sleep(0.1)
    state = last if re.fullmatch(r"[a-z0-9_,:-]*", last) else "unavailable"
    raise SmokeError(
        f"Private owner state did not converge before deadline (state={state})"
    )


def bff_headers(
    token: str, tenant: str, subject: str, request_id: str, key: str
) -> dict[str, str]:
    return {
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": token,
        "x-kokoro-namespace": tenant,
        "x-kokoro-principal-id": subject,
        "x-kokoro-request-id": request_id,
        "idempotency-key": key,
    }


def task_body(marker: str) -> dict[str, object]:
    return {
        "title": "Scheduler smoke " + marker,
        "prompt": "execute " + marker,
        "frequency": "daily",
        "time": "23:59",
        "timezone": "UTC",
        "next_run_at": "2026-09-22T12:00:00Z",
        "auto_approve": False,
    }


def create_task(
    base: str, token: str, tenant: str, subject: str, key: str, marker: str
) -> str:
    result = http_json(
        base,
        "/v1/scheduled-tasks",
        method="POST",
        headers=bff_headers(token, tenant, subject, "req-" + key, key),
        body=task_body(marker),
    )
    data = result.body.get("data")
    task = data.get("task") if isinstance(data, dict) else None
    task_id = task.get("id") if isinstance(task, dict) else None
    if not isinstance(task_id, str):
        raise SmokeError("BFF ScheduledTask response drift")
    return task_id


def schedule_name(task_id: str) -> str:
    return ("kokoro.scheduled." + re.sub(r"[^a-zA-Z0-9._-]", "-", task_id)).lower()[:64]


def expected_agent_run_id(tenant: str, callback: ProxyCall) -> str:
    occurrence = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?Z",
        callback.occurrence,
    )
    if occurrence is None or not callback.schedule:
        raise SmokeError("Scheduler callback identity was invalid")
    fraction = (occurrence.group(2) or "").rstrip("0")
    canonical_occurrence = occurrence.group(1) + (
        "Z" if not fraction else f".{fraction}Z"
    )
    material = json.dumps(
        [tenant, callback.schedule, canonical_occurrence],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return "run_bff_" + hashlib.sha256(material.encode()).hexdigest()


def assert_single_agent_admission(
    before: tuple[AgentCall, ...],
    after: tuple[AgentCall, ...],
    tenant: str,
    task_id: str,
    callback: ProxyCall,
) -> AgentCall:
    if callback.upstream_status != 202 or callback.schedule != schedule_name(task_id):
        raise SmokeError("Scheduler callback did not return the expected success")
    if len(after) != len(before) + 1 or after[: len(before)] != before:
        raise SmokeError("Scheduler callback did not cause exactly one Agent admission")
    call = after[-1]
    expected_run = expected_agent_run_id(tenant, callback)
    if (
        call.run_id != expected_run
        or call.body.get("run_id") != expected_run
        or call.body.get("session_id") != f"scheduled:{task_id}"
    ):
        raise SmokeError(
            "Scheduler callback Agent identity did not match its occurrence"
        )
    callback_request = callback.headers.get("x-request-id")
    if callback_request and (
        call.request_id != callback_request
        or call.body.get("request_id") != callback_request
    ):
        raise SmokeError("Scheduler callback Agent request lineage did not match")
    return call


def assert_agent_snapshot_unchanged(
    expected: tuple[AgentCall, ...], actual: tuple[AgentCall, ...]
) -> None:
    if actual != expected:
        raise SmokeError("Callback replay caused an additional Agent admission")


def deterministic_task_id(tenant: str, key: str) -> str:
    digest = hashlib.sha256(
        (tenant + "\x1f/scheduled-tasks\x1f" + key).encode()
    ).hexdigest()[:32]
    return "scheduled_" + digest


def wait_outbox(bff_url: str, tenant: str, task_id: str, command_type: str) -> None:
    query = (
        "SELECT status FROM bff_scheduled_task_outbox WHERE tenant_id = "
        + _sql_literal(tenant)
        + " AND task_id = "
        + _sql_literal(task_id)
        + " AND command_type = "
        + _sql_literal(command_type)
        + " ORDER BY created_at DESC LIMIT 1"
    )
    try:
        wait_sql(bff_url, query, "succeeded")
    except SmokeError:
        diagnostic = sql(
            bff_url,
            "SELECT status || ':' || COALESCE(last_error_code,'none') FROM bff_scheduled_task_outbox WHERE tenant_id = "
            + _sql_literal(tenant)
            + " AND task_id = "
            + _sql_literal(task_id)
            + " AND command_type = "
            + _sql_literal(command_type)
            + " ORDER BY created_at DESC LIMIT 1",
        )
        raise SmokeError(
            f"BFF Scheduler outbox did not converge ({diagnostic})"
        ) from None


def owner_control(
    scheduler_base: str,
    token: str,
    tenant: str,
    name: str,
    method: str,
    key: str,
    target_url: str,
    body: dict[str, object] | None = None,
    expected: int = 200,
) -> HTTPResult:
    headers = {
        "authorization": "Bearer " + token,
        "x-kokoro-tenant-id": tenant,
        "x-request-id": "inject-" + key,
        "idempotency-key": key,
    }
    payload = body
    if method != "DELETE" and payload is None:
        payload = {
            "name": name,
            "schedule": "59 23 * * *",
            "timezone": "UTC",
            "url": target_url,
            "method": "POST",
            "body": {"fixture": True},
            "retry": {
                "max_attempts": 3,
                "backoff_seconds": 1,
                "max_backoff_seconds": 2,
                "max_retry_window_seconds": 60,
            },
            "misfire_policy": "fire_once",
            "catch_up_limit": 1,
            "overlap_policy": "forbid",
            "paused": False,
        }
    return http_json(
        scheduler_base,
        "/internal/scheduler/v1/schedules/" + quote(name, safe=""),
        method=method,
        headers=headers,
        body=payload,
        expected=expected,
    )


def receipt_codes(scheduler_url: str, tenant: str, key: str) -> str:
    return sql(
        scheduler_url,
        "SELECT COALESCE(string_agg(result_code, ',' ORDER BY created_at,id),'') FROM scheduler_command_receipt WHERE tenant_id = "
        + _sql_literal(tenant)
        + " AND idempotency_key = "
        + _sql_literal(key),
    )


def schedule_snapshot(scheduler_url: str, tenant: str, name: str) -> str:
    return sql(
        scheduler_url,
        "SELECT count(*)::text || ':' || COALESCE(max(payload->>'prompt'),'') FROM scheduler_schedule WHERE tenant_id = "
        + _sql_literal(tenant)
        + " AND name = "
        + _sql_literal(name),
    )


def force_due(scheduler_url: str, tenant: str, name: str) -> None:
    changed = sql(
        scheduler_url,
        "UPDATE scheduler_schedule SET next_due_at = date_trunc('second', clock_timestamp()) - interval '1 second' + interval '0.123 seconds', "
        "claim_owner = NULL, claim_expires_at = NULL WHERE tenant_id = "
        + _sql_literal(tenant)
        + " AND name = "
        + _sql_literal(name)
        + " RETURNING name",
    )
    if changed != name:
        raise SmokeError("Private Scheduler due injection missed its owned row")


def replay_proxy_call(
    base: str, call: ProxyCall, body: bytes | None = None, expected: int = 202
) -> HTTPResult:
    payload = call.body if body is None else body
    headers = dict(call.headers)
    headers["content-length"] = str(len(payload))
    request = Request(
        base + call.path,
        data=payload,
        method=call.method,
        headers=headers,
    )
    try:
        response = build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=8)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, OSError, RemoteDisconnected):
        raise SmokeError("Scheduler replay request did not complete") from None
    with response:
        raw, status = response.read(MAX_HTTP_BYTES + 1), response.status
    if status != expected:
        raise SmokeError(f"Scheduler replay returned {status}, expected {expected}")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SmokeError("Scheduler replay response drift")
    return HTTPResult(status, value, {})


@dataclass(frozen=True)
class CaseFixture:
    bff_base: str
    scheduler_base: str
    bff_url: str
    scheduler_url: str
    web_token: str
    scheduler_token: str
    tenant: str
    subject: str
    proxy: ResponseDropState
    agent: AgentReceiptState
    restart: Callable[[], None]


def exercise_control_lifecycle(
    fixture: CaseFixture, cases: list[dict[str, str]]
) -> None:
    bff_base, bff_url = fixture.bff_base, fixture.bff_url
    scheduler_url, web_token = fixture.scheduler_url, fixture.web_token
    tenant, subject = fixture.tenant, fixture.subject
    task = create_task(
        bff_base, web_token, tenant, subject, "control-create", "control-create"
    )
    wait_outbox(bff_url, tenant, task, "scheduler.register")
    control_name = schedule_name(task)
    if (
        schedule_snapshot(scheduler_url, tenant, control_name)
        != "1:execute control-create"
        or receipt_codes(scheduler_url, tenant, "control-create") != "registered"
    ):
        raise SmokeError(
            "Control create did not persist the Scheduler schedule and receipt"
        )
    cases.append(
        {
            "name": "control_create",
            "status": "PASS",
            "evidence": "public mutation -> BFF outbox -> Scheduler create",
        }
    )
    http_json(
        bff_base,
        "/v1/scheduled-tasks/" + quote(task, safe=""),
        method="PATCH",
        headers=bff_headers(
            web_token, tenant, subject, "req-control-replace", "control-replace"
        ),
        body={"prompt": "control replaced"},
    )
    wait_outbox(bff_url, tenant, task, "scheduler.replace")
    if (
        schedule_snapshot(scheduler_url, tenant, control_name) != "1:control replaced"
        or receipt_codes(scheduler_url, tenant, "control-replace") != "updated"
    ):
        raise SmokeError("Control replace did not persist the new prompt and receipt")
    cases.append(
        {
            "name": "control_replace",
            "status": "PASS",
            "evidence": "public mutation -> BFF outbox -> Scheduler replace",
        }
    )
    http_json(
        bff_base,
        "/v1/scheduled-tasks/" + quote(task, safe=""),
        method="DELETE",
        headers=bff_headers(
            web_token, tenant, subject, "req-control-delete", "control-delete"
        ),
        body={},
    )
    wait_outbox(bff_url, tenant, task, "scheduler.delete")
    if (
        schedule_snapshot(scheduler_url, tenant, control_name) != "0:"
        or receipt_codes(scheduler_url, tenant, "control-delete") != "deleted"
    ):
        raise SmokeError(
            "Control delete did not remove the Scheduler schedule and persist its receipt"
        )
    cases.append(
        {
            "name": "control_delete",
            "status": "PASS",
            "evidence": "public mutation -> BFF outbox -> Scheduler delete",
        }
    )


def exercise_delete_404(
    fixture: CaseFixture, cases: list[dict[str, str]], target_url: str
) -> None:
    bff_base, scheduler_base = fixture.bff_base, fixture.scheduler_base
    bff_url, scheduler_url = fixture.bff_url, fixture.scheduler_url
    web_token, scheduler_token = fixture.web_token, fixture.scheduler_token
    tenant, subject = fixture.tenant, fixture.subject
    delete_task = create_task(
        bff_base, web_token, tenant, subject, "delete-404-create", "delete-404"
    )
    wait_outbox(bff_url, tenant, delete_task, "scheduler.register")
    delete_name = schedule_name(delete_task)
    owner_control(
        scheduler_base,
        scheduler_token,
        tenant,
        delete_name,
        "DELETE",
        "inject-delete-404",
        target_url,
    )
    http_json(
        bff_base,
        "/v1/scheduled-tasks/" + quote(delete_task, safe=""),
        method="DELETE",
        headers=bff_headers(web_token, tenant, subject, "req-delete-404", "delete-404"),
        body={},
    )
    wait_outbox(bff_url, tenant, delete_task, "scheduler.delete")
    if receipt_codes(scheduler_url, tenant, "delete-404") != "schedule_not_found":
        raise SmokeError("Delete 404 reconciliation branch was not observed")
    cases.append(
        {
            "name": "delete_404_reconciled",
            "status": "PASS",
            "evidence": "Scheduler 404 receipt reconciled by real BFF outbox",
        }
    )


def exercise_create_409(
    fixture: CaseFixture, cases: list[dict[str, str]], target_url: str
) -> None:
    bff_base, scheduler_base = fixture.bff_base, fixture.scheduler_base
    bff_url, scheduler_url = fixture.bff_url, fixture.scheduler_url
    web_token, scheduler_token = fixture.web_token, fixture.scheduler_token
    tenant, subject = fixture.tenant, fixture.subject
    create_key = "create-409"
    predicted = deterministic_task_id(tenant, create_key)
    predicted_name = schedule_name(predicted)
    predicted_body = {
        "name": predicted_name,
        "schedule": "59 23 * * *",
        "timezone": "UTC",
        "url": target_url,
        "method": "POST",
        "body": {
            "tenant_id": tenant,
            "task_id": predicted,
            "owner_id": subject,
            "prompt": "execute create-409",
            "auto_approve": False,
            "timezone": "UTC",
        },
        "retry": {
            "max_attempts": 3,
            "backoff_seconds": 30,
            "max_backoff_seconds": 300,
            "max_retry_window_seconds": 3600,
        },
        "misfire_policy": "fire_once",
        "catch_up_limit": 1,
        "overlap_policy": "forbid",
        "paused": False,
    }
    owner_control(
        scheduler_base,
        scheduler_token,
        tenant,
        predicted_name,
        "POST",
        "owner-precreate-create-409",
        target_url,
        predicted_body,
    )
    if (
        schedule_snapshot(scheduler_url, tenant, predicted_name)
        != "1:execute create-409"
        or receipt_codes(scheduler_url, tenant, "owner-precreate-create-409")
        != "registered"
    ):
        raise SmokeError("Create 409 owner precondition was not durably established")
    created = create_task(
        bff_base, web_token, tenant, subject, create_key, "create-409"
    )
    if created != predicted:
        raise SmokeError("BFF deterministic ScheduledTask identity drift")
    wait_outbox(bff_url, tenant, created, "scheduler.register")
    if (
        receipt_codes(scheduler_url, tenant, create_key)
        != "schedule_already_exists,updated"
    ):
        raise SmokeError("Create 409 to replace reconciliation branch was not observed")
    cases.append(
        {
            "name": "create_409_replaced",
            "status": "PASS",
            "evidence": "real Scheduler POST 409 durable receipt followed by generated PUT",
        }
    )


def exercise_replace_404(
    fixture: CaseFixture, cases: list[dict[str, str]], target_url: str
) -> None:
    bff_base, scheduler_base = fixture.bff_base, fixture.scheduler_base
    bff_url, scheduler_url = fixture.bff_url, fixture.scheduler_url
    web_token, scheduler_token = fixture.web_token, fixture.scheduler_token
    tenant, subject = fixture.tenant, fixture.subject
    replace_task = create_task(
        bff_base, web_token, tenant, subject, "replace-404-create", "replace-404"
    )
    wait_outbox(bff_url, tenant, replace_task, "scheduler.register")
    replace_name = schedule_name(replace_task)
    owner_control(
        scheduler_base,
        scheduler_token,
        tenant,
        replace_name,
        "DELETE",
        "inject-replace-404",
        target_url,
    )
    http_json(
        bff_base,
        "/v1/scheduled-tasks/" + quote(replace_task, safe=""),
        method="PATCH",
        headers=bff_headers(
            web_token, tenant, subject, "req-replace-404", "replace-404"
        ),
        body={"prompt": "replace 404 reconciled"},
    )
    wait_outbox(bff_url, tenant, replace_task, "scheduler.replace")
    if (
        receipt_codes(scheduler_url, tenant, "replace-404")
        != "schedule_not_found,registered"
    ):
        raise SmokeError("Replace 404 to create reconciliation branch was not observed")
    cases.append(
        {
            "name": "replace_404_created",
            "status": "PASS",
            "evidence": "real PUT 404 followed by generated POST",
        }
    )


def exercise_control_cases(fixture: CaseFixture, cases: list[dict[str, str]]) -> None:
    target_url = fixture.proxy.target_base + "/internal/bff/scheduled-tasks/dispatch"
    exercise_control_lifecycle(fixture, cases)
    exercise_delete_404(fixture, cases, target_url)
    exercise_create_409(fixture, cases, target_url)
    exercise_replace_404(fixture, cases, target_url)


def exercise_callback_replay_cases(
    fixture: CaseFixture, cases: list[dict[str, str]]
) -> None:
    bff_base, bff_url = fixture.bff_base, fixture.bff_url
    scheduler_url, web_token = fixture.scheduler_url, fixture.web_token
    tenant, subject = fixture.tenant, fixture.subject
    proxy, agent = fixture.proxy, fixture.agent
    callback_task = create_task(
        bff_base, web_token, tenant, subject, "callback-create", "callback"
    )
    wait_outbox(bff_url, tenant, callback_task, "scheduler.register")
    callback_name = schedule_name(callback_task)
    call_index = len(proxy.calls)
    before_callback = agent.snapshot()
    force_due(scheduler_url, tenant, callback_name)
    callback = proxy.wait_for_schedule(callback_name, after=call_index)
    if re.fullmatch(r".+\.123Z", callback.occurrence) is None:
        raise SmokeError("Fractional RFC3339Nano occurrence was not preserved")
    accepted_snapshot = agent.snapshot()
    assert_single_agent_admission(
        before_callback, accepted_snapshot, tenant, callback_task, callback
    )
    cases.append(
        {
            "name": "fractional_rfc3339_callback",
            "status": "PASS",
            "evidence": "real Scheduler dispatcher preserved .123Z",
        }
    )
    replay_proxy_call(proxy.upstream, callback)
    assert_agent_snapshot_unchanged(accepted_snapshot, agent.snapshot())
    cases.append(
        {
            "name": "duplicate_replay",
            "status": "PASS",
            "evidence": "durable BFF terminal receipt replay; Agent count one",
        }
    )
    changed = json.loads(callback.body)
    changed["prompt"] = "digest conflict"
    replay_proxy_call(
        proxy.upstream, callback, json.dumps(changed).encode(), expected=409
    )
    assert_agent_snapshot_unchanged(accepted_snapshot, agent.snapshot())
    cases.append(
        {
            "name": "same_key_different_digest_409",
            "status": "PASS",
            "evidence": "same opaque key with changed semantic digest rejected",
        }
    )
    mismatch = json.loads(callback.body)
    mismatch["tenant_id"] = tenant + "-mismatch"
    replay_proxy_call(
        proxy.upstream, callback, json.dumps(mismatch).encode(), expected=400
    )
    assert_agent_snapshot_unchanged(accepted_snapshot, agent.snapshot())
    cases.append(
        {
            "name": "trusted_tenant_mismatch_400",
            "status": "PASS",
            "evidence": "trusted header/body tenant mismatch rejected before Agent I/O",
        }
    )


def exercise_restart_case(fixture: CaseFixture, cases: list[dict[str, str]]) -> None:
    bff_base, bff_url = fixture.bff_base, fixture.bff_url
    scheduler_url, web_token = fixture.scheduler_url, fixture.web_token
    tenant, subject = fixture.tenant, fixture.subject
    proxy, agent, restart = fixture.proxy, fixture.agent, fixture.restart
    unknown_task = create_task(
        bff_base, web_token, tenant, subject, "unknown-create", "unknown"
    )
    wait_outbox(bff_url, tenant, unknown_task, "scheduler.register")
    unknown_name = schedule_name(unknown_task)
    before_unknown = agent.snapshot()
    proxy.drop_next_accepted_response()
    force_due(scheduler_url, tenant, unknown_name)
    if not proxy.wait_for_drop(30):
        raise SmokeError("Response-unknown proxy did not drop an accepted response")
    unknown_call = proxy.wait_for_schedule(unknown_name)
    accepted_snapshot = agent.snapshot()
    assert_single_agent_admission(
        before_unknown, accepted_snapshot, tenant, unknown_task, unknown_call
    )
    wait_sql(
        scheduler_url,
        "SELECT status FROM scheduler_dispatch_outbox WHERE tenant_id = "
        + _sql_literal(tenant)
        + " AND schedule_name = "
        + _sql_literal(unknown_name),
        "retrying",
    )
    restart()
    sql(
        scheduler_url,
        "UPDATE scheduler_dispatch_outbox SET status='retrying', next_attempt_at=clock_timestamp()-interval '1 second', claim_owner=NULL, claim_expires_at=NULL "
        "WHERE tenant_id = "
        + _sql_literal(tenant)
        + " AND schedule_name = "
        + _sql_literal(unknown_name),
    )
    wait_sql(
        scheduler_url,
        "SELECT status FROM scheduler_dispatch_outbox WHERE tenant_id = "
        + _sql_literal(tenant)
        + " AND schedule_name = "
        + _sql_literal(unknown_name),
        "succeeded",
    )
    assert_agent_snapshot_unchanged(accepted_snapshot, agent.snapshot())
    if (
        len(
            [
                call
                for call in proxy.calls
                if call.idempotency_key == unknown_call.idempotency_key
            ]
        )
        != 2
    ):
        raise SmokeError("Response-unknown retry did not preserve Scheduler identity")
    cases.append(
        {
            "name": "response_unknown_restart_retry",
            "status": "PASS",
            "evidence": "accepted response dropped; BFF restarted; same Scheduler identity replayed; Agent count one",
        }
    )


def exercise_cases(
    bff_base: str,
    scheduler_base: str,
    bff_url: str,
    scheduler_url: str,
    web_token: str,
    scheduler_token: str,
    tenant: str,
    subject: str,
    proxy: ResponseDropState,
    agent: AgentReceiptState,
    restart: Callable[[], None],
) -> list[dict[str, str]]:
    fixture = CaseFixture(
        bff_base,
        scheduler_base,
        bff_url,
        scheduler_url,
        web_token,
        scheduler_token,
        tenant,
        subject,
        proxy,
        agent,
        restart,
    )
    cases: list[dict[str, str]] = []
    exercise_control_cases(fixture, cases)
    exercise_callback_replay_cases(fixture, cases)
    exercise_restart_case(fixture, cases)
    return cases

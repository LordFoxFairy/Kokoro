#!/usr/bin/env python3
"""Run the current Stage 2 HTTP closure against the real BFF process.

This is intentionally a Root-owned orchestrator, not a copy of BFF business
logic. It builds and starts the independent ``kokoro-bff`` repository, then
exercises its public HTTP contract over loopback. The BFF's mock store keeps
the run deterministic and does not require PostgreSQL, Redis, or network
credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
BFF = ROOT / "kokoro-bff"


class E2EFailure(RuntimeError):
    """Raised when a current Stage 2 closure assertion fails."""


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def json_body(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise E2EFailure(f"BFF returned a non-JSON body: {error}") from error


def request(
    base: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], Any]:
    request_headers = {
        "accept": "application/json",
        "x-kokoro-service": "web-bff",
        "x-kokoro-internal-secret": "stage2-e2e-secret",
        "x-kokoro-namespace": "ns_test",
        "x-kokoro-principal-id": "user_test",
    }
    if headers:
        request_headers.update(headers)
    encoded = None
    if body is not None:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        request_headers.setdefault("content-type", "application/json")
    request_object = Request(
        f"{base}{path}",
        data=encoded,
        headers=request_headers,
        method=method,
    )
    try:
        with urlopen(request_object, timeout=5) as response:
            return response.status, dict(response.headers.items()), json_body(response.read())
    except HTTPError as error:
        return error.code, dict(error.headers.items()), json_body(error.read())
    except (TimeoutError, URLError) as error:
        raise E2EFailure(f"BFF request {method} {path} failed: {error}") from error


def assert_case(
    cases: list[dict[str, Any]],
    case_id: str,
    status: int,
    expected_status: int,
    predicate: bool,
    detail: str,
) -> None:
    passed = status == expected_status and predicate
    cases.append(
        {
            "id": case_id,
            "status": status,
            "expected_status": expected_status,
            "passed": passed,
            "detail": detail,
        }
    )
    if not passed:
        raise E2EFailure(
            f"{case_id} failed: status={status} expected={expected_status}; {detail}"
        )


def data(body: Any) -> Any:
    if not isinstance(body, dict) or "data" not in body:
        raise E2EFailure(f"BFF success envelope is missing data: {body!r}")
    return body["data"]


def error_code(body: Any) -> str:
    if not isinstance(body, dict):
        return ""
    error = body.get("error")
    return error.get("code", "") if isinstance(error, dict) else ""


def wait_ready(base: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 15
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read().decode("utf-8", "replace") if process.stdout else ""
            raise E2EFailure(f"BFF exited before readiness: {output[-4000:]}")
        try:
            status, _, body = request(base, "GET", "/healthz", headers={
                "x-kokoro-service": "",
                "x-kokoro-internal-secret": "",
                "x-kokoro-namespace": "",
                "x-kokoro-principal-id": "",
            })
            if status == 200 and body == {"status": "ok", "service": "kokoro-bff", "mode": "mock"}:
                return
            last_error = f"status={status} body={body!r}"
        except E2EFailure as error:
            last_error = str(error)
        time.sleep(0.1)
    raise E2EFailure(f"BFF did not become ready: {last_error}")


def run_flow(base: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    status, _, body = request(base, "GET", "/healthz", headers={
        "x-kokoro-service": "",
        "x-kokoro-internal-secret": "",
        "x-kokoro-namespace": "",
        "x-kokoro-principal-id": "",
    })
    assert_case(cases, "BFF-001", status, 200, body.get("service") == "kokoro-bff", "health probe")

    status, _, body = request(base, "GET", "/readyz", headers={
        "x-kokoro-service": "",
        "x-kokoro-internal-secret": "",
        "x-kokoro-namespace": "",
        "x-kokoro-principal-id": "",
    })
    assert_case(cases, "BFF-002", status, 200, data(body).get("status") == "ok" if isinstance(body, dict) and "data" in body else body.get("status") == "ok", "mock readiness")

    status, _, body = request(base, "GET", "/v1/projects", headers={"x-kokoro-internal-secret": ""})
    assert_case(cases, "BFF-003", status, 403, error_code(body) == "service_auth_failed", "business route rejects missing internal credential")

    status, _, body = request(base, "GET", "/v1/projects")
    projects = data(body)
    assert_case(cases, "BFF-004", status, 200, projects["projects"][0]["id"] == "project_kokoro", "authenticated project projection")

    create_body = {"name": "Stage 2 fixture", "description": "Root closure"}
    create_headers = {"idempotency-key": "stage2-project-create"}
    first_status, _, first = request(base, "POST", "/v1/projects", body=create_body, headers=create_headers)
    second_status, _, second = request(base, "POST", "/v1/projects", body=create_body, headers=create_headers)
    assert_case(cases, "BFF-005", first_status, 200, first == second and data(first)["project"]["name"] == "Stage 2 fixture", "idempotent project create replay")
    assert_case(cases, "BFF-006", second_status, 200, first == second, "replay returns the same receipt")
    conflict_status, _, conflict = request(base, "POST", "/v1/projects", body={"name": "Different"}, headers=create_headers)
    assert_case(cases, "BFF-007", conflict_status, 409, error_code(conflict) == "idempotency_conflict", "payload drift is rejected")

    missing_status, _, missing = request(base, "PATCH", "/v1/projects/project_kokoro", body={"instruction": "updated"})
    assert_case(cases, "BFF-008", missing_status, 400, error_code(missing) == "idempotency_key_required", "mutations require an idempotency key")
    instruction = {"instruction": "Stage 2 notes stay within the project."}
    update_status, _, updated = request(base, "PATCH", "/v1/projects/project_kokoro", body=instruction, headers={"idempotency-key": "stage2-instruction"})
    replay_status, _, replay = request(base, "PATCH", "/v1/projects/project_kokoro", body=instruction, headers={"idempotency-key": "stage2-instruction"})
    assert_case(cases, "BFF-009", update_status, 200, data(updated)["project"]["instruction"] == instruction["instruction"], "project instruction update")
    assert_case(cases, "BFF-010", replay_status, 200, updated == replay, "instruction update replay")
    revision_status, _, revisions = request(base, "GET", "/v1/projects/project_kokoro/instruction-revisions")
    assert_case(cases, "BFF-011", revision_status, 200, revisions["data"]["items"][0]["current"] is True, "revision history projection")

    preview_status, _, preview = request(base, "POST", "/v1/skills/github/preview", body={"repository": "https://github.com/LordFoxFairy/example-skill"})
    assert_case(cases, "BFF-012", preview_status, 200, data(preview)["default_branch"] == "main", "GitHub skill preview does not require mutation replay")
    import_headers = {"idempotency-key": "stage2-skill-import"}
    import_status, _, imported = request(base, "POST", "/v1/skills/github/import", body={"repository": "https://github.com/LordFoxFairy/example-skill"}, headers=import_headers)
    import_replay_status, _, import_replay = request(base, "POST", "/v1/skills/github/import", body={"repository": "https://github.com/LordFoxFairy/example-skill"}, headers=import_headers)
    assert_case(cases, "BFF-013", import_status, 200, data(imported)["skill"]["name"] == "example-skill", "GitHub skill import")
    assert_case(cases, "BFF-014", import_replay_status, 200, imported == import_replay, "GitHub skill import replay")
    for case_id, path, expected in (("BFF-015", "/v1/skills/catalog", "skills"), ("BFF-016", "/v1/skills/pool", "skills"), ("BFF-017", "/v1/skills/quota", "namespace")):
        skill_status, _, skill_body = request(base, "GET", path)
        assert_case(cases, case_id, skill_status, 200, expected in data(skill_body), f"{path} projection")
    disable_status, _, disabled = request(base, "POST", "/v1/skills/contract-review/disable", headers={"idempotency-key": "stage2-skill-disable"})
    enable_status, _, enabled = request(base, "POST", "/v1/skills/contract-review/enable", headers={"idempotency-key": "stage2-skill-enable"})
    assert_case(cases, "BFF-018", disable_status, 200, data(disabled)["ok"] is True, "skill disable")
    assert_case(cases, "BFF-019", enable_status, 200, data(enabled)["ok"] is True, "skill enable")

    mcp_body = {"name": "stage2-mcp", "transport": "streamable_http", "url": "https://mcp.example.test", "allowed_tools": ["search"], "secret_ref": None}
    mcp_status, _, mcp = request(base, "POST", "/v1/mcp/servers", body=mcp_body, headers={"idempotency-key": "stage2-mcp-register"})
    mcp_name = data(mcp)["server"]["name"]
    assert_case(cases, "BFF-020", mcp_status, 200, mcp_name == "stage2-mcp", "MCP registration")
    list_status, _, mcp_list = request(base, "GET", "/v1/mcp/servers")
    assert_case(cases, "BFF-021", list_status, 200, any(item["name"] == mcp_name for item in data(mcp_list)["servers"]), "MCP list")
    toggle_status, _, toggled = request(base, "POST", f"/v1/mcp/servers/{mcp_name}/disable", headers={"idempotency-key": "stage2-mcp-disable"})
    assert_case(cases, "BFF-022", toggle_status, 200, data(toggled)["ok"] is True, "MCP disable")

    schedule_body = {"title": "Stage 2 check", "prompt": "Run the closure check.", "frequency": "daily", "time": "10:00", "timezone": "UTC", "auto_approve": False}
    schedule_status, _, schedule = request(base, "POST", "/v1/scheduled-tasks", body=schedule_body, headers={"idempotency-key": "stage2-schedule-create"})
    schedule_id = data(schedule)["task"]["id"]
    assert_case(cases, "BFF-023", schedule_status, 200, data(schedule)["task"]["title"] == "Stage 2 check", "scheduled task create")
    schedule_patch_status, _, schedule_patch = request(base, "PATCH", f"/v1/scheduled-tasks/{schedule_id}", body={"enabled": False}, headers={"idempotency-key": "stage2-schedule-patch"})
    assert_case(cases, "BFF-024", schedule_patch_status, 200, data(schedule_patch)["task"]["enabled"] is False, "scheduled task update")
    retry_status, _, retry = request(base, "POST", f"/v1/scheduled-tasks/{schedule_id}/retry", headers={"idempotency-key": "stage2-schedule-retry"})
    assert_case(cases, "BFF-025", retry_status, 200, data(retry)["task"]["enabled"] is True, "scheduled task retry")

    setup_status, _, setup = request(base, "GET", "/v1/agents/connections/setup?platform=telegram")
    assert_case(cases, "BFF-026", setup_status, 200, data(setup)["platform"] == "telegram", "Agent connection projection")
    invalid_setup_status, _, invalid_setup = request(base, "GET", "/v1/agents/connections/setup?platform=irc")
    assert_case(cases, "BFF-027", invalid_setup_status, 400, error_code(invalid_setup) == "invalid_agent_platform", "Agent platform validation")
    library_status, _, library = request(base, "GET", "/v1/library")
    assert_case(cases, "BFF-028", library_status, 200, len(data(library)["items"]) > 0, "library projection")
    plans_status, _, plans = request(base, "GET", "/v1/billing/plans")
    assert_case(cases, "BFF-029", plans_status, 200, data(plans)["plans"][0]["id"] == "plan_starter", "billing plans projection")
    checkout_status, _, checkout = request(base, "POST", "/v1/billing/checkout", body={"plan_id": "plan_starter"}, headers={"idempotency-key": "stage2-checkout"})
    assert_case(cases, "BFF-030", checkout_status, 200, data(checkout)["checkout_url"].startswith("/billing/mock-checkout/"), "billing checkout projection")

    sessions_status, _, sessions = request(base, "GET", "/v1/sessions?scope=ns_test&project_ref=project_kokoro")
    assert_case(cases, "BFF-031", sessions_status, 200, data(sessions)["sessions"][0]["session_id"] == "session_kokoro", "Chat session list")
    detail_status, _, detail = request(base, "GET", "/v1/sessions/session_kokoro?scope=ns_test&project_ref=project_kokoro")
    assert_case(cases, "BFF-032", detail_status, 200, data(detail)["session"]["owner_id"] == "ns_test", "Chat session detail")
    message_body = {"content": "Close the Stage 2 loop."}
    message_headers = {"idempotency-key": "stage2-message"}
    message_status, _, message = request(base, "POST", "/v1/sessions/session_kokoro/messages?scope=ns_test&project_ref=project_kokoro", body=message_body, headers=message_headers)
    message_replay_status, _, message_replay = request(base, "POST", "/v1/sessions/session_kokoro/messages?scope=ns_test&project_ref=project_kokoro", body=message_body, headers=message_headers)
    assert_case(cases, "BFF-033", message_status, 200, data(message)["run_id"] == "run_1", "Chat message submit")
    assert_case(cases, "BFF-034", message_replay_status, 200, message == message_replay, "Chat message idempotency replay")
    # SSE is intentionally opaque to the JSON helper; read it as a stream so the
    # test exercises the same content type and event framing the Web adapter uses.
    sse_request = Request(f"{base}/v1/sessions/session_kokoro/events?scope=ns_test&project_ref=project_kokoro", headers={"x-kokoro-service": "web-bff", "x-kokoro-internal-secret": "stage2-e2e-secret", "x-kokoro-namespace": "ns_test", "x-kokoro-principal-id": "user_test"})
    with urlopen(sse_request, timeout=5) as sse_response:
        events_status = sse_response.status
        events_content_type = sse_response.headers.get("content-type", "")
        sse_text = sse_response.read().decode("utf-8")
    assert_case(cases, "BFF-035", events_status, 200, "text/event-stream" in events_content_type, "Chat SSE content type")
    assert_case(cases, "BFF-036", 200, 200, "message.user" in sse_text and "message.completed" in sse_text, "Chat SSE event stream")
    share_status, _, share = request(base, "POST", "/v1/sessions/session_kokoro/share?scope=ns_test&project_ref=project_kokoro", headers={"idempotency-key": "stage2-share"})
    share_id = data(share)["share_id"]
    assert_case(cases, "BFF-037", share_status, 200, share_id.startswith("shr_"), "Chat share creation")
    shared_status, _, shared = request(base, "GET", f"/v1/shared/{share_id}?scope=ns_test&project_ref=project_kokoro")
    assert_case(cases, "BFF-038", shared_status, 200, data(shared)["session"]["session_id"] == "session_kokoro", "shared session read")
    title_status, _, title = request(base, "PATCH", "/v1/sessions/session_kokoro/title?scope=ns_test&project_ref=project_kokoro", body={"title": "Stage 2 closed"}, headers={"idempotency-key": "stage2-title"})
    assert_case(cases, "BFF-039", title_status, 200, data(title)["ok"] is True, "Chat title update")
    control_status, _, control = request(base, "POST", "/v1/sessions/session_kokoro/runs/run_1/control?scope=ns_test&project_ref=project_kokoro", body={"action": "cancel"}, headers={"idempotency-key": "stage2-control-cancel"})
    assert_case(cases, "BFF-040", control_status, 200, data(control)["ok"] is True, "Chat run control")
    revoke_status, _, revoked = request(base, "DELETE", "/v1/sessions/session_kokoro/share?scope=ns_test&project_ref=project_kokoro", headers={"idempotency-key": "stage2-share-revoke"})
    assert_case(cases, "BFF-041", revoke_status, 200, data(revoked)["share_id"] == share_id, "Chat share revocation")
    delete_status, _, deleted = request(base, "DELETE", "/v1/sessions/session_kokoro?scope=ns_test&project_ref=project_kokoro", headers={"idempotency-key": "stage2-session-delete"})
    assert_case(cases, "BFF-042", delete_status, 200, data(deleted)["status"] == "deleted", "Chat session deletion")
    after_delete_status, _, after_delete = request(base, "GET", "/v1/sessions/session_kokoro?scope=ns_test&project_ref=project_kokoro")
    assert_case(cases, "BFF-043", after_delete_status, 404, error_code(after_delete) == "session_not_found", "deleted Chat session is no longer readable")

    return cases


def write_evidence(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
        json.dump(payload, temporary, ensure_ascii=False, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.chmod(temporary_path, 0o600)
    os.replace(temporary_path, path)


def stop_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    if not BFF.is_dir():
        raise E2EFailure(f"BFF repository is missing: {BFF}")

    subprocess.run(["pnpm", "build"], cwd=BFF, check=True)
    port = free_port()
    environment = {
        **os.environ,
        "KOKORO_BFF_MODE": "mock",
        "KOKORO_BFF_HOST": "127.0.0.1",
        "KOKORO_BFF_PORT": str(port),
        "KOKORO_DOMAIN": "dev.kokoro.localhost",
        "KOKORO_BFF_SHARED_SECRET": "stage2-e2e-secret",
    }
    process = subprocess.Popen(
        ["node", "dist/main.js"],
        cwd=BFF,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    base = f"http://127.0.0.1:{port}"
    evidence: dict[str, Any] = {
        "suite": "kokoro-stage2-bff-mock-e2e",
        "contract": "Kokoro Business API v1",
        "mode": "mock",
        "domain": "dev.kokoro.localhost",
        "cases": [],
    }
    try:
        wait_ready(base, process)
        evidence["cases"] = run_flow(base)
        evidence["status"] = "PASS"
        evidence["passed"] = len(evidence["cases"])
        evidence["failed"] = 0
        if args.evidence is not None:
            write_evidence(args.evidence.absolute(), evidence)
        print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
        return 0
    except BaseException as error:
        evidence["status"] = "FAIL"
        evidence["error"] = f"{type(error).__name__}: {error}"
        print(json.dumps(evidence, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        stop_process(process)


if __name__ == "__main__":
    raise SystemExit(main())

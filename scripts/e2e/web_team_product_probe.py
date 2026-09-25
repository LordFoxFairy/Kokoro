"""Browser-side Team Product assertions inside the owned Web/BFF/IAM HTTPS run.

This module owns no services or data. The composition runner supplies its
authenticated same-origin request function and observed BFF operations.
"""

from __future__ import annotations

import json
import re
from typing import Protocol


class TeamProbeError(RuntimeError):
    """A sanitized failure without response payloads or credentials."""


class Response(Protocol):
    status: int
    headers: dict[str, str]
    body: bytes


class Request(Protocol):
    def __call__(
        self,
        path: str,
        *,
        method: str = "GET",
        json_body: dict | None = None,
        origin: str | None = None,
    ) -> Response: ...


def _payload(
    response: Response, expected_status: int, operation: str = "request"
) -> dict:
    if response.status != expected_status:
        try:
            error_code = json.loads(response.body).get("error", {}).get("code")
        except (ValueError, AttributeError, TypeError):
            error_code = None
        detail = (
            f" ({error_code})"
            if isinstance(error_code, str)
            and re.fullmatch(r"[a-z0-9_]{1,64}", error_code)
            else ""
        )
        raise TeamProbeError(
            f"Team browser {operation} HTTP {response.status}{detail}, expected {expected_status}"
        )
    if "no-store" not in response.headers.get("cache-control", ""):
        raise TeamProbeError("Team browser cache policy invalid")
    request_id = response.headers.get("x-request-id")
    if (
        not isinstance(request_id, str)
        or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id) is None
    ):
        raise TeamProbeError("Team browser request ID invalid")
    if "application/json" not in response.headers.get("content-type", ""):
        raise TeamProbeError("Team browser content type invalid")
    try:
        body = json.loads(response.body)
    except (ValueError, UnicodeError):
        raise TeamProbeError("Team browser response malformed") from None
    if (
        not isinstance(body, dict)
        or not isinstance(body.get("meta"), dict)
        or body["meta"].get("request_id") != request_id
    ):
        raise TeamProbeError("Team browser response metadata invalid")
    if expected_status == 200:
        if set(body) != {"data", "meta"}:
            raise TeamProbeError("Team browser success envelope invalid")
    elif (
        set(body) != {"error", "meta"}
        or not isinstance(body.get("error"), dict)
        or set(body["error"]) != {"code", "message"}
        or not isinstance(body["error"].get("code"), str)
        or not body["error"]["code"]
    ):
        raise TeamProbeError("Team browser error envelope invalid")
    return body


def _count(observed: list[tuple[str, str]], operation: tuple[str, str]) -> int:
    return observed.count(operation)


def anonymous(request: Request, observed: list[tuple[str, str]]) -> None:
    operation = ("GET", "/v1/team/members")
    before = _count(observed, operation)
    body = _payload(request("/api/team/members?limit=5"), 401, "anonymous members")
    if (
        body["error"]["code"] != "unauthenticated"
        or _count(observed, operation) != before
    ):
        raise TeamProbeError(
            "Anonymous Team request reached BFF or changed error contract"
        )


def authenticated(
    request: Request,
    projection: dict,
    observed: list[tuple[str, str]],
    web_origin: str,
) -> None:
    subject = projection.get("subject")
    if not isinstance(subject, str) or not subject:
        raise TeamProbeError("Product Session subject missing")
    for kind in ("members", "roles"):
        operation = ("GET", f"/v1/team/{kind}")
        before = _count(observed, operation)
        body = _payload(request(f"/api/team/{kind}?limit=5"), 200, f"GET {kind}")
        if _count(observed, operation) != before + 1:
            raise TeamProbeError(f"Team {kind} did not cross Web to BFF exactly once")
        data, meta = body["data"], body["meta"]
        if (
            not isinstance(data, list)
            or len(data) > 5
            or set(meta) != {"request_id", "next_cursor"}
            or (
                meta["next_cursor"] is not None
                and not isinstance(meta["next_cursor"], str)
            )
        ):
            raise TeamProbeError(f"Team {kind} page invalid")
        if kind == "members" and not any(
            isinstance(item, dict)
            and item.get("user_id") == subject
            and isinstance(item.get("member_id"), str)
            and item.get("roles") == ["member"]
            and "email" not in item
            for item in data
        ):
            raise TeamProbeError("Current Team membership projection invalid")
        if kind == "roles" and not any(
            isinstance(item, dict)
            and item.get("name") == "member"
            and isinstance(item.get("permissions"), dict)
            and "read" in item["permissions"].get("member", [])
            for item in data
        ):
            raise TeamProbeError("Team role catalog omitted member read permission")

    invitation_operation = ("GET", "/v1/team/invitations")
    before = _count(observed, invitation_operation)
    invite = _payload(request("/api/team/invitations?limit=5"), 403, "GET invitations")
    if _count(observed, invitation_operation) != before + 1 or "data" in invite:
        raise TeamProbeError("Ordinary member invitation list was not denied by owner")

    mutation = ("POST", "/v1/team/invitations")
    before = _count(observed, mutation)
    valid_body = {"email": "blocked-member@example.test", "roles": ["member"]}
    foreign = _payload(
        request(
            "/api/team/invitations",
            method="POST",
            json_body=valid_body,
            origin="https://evil.example.test",
        ),
        403,
        "foreign-origin invitation",
    )
    if (
        foreign["error"]["code"] != "forbidden_origin"
        or _count(observed, mutation) != before
    ):
        raise TeamProbeError("Foreign-origin Team mutation reached BFF")
    forged = _payload(
        request(
            "/api/team/invitations",
            method="POST",
            json_body={**valid_body, "tenant_id": "forged"},
            origin=web_origin,
        ),
        400,
        "forged-tenant invitation",
    )
    if (
        forged["error"]["code"] != "invalid_team_request"
        or _count(observed, mutation) != before
    ):
        raise TeamProbeError("Caller-supplied Team tenant reached BFF")
    # The shared HTTPS probe proxy intentionally rejects chunked mutation
    # framing. Owner-side write authorization is covered by the BFF/IAM
    # contract tests; this browser probe covers the same-origin read path and
    # Web's pre-BFF mutation guards without changing that proxy's scope.

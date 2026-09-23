from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

import pytest

from scripts.e2e.bff_iam_admission_stub import AdmissionIdentity, iam_admission_stub
from scripts.e2e import bff_iam_admission_stub as stub


def request(
    base: str,
    token: str | None,
    *,
    path: str = "/internal/v1/session-authorizations/verify",
    body: bytes | None = b"",
    request_id: str = "smoke_request_1",
) -> tuple[int, dict[str, str], dict[str, object]]:
    headers = {"x-request-id": request_id}
    if token is not None:
        headers["authorization"] = "Bearer " + token
    call = Request(base + path, data=body, method="POST", headers=headers)
    try:
        response = build_opener(ProxyHandler({})).open(call, timeout=2)
    except HTTPError as error:
        response = error
    with response:
        return (
            response.status,
            {key.lower(): value for key, value in response.headers.items()},
            json.load(response),
        )


def test_fixed_bearer_maps_to_exact_trusted_identity_and_no_store() -> None:
    identity = AdmissionIdentity("tenant-a", "user-a", "session-a", "client-a")
    with iam_admission_stub({"fixed-token": identity}) as base:
        status, headers, body = request(base, "fixed-token")
        assert status == 200
        assert headers["cache-control"] == "no-store"
        assert headers["x-request-id"] == "smoke_request_1"
        assert body == {
            "data": {
                "allowed": True,
                "tenant_id": "tenant-a",
                "user_id": "user-a",
                "session_id": "session-a",
                "client_id": "client-a",
            }
        }
    assert request_is_closed(base)


def request_is_closed(base: str) -> bool:
    from urllib.error import URLError

    try:
        request(base, "fixed-token")
    except (URLError, OSError):
        return True
    return False


def test_unknown_or_missing_token_and_nonempty_body_are_rejected() -> None:
    identity = AdmissionIdentity("tenant-a", "user-a", "session-a", "client-a")
    with iam_admission_stub({"fixed-token": identity}) as base:
        for token, body, expected in (
            (None, b"", 401),
            ("wrong", b"", 401),
            ("fixed-token", b"{}", 400),
        ):
            status, headers, payload = request(base, token, body=body)
            assert status == expected
            assert headers["cache-control"] == "no-store"
            assert set(payload) == {"error"}
            assert set(payload["error"]) == {"code", "message", "retryable", "details"}


def test_concurrent_tokens_never_cross_identity_and_query_is_rejected() -> None:
    identities = {
        "token-a": AdmissionIdentity("tenant-a", "user-a", "session-a", "client-a"),
        "token-b": AdmissionIdentity("tenant-b", "user-b", "session-b", "client-b"),
    }
    with iam_admission_stub(identities) as base:
        with ThreadPoolExecutor(max_workers=8) as pool:
            calls = list(
                pool.map(
                    lambda token: request(base, token), ["token-a", "token-b"] * 16
                )
            )
        assert all(
            status == 200 and body["data"]["tenant_id"] == f"tenant-{token[-1]}"
            for token, (status, _, body) in zip(["token-a", "token-b"] * 16, calls)
        )
        status, _, body = request(
            base, "token-a", path="/internal/v1/session-authorizations/verify?extra=1"
        )
        assert status == 404
        assert body["error"]["code"] == "NOT_FOUND"


def test_invalid_request_id_is_replaced_by_a_legal_response_header() -> None:
    with iam_admission_stub(
        {"fixed-token": AdmissionIdentity("tenant", "user", "session", "client")}
    ) as base:
        status, headers, _ = request(
            base, "fixed-token", request_id="invalid.request.id"
        )
        assert status == 200
        assert "invalid.request.id" != headers["x-request-id"]
        assert headers["x-request-id"].replace("-", "").replace("_", "").isalnum()


def test_failed_listener_thread_start_closes_owned_socket(monkeypatch) -> None:
    created = []
    original_server = stub._Server

    def record_server(identities):
        server = original_server(identities)
        created.append(server)
        return server

    class FailingThread(Thread):
        def start(self) -> None:
            raise RuntimeError("injected thread start failure")

    monkeypatch.setattr(stub, "_Server", record_server)
    monkeypatch.setattr(stub, "Thread", FailingThread)
    with pytest.raises(RuntimeError, match="injected thread start failure"):
        with iam_admission_stub(
            {"token": AdmissionIdentity("tenant", "user", "session", "client")}
        ):
            pass
    assert len(created) == 1
    assert created[0].fileno() == -1

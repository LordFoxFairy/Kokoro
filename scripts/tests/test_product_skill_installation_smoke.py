"""Root evidence checks, not a substitute for the real owner composition."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest


PATH = Path(__file__).resolve().parents[1] / "e2e/product_skill_installation_smoke.py"


def helper():
    assert PATH.is_file(), "Product installation evidence helper is missing"
    spec = importlib.util.spec_from_file_location("product_installation_smoke", PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_collection_and_five_operations_match_pinned_bff_machine_contract():
    m = helper()
    root = PATH.parents[2]
    operations = json.loads(
        (root / "apps/kokoro-bff/contract/tests/v1-operations.json").read_text()
    )["operations"]
    actual = {
        (x["method"], x["path"])
        for x in operations
        if "skill-installations" in x["path"]
    }
    expected = {
        ("POST", m.COLLECTION),
        ("GET", m.COLLECTION),
        ("GET", m.COLLECTION + "/{installation_id}"),
        ("DELETE", m.COLLECTION + "/{installation_id}"),
        ("PUT", m.COLLECTION + "/{installation_id}/enabled"),
    }
    assert expected == actual
    assert m.COLLECTION == "/v1/skill-installations"


def installation(identity="installation-a", source="skill:source-a", **changes):
    return {
        "installation_id": identity,
        "source_ref": source,
        "series_id": "series-a",
        "revision": "1",
        "installed": True,
        "enabled": True,
        "installed_at": "2026-09-30T12:00:00.000Z",
        "updated_at": "2026-09-30T12:00:00.000Z",
        **changes,
    }


def ack(row, change, replayed=False):
    return {
        "data": {
            "installation": row,
            "change": change,
            "replayed": replayed,
            **({} if change == "unchanged" else {"event_id": "event-" + change}),
        }
    }


def error(code):
    return {"error": {"code": code, "message": "Public error", "retryable": False}}


def test_exact_public_installation_and_presence():
    m = helper()
    row = installation()
    assert m.require_installation(row) == row
    removed = installation(
        installed=False, enabled=False, removed_at="2026-09-30T12:00:00.000Z"
    )
    assert m.require_installation(removed) == removed
    bad = [
        {**row, "revision": 1},
        {**row, "revision": "18446744073709551616"},
        {**row, "revision": "01"},
        {**row, "revision": "0"},
        {**row, "enabled": 1},
        {**row, "installed": None},
        {**row, "asset_ref": "PRIVATE_TEST_BODY"},
        {**row, "removed_at": None},
        {**row, "removed_at": row["installed_at"]},
        {**row, "updated_at": "2026-09-29T12:00:00.000Z"},
        {**row, "installed_at": "2026-09-30T12:00:00+00:00"},
        {**row, "source_ref": "skill:skill:source-a"},
        {**row, "installed": False},
        {**removed, "enabled": True},
    ]
    for value in bad:
        with pytest.raises(m.ProductError) as caught:
            m.require_installation(value)
        assert "PRIVATE_TEST_BODY" not in str(caught.value)


def test_explicit_product_mode_and_agent_mode_are_disjoint():
    m = helper()
    m.preflight(False, False)
    m.preflight(True, False)
    m.preflight(False, True)
    for modes in [(True, True), (1, False), (False, None)]:
        with pytest.raises(m.ProductError):
            m.preflight(*modes)


def test_ack_malformed_change_is_rejected_not_unhashable_exception():
    m = helper()
    for change in [{}, [], None, 1]:
        with pytest.raises(m.ProductError):
            m.require_ack(
                (
                    200,
                    {
                        "data": {
                            "installation": installation(),
                            "change": change,
                            "replayed": False,
                        }
                    },
                ),
                "installed",
                False,
            )


def test_ack_event_presence_and_historical_replay_exactness():
    m = helper()
    first = m.require_ack((200, ack(installation(), "installed")), "installed", False)
    replay = m.require_ack(
        (200, ack(installation(), "installed", True)), "installed", True
    )
    m.require_replay(first, replay)
    for value in [
        ack(installation(), "disabled", True),
        ack(installation(enabled=False), "installed", True),
        ack(installation(), "installed"),
    ]:
        with pytest.raises(m.ProductError):
            m.require_replay(first, value["data"])
    for value in [
        ack(installation(), "unknown"),
        {"data": {**first, "replayed": 1}},
        {"data": {**first, "event_id": None}},
        {"data": {**first, "change": "unchanged"}},
        {"data": {**first, "private": "PRIVATE_TEST_BODY"}},
    ]:
        with pytest.raises(m.ProductError):
            m.require_ack((200, value), "installed", False)
    m.require_ack((200, ack(installation(), "unchanged")), "unchanged", False)
    with pytest.raises(m.ProductError):
        m.require_ack((204, ack(installation(), "removed")), "removed", False)


def test_page_top_level_false_presence_cursor_and_unique_ids():
    m = helper()
    disabled = installation(enabled=False)
    assert m.require_page((200, {"data": [disabled]})) == ([disabled], None)
    assert (
        m.require_page((200, {"data": [disabled], "meta": {"next_cursor": "opaque"}}))[
            1
        ]
        == "opaque"
    )
    for body in [
        {"data": {"installations": [disabled]}},
        {"data": [disabled, disabled]},
        {"data": [], "meta": {}},
        {"data": [], "meta": {"next_cursor": ""}},
        {"data": [], "meta": {"next_cursor": "é" * 2049}},
        {"data": [], "meta": {"next_cursor": None}},
        {"data": [], "has_more": False},
    ]:
        with pytest.raises(m.ProductError):
            m.require_page((200, body))


def test_strict_error_never_accepts_private_success_or_wrong_code():
    m = helper()
    m.require_error(
        (404, error("skill_installation_not_found")),
        404,
        "skill_installation_not_found",
    )
    for response in [
        (200, error("skill_installation_not_found")),
        (404, error("other")),
        (404, {**error("skill_installation_not_found"), "data": "private"}),
        (
            404,
            {
                "error": {
                    **error("skill_installation_not_found")["error"],
                    "retryable": 0,
                }
            },
        ),
    ]:
        with pytest.raises(m.ProductError):
            m.require_error(response, 404, "skill_installation_not_found")


def test_real_error_diagnostic_keeps_status_and_known_code_without_body():
    m = helper()
    with pytest.raises(m.ProductError) as caught:
        m.require_error(
            (
                503,
                {
                    "error": {
                        "code": "skill_installation_dependency_unavailable",
                        "message": "PRIVATE_TEST_BODY",
                        "retryable": True,
                    }
                },
            ),
            412,
            "skill_installation_precondition_failed",
        )
    assert "http=503" in str(caught.value)
    assert "expected_http=412" in str(caught.value)
    assert "code=skill_installation_dependency_unavailable" in str(caught.value)
    assert "PRIVATE_TEST_BODY" not in str(caught.value)
    with pytest.raises(m.ProductError) as caught:
        m.require_error(
            (404, {"error": {"code": "PRIVATE_TEST_BODY"}}),
            404,
            "skill_installation_not_found",
        )
    assert "code=invalid" in str(caught.value)
    assert "PRIVATE_TEST_BODY" not in str(caught.value)
    with pytest.raises(m.ProductError) as caught:
        m.require_error(
            (404, error("skill_installation_not_found")),
            "PRIVATE_TEST_BODY",
            "skill_installation_not_found",
        )
    assert "expected_http=invalid" in str(caught.value)
    assert "PRIVATE_TEST_BODY" not in str(caught.value)


def test_http_wire_has_exact_trusted_headers_delete_no_body_and_closes():
    m = helper()
    sent, closed = [], []

    class Connection:
        def __init__(self, host, port, timeout):
            assert (host, port, timeout) == ("127.0.0.1", 4401, 20)

        def request(self, method, path, body, headers):
            sent.append((method, path, body, headers))

        def getresponse(self):
            class Response:
                status = 200

                def getheaders(self):
                    return [
                        ("content-type", "application/json; charset=utf-8"),
                        ("cache-control", "no-store"),
                        ("x-request-id", sent[-1][3]["x-kokoro-request-id"]),
                    ]

                def read(self, limit):
                    assert limit == 1048577
                    return b'{"data":[]}'

            return Response()

        def close(self):
            closed.append(True)

    with patch.object(m.http.client, "HTTPConnection", Connection):
        client = m.PublicInstallationHttp("http://127.0.0.1:4401", "TOKEN", "SECRET")
        client("DELETE", "/v1/skill-installations/installation-a", key="stable-key")
        client("GET", "/v1/skill-installations?installed=false&enabled=false")
        client(
            "POST",
            "/v1/skill-installations",
            body={"source_ref": "skill:source-a"},
            key="install-key",
        )
    assert len(closed) == 3
    delete, get, post = sent
    assert delete[2] == b""
    assert delete[3]["content-length"] == "0"
    assert "content-type" not in delete[3]
    assert get[2] is None and "idempotency-key" not in get[3]
    assert json.loads(post[2]) == {"source_ref": "skill:source-a"}
    assert all(
        headers["authorization"] == "Bearer TOKEN"
        and headers["x-kokoro-service"] == "web-bff"
        and headers["x-kokoro-internal-secret"] == "SECRET"
        for _, _, _, headers in sent
    )
    assert all(
        not any("tenant" in k or "subject" in k for k in headers)
        for _, _, _, headers in sent
    )


@pytest.mark.parametrize(
    "bad",
    [
        "http://remote.example:4401",
        "http://127.0.0.1:3310",
        "http://user:pw@127.0.0.1:4401",
        "http://127.0.0.1:4401/path",
        "http://127.0.0.1:4401?x=1",
    ],
)
def test_transport_rejects_non_owned_origin_before_socket(bad):
    m = helper()
    with patch.object(m.http.client, "HTTPConnection") as connection:
        with pytest.raises(m.ProductError):
            m.PublicInstallationHttp(bad, "TOKEN", "SECRET")
        connection.assert_not_called()


@pytest.mark.parametrize(
    "headers,raw,status",
    [
        ([("content-type", "text/html")], b"{}", 200),
        (
            [
                ("content-type", "application/json"),
                ("cache-control", "public"),
                ("x-request-id", "request"),
            ],
            b"{}",
            200,
        ),
        (
            [
                ("content-type", "application/json"),
                ("cache-control", "no-store"),
                ("x-request-id", "request"),
                ("x-request-id", "request"),
            ],
            b"{}",
            200,
        ),
        ([], b"{}", 302),
        ([], b"PRIVATE_TEST_BODY", 200),
    ],
)
def test_http_invalid_response_closes_without_body_diagnostics(headers, raw, status):
    m = helper()
    closed = []

    class Connection:
        def __init__(self, *_a, **_kw):
            pass

        def request(self, *_a, **_kw):
            pass

        def getresponse(self):
            class Response:
                def getheaders(self):
                    return headers

                def read(self, _limit):
                    return raw

            response = Response()
            response.status = status
            return response

        def close(self):
            closed.append(True)

    with (
        patch.object(m.http.client, "HTTPConnection", Connection),
        pytest.raises(m.ProductError) as caught,
    ):
        m.PublicInstallationHttp("http://127.0.0.1:4401", "TOKEN", "SECRET")(
            "GET", "/v1/skill-installations"
        )
    assert closed == [True]
    assert "PRIVATE_TEST_BODY" not in str(caught.value)


def transcript():
    a, b = (
        installation(),
        installation("installation-b", "skill:source-b", series_id="series-b"),
    )
    da, db = {**a, "enabled": False}, {**b, "enabled": False}
    ra, rb = (
        {**da, "installed": False, "removed_at": da["updated_at"]},
        {**db, "installed": False, "removed_at": db["updated_at"]},
    )
    responses = [
        (200, {"data": []}),
        (200, ack(a, "installed")),
        (200, ack(a, "installed", True)),
        (200, {"data": a}),
        (200, ack(da, "disabled")),
        (200, ack(da, "disabled", True)),
        (200, {"data": da}),
        (200, ack(a, "installed", True)),
        (200, {"data": da}),
        (200, ack(b, "installed")),
        (200, ack(db, "disabled")),
        (200, {"data": [da], "meta": {"next_cursor": "opaque+/="}}),
        (200, {"data": [db]}),
        (200, ack(ra, "removed")),
        (200, ack(ra, "removed", True)),
        (200, {"data": ra}),
        (200, ack(a, "reinstalled")),
        (200, {"data": a}),
        (200, ack(ra, "removed")),
        (200, ack(rb, "removed")),
        (200, {"data": [ra, rb]}),
        (200, {"data": []}),
    ]
    return responses


def test_sequence_historical_ack_never_overwrites_current_pagination_and_removal():
    m = helper()
    calls, responses = [], transcript()

    def request(method, path, **kwargs):
        calls.append((method, path, deepcopy(kwargs)))
        return responses.pop(0)

    driver = m.ProductInstallationSmoke(request, "owned-run")
    proof = driver.exercise(("skill:source-a", "skill:source-b"))
    assert not responses
    assert proof["five_public_operations"] is True
    assert proof["historical_receipt_current_read"] is True
    assert proof["opaque_two_page_false_filter"] is True
    assert calls[1] == calls[2] == calls[7]
    assert "cursor=opaque%2B%2F%3D" in calls[12][1]
    assert all("expected_revision" not in json.dumps(x) for x in calls)
    assert {x[0] for x in calls} == {"GET", "POST", "PUT", "DELETE"}


def test_sequence_refuses_published_auto_install_and_bad_page_current():
    m = helper()
    for index, replacement in [
        (0, (200, {"data": [installation()]})),
        (8, (200, {"data": installation()})),
        (12, (200, {"data": [installation(enabled=False)]})),
    ]:
        responses = transcript()
        responses[index] = replacement
        with pytest.raises(m.ProductError):
            m.ProductInstallationSmoke(
                lambda *_a, **_kw: responses.pop(0), "owned-run"
            ).exercise(("skill:source-a", "skill:source-b"))


def test_sequence_rejects_identity_drift_inside_valid_mutation_receipt():
    m = helper()
    for field, value in [
        ("source_ref", "skill:other"),
        ("series_id", "series-other"),
        ("revision", "2"),
        ("installed_at", "2026-09-29T12:00:00.000Z"),
    ]:
        responses = transcript()
        changed = installation(enabled=False, **{field: value})
        responses[4] = (200, ack(changed, "disabled"))
        responses[5] = (200, ack(changed, "disabled", True))
        responses[6] = responses[8] = (200, {"data": changed})
        responses[11] = (200, {"data": [changed], "meta": {"next_cursor": "opaque+/="}})
        with pytest.raises(m.ProductError, match="identity_changed"):
            m.ProductInstallationSmoke(
                lambda *_a, **_kw: responses.pop(0), "owned-run"
            ).exercise(("skill:source-a", "skill:source-b"))


def test_unpublished_is_precondition_missing_is_private_not_found_and_revoke_all_five():
    m = helper()
    responses = [
        (412, error("skill_installation_precondition_failed")),
        (404, error("skill_installation_not_found")),
    ]
    calls = []

    def request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return responses.pop(0)

    driver = m.ProductInstallationSmoke(request, "owned-run")
    driver.before_publish("skill:source-a")
    assert len(calls) == 2
    responses.extend([(401, error("session_invalid"))] * 5)
    driver.installation_ids = ("installation-a", "installation-b")
    driver.require_revoked("skill:source-a")
    assert [x[0] for x in calls[2:]] == ["GET", "GET", "POST", "PUT", "DELETE"]
    assert not responses

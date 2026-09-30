"""Evidence for public personal installation APIs in the owned draft composition.

This module owns no service, database, canonical contract or resource cleanup.
It observes BFF public HTTP; importing it performs no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import http.client
import json
import re
import secrets
from typing import Protocol
from urllib.parse import quote, urlencode, urlsplit


COLLECTION = "/v1/skill-installations"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,190}\Z")
SOURCE = re.compile(r"skill:(?!skill:)[A-Za-z0-9][A-Za-z0-9._:-]{0,190}\Z")
FIELDS = frozenset(
    {
        "installation_id",
        "source_ref",
        "series_id",
        "revision",
        "installed",
        "enabled",
        "installed_at",
        "updated_at",
    }
)
CHANGES = frozenset(
    {
        "installed",
        "upgraded",
        "reinstalled",
        "enabled",
        "disabled",
        "removed",
        "unchanged",
    }
)


class ProductError(RuntimeError):
    """Fixed diagnostics only: no credential, private row or response body."""


def preflight(enabled: bool, agent_source: bool) -> None:
    if (
        type(enabled) is not bool
        or type(agent_source) is not bool
        or (enabled and agent_source)
    ):
        raise ProductError("product_installation_mode_invalid")


class Request(Protocol):
    def __call__(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, object] | None = None,
        key: str | None = None,
    ) -> tuple[int, object]: ...


def _instant(value: object) -> datetime:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", value) is None
    ):
        raise ProductError("product_installation_instant_invalid")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ProductError("product_installation_instant_invalid") from None


def require_installation(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) not in (
        FIELDS,
        FIELDS | {"removed_at"},
    ):
        raise ProductError("product_installation_fields_invalid")
    for name, pattern in (
        ("installation_id", ID),
        ("series_id", ID),
        ("source_ref", SOURCE),
    ):
        if not isinstance(value[name], str) or pattern.fullmatch(value[name]) is None:
            raise ProductError("product_installation_identity_invalid")
    revision = value["revision"]
    if (
        not isinstance(revision, str)
        or re.fullmatch(r"[1-9][0-9]{0,19}", revision) is None
        or int(revision) > 18446744073709551615
    ):
        raise ProductError("product_installation_revision_invalid")
    if type(value["installed"]) is not bool or type(value["enabled"]) is not bool:
        raise ProductError("product_installation_state_invalid")
    installed = _instant(value["installed_at"])
    updated = _instant(value["updated_at"])
    removed = _instant(value["removed_at"]) if "removed_at" in value else None
    if (
        updated < installed
        or (removed is not None and removed < installed)
        or (value["installed"] and removed is not None)
        or (not value["installed"] and (value["enabled"] or removed is None))
    ):
        raise ProductError("product_installation_state_invalid")
    return dict(value)


def require_ack(
    response: tuple[int, object], change: str, replayed: bool
) -> dict[str, object]:
    status, body = response
    if status != 200 or not isinstance(body, dict) or set(body) != {"data"}:
        raise ProductError("product_installation_ack_envelope_invalid")
    value = body["data"]
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("change"), str)
        or value.get("change") not in CHANGES
        or value.get("change") != change
        or type(value.get("replayed")) is not bool
        or value["replayed"] is not replayed
    ):
        raise ProductError("product_installation_ack_invalid")
    fields = {"installation", "change", "replayed"}
    if change != "unchanged":
        fields.add("event_id")
        if (
            not isinstance(value.get("event_id"), str)
            or ID.fullmatch(value["event_id"]) is None
        ):
            raise ProductError("product_installation_event_invalid")
    if set(value) != fields:
        raise ProductError("product_installation_ack_fields_invalid")
    return {**value, "installation": require_installation(value["installation"])}


def require_replay(original: dict[str, object], replay: dict[str, object]) -> None:
    if original["replayed"] is not False or replay != {**original, "replayed": True}:
        raise ProductError("product_installation_historical_receipt_changed")


def require_same_identity(
    before: dict[str, object], after: dict[str, object], *, reinstall=False
) -> None:
    fields = ("installation_id", "source_ref", "series_id", "revision")
    if not reinstall:
        fields += ("installed_at",)
    if any(before[name] != after[name] for name in fields) or _instant(
        after["updated_at"]
    ) < _instant(before["updated_at"]):
        raise ProductError("product_installation_mutation_identity_changed")


def require_page(
    response: tuple[int, object],
) -> tuple[list[dict[str, object]], str | None]:
    status, body = response
    if (
        status != 200
        or not isinstance(body, dict)
        or set(body) not in ({"data"}, {"data", "meta"})
        or not isinstance(body["data"], list)
    ):
        raise ProductError("product_installation_page_invalid")
    rows = [require_installation(value) for value in body["data"]]
    ids = [row["installation_id"] for row in rows]
    if len(set(ids)) != len(ids) or ids != sorted(ids):
        raise ProductError("product_installation_page_identity_invalid")
    cursor = None
    if "meta" in body:
        meta = body["meta"]
        if (
            not isinstance(meta, dict)
            or set(meta) != {"next_cursor"}
            or not isinstance(meta["next_cursor"], str)
            or not meta["next_cursor"]
            or len(meta["next_cursor"].encode("utf-8")) > 4096
        ):
            raise ProductError("product_installation_cursor_invalid")
        cursor = meta["next_cursor"]
    return rows, cursor


def require_error(
    response: tuple[int, object], expected_status: int, code: str
) -> None:
    status, body = response
    # Fixed public diagnostic labels only, never arbitrary upstream messages.
    known_codes = {
        "skill_installation_not_found",
        "skill_installation_precondition_failed",
        "skill_installation_forbidden",
        "skill_installation_dependency_unavailable",
        "skill_installation_dependency_timeout",
        "skill_installation_response_invalid",
        "skill_installation_rate_limited",
        "skill_installation_idempotency_conflict",
        "skill_installation_command_in_progress",
        "session_invalid",
        "bff_route_not_found",
        "invalid_skill_installation_request",
        "skill_installation_idempotency_key_required",
    }
    observed = body.get("error") if isinstance(body, dict) else None
    observed = observed.get("code") if isinstance(observed, dict) else None
    safe_code = (
        observed if isinstance(observed, str) and observed in known_codes else "invalid"
    )
    safe_status = status if type(status) is int and 100 <= status <= 599 else "invalid"
    safe_expected = (
        expected_status
        if type(expected_status) is int and 100 <= expected_status <= 599
        else "invalid"
    )
    detail = f" http={safe_status} expected_http={safe_expected} code={safe_code}"
    if (
        status != expected_status
        or not isinstance(body, dict)
        or set(body) != {"error"}
    ):
        raise ProductError("product_installation_error_envelope_invalid" + detail)
    error = body["error"]
    if (
        not isinstance(error, dict)
        or set(error) != {"code", "message", "retryable"}
        or error["code"] != code
        or not isinstance(error["message"], str)
        or not error["message"]
        or error["retryable"] is not False
    ):
        raise ProductError("product_installation_error_invalid" + detail)


@dataclass(frozen=True, slots=True)
class PublicInstallationHttp:
    base: str
    token: str = field(repr=False)
    secret: str = field(repr=False)

    def __post_init__(self) -> None:
        parsed = urlsplit(self.base)
        try:
            port = parsed.port
        except ValueError:
            raise ProductError("product_installation_origin_invalid") from None
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or port in {None, 3310}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ProductError("product_installation_origin_invalid")

    def __call__(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, object] | None = None,
        key: str | None = None,
    ) -> tuple[int, object]:
        if method not in {"GET", "POST", "PUT", "DELETE"} or not path.startswith(
            COLLECTION
        ):
            raise ProductError("product_installation_request_invalid")
        request_id = "product-installation-" + secrets.token_hex(12)
        headers = {
            "authorization": "Bearer " + self.token,
            "x-kokoro-service": "web-bff",
            "x-kokoro-internal-secret": self.secret,
            "x-kokoro-request-id": request_id,
        }
        encoded = None
        if method != "GET":
            if not isinstance(key, str) or not key:
                raise ProductError("product_installation_key_required")
            headers["idempotency-key"] = key
            if method == "DELETE":
                if body is not None:
                    raise ProductError("product_installation_delete_body_invalid")
                encoded = b""
                headers["content-length"] = "0"
            else:
                if not isinstance(body, dict):
                    raise ProductError("product_installation_body_required")
                encoded = json.dumps(body, separators=(",", ":")).encode()
                headers["content-type"] = "application/json"
        elif key is not None or body is not None:
            raise ProductError("product_installation_read_body_invalid")
        parsed = urlsplit(self.base)
        connection = http.client.HTTPConnection(
            parsed.hostname, parsed.port, timeout=20
        )
        try:
            connection.request(method, path, body=encoded, headers=headers)
            response = connection.getresponse()
            response_headers = response.getheaders()
            raw = response.read(1_048_577)
            status = response.status
        except (OSError, http.client.HTTPException):
            raise ProductError("product_installation_transport_failed") from None
        finally:
            connection.close()

        def single(name: str) -> str | None:
            values = [
                value for header, value in response_headers if header.lower() == name
            ]
            return values[0] if len(values) == 1 else None

        content_type = single("content-type")
        if (
            300 <= status < 400
            or len(raw) > 1_048_576
            or single("cache-control") != "no-store"
            or single("x-request-id") != request_id
            or content_type is None
            or content_type.split(";", 1)[0].strip().lower() != "application/json"
        ):
            raise ProductError("product_installation_response_headers_invalid")

        def unique_pairs(pairs):
            result = {}
            for name, value in pairs:
                if name in result:
                    raise ProductError("product_installation_duplicate_json_field")
                result[name] = value
            return result

        try:
            value = json.loads(
                raw,
                object_pairs_hook=unique_pairs,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
            )
        except (ValueError, UnicodeError):
            raise ProductError("product_installation_response_json_invalid") from None
        return status, value


class ProductInstallationSmoke:
    def __init__(self, request: Request, run_id: str):
        if (
            not isinstance(run_id, str)
            or re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id) is None
        ):
            raise ProductError("product_installation_run_identity_invalid")
        self.request = request
        self.run_id = run_id
        self.installation_ids: tuple[str, ...] = ()

    def _key(self, name: str) -> str:
        return "product-" + self.run_id + "-" + name

    def _get(self, identity: str, expected: dict[str, object]) -> None:
        status, body = self.request("GET", COLLECTION + "/" + quote(identity, safe=""))
        if (
            status != 200
            or not isinstance(body, dict)
            or set(body) != {"data"}
            or require_installation(body["data"]) != expected
        ):
            raise ProductError("product_installation_current_read_mismatch")

    def before_publish(self, source: str) -> None:
        require_error(
            self.request(
                "POST",
                COLLECTION,
                body={"source_ref": source},
                key=self._key("unpublished"),
            ),
            412,
            "skill_installation_precondition_failed",
        )
        require_error(
            self.request(
                "POST",
                COLLECTION,
                body={"source_ref": "skill:missing-" + self.run_id},
                key=self._key("missing"),
            ),
            404,
            "skill_installation_not_found",
        )

    def exercise(self, sources: tuple[str, str]) -> dict[str, bool]:
        if len(set(sources)) != 2 or any(
            not isinstance(x, str) or SOURCE.fullmatch(x) is None for x in sources
        ):
            raise ProductError("product_installation_distinct_sources_required")
        if require_page(self.request("GET", COLLECTION)) != ([], None):
            raise ProductError("product_installation_publish_auto_installed")

        def install(source: str, label: str, change="installed"):
            value = require_ack(
                self.request(
                    "POST",
                    COLLECTION,
                    body={"source_ref": source},
                    key=self._key(label),
                ),
                change,
                False,
            )
            row = value["installation"]
            if (
                row["source_ref"] != source
                or row["installed"] is not True
                or row["enabled"] is not True
            ):
                raise ProductError("product_installation_install_state_invalid")
            return value

        first = install(sources[0], "install-a")
        require_replay(
            first,
            require_ack(
                self.request(
                    "POST",
                    COLLECTION,
                    body={"source_ref": sources[0]},
                    key=self._key("install-a"),
                ),
                "installed",
                True,
            ),
        )
        a = first["installation"]
        aid = a["installation_id"]
        self._get(aid, a)
        enabled_path = COLLECTION + "/" + quote(aid, safe="") + "/enabled"
        disabled_ack = require_ack(
            self.request(
                "PUT", enabled_path, body={"enabled": False}, key=self._key("disable-a")
            ),
            "disabled",
            False,
        )
        require_replay(
            disabled_ack,
            require_ack(
                self.request(
                    "PUT",
                    enabled_path,
                    body={"enabled": False},
                    key=self._key("disable-a"),
                ),
                "disabled",
                True,
            ),
        )
        da = disabled_ack["installation"]
        require_same_identity(a, da)
        if (
            da["installation_id"] != aid
            or da["installed"] is not True
            or da["enabled"] is not False
        ):
            raise ProductError("product_installation_disabled_state_invalid")
        self._get(aid, da)
        require_replay(
            first,
            require_ack(
                self.request(
                    "POST",
                    COLLECTION,
                    body={"source_ref": sources[0]},
                    key=self._key("install-a"),
                ),
                "installed",
                True,
            ),
        )
        self._get(aid, da)
        second = install(sources[1], "install-b")
        b = second["installation"]
        bid = b["installation_id"]
        if aid == bid or a["series_id"] == b["series_id"]:
            raise ProductError("product_installation_distinct_series_required")
        self.installation_ids = (aid, bid)
        db = require_ack(
            self.request(
                "PUT",
                COLLECTION + "/" + quote(bid, safe="") + "/enabled",
                body={"enabled": False},
                key=self._key("disable-b"),
            ),
            "disabled",
            False,
        )["installation"]
        require_same_identity(b, db)
        if (
            db["installation_id"] != bid
            or db["installed"] is not True
            or db["enabled"] is not False
        ):
            raise ProductError("product_installation_disabled_state_invalid")
        query = {"installed": "true", "enabled": "false", "limit": "1"}
        rows, cursor = require_page(
            self.request("GET", COLLECTION + "?" + urlencode(query))
        )
        if len(rows) != 1 or cursor is None:
            raise ProductError("product_installation_first_page_invalid")
        last, next_cursor = require_page(
            self.request(
                "GET", COLLECTION + "?" + urlencode({**query, "cursor": cursor})
            )
        )
        expected = sorted([da, db], key=lambda row: row["installation_id"])
        if len(last) != 1 or next_cursor is not None or rows + last != expected:
            raise ProductError("product_installation_pagination_mismatch")

        current_rows = {aid: da, bid: db}

        def remove(identity: str, label: str):
            value = require_ack(
                self.request(
                    "DELETE",
                    COLLECTION + "/" + quote(identity, safe=""),
                    key=self._key(label),
                ),
                "removed",
                False,
            )
            row = value["installation"]
            require_same_identity(current_rows[identity], row)
            if (
                row["installation_id"] != identity
                or row["installed"] is not False
                or row["enabled"] is not False
            ):
                raise ProductError("product_installation_removed_state_invalid")
            current_rows[identity] = row
            return value

        removed = remove(aid, "remove-a")
        require_replay(
            removed,
            require_ack(
                self.request(
                    "DELETE",
                    COLLECTION + "/" + quote(aid, safe=""),
                    key=self._key("remove-a"),
                ),
                "removed",
                True,
            ),
        )
        self._get(aid, removed["installation"])
        reinstalled = install(sources[0], "reinstall-a", "reinstalled")["installation"]
        require_same_identity(removed["installation"], reinstalled, reinstall=True)
        if reinstalled["installation_id"] != aid:
            raise ProductError("product_installation_reinstall_identity_changed")
        self._get(aid, reinstalled)
        current_rows[aid] = reinstalled
        ra = remove(aid, "remove-a-final")["installation"]
        rb = remove(bid, "remove-b-final")["installation"]
        if require_page(
            self.request("GET", COLLECTION + "?installed=false&enabled=false&limit=100")
        ) != (sorted([ra, rb], key=lambda row: row["installation_id"]), None):
            raise ProductError("product_installation_removed_filter_mismatch")
        if require_page(
            self.request("GET", COLLECTION + "?installed=true&limit=100")
        ) != ([], None):
            raise ProductError("product_installation_removed_still_installed")
        return {
            "five_public_operations": True,
            "publish_does_not_install": True,
            "same_key_receipts": True,
            "historical_receipt_current_read": True,
            "opaque_two_page_false_filter": True,
            "removed_current_read": True,
            "reinstalled_stable_identity": True,
        }

    def require_revoked(self, source: str) -> None:
        if len(self.installation_ids) != 2:
            raise ProductError("product_installation_revocation_before_sequence")
        path = COLLECTION + "/" + quote(self.installation_ids[0], safe="")
        for method, target, body, label in (
            ("GET", path, None, None),
            ("GET", COLLECTION, None, None),
            ("POST", COLLECTION, {"source_ref": source}, "revoked-install"),
            ("PUT", path + "/enabled", {"enabled": True}, "revoked-enable"),
            ("DELETE", path, None, "revoked-remove"),
        ):
            require_error(
                self.request(
                    method,
                    target,
                    body=body,
                    key=None if label is None else self._key(label),
                ),
                401,
                "session_invalid",
            )

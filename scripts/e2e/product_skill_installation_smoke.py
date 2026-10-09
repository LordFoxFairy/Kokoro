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
import unicodedata
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
        "display_name",
        "summary",
        "source_status",
        "tags",
        "example_prompts",
        "category_keys",
        "product",
        "skill_updated_at",
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
SOURCE_STATUSES = frozenset({"active", "disabled", "withdrawn", "quarantined"})


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


def _javascript_length(value: str) -> int:
    try:
        return len(value.encode("utf-16-le")) // 2
    except UnicodeEncodeError:
        raise ProductError("product_installation_metadata_invalid") from None


def require_state_version(value: object) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[1-9][0-9]{0,18}", value) is None
        or int(value) > 9223372036854775807
    ):
        raise ProductError("product_state_version_invalid")
    return value


def _iam_ref(value: object) -> dict[str, object]:
    if (
        not isinstance(value, dict)
        or set(value) != {"kind", "id"}
        or not isinstance(value["kind"], str)
        or value["kind"] not in {"user", "organization"}
        or not isinstance(value["id"], str)
        or not 1 <= len(value["id"]) <= 255
        or value["id"] != value["id"].strip()
        or re.search(r"[\x00-\x1f\x7f]", value["id"])
    ):
        raise ProductError("product_publisher_identity_invalid")
    return value


def require_product_fields(row: dict[str, object], *, enriched: bool = True) -> None:
    """Strict current Product facts and display enrichment, not owner/body equality."""
    product = row.get("product")
    required = {"publication_audience", "state_version"}
    optional = {
        "creator_ref",
        "publisher",
        "source_kind",
        "creation_provenance",
        "cover",
        "presentation_kind",
    }
    if (
        not isinstance(product, dict)
        or not required <= set(product) <= required | optional
        or not isinstance(product["publication_audience"], str)
        or product["publication_audience"] not in {"owner", "tenant", "catalog"}
    ):
        raise ProductError("product_facts_invalid")
    require_state_version(product["state_version"])
    if "creator_ref" in product:
        _iam_ref(product["creator_ref"])
    if ("source_kind" in product) != ("publisher" in product):
        raise ProductError("product_source_publisher_invalid")
    publisher = product.get("publisher")
    if "publisher" in product:
        if not isinstance(publisher, dict):
            raise ProductError("product_publisher_invalid")
        if not isinstance(product["source_kind"], str):
            raise ProductError("product_source_kind_invalid")
        if product["source_kind"] in {"personal", "official"}:
            if (
                set(publisher) != {"kind", "iam"}
                or publisher["kind"] != "iam"
                or product.get("presentation_kind") != "first_party"
            ):
                raise ProductError("product_publisher_invalid")
            _iam_ref(publisher["iam"])
        elif product["source_kind"] == "third_party":
            if (
                set(publisher) != {"kind", "github_repository"}
                or publisher["kind"] != "github_repository"
                or product.get("presentation_kind") != "github_repository"
            ):
                raise ProductError("product_publisher_invalid")
            _github_repository(publisher["github_repository"])
        else:
            raise ProductError("product_source_kind_invalid")
    if "presentation_kind" in product and (
        not isinstance(product["presentation_kind"], str)
        or product["presentation_kind"]
        not in {
            "first_party",
            "github_repository",
        }
    ):
        raise ProductError("product_presentation_invalid")
    if "creation_provenance" in product:
        provenance = product["creation_provenance"]
        if not isinstance(provenance, dict):
            raise ProductError("product_provenance_invalid")
        kind = provenance.get("kind")
        if kind == "local":
            if set(provenance) != {"kind"}:
                raise ProductError("product_provenance_invalid")
        elif kind == "ai":
            keys = {
                "kind",
                "conversation_id",
                "run_ref",
                "artifact_ref",
                "source_event_id",
                "source_event_seq",
                "source_event_digest",
                "asset_ref",
                "content_sha256",
                "size_bytes",
                "mime_type",
            }
            if set(provenance) != keys:
                raise ProductError("product_provenance_invalid")
            for name in (
                "conversation_id",
                "run_ref",
                "artifact_ref",
                "source_event_id",
                "asset_ref",
            ):
                _fact_text(provenance[name], 255)
            require_state_version(provenance["source_event_seq"])
            _fact_digest(provenance["source_event_digest"])
            _package_facts(provenance)
        elif kind == "github":
            _github_repository(
                {
                    k: v
                    for k, v in provenance.items()
                    if k
                    not in {"asset_ref", "content_sha256", "size_bytes", "mime_type"}
                }
            )
            if set(provenance) - {
                "kind",
                "repository_id",
                "repository_url",
                "owner_login",
                "owner_url",
                "commit",
                "path",
                "repo_stats",
                "asset_ref",
                "content_sha256",
                "size_bytes",
                "mime_type",
            }:
                raise ProductError("product_provenance_invalid")
            _package_facts(provenance)
            if "asset_ref" in provenance:
                _fact_text(provenance["asset_ref"], 255)
        else:
            raise ProductError("product_provenance_invalid")
    if product.get("source_kind") == "third_party":
        provenance = product.get("creation_provenance", {})
        if provenance.get("kind") != "github" or publisher["github_repository"][
            "repository_id"
        ] != provenance.get("repository_id"):
            raise ProductError("product_provenance_publisher_invalid")
    if "cover" in product:
        cover = product["cover"]
        if (
            not isinstance(cover, dict)
            or set(cover)
            != {
                "asset_ref",
                "content_sha256",
                "size_bytes",
                "mime_type",
                "width",
                "height",
            }
            or not isinstance(cover["mime_type"], str)
            or cover["mime_type"] not in {"image/png", "image/jpeg"}
        ):
            raise ProductError("product_cover_invalid")
        _fact_text(cover["asset_ref"], 255)
        _fact_digest(cover["content_sha256"])
        require_state_version(cover["size_bytes"])
        if int(cover["size_bytes"]) > 2097152 or any(
            type(cover[x]) is not int or not 1 <= cover[x] <= 4096
            for x in ("width", "height")
        ):
            raise ProductError("product_cover_invalid")
    profile = row.get("publisher_profile")
    if enriched and isinstance(publisher, dict) and publisher.get("kind") == "iam":
        if (
            not isinstance(profile, dict)
            or profile.get("kind") != publisher["iam"]["kind"]
            or profile.get("id") != publisher["iam"]["id"]
        ):
            raise ProductError("product_publisher_profile_invalid")
        if profile.get("status") == "found":
            if (
                set(profile) != {"kind", "id", "status", "display_name", "image_url"}
                or not isinstance(profile["display_name"], str)
                or (
                    profile["image_url"] is not None
                    and not isinstance(profile["image_url"], str)
                )
            ):
                raise ProductError("product_publisher_profile_invalid")
        elif profile.get("status") == "missing":
            if set(profile) != {"kind", "id", "status"} or profile["kind"] != "user":
                raise ProductError("product_publisher_profile_invalid")
        else:
            raise ProductError("product_publisher_profile_invalid")
    elif "publisher_profile" in row:
        raise ProductError("product_publisher_profile_invalid")
    examples, categories = row.get("example_prompts"), row.get("category_keys")
    if (
        not isinstance(examples, list)
        or len(examples) > 10
        or any(
            not isinstance(x, str)
            or not 1 <= len(x) <= 1000
            or not x.strip()
            or "\x00" in x
            for x in examples
        )
    ):
        raise ProductError("product_examples_invalid")
    try:
        if sum(len(x.encode("utf-8")) for x in examples) > 16384:
            raise ProductError("product_examples_invalid")
    except UnicodeError:
        raise ProductError("product_examples_invalid") from None
    if (
        not isinstance(categories, list)
        or len(categories) > 8
        or any(
            not isinstance(x, str)
            or x
            not in {
                "programming",
                "data",
                "automation",
                "business",
                "design",
                "media",
                "content",
                "apps",
            }
            for x in categories
        )
        or len(set(categories)) != len(categories)
    ):
        raise ProductError("product_categories_invalid")
    if not isinstance(row.get("skill_updated_at"), str) or not row[
        "skill_updated_at"
    ].endswith("Z"):
        raise ProductError("product_skill_timestamp_invalid")
    _instant(row["skill_updated_at"])


def _fact_text(value: object, limit: int) -> None:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= limit
        or value.strip() != value
        or re.search(r"[\x00-\x1f\x7f\ud800-\udfff]", value)
    ):
        raise ProductError("product_fact_text_invalid")


def _fact_digest(value: object) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        raise ProductError("product_digest_invalid")


def _package_facts(value: dict[str, object]) -> None:
    if (
        not {"content_sha256", "size_bytes", "mime_type"} <= set(value)
        or value["mime_type"] != "application/zip"
    ):
        raise ProductError("product_package_invalid")
    _fact_digest(value["content_sha256"])
    require_state_version(value["size_bytes"])
    if int(value["size_bytes"]) > 33554432:
        raise ProductError("product_package_invalid")


def _github_repository(value: object) -> None:
    required = {
        "kind",
        "repository_id",
        "repository_url",
        "owner_login",
        "owner_url",
        "commit",
        "path",
    }
    if (
        not isinstance(value, dict)
        or not required <= set(value) <= required | {"repo_stats"}
        or value["kind"] != "github"
    ):
        raise ProductError("product_repository_invalid")
    if (
        not isinstance(value["repository_id"], str)
        or re.fullmatch(r"[1-9][0-9]{0,254}", value["repository_id"]) is None
    ):
        raise ProductError("product_repository_invalid")
    _fact_text(value["owner_login"], 255)
    match = (
        re.fullmatch(
            r"https://github.com/([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)/([A-Za-z0-9_.-]+)",
            value["repository_url"],
        )
        if isinstance(value["repository_url"], str)
        else None
    )
    if (
        match is None
        or match[1] != value["owner_login"]
        or match[2] in {".", ".."}
        or value["owner_url"] != "https://github.com/" + value["owner_login"]
        or not isinstance(value["commit"], str)
        or re.fullmatch(r"[a-f0-9]{40}(?:[a-f0-9]{24})?", value["commit"]) is None
    ):
        raise ProductError("product_repository_invalid")
    path = value["path"]
    if path != "":
        _fact_text(path, 2048)
        if "\\" in path or any(x in {"", ".", ".."} for x in path.split("/")):
            raise ProductError("product_repository_invalid")
    if "repo_stats" in value:
        stats = value["repo_stats"]
        if (
            not isinstance(stats, dict)
            or set(stats) != {"stars", "forks", "observed_at", "metadata_source_url"}
            or stats["metadata_source_url"]
            != "https://api.github.com/repos/" + match[1] + "/" + match[2]
        ):
            raise ProductError("product_repository_stats_invalid")
        for x in ("stars", "forks"):
            if (
                not isinstance(stats[x], str)
                or re.fullmatch(r"0|[1-9][0-9]{0,18}", stats[x]) is None
                or int(stats[x]) > 9223372036854775807
            ):
                raise ProductError("product_repository_stats_invalid")
        _instant(stats["observed_at"])


def require_installation(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not FIELDS <= set(value) <= FIELDS | {
        "removed_at",
        "available_update",
        "publisher_profile",
    }:
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
    display_name = value["display_name"]
    summary = value["summary"]
    if (
        not isinstance(display_name, str)
        or not display_name.strip()
        or _javascript_length(display_name) > 255
        or not isinstance(summary, str)
        or _javascript_length(summary) > 65535
        or not isinstance(value["source_status"], str)
        or value["source_status"] not in SOURCE_STATUSES
    ):
        raise ProductError("product_installation_metadata_invalid")
    require_product_fields(value)
    tags = value["tags"]
    if (
        not isinstance(tags, list)
        or len(tags) > 100
        or any(
            not isinstance(x, str) or not x.strip() or _javascript_length(x) > 128
            for x in tags
        )
        or len(set(tags)) != len(tags)
    ):
        raise ProductError("product_installation_tags_invalid")
    if "available_update" in value:
        update = value["available_update"]
        if (
            not isinstance(update, dict)
            or set(update) != {"source_ref", "revision"}
            or not isinstance(update["source_ref"], str)
            or SOURCE.fullmatch(update["source_ref"]) is None
            or update["source_ref"] == value["source_ref"]
            or not isinstance(update["revision"], str)
            or re.fullmatch(r"[1-9][0-9]{0,19}", update["revision"]) is None
            or not int(revision) < int(update["revision"]) <= 18446744073709551615
        ):
            raise ProductError("product_installation_available_update_invalid")
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

    def verify_filtered_pages(
        self, expected: list[dict[str, object]], query_text: str
    ) -> dict[str, bool]:
        """Actual owner HTTP filters before pagination; never filter the returned page locally."""
        expected = sorted(expected, key=lambda row: row["installation_id"])
        query = {
            "installed": "true",
            "enabled": "false",
            "source_kind": "personal",
            "query": query_text,
            "limit": "1",
        }
        rows, cursor = require_page(
            self.request("GET", COLLECTION + "?" + urlencode(query))
        )
        if len(rows) != 1 or cursor is None:
            raise ProductError("product_filtered_first_page_invalid")
        last, after = require_page(
            self.request(
                "GET", COLLECTION + "?" + urlencode({**query, "cursor": cursor})
            )
        )
        if after is not None or rows + last != expected:
            raise ProductError("product_filtered_pagination_invalid")
        for source in ("official", "third_party"):
            if require_page(
                self.request(
                    "GET",
                    COLLECTION
                    + "?"
                    + urlencode(
                        {"source_kind": source, "query": query_text, "limit": "100"}
                    ),
                )
            ) != ([], None):
                raise ProductError("product_source_filter_invalid")
        if require_page(
            self.request(
                "GET",
                COLLECTION
                + "?"
                + urlencode(
                    {
                        "source_kind": "personal",
                        "query": " \t" + query_text + " \n",
                        "limit": "100",
                    }
                ),
            )
        ) != (expected, None):
            raise ProductError("product_trimmed_query_invalid")
        if require_page(
            self.request(
                "GET",
                COLLECTION
                + "?"
                + urlencode(
                    {"source_kind": "personal", "query": "%_\\", "limit": "100"}
                ),
            )
        ) != ([], None):
            raise ProductError("product_literal_query_invalid")
        # Formal Public9.0.1 maps owner cursor input errors to the same strict 400.
        for changes in ({"source_kind": "official"}, {"query": "different-query"}):
            require_error(
                self.request(
                    "GET",
                    COLLECTION
                    + "?"
                    + urlencode({**query, **changes, "cursor": cursor}),
                ),
                400,
                "invalid_skill_installation_request",
            )
        for suffix in (
            "source_kind=unknown",
            "source_kind=personal&source_kind=official",
            "query=%20",
            "query=a&query=b",
            "query=" + "a" * 1025,
        ):
            require_error(
                self.request("GET", COLLECTION + "?" + suffix),
                400,
                "invalid_skill_installation_request",
            )
        return {
            "source_query_before_pagination": True,
            "cursor_filter_binding": True,
            "literal_query": True,
        }

    def verify_package(self, row: dict[str, object], expected_text: str) -> None:
        directory = (
            COLLECTION + "/" + quote(row["installation_id"], safe="") + "/package"
        )
        expected_files = None
        for path, selected in (
            (directory, False),
            (directory + "?file_path=SKILL.md", True),
        ):
            status, body = self.request("GET", path)
            if status != 200 or not isinstance(body, dict) or set(body) != {"data"}:
                raise ProductError("product_package_envelope_invalid")
            data = body["data"]
            if (
                not isinstance(data, dict)
                or set(data) != {"source_ref", "revision", "files", "selected_file"}
                or data["source_ref"] != row["source_ref"]
                or data["revision"] != row["revision"]
                or not isinstance(data["files"], list)
                or len(data["files"]) > 128
            ):
                raise ProductError("product_package_identity_invalid")
            names = []
            for file in data["files"]:
                if (
                    not isinstance(file, dict)
                    or set(file) != {"path", "size_bytes"}
                    or not isinstance(file["path"], str)
                ):
                    raise ProductError("product_package_file_invalid")
                name = file["path"]
                try:
                    encoded = name.encode("utf-8")
                except UnicodeError:
                    raise ProductError("product_package_file_invalid") from None
                if (
                    not name
                    or name.startswith("\ufeff")
                    or len(encoded) > 256
                    or unicodedata.normalize("NFC", name) != name
                    or "\\" in name
                    or "\x00" in name
                    or re.match(r"^[A-Za-z]:", name)
                    or any(x in {"", ".", ".."} for x in name.split("/"))
                    or not isinstance(file["size_bytes"], str)
                    or re.fullmatch(r"0|[1-9][0-9]{0,19}", file["size_bytes"]) is None
                    or int(file["size_bytes"]) > 18446744073709551615
                ):
                    raise ProductError("product_package_file_invalid")
                names.append(name)
            if names != sorted(set(names)) or "SKILL.md" not in names:
                raise ProductError("product_package_directory_invalid")
            if not selected:
                if data["selected_file"] is not None:
                    raise ProductError("product_package_file_presence_invalid")
                expected_files = data["files"]
            else:
                if (
                    data["files"] != expected_files
                    or data["selected_file"]
                    != {"path": "SKILL.md", "text": expected_text}
                    or int(data["files"][names.index("SKILL.md")]["size_bytes"])
                    != len(expected_text.encode("utf-8"))
                ):
                    raise ProductError("product_package_text_invalid")

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

        filter_proof = self.verify_filtered_pages(
            expected, a["display_name"].split()[0]
        )
        self.verify_package(b, "# Sandbox\n\nOwned signed PUT smoke.\n")
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
            "six_public_operations": True,
            **filter_proof,
            "installation_package_exact_text": True,
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
            ("GET", path + "/package?file_path=SKILL.md", None, None),
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

    def reinstall_for_lifecycle(self, source: str) -> dict[str, object]:
        value = require_ack(
            self.request(
                "POST",
                COLLECTION,
                body={"source_ref": source},
                key=self._key("lifecycle-reinstall"),
            ),
            "reinstalled",
            False,
        )
        row = value["installation"]
        if (
            row["source_ref"] != source
            or row["installed"] is not True
            or row["enabled"] is not True
            or row["source_status"] != "active"
        ):
            raise ProductError("product_installation_lifecycle_reinstall_invalid")
        return row

    def require_lifecycle_source_status(
        self, before: dict[str, object], expected: str
    ) -> dict[str, object]:
        status, body = self.request(
            "GET", COLLECTION + "/" + quote(str(before["installation_id"]), safe="")
        )
        if status != 200 or not isinstance(body, dict) or set(body) != {"data"}:
            raise ProductError("product_installation_lifecycle_read_invalid")
        after = require_installation(body["data"])
        if after != {**before, "source_status": expected}:
            raise ProductError("product_installation_lifecycle_identity_changed")
        return after

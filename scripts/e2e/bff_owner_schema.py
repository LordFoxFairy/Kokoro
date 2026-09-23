"""Build the fixed owner-schema PostgreSQL URL used by Root BFF smokes."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


BFF_OWNER_SCHEMA = "kokoro_bff"
_REMOVED_QUERY_KEYS = frozenset({"options", "schema", "search_path"})


def bff_owner_database_url(database_url: str) -> str:
    """Target BFF's schema while retaining unrelated connection parameters."""
    try:
        parsed = urlsplit(database_url)
        if parsed.scheme not in {"postgres", "postgresql"} or parsed.fragment:
            raise ValueError
        # Force urllib to validate a malformed explicit port before returning it.
        parsed.port
    except ValueError:
        raise ValueError("BFF smoke requires an unambiguous PostgreSQL URL") from None
    query = [
        (name, value)
        for name, value in parse_qsl(parsed.query, keep_blank_values=True)
        if name.lower() not in _REMOVED_QUERY_KEYS
    ]
    query.append(("schema", BFF_OWNER_SCHEMA))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), ""))

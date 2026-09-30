"""Explicit private OpenAI-compatible provider profile for owned development runs.

Importing this module does not read credentials or create a network client.
Inventory observations establish reachability, not successful inference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import ssl
import stat
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    ProxyHandler,
    Request,
    build_opener,
)

MAX_CREDENTIAL_BYTES = 16_384
MAX_INVENTORY_BYTES = 1_048_576


class ProviderError(RuntimeError):
    """Sanitized provider boundary failure; never includes upstream content."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ExternalModelConfig:
    base_url: str
    model: str
    api_key: str = field(repr=False)

    def __post_init__(self) -> None:
        try:
            parsed = urlsplit(self.base_url)
            valid = (
                parsed.scheme == "https"
                and bool(parsed.hostname)
                and parsed.port in (None, 443)
                and parsed.path == "/v1"
                and parsed.username is None
                and parsed.password is None
                and "?" not in self.base_url
                and "#" not in self.base_url
                and self.base_url.isascii()
                and all(32 < ord(c) < 127 for c in self.base_url)
            )
        except (ValueError, TypeError, AttributeError):
            valid = False
        if not valid:
            raise ProviderError("external model requires an explicit HTTPS /v1 base")
        if (
            not isinstance(self.model, str)
            or not 1 <= len(self.model) <= 255
            or any(ord(c) <= 32 or ord(c) == 127 for c in self.model)
            or not isinstance(self.api_key, str)
            or not 1 <= len(self.api_key) <= 8192
            or any(ord(c) <= 32 or ord(c) > 126 for c in self.api_key)
        ):
            raise ProviderError("external model profile fields are invalid")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProviderError("provider JSON has duplicate fields")
        result[key] = value
    return result


def load_external(path: Path) -> ExternalModelConfig:
    """Read once from a no-follow private regular file using the same descriptor."""
    descriptor = None
    try:
        if not path.is_absolute():
            raise ProviderError("external model credential path must be absolute")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_size > MAX_CREDENTIAL_BYTES
        ):
            raise ProviderError(
                "external model credential file must be owned and private"
            )
        raw = os.read(descriptor, MAX_CREDENTIAL_BYTES + 1)
        if len(raw) > MAX_CREDENTIAL_BYTES:
            raise ProviderError("external model credential file is oversized")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        if not isinstance(value, dict) or set(value) != {
            "base_url",
            "model",
            "api_key",
        }:
            raise ProviderError("external model credential file has unexpected fields")
        return ExternalModelConfig(**value)
    except (OSError, ValueError, TypeError):
        raise ProviderError("external model credential file is invalid") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def provider_preflight(config: ExternalModelConfig) -> None:
    """Read bounded model inventory with verified TLS; never do paid health inference."""
    try:
        opener = build_opener(
            ProxyHandler({}),
            HTTPSHandler(context=ssl.create_default_context()),
            NoRedirect(),
        )
        request = Request(
            config.base_url + "/models",
            headers={
                "Authorization": "Bearer " + config.api_key,
                "Accept": "application/json",
                "User-Agent": "OpenAI/Python",
            },
        )
        with opener.open(request, timeout=10) as response:
            raw = response.read(MAX_INVENTORY_BYTES + 1)
            if response.status != 200 or len(raw) > MAX_INVENTORY_BYTES:
                raise ProviderError("external model inventory rejected")
        value = json.loads(raw, object_pairs_hook=_unique_object)
        items = value.get("data") if isinstance(value, dict) else None
        if not isinstance(items, list) or any(
            not isinstance(item, dict) for item in items
        ):
            raise ProviderError("external model inventory invalid")
        if sum(item.get("id") == config.model for item in items) != 1:
            raise ProviderError("explicit external model is absent or ambiguous")
    except (OSError, ValueError, TypeError, URLError):
        raise ProviderError("external model inventory unavailable") from None

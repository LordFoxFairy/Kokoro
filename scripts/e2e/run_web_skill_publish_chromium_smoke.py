#!/usr/bin/env python3
"""Skill Chromium prerequisites; intentionally not a full publish UI acceptance.

This stage provisions only a random owned ObjectStore bucket and tests its exact
CORS control plane. No PG/Redis/process resources are created before that gate.
The browser data-plane gate is deferred until exact bucket CORS is supported.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
import secrets
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_bff_skill_draft_sandbox_smoke as sandbox
import run_agent_storage_artifact_smoke as storage


class SmokeError(RuntimeError):
    """Sanitized prerequisite failure."""


def https_origin(value: str) -> str:
    try:
        url = urlsplit(value)
        valid = (
            url.scheme == "https"
            and (
                url.hostname in {"127.0.0.1", "localhost", "::1"}
                or re.fullmatch(r"web-[a-f0-9]{24}\.example\.test", url.hostname or "")
            )
            and url.port is not None
            and url.port != 3310
            and not url.username
            and not url.password
            and not url.path
            and not url.query
            and not url.fragment
        )
    except ValueError:
        valid = False
    if not valid:
        raise SmokeError("isolated HTTPS Web origin required (3310 reserved)")
    return value


def cors_configuration(web_origin: str) -> dict[str, object]:
    return {
        "CORSRules": [
            {
                "AllowedOrigins": [https_origin(web_origin)],
                "AllowedMethods": ["PUT"],
                "AllowedHeaders": ["content-type"],
                "MaxAgeSeconds": 0,
            }
        ]
    }


def configure_cors(s3: object, bucket: str, web_origin: str) -> None:
    expected = cors_configuration(web_origin)
    try:
        s3.put_bucket_cors(Bucket=bucket, CORSConfiguration=expected)
        actual = s3.get_bucket_cors(Bucket=bucket)
    except Exception as error:
        response = getattr(error, "response", {})
        code = response.get("Error", {}).get("Code")
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code == "NotImplemented" and status == 501:
            raise SmokeError("bucket CORS unsupported: NotImplemented (501)") from None
        raise SmokeError("bucket CORS configuration/readback failed") from None
    if actual.get("CORSRules") != expected["CORSRules"]:
        raise SmokeError(
            "bucket CORS readback differs from exact origin/PUT/content-type rule"
        )


def probe_bucket_cors(env: dict[str, str], web_origin: str) -> dict[str, object]:
    """Only delete a bucket after successful create ACK; never touch shared data."""
    https_origin(web_origin)
    for name in (
        "KOKORO_OBJECT_STORE_ENDPOINT",
        "KOKORO_OBJECT_STORE_REGION",
        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID",
        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY",
    ):
        if not env.get(name):
            raise SmokeError(f"{name} is required")
    sandbox.local_http_origin(env["KOKORO_OBJECT_STORE_ENDPOINT"], "ObjectStore")
    if (
        env.get("KOKORO_OBJECT_STORE_PROFILE") != "custom"
        or env.get("KOKORO_OBJECT_STORE_FORCE_PATH_STYLE") != "true"
    ):
        raise SmokeError("explicit custom path-style ObjectStore profile required")
    if env.get("AWS_SESSION_TOKEN") or env.get("KOKORO_OBJECT_STORE_SESSION_TOKEN"):
        raise SmokeError("session credentials unsupported for owned bucket gate")
    bucket = sandbox.owned_bucket_name("kokoro-skill-browser", secrets.token_hex(12))
    s3 = storage._s3(env)
    created = False

    def mark_created() -> None:
        nonlocal created
        created = True

    restore = sandbox.install_sigterm_cleanup_handler()
    try:
        sandbox.require_bucket_absent(s3, bucket)
        sandbox.create_owned_bucket(
            s3, bucket, env["KOKORO_OBJECT_STORE_REGION"], mark_created
        )
        configure_cors(s3, bucket, web_origin)
    finally:
        try:
            if created:
                sandbox.delete_owned_bucket(s3, bucket, storage)
                sandbox.require_bucket_absent(s3, bucket)
        finally:
            restore()
            s3.close()
    return {
        "phase": "bucket-cors-control-plane",
        "exact_cors": True,
        "resources": "clean",
        "ui_publish": "not-run",
        "chromium_put": "not-run",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cors-preflight", action="store_true", required=True)
    parser.add_argument("--web-origin", required=True)
    args = parser.parse_args()
    try:
        result = probe_bucket_cors(dict(os.environ), args.web_origin)
    except (SmokeError, sandbox.SmokeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    except Exception:
        print("ObjectStore prerequisite failed (details suppressed)", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

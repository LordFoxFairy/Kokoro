#!/usr/bin/env python3
"""Drift gate for the Admin browser API contract.

`contract/openapi/admin-web-v1.yaml` is the source of truth for the Admin
browser plane, but a contract nobody checks rots. This parses the Fastify route
registrations out of the Admin server and demands exact set equality with the
document, so a route added, removed or re-verbed on either side fails the build.

Only the browser plane is in scope. Three kinds of route are deliberately
excluded, each because it belongs to a different plane rather than because it is
inconvenient:

* ``/`` — the operator landing page, HTML rather than a JSON API.
* ``/healthz`` and ``/metrics`` — operational endpoints registered by
  platform-kit helpers, consumed by probes and Prometheus, not by the browser.
* ``kokoro.platform.admin.v1.AdminAuthService`` — the privileged
  service-to-service Connect plane. Per the transport spec the two planes stay
  separate and must not share one client package, so mixing them into this
  document would defeat the split.

Exit non-zero on any mismatch. Codes are stable and snake_case.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OPENAPI = ROOT / "contract" / "openapi" / "admin-web-v1.yaml"
DEFAULT_SERVER = (
    ROOT / "kokoro-platform" / "kokoro-platform-admin" / "src" / "server.ts"
)

HTTP_METHODS = ("get", "post", "put", "patch", "delete")

# Routes that exist on the Admin server but are not part of the browser contract.
# Keyed by path so an unexpected method on the same path still fails.
EXCLUDED_PATHS = {
    "/": "operator landing page, serves HTML rather than a JSON API",
    "/healthz": "operational probe registered by platform-kit registerHealthRoute",
    "/metrics": "Prometheus scrape registered by platform-kit registerMetricsRoute",
}

# platform-kit helpers that register routes without a literal app.<verb>( call.
# Listed so a newly introduced helper is reported rather than silently missed.
KNOWN_HELPERS = {
    "registerHealthRoute": "/healthz",
    "registerMetricsRoute": "/metrics",
}

ROUTE_RE = re.compile(
    r"""\bapp\.(?P<method>%s)\(\s*(?P<quote>["'`])(?P<path>[^"'`]+)(?P=quote)"""
    % "|".join(HTTP_METHODS)
)
HELPER_RE = re.compile(r"\b(?P<helper>register[A-Za-z]+Route)\s*\(")


class GateError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def normalise(path: str) -> str:
    """Fastify writes ``:id``; OpenAPI writes ``{id}``."""
    return re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", r"{\1}", path)


def parse_server_routes(source: Path) -> set[tuple[str, str]]:
    if not source.is_file():
        raise GateError("admin_openapi_server_missing", str(source))
    text = source.read_text(encoding="utf-8")

    unknown = {
        m.group("helper")
        for m in HELPER_RE.finditer(text)
        if m.group("helper") not in KNOWN_HELPERS
    }
    if unknown:
        raise GateError(
            "admin_openapi_unknown_route_helper",
            f"{', '.join(sorted(unknown))} registers routes this gate cannot see",
        )

    routes: set[tuple[str, str]] = set()
    for match in ROUTE_RE.finditer(text):
        path = normalise(match.group("path"))
        if path in EXCLUDED_PATHS:
            continue
        routes.add((match.group("method").lower(), path))
    if not routes:
        raise GateError("admin_openapi_no_routes_parsed", str(source))
    return routes


def parse_openapi(document: Path) -> tuple[set[tuple[str, str]], dict]:
    if not document.is_file():
        raise GateError("admin_openapi_document_missing", str(document))
    try:
        spec = yaml.safe_load(document.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - message varies by input
        raise GateError("admin_openapi_document_unparseable", str(exc)) from exc
    if not isinstance(spec, dict):
        raise GateError("admin_openapi_document_unparseable", "top level is not a mapping")

    version = str(spec.get("openapi", ""))
    if not version.startswith("3.1"):
        raise GateError("admin_openapi_version_unsupported", version or "<missing>")

    paths = spec.get("paths")
    if not isinstance(paths, dict) or not paths:
        raise GateError("admin_openapi_paths_missing", str(document))

    operations: set[tuple[str, str]] = set()
    for path, item in paths.items():
        if path in EXCLUDED_PATHS:
            raise GateError("admin_openapi_excluded_path_declared", path)
        if not isinstance(item, dict):
            raise GateError("admin_openapi_path_item_invalid", path)
        for method in item:
            if method.lower() in HTTP_METHODS:
                operations.add((method.lower(), path))
    return operations, spec


def compare(server: set[tuple[str, str]], document: set[tuple[str, str]]) -> None:
    missing = sorted(server - document)
    orphan = sorted(document - server)

    server_paths = {p for _, p in server}
    document_paths = {p for _, p in document}
    both = server_paths & document_paths
    mismatched = sorted(
        p
        for p in both
        if {m for m, q in server if q == p} != {m for m, q in document if q == p}
    )
    if mismatched:
        raise GateError(
            "admin_openapi_method_mismatch",
            "; ".join(
                f"{p} server={sorted(m for m, q in server if q == p)} "
                f"document={sorted(m for m, q in document if q == p)}"
                for p in mismatched
            ),
        )
    if missing:
        raise GateError(
            "admin_openapi_path_missing",
            ", ".join(f"{m.upper()} {p}" for m, p in missing),
        )
    if orphan:
        raise GateError(
            "admin_openapi_path_orphan",
            ", ".join(f"{m.upper()} {p}" for m, p in orphan),
        )


def run(openapi: Path, server: Path) -> str:
    routes = parse_server_routes(server)
    operations, _ = parse_openapi(openapi)
    compare(routes, operations)
    paths = len({p for _, p in operations})
    return (
        f"admin_openapi_ok: {paths} paths, {len(operations)} operations, "
        f"{len(EXCLUDED_PATHS)} excluded non-browser routes"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openapi", type=Path, default=DEFAULT_OPENAPI)
    parser.add_argument("--server", type=Path, default=DEFAULT_SERVER)
    args = parser.parse_args(argv)
    try:
        sys.stdout.write(run(args.openapi, args.server) + "\n")
    except GateError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Drift gate for the Admin browser API contract.

`contract/openapi/admin-web-v1.yaml` is the source of truth for the Admin
browser plane, but a contract nobody checks rots. This parses the Fastify route
registrations out of the Admin server and demands exact set equality with the
document, so a route added, removed or re-verbed on either side fails.

The parser is deliberately loud rather than lenient. Anything it cannot map to
exactly one operation -- a wildcard registration, a non-literal path, an
unrecognised route helper -- stops the gate instead of being skipped, because a
route this file cannot see is precisely the route that drifts unnoticed.

Only the browser plane is in scope. Exclusions are declared as method/path pairs
so an unexpected verb on an excluded path still fails, and an exclusion that
stops matching anything is reported as stale rather than lingering forever:

* ``GET /`` -- the operator landing page, HTML rather than a JSON API.
* ``GET /healthz`` and ``GET /metrics`` -- operational endpoints for probes and
  Prometheus. They are registered by platform-kit helpers rather than by a
  literal call in this file, so they are listed for the document side only.
* ``kokoro.platform.admin.v1.AdminAuthService`` -- the privileged
  service-to-service Connect plane. Per the transport spec the two planes stay
  separate and must not share one client package.

Exit non-zero on any mismatch, reporting every violation found rather than only
the first class encountered.
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

# Every verb Fastify exposes as app.<verb>(). Missing one silently hides routes.
HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")

# Registrations that cannot map to exactly one OpenAPI operation. Seeing one is
# a hard stop: app.all() fans out across verbs and app.route() takes its method
# from an object literal this regex has no business interpreting.
WILDCARD_RE = re.compile(r"\bapp\.(?P<form>all|route)\s*\(")

# Excluded as (method, path). Keyed on both so app.post("/") is not waved
# through by an exclusion that only ever meant GET.
EXCLUDED_ROUTES = {
    ("get", "/"): "operator landing page, serves HTML rather than a JSON API",
    ("get", "/healthz"): "probe endpoint registered by platform-kit registerHealthRoute",
    ("get", "/metrics"): "Prometheus scrape registered by platform-kit registerMetricsRoute",
}

# Exclusions that the server parser can never match, because the route comes
# from a platform-kit helper rather than a literal app.<verb>( call here. They
# still apply to the document side, so they are not reported as stale.
HELPER_PROVIDED = {("get", "/healthz"), ("get", "/metrics")}

# platform-kit helpers that register routes without a literal app.<verb>( call.
KNOWN_HELPERS = {"registerHealthRoute", "registerMetricsRoute"}

# The trailing window is a lookahead so the match consumes only `app.<verb>(`.
# Consuming it would let one registration swallow the next and hide it from
# finditer, which is the exact failure mode this gate exists to prevent.
ROUTE_RE = re.compile(
    r"""\bapp\.(?P<method>%s)\s*\(\s*(?=(?P<rest>.{0,80}))""" % "|".join(HTTP_METHODS),
    re.DOTALL,
)
LITERAL_RE = re.compile(r"""^(?P<quote>["'`])(?P<path>[^"'`]*)(?P=quote)""")
HELPER_RE = re.compile(r"\b(?P<helper>register[A-Za-z]*Routes?)\s*\(")
VERSION_RE = re.compile(r"^3\.1\.\d+$")


class GateError(Exception):
    def __init__(self, code: str, detail: str = "", *, preformatted: bool = False) -> None:
        if preformatted:
            message = detail
        else:
            message = f"{code}: {detail}" if detail else code
        super().__init__(message)
        self.code = code


def _strip_line_comments(text: str) -> str:
    """Blank out `//` comments so commented-out routes are not read as real.

    Only whole-line comments are removed, and `://` is left alone so URLs in
    trailing comments cannot corrupt the offsets.
    """
    out = []
    for line in text.splitlines():
        stripped = line.lstrip()
        out.append("" if stripped.startswith("//") else line)
    return "\n".join(out)


def normalise(path: str) -> str:
    """Fastify writes ``:id``; OpenAPI writes ``{id}``."""
    return re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", r"{\1}", path)


def parse_server_routes(source: Path) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """Return (contract routes, excluded routes actually seen)."""
    if not source.is_file():
        raise GateError("admin_openapi_server_missing", str(source))
    text = _strip_line_comments(source.read_text(encoding="utf-8"))

    wildcards = sorted({m.group("form") for m in WILDCARD_RE.finditer(text)})
    if wildcards:
        raise GateError(
            "admin_openapi_wildcard_registration",
            f"app.{{{','.join(wildcards)}}}() cannot map to one operation; "
            "register each verb explicitly",
        )

    unknown = sorted(
        {
            m.group("helper")
            for m in HELPER_RE.finditer(text)
            if m.group("helper") not in KNOWN_HELPERS
        }
    )
    if unknown:
        raise GateError(
            "admin_openapi_unknown_route_helper",
            f"{', '.join(unknown)} registers routes this gate cannot see",
        )

    routes: set[tuple[str, str]] = set()
    seen_exclusions: set[tuple[str, str]] = set()
    unreadable: list[str] = []
    for match in ROUTE_RE.finditer(text):
        literal = LITERAL_RE.match(match.group("rest").lstrip())
        if literal is None:
            unreadable.append(match.group("method"))
            continue
        entry = (match.group("method").lower(), normalise(literal.group("path")))
        if entry in EXCLUDED_ROUTES:
            seen_exclusions.add(entry)
            continue
        routes.add(entry)

    if unreadable:
        raise GateError(
            "admin_openapi_route_source_unreadable",
            f"app.{{{','.join(sorted(set(unreadable)))}}}() called without a literal "
            "path; the gate cannot verify a route it cannot read",
        )
    if not routes:
        raise GateError("admin_openapi_no_routes_parsed", str(source))
    return routes, seen_exclusions


def parse_openapi(document: Path) -> set[tuple[str, str]]:
    if not document.is_file():
        raise GateError("admin_openapi_document_missing", str(document))
    try:
        spec = yaml.safe_load(document.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - message varies by input
        raise GateError("admin_openapi_document_unparseable", str(exc)) from exc
    if not isinstance(spec, dict):
        raise GateError("admin_openapi_document_unparseable", "top level is not a mapping")

    version = str(spec.get("openapi", ""))
    if not VERSION_RE.match(version):
        raise GateError("admin_openapi_version_unsupported", version or "<missing>")

    paths = spec.get("paths")
    if not isinstance(paths, dict) or not paths:
        raise GateError("admin_openapi_paths_missing", str(document))

    operations: set[tuple[str, str]] = set()
    for path, item in paths.items():
        if not isinstance(item, dict):
            raise GateError("admin_openapi_path_item_invalid", str(path))
        for method in item:
            if method.lower() not in HTTP_METHODS:
                continue
            entry = (method.lower(), path)
            if entry in EXCLUDED_ROUTES:
                raise GateError(
                    "admin_openapi_excluded_path_declared",
                    f"{method.upper()} {path} is out of scope: {EXCLUDED_ROUTES[entry]}",
                )
            operations.add(entry)
    return operations


def compare(server: set[tuple[str, str]], document: set[tuple[str, str]]) -> None:
    """Report every violation at once; one class at a time hides the rest."""
    problems: list[str] = []

    server_paths = {p for _, p in server}
    document_paths = {p for _, p in document}
    for path in sorted(server_paths & document_paths):
        smeth = {m for m, q in server if q == path}
        dmeth = {m for m, q in document if q == path}
        if smeth != dmeth:
            problems.append(
                f"admin_openapi_method_mismatch: {path} "
                f"server={sorted(smeth)} document={sorted(dmeth)}"
            )

    missing = sorted(server - document)
    if missing:
        problems.append(
            "admin_openapi_path_missing: "
            + ", ".join(f"{m.upper()} {p}" for m, p in missing)
        )
    orphan = sorted(document - server)
    if orphan:
        problems.append(
            "admin_openapi_path_orphan: "
            + ", ".join(f"{m.upper()} {p}" for m, p in orphan)
        )
    if problems:
        # Each entry already carries its own code, so report them verbatim
        # rather than prefixing the first code onto the combined message.
        raise GateError(
            problems[0].split(":", 1)[0], "; ".join(problems), preformatted=True
        )


def check_stale_exclusions(seen: set[tuple[str, str]]) -> None:
    expected = set(EXCLUDED_ROUTES) - HELPER_PROVIDED
    stale = sorted(expected - seen)
    if stale:
        raise GateError(
            "admin_openapi_stale_exclusion",
            ", ".join(f"{m.upper()} {p}" for m, p in stale)
            + " is excluded but no longer registered; drop the exclusion",
        )


def run(openapi: Path, server: Path) -> str:
    routes, seen_exclusions = parse_server_routes(server)
    operations = parse_openapi(openapi)
    compare(routes, operations)
    check_stale_exclusions(seen_exclusions)
    paths = len({p for _, p in operations})
    return (
        f"admin_openapi_ok: {paths} paths, {len(operations)} operations, "
        f"{len(seen_exclusions)} excluded at source, "
        f"{len(HELPER_PROVIDED)} helper-registered"
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

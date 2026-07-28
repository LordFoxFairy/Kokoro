#!/usr/bin/env python3
"""Drift gate for the Admin browser API contract.

`contract/openapi/admin-web-v1.yaml` is the source of truth for the Admin
browser plane, but a contract nobody checks rots. This parses the Fastify route
registrations out of the Admin server and demands exact set equality with the
document, so a route added, removed or re-verbed on either side fails. It also
proves the browser can reach exactly that operation set through one of two
mutually exclusive authorities: an enumerated transparent Next rewrite, or an
explicit local Route Handler whose exported HTTP methods are parsed literally.

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
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OPENAPI = ROOT / "contract" / "openapi" / "admin-web-v1.yaml"
DEFAULT_SERVER = (
    ROOT / "kokoro-platform" / "kokoro-platform-admin" / "src" / "server.ts"
)
DEFAULT_PROXY = ROOT / "kokoro-web" / "apps" / "admin" / "next.config.ts"
DEFAULT_LOCAL_ROUTES = ROOT / "kokoro-web" / "apps" / "admin" / "app" / "api"
SOURCE_INSPECTOR = ROOT / "scripts" / "contract" / "inspect_admin_browser_sources.mjs"
INSPECTION_GATEWAY_URL = "http://kokoro-contract-gateway.invalid"

# Fetch permits these methods on the Admin browser plane. OpenAPI 3.1 and
# Fastify also understand TRACE, so it is recognized separately and rejected
# rather than being silently ignored.
BROWSER_HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
OPENAPI_HTTP_METHODS = (*BROWSER_HTTP_METHODS, "trace")

# Excluded as (method, path). Keyed on both so app.post("/") is not waved
# through by an exclusion that only ever meant GET.
EXCLUDED_ROUTES = {
    ("get", "/"): "operator landing page, serves HTML rather than a JSON API",
    (
        "get",
        "/healthz",
    ): "probe endpoint registered by platform-kit registerHealthRoute",
    (
        "get",
        "/metrics",
    ): "Prometheus scrape registered by platform-kit registerMetricsRoute",
}

# Exclusions that the server parser can never match, because the route comes
# from a platform-kit helper rather than a literal app.<verb>( call here. They
# still apply to the document side, so they are not reported as stale.
HELPER_PROVIDED = {("get", "/healthz"), ("get", "/metrics")}

# platform-kit helpers that register routes without a literal app.<verb>( call.
KNOWN_HELPERS = {"registerHealthRoute", "registerMetricsRoute"}

VERSION_RE = re.compile(r"^3\.1\.\d+$")

# The Admin app transparently forwards exactly these paths. Security-filtered
# paths use local Route Handlers instead; the two authorities are combined and
# checked as a method/path operation set, never as competing path lists.
PROXY_DYNAMIC_SEGMENT_RE = re.compile(r":[A-Za-z_][A-Za-z0-9_]*")
LOCAL_ROUTE_FILE_RE = re.compile(r"^route\.(?:[cm]?[jt]sx?)$")
LOCAL_EXPORTED_NAME_RE = re.compile(r"^[A-Z]+$")
LOCAL_DYNAMIC_SEGMENT_RE = re.compile(r"^\[(?P<name>[A-Za-z_][A-Za-z0-9_]*)\]$")

# Auth.js owns this local route; it does not forward to Platform and therefore is
# outside the Platform Admin browser contract checked here.
LOCAL_ROUTE_EXCLUSIONS = {
    "auth/[...nextauth]/route.ts": "Auth.js session endpoint, not a Platform gateway route",
}


class GateError(Exception):
    def __init__(
        self, code: str, detail: str = "", *, preformatted: bool = False
    ) -> None:
        if preformatted:
            message = detail
        else:
            message = f"{code}: {detail}" if detail else code
        super().__init__(message)
        self.code = code


def _inspect_typescript(mode: str, sources: list[Path], error_code: str) -> object:
    if not SOURCE_INSPECTOR.is_file():
        raise GateError(error_code, f"source inspector missing: {SOURCE_INSPECTOR}")
    node = shutil.which("node")
    if node is None:
        raise GateError(error_code, "node executable is unavailable")
    environment = {
        "KOKORO_GATEWAY_URL": INSPECTION_GATEWAY_URL,
        "NODE_ENV": "production",
    }
    try:
        completed = subprocess.run(
            [
                node,
                "--no-warnings",
                "--experimental-strip-types",
                str(SOURCE_INSPECTOR),
                mode,
                *(str(source) for source in sources),
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateError(error_code, f"source inspection failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        raise GateError(
            error_code,
            detail[-1] if detail else f"source inspector exited {completed.returncode}",
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GateError(error_code, "source inspector returned invalid JSON") from exc


def _normalise_proxy_path(path: str) -> str:
    if not path.startswith("/") or "\\" in path or "?" in path or "#" in path:
        raise GateError("admin_openapi_proxy_path_unreadable", path)
    parts: list[str] = []
    for segment in path.split("/")[1:]:
        if not segment or segment in {".", ".."}:
            raise GateError("admin_openapi_proxy_path_unreadable", path)
        if segment.startswith(":"):
            if PROXY_DYNAMIC_SEGMENT_RE.fullmatch(segment) is None:
                raise GateError("admin_openapi_proxy_path_unreadable", path)
            parts.append("{" + segment[1:] + "}")
            continue
        if any(marker in segment for marker in (":", "*", "[", "]", "{", "}")):
            raise GateError("admin_openapi_proxy_path_unreadable", path)
        parts.append(segment)
    return "/" + "/".join(parts)


def normalise(path: str) -> str:
    """Fastify writes ``:id``; OpenAPI writes ``{id}``."""
    return re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", r"{\1}", path)


def parse_server_routes(
    source: Path,
) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """Return provider routes and exclusions proven from the TypeScript AST."""
    if not source.is_file():
        raise GateError("admin_openapi_server_missing", str(source))
    inspected = _inspect_typescript(
        "server-routes", [source], "admin_openapi_route_source_unreadable"
    )
    expected_keys = {
        "customMethodRegistrations",
        "methodReferences",
        "pluginRegisters",
        "routeHelpers",
        "routes",
        "unreadableMethods",
        "unsupportedReceivers",
        "unsupportedBrowserMethods",
        "wildcards",
    }
    if not isinstance(inspected, dict) or set(inspected) != expected_keys:
        raise GateError(
            "admin_openapi_route_source_unreadable",
            "TypeScript inspector returned an invalid provider route inventory",
        )

    list_fields = {
        key: value
        for key in expected_keys - {"routes"}
        if isinstance((value := inspected[key]), list)
        and all(isinstance(entry, str) for entry in value)
    }
    if len(list_fields) != len(expected_keys) - 1 or not isinstance(
        inspected["routes"], list
    ):
        raise GateError(
            "admin_openapi_route_source_unreadable",
            "TypeScript inspector returned malformed provider route fields",
        )

    wildcards = sorted(set(list_fields["wildcards"]))
    if wildcards:
        raise GateError(
            "admin_openapi_wildcard_registration",
            f"app.{{{','.join(wildcards)}}}() cannot map to one operation; "
            "register each verb explicitly",
        )

    unknown = sorted(set(list_fields["routeHelpers"]) - KNOWN_HELPERS)
    if unknown:
        raise GateError(
            "admin_openapi_unknown_route_helper",
            f"{', '.join(unknown)} registers routes this gate cannot see",
        )

    unsupported_receivers = sorted(set(list_fields["unsupportedReceivers"]))
    if unsupported_receivers:
        raise GateError(
            "admin_openapi_route_receiver_unreadable",
            ", ".join(unsupported_receivers)
            + " may register a route through an unverified Fastify receiver",
        )

    plugin_registers = sorted(set(list_fields["pluginRegisters"]))
    if plugin_registers:
        raise GateError(
            "admin_openapi_route_plugin_unreadable",
            ", ".join(plugin_registers)
            + " may add routes outside the provider inventory",
        )

    custom_methods = sorted(set(list_fields["customMethodRegistrations"]))
    if custom_methods:
        raise GateError(
            "admin_openapi_route_custom_method_unreadable",
            ", ".join(custom_methods)
            + " may add an HTTP shorthand outside the recognized method set",
        )

    method_references = sorted(set(list_fields["methodReferences"]))
    if method_references:
        raise GateError(
            "admin_openapi_route_method_reference_unreadable",
            ", ".join(method_references)
            + " references a Fastify route method outside a direct registration call",
        )

    unsupported_browser_methods = sorted(set(list_fields["unsupportedBrowserMethods"]))
    if unsupported_browser_methods:
        raise GateError(
            "admin_openapi_browser_method_unsupported",
            ", ".join(method.upper() for method in unsupported_browser_methods)
            + " is not permitted by the Fetch browser transport",
        )

    unreadable = sorted(set(list_fields["unreadableMethods"]))
    if unreadable:
        raise GateError(
            "admin_openapi_route_source_unreadable",
            f"app.{{{','.join(unreadable)}}}() called without a literal string path; "
            "the gate cannot verify a route it cannot read",
        )

    route_entries: list[tuple[str, str]] = []
    for route in inspected["routes"]:
        if (
            not isinstance(route, dict)
            or set(route) != {"method", "path"}
            or not isinstance(route["method"], str)
            or not isinstance(route["path"], str)
            or route["method"] not in BROWSER_HTTP_METHODS
        ):
            raise GateError(
                "admin_openapi_route_source_unreadable",
                "TypeScript inspector returned a malformed provider route",
            )
        route_entries.append((route["method"], normalise(route["path"])))

    duplicates = sorted(
        {entry for entry in route_entries if route_entries.count(entry) > 1}
    )
    if duplicates:
        raise GateError(
            "admin_openapi_route_duplicate",
            ", ".join(f"{method.upper()} {path}" for method, path in duplicates),
        )

    routes: set[tuple[str, str]] = set()
    seen_exclusions: set[tuple[str, str]] = set()
    for entry in route_entries:
        if entry in EXCLUDED_ROUTES:
            seen_exclusions.add(entry)
            continue
        routes.add(entry)
    if not routes:
        raise GateError("admin_openapi_no_routes_parsed", str(source))
    return routes, seen_exclusions


def parse_proxy_paths(config: Path) -> set[str]:
    """Evaluate Next's real rewrite result and return its transparent sources."""
    if not config.is_file():
        raise GateError("admin_openapi_proxy_config_missing", str(config))
    inspected = _inspect_typescript(
        "rewrites", [config], "admin_openapi_proxy_wiring_unreadable"
    )
    if not isinstance(inspected, dict) or set(inspected) != {"fallback"}:
        raise GateError(
            "admin_openapi_proxy_wiring_unreadable",
            "rewrites() must return exactly one fallback array",
        )
    fallback = inspected["fallback"]
    if not isinstance(fallback, list) or not fallback:
        raise GateError(
            "admin_openapi_proxy_wiring_unreadable",
            "rewrites().fallback must be a non-empty array",
        )
    paths: list[str] = []
    for entry in fallback:
        if not isinstance(entry, dict) or set(entry) != {"source", "destination"}:
            raise GateError(
                "admin_openapi_proxy_wiring_unreadable",
                "each fallback rewrite must contain exactly source and destination",
            )
        source = entry["source"]
        destination = entry["destination"]
        if not isinstance(source, str) or not isinstance(destination, str):
            raise GateError(
                "admin_openapi_proxy_wiring_unreadable",
                "fallback rewrite source and destination must be strings",
            )
        if destination != f"{INSPECTION_GATEWAY_URL}{source}":
            raise GateError(
                "admin_openapi_proxy_destination_unreadable",
                f"{source} does not map exactly to the configured gateway",
            )
        paths.append(_normalise_proxy_path(source))
    duplicates = sorted({path for path in paths if paths.count(path) > 1})
    if duplicates:
        raise GateError("admin_openapi_proxy_path_duplicate", ", ".join(duplicates))
    return set(paths)


def _local_route_path(relative: Path) -> str:
    parts: list[str] = ["api"]
    for segment in relative.parts[:-1]:
        dynamic = LOCAL_DYNAMIC_SEGMENT_RE.match(segment)
        if dynamic is not None:
            parts.append("{" + dynamic.group("name") + "}")
            continue
        if segment.startswith("(") and segment.endswith(")"):
            # Next route groups organise source without changing the URL.
            continue
        if segment.startswith("[") or segment.endswith("]") or segment.startswith("@"):
            raise GateError(
                "admin_openapi_local_route_unreadable",
                f"{relative.as_posix()} uses a catch-all, optional, or parallel segment",
            )
        parts.append(segment)
    return "/" + "/".join(parts)


def parse_local_routes(root: Path) -> set[tuple[str, str]]:
    """Read top-level handler exports from Admin Next Route Handlers via TS AST."""
    if not root.is_dir():
        return set()

    operations: set[tuple[str, str]] = set()
    sources_by_path: dict[str, Path] = {}
    route_sources: list[tuple[Path, str, str]] = []
    candidates = sorted(
        path
        for path in root.rglob("route.*")
        if path.is_file() and LOCAL_ROUTE_FILE_RE.match(path.name)
    )
    for source in candidates:
        relative = source.relative_to(root)
        relative_name = relative.as_posix()
        if relative_name in LOCAL_ROUTE_EXCLUSIONS:
            continue
        path = _local_route_path(relative)
        previous = sources_by_path.get(path)
        if previous is not None:
            raise GateError(
                "admin_openapi_local_route_duplicate",
                f"{path} is declared by {previous.relative_to(root).as_posix()} and {relative_name}",
            )
        sources_by_path[path] = source
        route_sources.append((source, relative_name, path))

    if not route_sources:
        return operations
    inspected = _inspect_typescript(
        "route-exports",
        [source for source, _, _ in route_sources],
        "admin_openapi_local_route_unreadable",
    )
    if not isinstance(inspected, list) or len(inspected) != len(route_sources):
        raise GateError(
            "admin_openapi_local_route_unreadable",
            "TypeScript inspector returned an incomplete route inventory",
        )

    for (source, relative_name, path), result in zip(
        route_sources, inspected, strict=True
    ):
        if (
            not isinstance(result, dict)
            or set(result) != {"exports", "file"}
            or result["file"] != str(source.resolve())
            or not isinstance(result["exports"], list)
        ):
            raise GateError(
                "admin_openapi_local_route_unreadable",
                f"invalid TypeScript inspection result for {relative_name}",
            )
        declared: list[str] = []
        for exported in result["exports"]:
            if (
                not isinstance(exported, dict)
                or set(exported) != {"kind", "name"}
                or not isinstance(exported["kind"], str)
                or not isinstance(exported["name"], str)
            ):
                raise GateError(
                    "admin_openapi_local_route_unreadable",
                    f"invalid TypeScript export result for {relative_name}",
                )
            if exported["kind"] == "export-all":
                raise GateError(
                    "admin_openapi_local_route_unreadable",
                    f"{relative_name} uses an export-all whose HTTP methods cannot be proven",
                )
            if LOCAL_EXPORTED_NAME_RE.fullmatch(exported["name"]) is None:
                continue
            if exported["kind"] not in {"function", "variable-function"}:
                raise GateError(
                    "admin_openapi_local_route_unreadable",
                    f"{relative_name} does not declare {exported['name']} as a local callable",
                )
            declared.append(exported["name"].lower())

        unsupported = sorted(
            {method for method in declared if method not in BROWSER_HTTP_METHODS}
        )
        if unsupported:
            raise GateError(
                "admin_openapi_local_method_unsupported",
                f"{relative_name} exports {', '.join(method.upper() for method in unsupported)}",
            )
        if not declared:
            raise GateError(
                "admin_openapi_local_route_unreadable",
                f"{relative_name} has no literal exported HTTP handler",
            )
        duplicates = sorted(
            {method for method in declared if declared.count(method) > 1}
        )
        if duplicates:
            raise GateError(
                "admin_openapi_local_method_duplicate",
                f"{relative_name} exports {', '.join(method.upper() for method in duplicates)} more than once",
            )
        operations.update((method, path) for method in declared)
    return operations


def compare_browser_authorities(
    document: set[tuple[str, str]],
    server: set[tuple[str, str]],
    proxy_paths: set[str],
    local: set[tuple[str, str]],
) -> tuple[int, int]:
    document_paths = {path for _, path in document}
    local_paths = {path for _, path in local}

    proxy_orphans = sorted(proxy_paths - document_paths)
    if proxy_orphans:
        raise GateError("admin_openapi_proxy_path_orphan", ", ".join(proxy_orphans))

    duplicate_authority = sorted(proxy_paths & local_paths)
    if duplicate_authority:
        raise GateError(
            "admin_openapi_browser_authority_duplicate",
            ", ".join(duplicate_authority)
            + " is owned by both a transparent rewrite and a local Route Handler",
        )

    local_orphan_paths = sorted(local_paths - document_paths)
    if local_orphan_paths:
        orphan_operations = sorted(
            (method, path) for method, path in local if path in set(local_orphan_paths)
        )
        raise GateError(
            "admin_openapi_local_operation_orphan",
            ", ".join(f"{method.upper()} {path}" for method, path in orphan_operations),
        )

    for path in sorted(local_paths & document_paths):
        local_methods = {method for method, candidate in local if candidate == path}
        document_methods = {
            method for method, candidate in document if candidate == path
        }
        if local_methods != document_methods:
            raise GateError(
                "admin_openapi_local_method_mismatch",
                f"{path} local={sorted(local_methods)} document={sorted(document_methods)}",
            )

    # A transparent rewrite intentionally has no method policy; the Platform
    # provider's registered methods are its exact semantic operation set.
    transparent = {(method, path) for method, path in server if path in proxy_paths}
    browser = transparent | local
    missing = sorted(document - browser)
    if missing:
        raise GateError(
            "admin_openapi_browser_operation_missing",
            ", ".join(f"{method.upper()} {path}" for method, path in missing),
        )
    orphan = sorted(browser - document)
    if orphan:  # Defensive: the targeted checks above should identify the owner first.
        raise GateError(
            "admin_openapi_browser_operation_orphan",
            ", ".join(f"{method.upper()} {path}" for method, path in orphan),
        )
    return len(transparent), len(local)


def parse_openapi(document: Path) -> set[tuple[str, str]]:
    if not document.is_file():
        raise GateError("admin_openapi_document_missing", str(document))
    try:
        spec = yaml.safe_load(document.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - message varies by input
        raise GateError("admin_openapi_document_unparseable", str(exc)) from exc
    if not isinstance(spec, dict):
        raise GateError(
            "admin_openapi_document_unparseable", "top level is not a mapping"
        )

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
            lower_method = method.lower()
            if lower_method not in OPENAPI_HTTP_METHODS:
                continue
            if lower_method not in BROWSER_HTTP_METHODS:
                raise GateError(
                    "admin_openapi_browser_method_unsupported",
                    f"{method.upper()} {path} is not permitted by the Fetch browser transport",
                )
            entry = (lower_method, path)
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


def run(
    openapi: Path,
    server: Path,
    proxy: Path | None = None,
    local_routes: Path | None = None,
) -> str:
    routes, seen_exclusions = parse_server_routes(server)
    operations = parse_openapi(openapi)
    compare(routes, operations)
    check_stale_exclusions(seen_exclusions)
    document_paths = {p for _, p in operations}
    transparent = 0
    local = 0
    if proxy is not None:
        proxy_paths = parse_proxy_paths(proxy)
        local_operations = parse_local_routes(
            local_routes if local_routes is not None else proxy.parent / "app" / "api"
        )
        transparent, local = compare_browser_authorities(
            operations, routes, proxy_paths, local_operations
        )
    paths = len(document_paths)
    return (
        f"admin_openapi_ok: {paths} paths, {len(operations)} operations, "
        f"{len(seen_exclusions)} excluded at source, "
        f"{len(HELPER_PROVIDED)} helper-registered, "
        f"{transparent} transparent browser operations, "
        f"{local} local BFF operations"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openapi", type=Path, default=DEFAULT_OPENAPI)
    parser.add_argument("--server", type=Path, default=DEFAULT_SERVER)
    parser.add_argument("--proxy", type=Path, default=DEFAULT_PROXY)
    parser.add_argument("--local-routes", type=Path, default=DEFAULT_LOCAL_ROUTES)
    args = parser.parse_args(argv)
    try:
        sys.stdout.write(
            run(args.openapi, args.server, args.proxy, args.local_routes) + "\n"
        )
    except GateError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

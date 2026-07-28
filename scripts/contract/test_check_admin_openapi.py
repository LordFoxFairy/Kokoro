"""Negative fixtures for the Admin browser contract drift gate.

Each case proves the gate rejects a specific way the contract and the server can
drift apart. A gate that only ever passes is indistinguishable from no gate.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from check_admin_openapi import GateError, run

SERVER = textwrap.dedent(
    """
    export function createAdminServer() {
      registerHealthRoute(app, "kokoro-platform-admin");
      registerMetricsRoute(app, "kokoro-platform-admin");
      app.get("/", async (_request, reply) => reply.type("text/html").send("<html/>"));
      app.get("/api/me", async (request, reply) => sendData(reply, {}));
      app.post("/api/operators/:id/status", async (request, reply) => sendData(reply, {}));
    }
    """
)

OPENAPI = textwrap.dedent(
    """
    openapi: 3.1.0
    info:
      title: Kokoro Admin Browser API
      version: 1.0.0
    paths:
      /api/me:
        get:
          responses:
            "200":
              description: ok
      /api/operators/{id}/status:
        post:
          responses:
            "200":
              description: ok
    """
)


def write(
    tmp_path: Path, server: str = SERVER, openapi: str = OPENAPI
) -> tuple[Path, Path]:
    s = tmp_path / "server.ts"
    o = tmp_path / "admin-web-v1.yaml"
    s.write_text(server, encoding="utf-8")
    o.write_text(openapi, encoding="utf-8")
    return o, s


def test_matching_contract_passes(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    line = run(openapi, server)
    assert line.startswith("admin_openapi_ok:")
    assert "2 paths, 2 operations" in line


def test_fastify_param_syntax_is_normalised(tmp_path: Path) -> None:
    """`:id` and `{id}` denote the same route and must not be reported as drift."""
    openapi, server = write(tmp_path)
    assert "admin_openapi_ok" in run(openapi, server)


def test_route_absent_from_document_fails(tmp_path: Path) -> None:
    openapi, server = write(
        tmp_path,
        server=SERVER + '\napp.get("/api/audit", async () => {});\n',
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_path_missing"
    assert "/api/audit" in str(excinfo.value)


def test_document_route_absent_from_server_fails(tmp_path: Path) -> None:
    openapi, server = write(
        tmp_path,
        openapi=OPENAPI
        + '  /api/ghost:\n    get:\n      responses:\n        "200":\n          description: ok\n',
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_path_orphan"
    assert "/api/ghost" in str(excinfo.value)


def test_method_mismatch_fails(tmp_path: Path) -> None:
    openapi, server = write(
        tmp_path,
        openapi=OPENAPI.replace("  /api/me:\n    get:", "  /api/me:\n    post:"),
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_method_mismatch"


def test_method_mismatch_fixture_actually_mutates() -> None:
    """Guards the fixture itself: a no-op replace would make the case vacuous."""
    mutated = OPENAPI.replace("  /api/me:\n    get:", "  /api/me:\n    post:")
    assert mutated != OPENAPI


def test_openapi_30_is_rejected(tmp_path: Path) -> None:
    openapi, server = write(tmp_path, openapi=OPENAPI.replace("3.1.0", "3.0.3"))
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_version_unsupported"


def test_excluded_route_declared_in_document_fails(tmp_path: Path) -> None:
    """The landing page is out of scope; silently documenting it hides the split."""
    openapi, server = write(
        tmp_path,
        openapi=OPENAPI
        + '  /:\n    get:\n      responses:\n        "200":\n          description: ok\n',
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_excluded_path_declared"


def test_unknown_route_helper_fails(tmp_path: Path) -> None:
    """A new platform-kit helper registers routes this gate cannot see."""
    openapi, server = write(
        tmp_path,
        server=SERVER + '\nregisterDebugRoute(app, "kokoro-platform-admin");\n',
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_unknown_route_helper"


def test_unparseable_document_fails(tmp_path: Path) -> None:
    openapi, server = write(tmp_path, openapi="openapi: [3.1.0\n  broken:\n")
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_document_unparseable"


def test_missing_server_source_fails(tmp_path: Path) -> None:
    openapi, _ = write(tmp_path)
    with pytest.raises(GateError) as excinfo:
        run(openapi, tmp_path / "absent.ts")
    assert excinfo.value.code == "admin_openapi_server_missing"


# --- fail-open holes found by adversarial review of this gate ------------------
# Each case adds a real browser route to the server and leaves the document
# alone. Before these fixes every one of them exited 0.


@pytest.mark.parametrize("verb", ["head", "options"])
def test_less_common_verbs_are_not_invisible(tmp_path: Path, verb: str) -> None:
    openapi, server = write(
        tmp_path, server=SERVER + f'\napp.{verb}("/api/ghost", async () => {{}});\n'
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_path_missing"


@pytest.mark.parametrize("form", ["all", "route"])
def test_wildcard_registration_stops_the_gate(tmp_path: Path, form: str) -> None:
    """app.all()/app.route() cannot map to one operation, so stop rather than skip."""
    snippet = (
        '\napp.all("/api/ghost", async () => {});\n'
        if form == "all"
        else '\napp.route({ method: "POST", url: "/api/ghost" });\n'
    )
    openapi, server = write(tmp_path, server=SERVER + snippet)
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_wildcard_registration"


def test_non_literal_path_stops_the_gate(tmp_path: Path) -> None:
    """Hoisting a path into a constant must not remove it from the gate's view."""
    openapi, server = write(
        tmp_path,
        server=SERVER
        + '\nconst ghost = "/api/ghost";\napp.get(ghost, async () => {});\n',
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_route_source_unreadable"


def test_fastify_alias_registration_stops_the_gate(tmp_path: Path) -> None:
    openapi, server = write(
        tmp_path,
        server=SERVER
        + '\nconst router = app;\nrouter.get("/api/ghost", async () => {});\n',
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server)

    assert excinfo.value.code == "admin_openapi_route_receiver_unreadable"


def test_fastify_plugin_registration_stops_the_gate(tmp_path: Path) -> None:
    openapi, server = write(
        tmp_path,
        server=SERVER + "\napp.register(importedBrowserPlugin);\n",
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server)

    assert excinfo.value.code == "admin_openapi_route_plugin_unreadable"


def test_duplicate_provider_registration_stops_the_gate(tmp_path: Path) -> None:
    openapi, server = write(
        tmp_path,
        server=SERVER + '\napp.get("/api/me", async () => {});\n',
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server)

    assert excinfo.value.code == "admin_openapi_route_duplicate"


def test_fastify_trace_registration_is_rejected_for_the_browser_plane(
    tmp_path: Path,
) -> None:
    openapi, server = write(
        tmp_path,
        server=SERVER + '\napp.trace("/api/ghost", async () => {});\n',
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server)

    assert excinfo.value.code == "admin_openapi_browser_method_unsupported"


def test_openapi_trace_operation_is_rejected_for_the_browser_plane(
    tmp_path: Path,
) -> None:
    openapi_with_trace = OPENAPI.replace(
        "  /api/operators/{id}/status:\n",
        '    trace:\n      responses:\n        "200":\n          description: forbidden browser verb\n'
        "  /api/operators/{id}/status:\n",
    )
    assert openapi_with_trace != OPENAPI
    openapi, server = write(tmp_path, openapi=openapi_with_trace)

    with pytest.raises(GateError) as excinfo:
        run(openapi, server)

    assert excinfo.value.code == "admin_openapi_browser_method_unsupported"


def test_fastify_add_http_method_stops_the_gate(tmp_path: Path) -> None:
    openapi, server = write(
        tmp_path,
        server=SERVER + '\napp.addHttpMethod("SEARCH");\n',
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server)

    assert excinfo.value.code == "admin_openapi_route_custom_method_unreadable"


def test_fastify_method_alias_stops_the_gate(tmp_path: Path) -> None:
    openapi, server = write(
        tmp_path,
        server=SERVER
        + '\nconst registerGet = app.get.bind(app);\nregisterGet("/api/ghost", async () => {});\n',
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server)

    assert excinfo.value.code == "admin_openapi_route_method_reference_unreadable"


def test_template_string_cannot_pretend_to_register_a_provider_route(
    tmp_path: Path,
) -> None:
    server_without_me = SERVER.replace(
        'app.get("/api/me", async (request, reply) => sendData(reply, {}));',
        'const documentation = `\napp.get("/api/me", handler);\n`;',
    )
    openapi, server = write(tmp_path, server=server_without_me)

    with pytest.raises(GateError) as excinfo:
        run(openapi, server)

    assert excinfo.value.code == "admin_openapi_path_orphan"
    assert "GET /api/me" in str(excinfo.value)


def test_excluded_path_with_unexpected_method_fails(tmp_path: Path) -> None:
    """`/` is excluded as GET only; POST on it is a real API route."""
    openapi, server = write(
        tmp_path, server=SERVER + '\napp.post("/", async () => {});\n'
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_path_missing"


def test_plural_route_helper_is_detected(tmp_path: Path) -> None:
    openapi, server = write(tmp_path, server=SERVER + "\nregisterGhostRoutes(app);\n")
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_unknown_route_helper"


def test_openapi_310_is_not_mistaken_for_31(tmp_path: Path) -> None:
    openapi, server = write(tmp_path, openapi=OPENAPI.replace("3.1.0", "3.10.0"))
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_version_unsupported"


def test_all_violations_reported_together(tmp_path: Path) -> None:
    """Reporting one class at a time hides the rest of the drift."""
    openapi, server = write(
        tmp_path,
        openapi=OPENAPI.replace("  /api/me:\n    get:", "  /api/renamed:\n    put:"),
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    message = str(excinfo.value)
    assert "/api/me" in message
    assert "/api/renamed" in message


def test_stale_exclusion_is_reported(tmp_path: Path) -> None:
    """An exclusion whose route is gone must be dropped, not left to rot."""
    openapi, server = write(
        tmp_path, server=SERVER.replace('app.get("/", async', 'app.getX("/", async')
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server)
    assert excinfo.value.code == "admin_openapi_stale_exclusion"


def test_commented_out_route_is_not_counted(tmp_path: Path) -> None:
    openapi, server = write(
        tmp_path, server=SERVER + '\n// app.get("/api/ghost", handler);\n'
    )
    assert "admin_openapi_ok" in run(openapi, server)


def test_success_line_separates_source_and_helper_exclusions(tmp_path: Path) -> None:
    """/healthz and /metrics never reach the parser, so do not claim they did."""
    openapi, server = write(tmp_path)
    line = run(openapi, server)
    assert "1 excluded at source" in line
    assert "2 helper-registered" in line


# --- browser proxy list -------------------------------------------------------
# Enumerating the proxied paths removed a catch-all rewrite, which makes the list
# a third thing that can drift from the contract.

PROXY = """
const GATEWAY_PROXY_PATHS = [
  "/api/me",
  "/api/operators/:id/status",
] as const;

const gatewayUrl = process.env.KOKORO_GATEWAY_URL ?? "http://gateway.test";
const nextConfig = {
  async rewrites() {
    return {
      fallback: GATEWAY_PROXY_PATHS.map((source) => ({ source, destination: `${gatewayUrl}${source}` })),
    };
  },
};
export default nextConfig;
"""


def test_proxy_list_matching_the_contract_passes(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY, encoding="utf-8")
    line = run(openapi, server, proxy)
    assert "2 transparent browser operations" in line
    assert "0 local BFF operations" in line


def test_proxy_missing_a_contract_path_fails(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY.replace('  "/api/me",\n', ""), encoding="utf-8")
    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)
    assert excinfo.value.code == "admin_openapi_browser_operation_missing"


def test_proxy_forwarding_an_undeclared_path_fails(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(
        PROXY.replace("] as const", '  "/api/ghost",\n] as const'), encoding="utf-8"
    )
    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)
    assert excinfo.value.code == "admin_openapi_proxy_path_orphan"


def test_missing_rewrites_function_stops_the_gate(tmp_path: Path) -> None:
    """Deleting the executable rewrite authority must fail, not silently skip it."""
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text("const OTHER = [] as const;\n", encoding="utf-8")
    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)
    assert excinfo.value.code == "admin_openapi_proxy_wiring_unreadable"


def test_duplicate_transparent_rewrite_entry_fails(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(
        PROXY.replace('  "/api/me",\n', '  "/api/me",\n  "/api/me",\n'),
        encoding="utf-8",
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_proxy_path_duplicate"


@pytest.mark.parametrize(
    "commented_entry",
    [
        '  // "/api/operators/:id/status",\n',
        '  /* "/api/operators/:id/status", */\n',
    ],
)
def test_commented_proxy_entry_cannot_authorize_an_operation(
    tmp_path: Path, commented_entry: str
) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(
        PROXY.replace('  "/api/operators/:id/status",\n', commented_entry),
        encoding="utf-8",
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_browser_operation_missing"
    assert "POST /api/operators/{id}/status" in str(excinfo.value)


def test_proxy_declaration_inside_a_string_cannot_shadow_the_real_list(
    tmp_path: Path,
) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    decoy = (
        "const note = 'const GATEWAY_PROXY_PATHS = ["
        '"/api/me", "/api/operators/:id/status"'
        "] as const';\n"
    )
    real_without_post = PROXY.replace('  "/api/operators/:id/status",\n', "")
    proxy.write_text(decoy + real_without_post, encoding="utf-8")

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_browser_operation_missing"


def test_dynamic_proxy_expression_stops_the_gate_instead_of_being_skipped(
    tmp_path: Path,
) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(
        PROXY.replace(
            '  "/api/operators/:id/status",\n',
            "  `/api/operators/${operatorId}/status`,\n",
        ),
        encoding="utf-8",
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_proxy_wiring_unreadable"


def test_catch_all_proxy_segment_stops_the_gate(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(
        PROXY.replace(
            '  "/api/operators/:id/status",\n',
            '  "/api/operators/:id*/status",\n',
        ),
        encoding="utf-8",
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_proxy_path_unreadable"


def test_unwired_proxy_list_cannot_claim_browser_authority(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(
        PROXY.replace(
            "fallback: GATEWAY_PROXY_PATHS.map((source) => ({ source, destination: `${gatewayUrl}${source}` }))",
            "fallback: []",
        ),
        encoding="utf-8",
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_proxy_wiring_unreadable"


def test_regex_literal_cannot_pretend_to_be_an_executable_rewrite(
    tmp_path: Path,
) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(
        r"""const decoy = /const GATEWAY_PROXY_PATHS = ["\/api\/me","\/api\/operators\/:id\/status"] as const/;
export default { async rewrites() { return { fallback: [] }; } };
""",
        encoding="utf-8",
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_proxy_wiring_unreadable"


def write_local_route(root: Path, path: str, methods: tuple[str, ...]) -> Path:
    route = root / path / "route.ts"
    route.parent.mkdir(parents=True, exist_ok=True)
    route.write_text(
        "\n".join(
            f"export async function {method}(request: Request): Promise<Response> {{ return new Response(); }}"
            for method in methods
        ),
        encoding="utf-8",
    )
    return route


def test_transparent_and_local_authorities_cover_the_contract_together(
    tmp_path: Path,
) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY.replace('  "/api/me",\n', ""), encoding="utf-8")
    write_local_route(tmp_path / "app" / "api", "me", ("GET",))

    line = run(openapi, server, proxy)

    assert "1 transparent browser operations" in line
    assert "1 local BFF operations" in line


def test_local_dynamic_segment_is_normalised_to_openapi_syntax(tmp_path: Path) -> None:
    dynamic_server = SERVER.replace("/api/me", "/api/modules/:moduleId")
    dynamic_openapi = OPENAPI.replace("/api/me", "/api/modules/{moduleId}")
    openapi, server = write(tmp_path, server=dynamic_server, openapi=dynamic_openapi)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY.replace('  "/api/me",\n', ""), encoding="utf-8")
    write_local_route(tmp_path / "app" / "api", "modules/[moduleId]", ("GET",))

    assert "admin_openapi_ok" in run(openapi, server, proxy)


def test_same_path_cannot_be_owned_by_rewrite_and_local_handler(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY, encoding="utf-8")
    write_local_route(tmp_path / "app" / "api", "me", ("GET",))

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_browser_authority_duplicate"
    assert "/api/me" in str(excinfo.value)


def test_local_handler_method_drift_fails(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY.replace('  "/api/me",\n', ""), encoding="utf-8")
    write_local_route(tmp_path / "app" / "api", "me", ("POST",))

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_local_method_mismatch"
    assert "local=['post'] document=['get']" in str(excinfo.value)


def test_local_handler_for_undeclared_path_fails(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY, encoding="utf-8")
    write_local_route(tmp_path / "app" / "api", "ghost", ("GET",))

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_local_operation_orphan"
    assert "GET /api/ghost" in str(excinfo.value)


def test_local_route_without_a_literal_handler_method_fails(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY.replace('  "/api/me",\n', ""), encoding="utf-8")
    route = write_local_route(tmp_path / "app" / "api", "me", ())
    route.write_text('export { GET } from "./handler";\n', encoding="utf-8")

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_local_route_unreadable"


def test_commented_local_handler_does_not_count(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY.replace('  "/api/me",\n', ""), encoding="utf-8")
    route = write_local_route(tmp_path / "app" / "api", "me", ())
    route.write_text("const note = 1; // export function GET() {}\n", encoding="utf-8")

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_local_route_unreadable"


def test_template_string_cannot_pretend_to_export_a_local_handler(
    tmp_path: Path,
) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY.replace('  "/api/me",\n', ""), encoding="utf-8")
    route = write_local_route(tmp_path / "app" / "api", "me", ())
    route.write_text(
        "const documentation = `\nexport async function GET() {}\n`;\n",
        encoding="utf-8",
    )

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_local_route_unreadable"


def test_non_callable_variable_cannot_pretend_to_be_a_local_handler(
    tmp_path: Path,
) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY.replace('  "/api/me",\n', ""), encoding="utf-8")
    route = write_local_route(tmp_path / "app" / "api", "me", ())
    route.write_text("export const GET = 42;\n", encoding="utf-8")

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_local_route_unreadable"


def test_local_catch_all_route_fails_instead_of_being_misnormalised(
    tmp_path: Path,
) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY, encoding="utf-8")
    write_local_route(tmp_path / "app" / "api", "docs/[...slug]", ("GET",))

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_local_route_unreadable"


def test_duplicate_local_route_sources_fail(tmp_path: Path) -> None:
    openapi, server = write(tmp_path)
    proxy = tmp_path / "next.config.ts"
    proxy.write_text(PROXY.replace('  "/api/me",\n', ""), encoding="utf-8")
    route = write_local_route(tmp_path / "app" / "api", "me", ("GET",))
    route.with_suffix(".js").write_text("export function GET() {}\n", encoding="utf-8")

    with pytest.raises(GateError) as excinfo:
        run(openapi, server, proxy)

    assert excinfo.value.code == "admin_openapi_local_route_duplicate"

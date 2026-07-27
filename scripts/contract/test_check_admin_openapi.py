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


def write(tmp_path: Path, server: str = SERVER, openapi: str = OPENAPI) -> tuple[Path, Path]:
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
        openapi=OPENAPI + '  /api/ghost:\n    get:\n      responses:\n        "200":\n          description: ok\n',
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
        openapi=OPENAPI + '  /:\n    get:\n      responses:\n        "200":\n          description: ok\n',
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

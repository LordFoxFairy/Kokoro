"""Fail-closed guards for the real model composition, no infrastructure startup."""

from pathlib import Path
import importlib
import pytest

MODULE = "scripts.e2e.run_web_real_model_worker_smoke"


def module():
    assert Path("scripts/e2e/run_web_real_model_worker_smoke.py").is_file(), (
        "real runner absent"
    )
    return importlib.import_module(MODULE)


def test_real_mode_is_explicit_and_does_not_accept_fixture():
    m = module()
    config = m.RealModelConfig("http://127.0.0.1:11434", "qwen3:8b", "a" * 40)
    assert config.model == "qwen3:8b"
    for endpoint in (
        "http://remote.test",
        "http://127.0.0.1:3310",
        "http://127.0.0.1:11434/v1",
        "http://user:pass@127.0.0.1:11434",
    ):
        with pytest.raises(m.SmokeError):
            m.RealModelConfig(endpoint, "qwen3:8b", "a" * 40)
    for model in ("", "fixture", "smoke-model"):
        with pytest.raises(m.SmokeError):
            m.RealModelConfig("http://127.0.0.1:11434", model, "a" * 40)


def valid_evidence():
    return dict(
        browser="chromium",
        message_post_status=202,
        agui_status=200,
        conversation_id="conv_abc",
        run_id="run_abc",
        artifact_id="artifact-abc",
        asset_id="asset-abc",
        text_marker_visible=True,
        live_delivery=True,
        reload_card_count=1,
        download_sha256="b" * 64,
        member_statuses=[404, 404, 404],
    )


def test_stage_validation_requires_text_and_artifact_from_one_run():
    m = module()
    evidence = valid_evidence()
    m.validate_browser_evidence(evidence, "b" * 64)
    for key, bad in [
        ("run_id", ""),
        ("message_post_status", 200),
        ("text_marker_visible", False),
        ("live_delivery", False),
        ("reload_card_count", 2),
        ("download_sha256", "c" * 64),
        ("member_statuses", [200, 404, 404]),
    ]:
        with pytest.raises(m.SmokeError):
            m.validate_browser_evidence({**evidence, key: bad}, "b" * 64)


def test_runner_never_calls_manual_execution_or_fixture_boundary():
    module()
    source = Path("scripts/e2e/run_web_real_model_worker_smoke.py").read_text()
    for forbidden in (
        "_deliver_pending(",
        "claim_dispatch(",
        "journal_tool_started(",
        "RunEmitter",
        "system_model_fixtures(",
    ):
        assert forbidden not in source
    assert '"kokoro-agent-worker"' in source
    assert "real_model_scenario=" in source
    assert "seed_control_plane(" in source


def test_transparent_model_proxy_forwards_real_bytes_and_requires_stream():
    import http.client
    import json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    m = module()
    observed = []
    payload = (
        b'data: {"choices":[{"delta":{"content":"real upstream"}}]}\n\ndata: [DONE]\n\n'
    )

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            observed.append(
                json.loads(self.rfile.read(int(self.headers["content-length"])))
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    proxy = m.ObservingProxy(
        f"http://127.0.0.1:{upstream.server_port}",
        kind="model",
        token="key",
        tenant="tenant",
        model="qwen3:8b",
        revision="revision",
        timeout=2,
    )
    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1", proxy.server_port, timeout=3
        )
        body = {"model": "qwen3:8b", "stream": True, "messages": []}
        connection.request(
            "POST",
            "/v1/chat/completions",
            json.dumps(body),
            {"authorization": "Bearer key"},
        )
        response = connection.getresponse()
        assert response.status == 200
        assert response.read() == payload
        assert observed == [body]
        assert proxy.requests == proxy.successes == 1
        assert not proxy.errors
        connection.close()
        connection = http.client.HTTPConnection(
            "127.0.0.1", proxy.server_port, timeout=3
        )
        connection.request(
            "POST",
            "/v1/chat/completions",
            json.dumps({**body, "stream": False}),
            {"authorization": "Bearer key"},
        )
        with pytest.raises(http.client.RemoteDisconnected):
            connection.getresponse()
        assert len(observed) == 1
        assert proxy.errors == ["upstream_observation_failed"]
        connection.close()
    finally:
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=3)


def test_system_proxy_rejects_wrong_tenant_without_network():
    import http.client
    import json

    m = module()
    proxy = m.ObservingProxy(
        "http://127.0.0.1:1",
        kind="system",
        token="key",
        tenant="tenant",
        model="qwen3:8b",
        revision="revision",
        timeout=1,
    )
    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1", proxy.server_port, timeout=3
        )
        connection.request(
            "POST",
            "/v1/system/model-catalog/resolve",
            json.dumps({"feature_key": "chat"}),
            {
                "authorization": "Bearer key",
                "x-kokoro-tenant-id": "another",
                "x-kokoro-service": "kokoro-agent",
            },
        )
        with pytest.raises(http.client.RemoteDisconnected):
            connection.getresponse()
        assert proxy.requests == 0
        assert proxy.errors == ["upstream_observation_failed"]
        connection.close()
    finally:
        proxy.close()


def test_worker_lease_pid_must_belong_to_registered_process_group(monkeypatch):
    import socket

    m = module()
    monkeypatch.setattr(m.os, "getpgid", lambda pid: 100 if pid == 101 else 200)
    assert m.worker_owns_lease(f"{socket.gethostname()}-101", 100)
    assert not m.worker_owns_lease(f"{socket.gethostname()}-102", 100)
    assert not m.worker_owns_lease("artifact-combo-smoke", 100)


@pytest.mark.parametrize(
    "invalid", [None, {}, {"timeout_ms": 1}, {"web_origin": "https://remote.test"}]
)
def test_browser_rejects_invalid_input_before_launch(invalid):
    import json
    import subprocess

    m = module()
    result = subprocess.run(
        ["node", str(m.DRIVER)],
        input=json.dumps(invalid),
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 1
    assert result.stderr == "REAL_MODEL_FAILURE:input\n"


def test_durable_evidence_requires_worker_owned_write_and_single_delivery(monkeypatch):
    m = module()
    monkeypatch.setattr(
        m, "worker_owns_lease", lambda owner, group: owner == "worker" and group == 42
    )
    row = {
        "terminal": True,
        "generation": 1,
        "owner": "worker",
        "file_writes": 1,
        "deliveries": 1,
        "events": ["run.started", "delivery.created", "run.completed"],
    }
    for change in (
        {},
        {"file_writes": 0},
        {"owner": "artifact-combo-smoke"},
        {"deliveries": 2},
        {"events": ["run.started", "run.completed", "delivery.created"]},
    ):
        results = iter([{**row, **change}, {"count": 1}])
        monkeypatch.setattr(m, "_query", lambda *_: next(results))
        if change:
            with pytest.raises(m.SmokeError, match="lease/journal/terminal"):
                m.durable_evidence(
                    None, "owned-db", valid_evidence(), "tenant", 42, "b" * 64
                )
        else:
            assert m.durable_evidence(
                None, "owned-db", valid_evidence(), "tenant", 42, "b" * 64
            )["storage"] == {"count": 1}


def test_durable_evidence_accepts_owner_resource_ids_but_rejects_sql_input(monkeypatch):
    m = module()
    monkeypatch.setattr(m, "worker_owns_lease", lambda *_: True)
    row = {
        "terminal": True,
        "generation": 1,
        "owner": "worker",
        "file_writes": 1,
        "deliveries": 1,
        "events": ["delivery.created", "run.completed"],
    }
    evidence = {
        **valid_evidence(),
        "artifact_id": "artifact:abc123",
        "asset_id": "asset:abc123",
    }
    results = iter([row, {"count": 1}])
    monkeypatch.setattr(m, "_query", lambda *_: next(results))
    assert m.durable_evidence(None, "owned-db", evidence, "tenant", 42, "b" * 64)
    for malicious in ("artifact:' OR true --", "artifact:abc;", "artifact:abc\n"):
        with pytest.raises(m.SmokeError, match="SQL evidence identity rejected"):
            m.durable_evidence(
                None,
                "owned-db",
                {**evidence, "artifact_id": malicious},
                "tenant",
                42,
                "b" * 64,
            )


def test_harness_registers_system_in_existing_owned_lifecycle():
    source = Path("scripts/e2e/run_web_project_resource_chromium_smoke.py").read_text()
    assert '"owner_db_url": owner_db_url' in source
    assert '"processes": process_list' in source
    assert '"proxies": proxies' in source
    assert '"infra": infra' in source
    assert source.index("for process in reversed(process_list):") < source.index(
        "infra.cleanup()"
    )
    real = Path("scripts/e2e/run_web_real_model_worker_smoke.py").read_text()
    assert 'system_db = c["owner_db_url"]' in real
    assert 'c["processes"].append(system_process)' in real
    assert 'c["processes"].append(process)' in real
    assert 'c["processes"].append(browser_process)' in real

"""Billing composition mocks plus an isolated slow-body HTTP deadline regression."""

import io
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/dev"))
sys.path.insert(0, str(ROOT / "scripts/e2e"))
import local_billing_runtime as billing
import serve_local_login as launcher


@pytest.fixture
def owned(monkeypatch):
    registry = Mock()
    item = billing.LocalBillingRuntime(
        node=Path("/owned/node24/bin/node"),
        node_environment={
            "NODE_OPTIONS": "--import=file:///owned/node-parent-guard.mjs"
        },
        credentials=registry,
        log=io.BytesIO(),
    )
    ready = SimpleNamespace(
        base_url="http://127.0.0.1:43180",
        issuer_url="http://127.0.0.1:43181/iam",
    )
    process = Mock()
    process.poll.return_value = None
    command = Mock(return_value=0)
    spawn = Mock(return_value=process)
    wait = Mock()
    monkeypatch.setattr(billing.runtime, "run_owned_command", command)
    monkeypatch.setattr(billing.runtime, "free_port", lambda: 43182)
    monkeypatch.setattr(billing.subprocess, "Popen", spawn)
    monkeypatch.setattr(billing.local_chat_runtime, "registration_guard", nullcontext)
    monkeypatch.setattr(billing, "wait_billing_ready", wait)
    return item, ready, registry, command, spawn, wait, process


def test_official_owner_commands_dist_guard_and_independent_five_factor_mapping(owned):
    item, ready, registry, command, spawn, wait, process = owned
    result = item.start(
        "postgresql://local/owned?schema=old&options=-c&sslmode=disable", ready
    )
    assert [call.args[0] for call in command.call_args_list] == [
        ["/owned/node24/bin/corepack", "pnpm", "build"],
        ["/owned/node24/bin/corepack", "pnpm", "db:apply-schema"],
    ]
    assert [call.kwargs["timeout"] for call in command.call_args_list] == [120, 180]
    assert all(call.kwargs["cwd"] == billing.BILLING for call in command.call_args_list)
    environment = spawn.call_args.kwargs["env"]
    assert parse_qs(urlsplit(environment["DATABASE_URL"]).query) == {
        "schema": ["kokoro_billing"],
        "sslmode": ["disable"],
    }
    assert spawn.call_args.args[0] == [
        str(item.node),
        str(billing.BILLING / "dist/src/main.js"),
    ]
    assert spawn.call_args.kwargs["start_new_session"] is True
    assert environment["NODE_OPTIONS"] == item.node_environment["NODE_OPTIONS"]
    assert environment["BILLING_AUTH_MODE"] == "jwks"
    assert environment["BILLING_AUTH_JWKS_URL"] == "http://127.0.0.1:43180/iam/jwks"
    assert environment["BILLING_AUTH_JWT_ISSUER"] == ready.issuer_url
    assert environment["BILLING_AUTH_JWT_AUDIENCE"] == billing.BILLING_AUDIENCE
    assert environment["BILLING_ENABLED_PROVIDERS"] == ""
    credentials = [
        environment[name]
        for name in (
            "INTERNAL_SERVICE_SECRET",
            "BILLING_BFF_SERVICE_TOKEN",
            "BILLING_OPERATOR_PROXY_SECRET",
        )
    ]
    assert len(set(credentials)) == 3
    assert all(
        len(value) >= 32 and value.isascii() and value.isalnum()
        for value in credentials
    )
    assert [call.args[0] for call in registry.add.call_args_list] == credentials
    assert result == {
        "KOKORO_BILLING_BASE_URL": "http://127.0.0.1:43182",
        "KOKORO_INTERNAL_SECRET_BFF": credentials[0],
        "KOKORO_BILLING_BFF_SERVICE_TOKEN": credentials[1],
    }
    assert credentials[2] not in result.values()
    # Tenant and u1 subject are encoded by BFF from its admitted RequestContext,
    # not by Root or by forwarding the human user's access Bearer to Billing.
    assert not any("TENANT" in name or "SUBJECT" in name for name in result)
    wait.assert_called_once_with("http://127.0.0.1:43182", process)
    item.require_alive()


@pytest.mark.parametrize(
    "url",
    [
        "https://local/owned",
        "postgresql://local/",
        "postgresql://local:bad/owned",
        "postgresql://local/owned#other",
    ],
)
def test_owner_url_rejects_invalid_inputs_without_exposing_endpoint(url):
    with pytest.raises(billing.BillingRuntimeError, match="identity invalid"):
        billing.billing_owner_database_url(url)


def test_owner_url_has_exactly_one_schema_and_no_options():
    raw = "postgresql://local/owned?schema=x&schema=y&options=private&OPTIONS=private&search_path=wrong&application_name=fixture"
    parsed = urlsplit(billing.billing_owner_database_url(raw))
    assert parsed.path == "/owned"
    assert parse_qs(parsed.query) == {
        "schema": ["kokoro_billing"],
        "application_name": ["fixture"],
    }


@pytest.mark.parametrize("failure", [0, 1])
def test_build_or_installer_failure_never_starts_owner(owned, failure):
    item, ready, _registry, command, spawn, _wait, _process = owned
    command.side_effect = [1] if failure == 0 else [0, 1]
    with pytest.raises(billing.BillingRuntimeError):
        item.start("postgresql://local/owned", ready)
    spawn.assert_not_called()
    assert item.quiescent
    assert item.close() == []
    assert item.close() == []


def test_unknown_command_cleanup_is_not_claimed_quiescent(owned):
    item, ready, _registry, command, spawn, _wait, _process = owned
    command.side_effect = RuntimeError("private endpoint or secret")
    with pytest.raises(billing.BillingRuntimeError, match="^Billing startup failed$"):
        item.start("postgresql://local/owned", ready)
    spawn.assert_not_called()
    assert not item.quiescent
    assert item.close() == ["Billing command cleanup requires reconciliation"]


def test_readiness_failure_keeps_partial_process_registered_until_close(
    owned, monkeypatch
):
    item, ready, _registry, _command, _spawn, wait, process = owned
    wait.side_effect = billing.BillingRuntimeError(
        "Billing readiness deadline exceeded"
    )
    with pytest.raises(billing.BillingRuntimeError):
        item.start("postgresql://local/owned", ready)
    assert item.process is process
    assert not item.quiescent

    def stop(target):
        assert target is process
        process.poll.return_value = 0

    close = Mock(side_effect=stop)
    monkeypatch.setattr(billing.runtime, "stop_owned_process", close)
    assert item.close() == []
    assert item.quiescent
    assert item.close() == []
    close.assert_called_once()


@pytest.mark.parametrize("raises", [True, False])
def test_failed_stop_preserves_dependencies_and_is_not_a_false_zero(
    owned, monkeypatch, raises
):
    item, ready, *_rest = owned
    item.start("postgresql://local/owned", ready)
    stop = Mock(side_effect=RuntimeError("private") if raises else None)
    monkeypatch.setattr(billing.runtime, "stop_owned_process", stop)
    assert item.close() == ["Billing process cleanup", "Billing dependencies preserved"]
    assert not item.quiescent


def test_alive_and_start_after_close_fail_closed(owned):
    item, ready, *_rest = owned
    with pytest.raises(billing.BillingRuntimeError):
        item.require_alive()
    assert item.close() == []
    with pytest.raises(billing.BillingRuntimeError):
        item.start("postgresql://local/owned", ready)


def test_credential_collision_fails_closed_and_registers_generated_values(monkeypatch):
    monkeypatch.setattr(billing.secrets, "token_hex", lambda _length: "a" * 64)
    registry = Mock()
    item = billing.LocalBillingRuntime(
        node=Path("/unused"),
        node_environment={},
        credentials=registry,
        log=io.BytesIO(),
    )
    with pytest.raises(billing.BillingRuntimeError, match="not distinct"):
        item.start("postgresql://local/owned", SimpleNamespace())
    assert registry.add.call_count == 3


@pytest.mark.parametrize("mode", ["ready", "malformed", "unavailable", "exited"])
def test_readiness_is_finite_and_uses_only_the_owner_shape(monkeypatch, mode):
    process = Mock()
    process.poll.return_value = 1 if mode == "exited" else None
    now = iter([0, 1, 31, 31])
    monkeypatch.setattr(billing.time, "monotonic", lambda: next(now))
    monkeypatch.setattr(billing.time, "sleep", Mock())
    request = Mock(
        return_value=billing.READY if mode == "ready" else {"status": "ready"}
    )
    if mode == "unavailable":
        request.side_effect = OSError("private")
    monkeypatch.setattr(billing, "_billing_ready_body", request)
    if mode == "ready":
        # One extra absolute-time check after receiving the response.
        values = iter([0, 1, 2])
        monkeypatch.setattr(billing.time, "monotonic", lambda: next(values))
        billing.wait_billing_ready("http://127.0.0.1:43182", process)
        request.assert_called_once_with("http://127.0.0.1:43182", 30.0)
    else:
        with pytest.raises(billing.BillingRuntimeError):
            billing.wait_billing_ready("http://127.0.0.1:43182", process)


@pytest.mark.parametrize(
    "billing_state,with_chat",
    [
        (state, chat)
        for chat in (False, True)
        for state in (
            "ready",
            "partial",
            "not-quiescent",
            "close-raises",
            "consumer-active",
        )
    ]
    + [("chat-failed", True)],
)
def test_launcher_closes_consumers_then_billing_then_iam_and_gates_database(
    monkeypatch, tmp_path, billing_state, with_chat
):
    resources = Mock()
    resources.command.return_value = "PONG"
    resources.create_database.return_value = "postgresql://local/owned"
    ready = SimpleNamespace(
        database_name="iam-owned",
        redis_prefix="iam:",
        client_secret="fixture-iam-secret",
        password="fixture-password",
        base_url="http://127.0.0.1:43180",
        issuer_url="http://127.0.0.1:43181/iam",
        redirect_uri="http://127.0.0.1:43181/callback",
        post_logout_redirect_uri="http://127.0.0.1:43181/logout",
        tenant_id="tenant",
    )
    args = SimpleNamespace(
        chat=with_chat,
        uv_bin=Path("/unused/uv"),
        model_origin="http://127.0.0.1:11434",
        model="fixture-model",
        agent_redis_url="redis://local/10",
        postgres_admin_url="postgresql://local/postgres",
        redis_url="redis://local/9",
        iam_node_bin=Path("/node24"),
        bff_node_bin=Path("/node22"),
        web_node_bin=Path("/node22"),
        billing_node_bin=Path("/node24"),
    )
    iam, bff = Mock(), Mock()
    iam.poll.return_value = bff.poll.return_value = None
    trace = []
    chat = Mock()
    chat.quiescent = True
    shared_secret = "fixture-existing-bff-identity-" + "a" * 32
    chat.start.return_value = {"KOKORO_INTERNAL_SECRET_BFF": shared_secret}
    if billing_state == "chat-failed":
        chat.start.side_effect = launcher.chat_runtime.ChatError("private")
    chat.close.side_effect = lambda: trace.append("chat") or []
    monkeypatch.setattr(launcher.chat_runtime, "preflight", Mock())
    monkeypatch.setattr(
        launcher.chat_runtime, "LocalChatRuntime", lambda **_kwargs: chat
    )
    item = Mock()
    item.quiescent = billing_state != "not-quiescent"
    item.start.return_value = {"KOKORO_BILLING_BASE_URL": "http://127.0.0.1:43182"}
    if billing_state == "partial":
        item.start.side_effect = billing.BillingRuntimeError("private")

    def close_billing():
        trace.append("billing")
        if billing_state == "close-raises":
            raise RuntimeError("private")
        return [] if item.quiescent else ["Billing dependencies preserved"]

    item.close.side_effect = close_billing

    def stop(process):
        trace.append("iam" if process is iam else "consumer")
        if process is bff and billing_state == "consumer-active":
            raise RuntimeError("private")

    monkeypatch.setattr(launcher, "parse_args", lambda _argv: args)
    preflight = Mock()
    monkeypatch.setattr(launcher, "verify_login_release_inputs", preflight)
    monkeypatch.setattr(launcher, "require_free_web_port", Mock())
    monkeypatch.setattr(
        launcher.tempfile,
        "TemporaryDirectory",
        lambda **_kwargs: nullcontext(str(tmp_path)),
    )
    monkeypatch.setattr(launcher.runtime, "OwnedResources", lambda *_args: resources)
    monkeypatch.setattr(
        launcher.session, "node_environment", Mock(side_effect=lambda *_args: {})
    )
    monkeypatch.setattr(launcher.runtime, "run_owned_command", Mock(return_value=0))
    monkeypatch.setattr(launcher.runtime, "install_schema", Mock())
    monkeypatch.setattr(launcher.web_smoke, "named_iam_identity", lambda _id: ready)
    monkeypatch.setattr(
        launcher.web_smoke,
        "iam_owned_inventory",
        Mock(side_effect=[(set(), set()), ({"iam-owned"}, set())]),
    )
    monkeypatch.setattr(launcher.web_smoke, "validate_ready", lambda *_args: ready)
    monkeypatch.setattr(
        launcher.product_session, "web_redis_keys", Mock(return_value=set())
    )
    monkeypatch.setattr(launcher.session, "ProtocolReader", Mock())
    monkeypatch.setattr(launcher.subprocess, "Popen", Mock(return_value=iam))
    monkeypatch.setattr(launcher.runtime, "start_process", Mock(return_value=bff))
    monkeypatch.setattr(
        launcher.runtime,
        "wait_ready",
        Mock(side_effect=launcher.LaunchError("bounded test exit")),
    )
    monkeypatch.setattr(launcher.runtime, "stop_owned_process", Mock(side_effect=stop))
    monkeypatch.setattr(
        launcher.billing_runtime, "LocalBillingRuntime", lambda **_kwargs: item
    )
    monkeypatch.setattr(launcher.web_smoke, "reconcile_iam_identity", Mock())
    monkeypatch.setattr(launcher.previous, "assert_log_clean", Mock())
    monkeypatch.setattr(launcher.signal, "signal", Mock())
    with pytest.raises(launcher.LaunchError):
        launcher.main([])
    preflight.assert_called_once_with(
        storage=False, platform=False, billing=True, admin=False
    )
    assert any(
        call.args == (args.billing_node_bin, "v24.20.0", args.billing_node_bin.parent)
        for call in launcher.session.node_environment.call_args_list
    )
    if billing_state == "chat-failed":
        item.start.assert_not_called()
        launcher.runtime.start_process.assert_not_called()
        assert trace == ["chat", "iam"]
        resources.cleanup.assert_called_once()
        return
    item.start.assert_called_once_with(
        "postgresql://local/owned",
        ready,
        bff_internal_secret=shared_secret if with_chat else None,
    )
    if billing_state in {"ready", "partial"}:
        assert trace == ([] if billing_state == "partial" else ["consumer"]) + [
            "billing"
        ] + (["chat"] if with_chat else []) + ["iam"]
        resources.cleanup.assert_called_once()
    else:
        resources.cleanup.assert_not_called()
        launcher.web_smoke.reconcile_iam_identity.assert_not_called()
        assert "iam" not in trace
        if billing_state == "consumer-active":
            item.close.assert_not_called()
    assert launcher.failure_category(billing.BillingRuntimeError("secret")) == "billing"


def test_chat_bff_internal_identity_is_shared_but_billing_bearer_and_operator_are_independent(
    owned,
):
    item, ready, registry, _command, spawn, _wait, _process = owned
    existing = "existing-root-bff-identity-" + "a" * 32
    result = item.start("postgresql://local/owned", ready, bff_internal_secret=existing)
    environment = spawn.call_args.kwargs["env"]
    assert result["KOKORO_INTERNAL_SECRET_BFF"] == existing
    assert environment["INTERNAL_SERVICE_SECRET"] == existing
    assert (
        len(
            {
                existing,
                environment["BILLING_BFF_SERVICE_TOKEN"],
                environment["BILLING_OPERATOR_PROXY_SECRET"],
            }
        )
        == 3
    )
    assert registry.add.call_args_list[0].args == (existing,)


@pytest.mark.parametrize(
    "secret",
    ["short", "x" * 31, "x" * 4097, "x" * 32 + " ", "x" * 32 + "\n", "非" * 32],
)
def test_shared_bff_internal_identity_is_validated_before_commands(owned, secret):
    item, ready, _registry, command, spawn, _wait, _process = owned
    with pytest.raises(billing.BillingRuntimeError, match="identity invalid"):
        item.start("postgresql://local/owned", ready, bff_internal_secret=secret)
    command.assert_not_called()
    spawn.assert_not_called()


@pytest.mark.parametrize("slow_phase", ["headers", "body"])
def test_readiness_slow_body_has_absolute_deadline(monkeypatch, slow_phase):
    import json
    import socket
    import threading
    import time

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(2)
    stopped = threading.Event()
    disconnected = threading.Event()
    payload = json.dumps(billing.READY).encode()

    def serve():
        try:
            connection, _ = listener.accept()
            with connection:
                connection.recv(4096)
                headers = (
                    b"HTTP/1.1 200 OK\r\nContent-Length: "
                    + str(len(payload)).encode()
                    + b"\r\n\r\n"
                )
                if slow_phase == "headers":
                    for byte in headers:
                        if stopped.wait(0.02):
                            break
                        connection.sendall(bytes([byte]))
                else:
                    connection.sendall(headers)
                for byte in payload:
                    if stopped.wait(0.02):
                        break
                    connection.sendall(bytes([byte]))
        except (OSError, TimeoutError):
            disconnected.set()

    worker = threading.Thread(target=serve)
    worker.start()
    monkeypatch.setattr(billing, "READY_TIMEOUT_SECONDS", 0.2)
    process = Mock()
    process.poll.return_value = None
    started = time.monotonic()
    try:
        with pytest.raises(billing.BillingRuntimeError, match="deadline"):
            billing.wait_billing_ready(
                f"http://127.0.0.1:{listener.getsockname()[1]}", process
            )
        assert time.monotonic() - started < 0.8
        assert disconnected.wait(0.5), "deadline must close the owned socket"
    finally:
        stopped.set()
        listener.close()
        worker.join(timeout=2)
    assert not worker.is_alive()

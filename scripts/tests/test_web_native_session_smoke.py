"""Root native smoke lifecycle tests; no services or infrastructure connections."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

PATH = Path(__file__).resolve().parents[1] / "e2e/run_web_native_session_smoke.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("web_native_session_smoke", PATH)
smoke = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = smoke
spec.loader.exec_module(smoke)


def node_fixture(directory, name, version):
    path = directory / name
    path.write_text(f"#!/bin/sh\nprintf '%s\\n' '{version}'\n")
    path.chmod(0o700)
    return path


def arguments(tmp_path):
    return SimpleNamespace(
        iam_node_bin=node_fixture(tmp_path, "iam-node", "v24.20.0"),
        bff_node_bin=node_fixture(tmp_path, "bff-node", "v24.20.0"),
        web_node_bin=node_fixture(tmp_path, "web-node", "v22.23.4"),
        expected_iam_sha="a" * 40,
        expected_bff_sha="b" * 40,
        expected_app_sha="c" * 40,
        allow_unpublished_iam_gitlink=False,
        browser_journeys=False,
        postgres_admin_url="postgresql://user:postgres-secret@localhost/test_admin",
        redis_url="redis://user:redis-secret@localhost/0",
    )


def prepare_main(tmp_path, monkeypatch):
    args = arguments(tmp_path)
    monkeypatch.setattr(smoke, "parse_args", lambda _: args)
    monkeypatch.setattr(
        smoke,
        "verify_source",
        lambda *a: {"sha": a[1], "clean": True, "root_gitlink_matches": True},
    )
    monkeypatch.setattr(smoke, "EVIDENCE_ROOT", tmp_path / "evidence", raising=False)
    return args


def read_receipt(tmp_path):
    files = list((tmp_path / "evidence").glob("*/receipt.json"))
    assert len(files) == 1
    return json.loads(files[0].read_text()), files[0]


def test_native_preflight_accepts_current_owner_nodes_before_resource_allocation(
    tmp_path, monkeypatch
):
    args = prepare_main(tmp_path, monkeypatch)
    resources = Mock(side_effect=RuntimeError("resource-boundary"))
    monkeypatch.setattr(smoke.runtime, "OwnedResources", resources)
    with pytest.raises(smoke.SmokeError):
        smoke.main([])
    resources.assert_called_once()
    receipt, _ = read_receipt(tmp_path)
    assert receipt["stage"] == "resource allocation"
    assert receipt["sources"]["app"]["sha"] == args.expected_app_sha
    assert receipt["node_versions"] == {
        "iam": "24.20.0",
        "bff": "24.20.0",
        "app": "22.23.4",
    }
    assert receipt["required_node_versions"] == receipt["node_versions"]


@pytest.mark.parametrize(
    "owner,version", [("bff", "v22.22.2"), ("web", "v22.22.2"), ("iam", "v22.23.4")]
)
def test_obsolete_nodes_fail_preflight_without_allocating_resources(
    tmp_path, monkeypatch, owner, version
):
    args = prepare_main(tmp_path, monkeypatch)
    setattr(args, owner + "_node_bin", node_fixture(tmp_path, "obsolete-node", version))
    resources = Mock()
    monkeypatch.setattr(smoke.runtime, "OwnedResources", resources)
    with pytest.raises(smoke.SmokeError):
        smoke.main([])
    resources.assert_not_called()
    receipt, _ = read_receipt(tmp_path)
    assert receipt["stage"] == "runtime preflight"
    key = "app" if owner == "web" else owner
    assert receipt["node_versions"][key] == version.removeprefix("v")
    order = ["iam", "bff", "app"]
    for later in order[order.index(key) + 1 :]:
        assert receipt["node_versions"][later] is None


def resources_fixture():
    return SimpleNamespace(
        cleanup=Mock(),
        verify_clean=Mock(),
        command=Mock(),
        redis_url="redis://localhost/0",
    )


def test_cleanup_reports_failures_but_preserves_dependencies_until_quiescent(
    monkeypatch,
):
    stopped = []

    def stop(process):
        stopped.append(process)
        raise RuntimeError("postgresql://user:password@host secret-cookie")

    monkeypatch.setattr(smoke.runtime, "stop_owned_process", stop)
    resources = resources_fixture()
    proxies = [
        SimpleNamespace(close=Mock(side_effect=RuntimeError("proxy-secret"))),
        SimpleNamespace(close=Mock()),
    ]
    reader = SimpleNamespace(close=Mock())
    with pytest.raises(smoke.SmokeError, match="cleanup") as caught:
        smoke.close_native_resources([1, 2], proxies, reader, resources)
    assert stopped == [2, 1]
    for proxy in proxies:
        proxy.close.assert_called_once()
    resources.cleanup.assert_not_called()
    resources.verify_clean.assert_not_called()
    reader.close.assert_called_once()
    assert caught.value.quiescent is False
    assert "password" not in str(caught.value)
    assert "secret" not in str(caught.value)


def test_quiescent_cleanup_attempts_verification_after_database_failure(monkeypatch):
    monkeypatch.setattr(smoke.runtime, "stop_owned_process", Mock())
    resources = resources_fixture()
    resources.cleanup.side_effect = RuntimeError("private-url")
    reader = SimpleNamespace(close=Mock(side_effect=OSError("private-path")))
    with pytest.raises(smoke.SmokeError, match="cleanup") as caught:
        smoke.close_native_resources([1], [], reader, resources)
    assert caught.value.quiescent is True
    resources.cleanup.assert_called_once()
    resources.verify_clean.assert_called_once()
    assert "private" not in str(caught.value)


def test_cleanup_rejects_leaked_named_iam_fixture_resources(monkeypatch):
    identity = SimpleNamespace(database_name="owned", redis_prefix="owned:")
    resources = resources_fixture()
    monkeypatch.setattr(
        smoke.web, "iam_owned_inventory", lambda *_: ({"owned"}, {"owned:key"})
    )
    with pytest.raises(smoke.SmokeError, match="IAM resource cleanup"):
        smoke.close_native_resources(
            [], [], None, resources, iam_identity=identity, iam_before=(set(), set())
        )
    resources.cleanup.assert_called_once()
    resources.verify_clean.assert_called_once()
    resources.command.assert_not_called()  # The runner never deletes an unattributed IAM resource.


def test_iam_inventory_queries_exact_identity_not_unrelated_fixtures():
    identity = SimpleNamespace(
        database_name="iam_web_oidc_" + "a" * 32,
        redis_prefix="iam:test:bff-session-admission-host:own:",
    )
    commands = []

    def command(args):
        commands.append(args)
        if args[0] == "psql":
            assert "LIKE" not in args[-1]
            assert identity.database_name in args[-1]
            return ""
        assert args[-1] == identity.redis_prefix + "*"
        return ""

    resources = smoke.runtime.OwnedResources(
        "postgresql://localhost/postgres",
        "redis://localhost/0",
        "a" * 24,
        command=command,
    )
    smoke.close_native_resources(
        [], [], None, resources, iam_identity=identity, iam_before=(set(), set())
    )
    assert len(commands) == 2


def test_proxy_thread_still_alive_defers_dependency_cleanup():
    resources = resources_fixture()
    proxy = SimpleNamespace(close=Mock(), thread=SimpleNamespace(is_alive=lambda: True))
    with pytest.raises(smoke.SmokeError) as caught:
        smoke.close_native_resources([], [proxy], None, resources)
    assert caught.value.quiescent is False
    resources.cleanup.assert_not_called()


def web_prefixes(origin):
    digest = hashlib.sha256(origin.encode()).hexdigest()
    return [f"kokoro:web:{name}:{digest}:" for name in ("iam-signin-flow", "iam-csrf")]


def test_native_web_redis_cleans_only_current_origin_flow_and_csrf():
    origin = "https://web-native-own.example.test"
    prefixes = web_prefixes(origin)
    keys = {prefixes[0] + "flow", prefixes[1] + "csrf", "someone-elses-key"}
    commands = []

    def command(args):
        commands.append(args)
        if "--scan" in args:
            return "\n".join(key for key in keys if key.startswith(args[-1][:-1]))
        if "UNLINK" in args:
            keys.difference_update(args[args.index("UNLINK") + 1 :])
            return "1"
        raise AssertionError(args)

    resources = resources_fixture()
    resources.command = command
    smoke.close_native_resources(
        [], [], None, resources, web_origin=origin, web_before=set()
    )
    assert keys == {"someone-elses-key"}
    assert all("FLUSH" not in " ".join(args) for args in commands)
    resources.cleanup.assert_called_once()


def test_native_web_redis_refuses_out_of_namespace_scan_results():
    resources = resources_fixture()
    resources.command.return_value = "someone-elses-key"
    with pytest.raises(smoke.SmokeError, match="Web Redis cleanup"):
        smoke.close_native_resources(
            [],
            [],
            None,
            resources,
            web_origin="https://web-native-own.example.test",
            web_before=set(),
        )
    assert all(
        "UNLINK" not in call.args[0] for call in resources.command.call_args_list
    )
    resources.cleanup.assert_called_once()


def test_preexisting_web_namespace_is_not_deleted():
    resources = resources_fixture()
    with pytest.raises(smoke.SmokeError, match="Web Redis cleanup"):
        smoke.close_native_resources(
            [],
            [],
            None,
            resources,
            web_origin="https://web-native-own.example.test",
            web_before={"preexisting"},
        )
    resources.command.assert_not_called()


@pytest.mark.parametrize("mismatch", ["sha", "dirty", "gitlink"])
def test_source_identity_and_clean_gitlink_gates_remain_strict(monkeypatch, mismatch):
    expected = "a" * 40
    monkeypatch.setattr(
        smoke.runtime,
        "command_output",
        Mock(
            side_effect=[
                "b" * 40 if mismatch == "sha" else expected,
                " M source.ts" if mismatch == "dirty" else "",
                "160000 commit "
                + ("c" * 40 if mismatch == "gitlink" else expected)
                + "\tapps/kokoro-app",
            ]
        ),
    )
    with pytest.raises(smoke.SmokeError):
        smoke.verify_source(smoke.APP, expected, "apps/kokoro-app")


def test_partial_build_failure_persists_only_sanitized_receipt(tmp_path, monkeypatch):
    args = prepare_main(tmp_path, monkeypatch)
    resources = resources_fixture()
    monkeypatch.setattr(smoke.runtime, "OwnedResources", lambda *_: resources)

    def failed_build(*_, **kwargs):
        kwargs["log"].write(args.postgres_admin_url.encode())
        raise RuntimeError(args.redis_url + " secret-cookie")

    monkeypatch.setattr(smoke, "run_native_command", failed_build, raising=False)
    with pytest.raises(smoke.SmokeError) as caught:
        smoke.main([])
    receipt, path = read_receipt(tmp_path)
    assert receipt["stage"] == "BFF build"
    assert receipt["status"] == "failed"
    assert receipt["cleanup"]["status"] == "passed"
    assert receipt["cleanup"]["quiescent"] is True
    assert receipt["completed_checks"] == 0
    assert path.stat().st_mode & 0o777 == 0o600
    for file in (tmp_path / "evidence").rglob("*"):
        if file.is_file():
            assert b"secret" not in file.read_bytes()
            assert b"postgresql:" not in file.read_bytes()
    assert "secret" not in str(caught.value)
    resources.cleanup.assert_called_once()


def test_live_consumer_preserves_iam_provider_and_credentials(monkeypatch):
    provider, consumer = object(), object()
    stopped = []

    def stop(process):
        stopped.append(process)
        if process is consumer:
            raise RuntimeError("still live")

    monkeypatch.setattr(smoke.runtime, "stop_owned_process", stop)
    resources = resources_fixture()
    with pytest.raises(smoke.SmokeError) as caught:
        smoke.close_native_resources(
            [provider, consumer], [], None, resources, iam_process=provider
        )
    assert stopped == [consumer]
    assert caught.value.quiescent is False
    resources.cleanup.assert_not_called()


def test_failed_build_or_schema_command_remains_tracked_for_teardown(
    tmp_path, monkeypatch
):
    process = SimpleNamespace(
        wait=Mock(side_effect=smoke.subprocess.TimeoutExpired("fixture", 1))
    )
    monkeypatch.setattr(smoke.subprocess, "Popen", Mock(return_value=process))
    processes = []
    with pytest.raises(smoke.SmokeError):
        smoke.run_native_command(
            ["fixture"], cwd=tmp_path, env={}, log=None, processes=processes
        )
    assert processes == [process]


def simulate_main(
    tmp_path,
    monkeypatch,
    *,
    fail_stop=False,
    fail_cleanup=False,
    browser_driver=None,
    succeeds=False,
    native_success=False,
):
    args = prepare_main(tmp_path, monkeypatch)
    args.browser_journeys = browser_driver is not None
    if browser_driver is not None:
        monkeypatch.setattr(
            smoke, "run_browser_journeys", browser_driver, raising=False
        )
    resources = resources_fixture()
    if fail_cleanup:
        resources.cleanup.side_effect = RuntimeError("database cleanup unavailable")
    resources.create_database = lambda _: "postgresql://localhost/own"
    resources.command = lambda cmd: "PONG" if cmd[-1] == "PING" else ""
    monkeypatch.setattr(smoke.runtime, "OwnedResources", lambda *_: resources)
    monkeypatch.setattr(smoke.session, "node_environment", lambda *_: {})
    monkeypatch.setattr(
        smoke,
        "observe_node_version",
        lambda node: "22.23.4" if node == args.web_node_bin else "24.20.0",
    )
    monkeypatch.setattr(
        smoke, "run_native_command", lambda *_, **__: None, raising=False
    )
    monkeypatch.setattr(smoke.runtime, "install_schema", lambda *_: None)
    monkeypatch.setattr(smoke.runtime, "run_owned_command", lambda *_, **__: 0)
    monkeypatch.setattr(smoke.web, "iam_owned_inventory", lambda *_: (set(), set()))
    monkeypatch.setattr(smoke.runtime, "wait_ready", lambda *_: None)
    monkeypatch.setattr(smoke.runtime, "free_port", lambda: 1234)
    monkeypatch.setattr(smoke.web, "certificate", lambda *_: None)
    monkeypatch.setattr(smoke.web, "isolated_next", lambda directory: directory)
    proxy_factory = Mock(
        side_effect=lambda *_, **__: SimpleNamespace(
            server_port=1234, close=lambda: None
        )
    )
    monkeypatch.setattr(smoke.web, "Proxy", proxy_factory)
    monkeypatch.setattr(
        smoke.web,
        "https_browser",
        (lambda *_args, **_kwargs: SimpleNamespace(status=200, body=b"{}"))
        if browser_driver is not None
        else lambda *_: (_ for _ in ()).throw(
            RuntimeError("failed-http secret-cookie")
        ),
    )
    made = []
    environments = []
    credential = []

    def popen(*_, **kwargs):
        import io

        process = SimpleNamespace(
            stdin=io.BytesIO(),
            stdout=SimpleNamespace(fileno=lambda: 1, close=lambda: None),
            poll=lambda: None,
        )
        made.append(process)
        environments.append(kwargs["env"])
        if len(made) == 1:
            file = Path(kwargs["env"]["TMPDIR"]) / "receiver.json"
            file.write_text(json.dumps({"entries": [{"secret": "receiver-secret"}]}))
            credential.append(file)
        return process

    monkeypatch.setattr(smoke.subprocess, "Popen", popen)
    monkeypatch.setattr(smoke.runtime, "start_process", lambda *a: popen(env=a[2]))
    reader = SimpleNamespace(
        record=lambda: {
            "kind": "ready",
            "base_url": "http://127.0.0.1:1234",
            "access_token": "access-secret",
            "tenant_id": "tenant",
            "user_id": "user",
        },
        close=lambda: None,
    )
    monkeypatch.setattr(smoke.session, "ProtocolReader", lambda _: reader)
    monkeypatch.setattr(
        smoke,
        "native_command",
        lambda *_: smoke.NativeReceipt(
            "kokoro-issuer.session_token=cookie-secret",
            str(credential[0]),
            environments[0]["IAM_TEST_WEB_ORIGIN"],
        ),
    )
    stopped = []

    def stop(process):
        stopped.append(process)
        if fail_stop and process is made[1]:
            raise RuntimeError("still live")

    monkeypatch.setattr(smoke.runtime, "stop_owned_process", stop)
    if native_success:
        ready_record = reader.record()
        reader.record = Mock(
            side_effect=[
                ready_record,
                {"kind": "result", "command": "signout", "status": "ok"},
            ]
        )
        responses = [
            (200, {}),
            (
                200,
                {
                    "authenticated": True,
                    "mode": "native",
                    "subject": "user",
                    "expires_at": 123,
                },
            ),
            (200, {"projects": []}),
            (401, {"error": {"code": "native_session_required"}}),
        ]
        monkeypatch.setattr(
            smoke.web,
            "https_browser",
            Mock(
                side_effect=[
                    SimpleNamespace(status=status, body=json.dumps(body).encode())
                    for status, body in responses
                ]
            ),
        )
    if succeeds:
        assert smoke.main([]) == 0
    else:
        with pytest.raises(smoke.SmokeError):
            smoke.main([])
    # Only browser mode's Web instance opts in; the default remains HTTP-only.
    assert len(proxy_factory.call_args_list) == 2
    assert proxy_factory.call_args_list[0].kwargs == {}
    assert proxy_factory.call_args.kwargs == {"hmr_websocket": args.browser_journeys}
    return args, resources, made, environments, credential, stopped


@pytest.mark.parametrize("fail_stop", [False, True])
def test_partial_web_start_tracks_redis_and_retains_files_only_if_not_quiescent(
    tmp_path, monkeypatch, fail_stop
):
    args, resources, processes, environments, credential, stopped = simulate_main(
        tmp_path, monkeypatch, fail_stop=fail_stop
    )
    assert environments[-1]["KOKORO_WEB_REDIS_URL"] == args.redis_url
    assert "IAM_TEST_RESOURCE_ID" in environments[0]
    assert "IAM_TEST_RESOURCE_OWNER_TOKEN" in environments[0]
    receipt, path = read_receipt(tmp_path)
    assert receipt["stage"] == "Web HTTPS preflight"
    assert receipt["cleanup"]["quiescent"] is not fail_stop
    assert credential[0].exists() is fail_stop
    assert "secret" not in path.read_text()
    if fail_stop:
        assert processes[0] not in stopped
        resources.cleanup.assert_not_called()
    else:
        assert stopped == processes[::-1]
        resources.cleanup.assert_called_once()


def test_force_stop_iam_avoids_eof_graceful_deletion_when_consumer_lives(monkeypatch):
    provider = SimpleNamespace(pid=42, wait=Mock(return_value=-9))
    consumer = SimpleNamespace(pid=43)
    kill = Mock()
    monkeypatch.setattr(smoke.os, "killpg", kill)
    monkeypatch.setattr(smoke.runtime, "process_group_exists", Mock(return_value=False))
    monkeypatch.setattr(
        smoke.runtime,
        "stop_owned_process",
        Mock(side_effect=RuntimeError("consumer live")),
    )
    resources = resources_fixture()
    with pytest.raises(smoke.SmokeError) as caught:
        smoke.close_native_resources(
            [provider, consumer], [], None, resources, iam_process=provider
        )
    kill.assert_called_once_with(42, 9)
    provider.wait.assert_called_once_with(timeout=5)
    assert caught.value.quiescent is False
    resources.cleanup.assert_not_called()


def test_quiescent_cleanup_closes_protocol_pipes_after_reader(monkeypatch):
    events = []
    process = SimpleNamespace(
        stdin=SimpleNamespace(close=lambda: events.append("stdin")),
        stdout=SimpleNamespace(close=lambda: events.append("stdout")),
    )
    reader = SimpleNamespace(close=lambda: events.append("reader"))
    monkeypatch.setattr(
        smoke.runtime, "stop_owned_process", lambda _: events.append("stop")
    )
    smoke.close_native_resources([process], [], reader, resources_fixture())
    assert events == ["stop", "reader", "stdin", "stdout"]


def test_source_failure_never_claims_runtime_versions(tmp_path, monkeypatch):
    prepare_main(tmp_path, monkeypatch)
    monkeypatch.setattr(
        smoke, "verify_source", Mock(side_effect=RuntimeError("source"))
    )
    with pytest.raises(smoke.SmokeError):
        smoke.main([])
    receipt, _ = read_receipt(tmp_path)
    assert receipt["node_versions"] == {"iam": None, "bff": None, "app": None}
    assert receipt["required_node_versions"] == {
        "iam": "24.20.0",
        "bff": "24.20.0",
        "app": "22.23.4",
    }


def test_inventory_failure_still_kills_and_waits_for_exact_owned_iam(monkeypatch):
    provider = SimpleNamespace(pid=42, wait=Mock(return_value=-9))
    consumer = SimpleNamespace(pid=43)
    kill = Mock()
    monkeypatch.setattr(smoke.os, "killpg", kill)
    monkeypatch.setattr(
        smoke.runtime,
        "process_group_exists",
        Mock(side_effect=OSError("ps unavailable")),
    )
    monkeypatch.setattr(
        smoke.runtime,
        "stop_owned_process",
        Mock(side_effect=RuntimeError("consumer live")),
    )
    resources = resources_fixture()
    with pytest.raises(smoke.NativeCleanupError) as caught:
        smoke.close_native_resources(
            [provider, consumer], [], None, resources, iam_process=provider
        )
    kill.assert_called_once_with(42, smoke.signal.SIGKILL)
    provider.wait.assert_called_once_with(timeout=5)
    assert caught.value.quiescent is False
    resources.cleanup.assert_not_called()


def test_retained_dependencies_have_private_exact_recovery_record(
    tmp_path, monkeypatch
):
    args, _, _, environments, _, _ = simulate_main(
        tmp_path, monkeypatch, fail_stop=True
    )
    receipt, receipt_path = read_receipt(tmp_path)
    index = receipt["cleanup"]["recovery_record"]
    record_path = receipt_path.parent / index
    record = json.loads(record_path.read_text())
    resource_id = environments[0]["IAM_TEST_RESOURCE_ID"]
    token = environments[0]["IAM_TEST_RESOURCE_OWNER_TOKEN"]
    assert record == {
        "resource_id": resource_id,
        "database_name": "iam_web_oidc_" + resource_id.replace("-", ""),
        "redis_prefix": f"iam:test:bff-session-admission-host:{resource_id}:",
        "owner_token": token,
    }
    assert record_path.stat().st_mode & 0o777 == 0o600
    assert record_path.parent.stat().st_mode & 0o777 == 0o700
    assert token not in receipt_path.read_text()
    assert args.postgres_admin_url not in record_path.read_text()
    assert args.redis_url not in record_path.read_text()


def test_successful_cleanup_removes_private_recovery_record(tmp_path, monkeypatch):
    simulate_main(tmp_path, monkeypatch)
    receipt, path = read_receipt(tmp_path)
    assert receipt["cleanup"]["recovery_record"] is None
    assert list(path.parent.iterdir()) == [path]


def test_source_failure_keeps_expected_and_previously_observed_owners(
    tmp_path, monkeypatch
):
    args = prepare_main(tmp_path, monkeypatch)
    iam_observation = {
        "sha": args.expected_iam_sha,
        "clean": True,
        "root_gitlink_matches": True,
    }
    monkeypatch.setattr(
        smoke,
        "verify_source",
        Mock(side_effect=[iam_observation, RuntimeError("source failure")]),
    )
    with pytest.raises(smoke.SmokeError):
        smoke.main([])
    receipt, _ = read_receipt(tmp_path)
    assert receipt["sources"] == {"iam": iam_observation}
    assert receipt["expected_sources"] == {
        "iam": args.expected_iam_sha,
        "bff": args.expected_bff_sha,
        "app": args.expected_app_sha,
    }
    assert receipt["node_versions"] == {"iam": None, "bff": None, "app": None}


def test_quiescent_but_failed_dependency_cleanup_retains_recovery(
    tmp_path, monkeypatch
):
    simulate_main(tmp_path, monkeypatch, fail_cleanup=True)
    receipt, path = read_receipt(tmp_path)
    assert receipt["cleanup"]["quiescent"] is True
    assert receipt["cleanup"]["status"] == "failed"
    assert (path.parent / receipt["cleanup"]["recovery_record"]).is_file()


def test_missing_owned_iam_process_group_still_reaps_child(monkeypatch):
    provider = SimpleNamespace(pid=42, wait=Mock(return_value=-9))
    consumer = SimpleNamespace(pid=43)
    monkeypatch.setattr(smoke.os, "killpg", Mock(side_effect=ProcessLookupError()))
    monkeypatch.setattr(smoke.runtime, "process_group_exists", Mock(return_value=False))
    monkeypatch.setattr(
        smoke.runtime,
        "stop_owned_process",
        Mock(side_effect=RuntimeError("consumer live")),
    )
    with pytest.raises(smoke.NativeCleanupError) as caught:
        smoke.close_native_resources(
            [provider, consumer], [], None, resources_fixture(), iam_process=provider
        )
    provider.wait.assert_called_once_with(timeout=5)
    assert "IAM forced process cleanup failed" not in caught.value.failures
    assert caught.value.quiescent is False


def test_invalid_runtime_probe_output_is_not_copied_into_receipt(tmp_path, monkeypatch):
    args = prepare_main(tmp_path, monkeypatch)
    args.iam_node_bin = node_fixture(tmp_path, "invalid-node", "private-not-a-version")
    resources = Mock()
    monkeypatch.setattr(smoke.runtime, "OwnedResources", resources)
    with pytest.raises(smoke.SmokeError):
        smoke.main([])
    resources.assert_not_called()
    receipt, path = read_receipt(tmp_path)
    assert receipt["node_versions"] == {"iam": None, "bff": None, "app": None}
    assert "private-not-a-version" not in path.read_text()


# Browser-mode orchestration boundaries; all fixtures below remain process-local.
def native_cli_args(tmp_path):
    args = arguments(tmp_path)
    result = []
    for name in (
        "postgres_admin_url",
        "redis_url",
        "iam_node_bin",
        "bff_node_bin",
        "web_node_bin",
        "expected_iam_sha",
        "expected_bff_sha",
        "expected_app_sha",
    ):
        result.extend(["--" + name.replace("_", "-"), str(getattr(args, name))])
    return result


@pytest.mark.parametrize("selected", [False, True])
def test_browser_journeys_are_explicit_opt_in(tmp_path, selected):
    argv = native_cli_args(tmp_path)
    if selected:
        argv.append("--browser-journeys")
    args = smoke.parse_args(argv)
    assert getattr(args, "browser_journeys", None) is selected


def browser_broker(tmp_path, responses):
    broker_type = getattr(smoke, "BrowserBroker", None)
    assert callable(broker_type), (
        "browser commands need the bounded private owner broker"
    )
    stream_path = tmp_path / "owner-pipe"
    stream = stream_path.open("w+b", buffering=0)
    stream.getvalue = stream_path.read_bytes
    process = SimpleNamespace(stdin=stream)
    reader = SimpleNamespace(record=Mock(side_effect=responses))
    credentials = smoke.web.previous.CredentialRegistry()
    broker = broker_type(process, reader, credentials=credentials, timeout=0.25)
    return broker, process, reader, credentials


def test_browser_fixture_and_bound_cookie_stay_in_private_protocol(tmp_path, capsys):
    credential_file = tmp_path / "receiver.json"
    credential_file.write_text("{}")
    fixture = {
        "kind": "browser_fixture",
        "email": "fixture@example.test",
        "password": "private-browser-password",
        "tenant_id": "fixed-tenant",
        "credential_file": str(credential_file),
        "web_origin": "https://web-native-fixture.example.test",
    }
    bound = {"kind": "result", "command": "bind_browser_session", "status": "ok"}
    broker, process, reader, credentials = browser_broker(tmp_path, [fixture, bound])
    assert broker.dispatch({"command": "browser_fixture"}) == fixture
    cookie = "kokoro-issuer.session_token=private-browser-cookie"
    assert (
        broker.dispatch(
            {
                "command": "bind_browser_session",
                "slot": "primary",
                "cookie": cookie,
            }
        )
        == bound
    )
    assert [json.loads(line) for line in process.stdin.getvalue().splitlines()] == [
        {"command": "browser_fixture"},
        {"command": "bind_browser_session", "slot": "primary", "cookie": cookie},
    ]
    assert "private-browser-password" in credentials.values()
    assert "private-browser-cookie" in credentials.values()
    assert all(
        call.kwargs.get("timeout", call.args[0] if call.args else None) <= 0.25
        for call in reader.record.call_args_list
    )
    captured = capsys.readouterr()
    assert "private-browser" not in captured.out + captured.err


@pytest.mark.parametrize(
    "command",
    [
        {"command": "reset"},
        {"command": "stop"},
        {"command": "native"},
        {"command": "signout"},
        {"command": "browser_fixture", "sql": "DELETE"},
        {"command": "bind_browser_session", "slot": "third", "cookie": "x"},
        {
            "command": "bind_browser_session",
            "slot": "primary",
            "cookie": "kokoro-issuer.session_token=x; arbitrary=y",
        },
        {
            "command": "bind_browser_session",
            "slot": "primary",
            "cookie": "kokoro-issuer.session_token=x\nsecret",
        },
        {
            "command": "activate_browser_tenant",
            "slot": "primary",
            "tenant": "arbitrary",
        },
        {"command": "revoke_browser_membership", "user_id": "someone-else"},
    ],
)
def test_browser_broker_rejects_unapproved_commands_without_owner_io(tmp_path, command):
    broker, process, reader, _ = browser_broker(tmp_path, [])
    with pytest.raises(smoke.SmokeError):
        broker.dispatch(command)
    assert process.stdin.getvalue() == b""
    reader.record.assert_not_called()


@pytest.mark.parametrize(
    "response",
    [
        {"kind": "result", "command": "revoke_browser_session", "status": "ok"},
        {
            "kind": "result",
            "command": "activate_browser_tenant",
            "status": "ok",
            "cookie": "secret",
        },
        {"kind": "error", "code": "mutation_rejected"},
        {
            "kind": "browser_session",
            "slot": "primary",
            "exists": True,
            "member": True,
            "active_tenant": "other",
        },
    ],
)
def test_browser_broker_rejects_owner_error_or_response_drift(tmp_path, response):
    broker, _, _, _ = browser_broker(tmp_path, [response])
    with pytest.raises(smoke.SmokeError) as caught:
        broker.dispatch(
            {"command": "activate_browser_tenant", "slot": "primary", "tenant": "other"}
        )
    assert "secret" not in str(caught.value)


def complete_browser_result():
    fixed = {
        "exists": True,
        "unexpired": True,
        "member": True,
        "active_tenant": "fixed",
    }
    deleted = {
        "exists": False,
        "unexpired": False,
        "member": True,
        "active_tenant": "none",
    }
    return {
        "kind": "browser_result",
        "journeys": {
            "cold_login": {
                "initial_issuer_cookies": 0,
                "sign_in_status": 303,
                "session_status": 200,
                "authenticated": True,
                "projects_status": 200,
                "profile_status": 200,
                "profile_visible": True,
                "owner": dict(fixed),
            },
            "tenant_rejection_recovery": {
                "foreign_owner": {**fixed, "active_tenant": "other"},
                "pre_mutation_profile_visible": True,
                "session_status": 401,
                "session_error_code": "native_session_required",
                "projects_status": 403,
                "projects_error_code": "product_tenant_forbidden",
                "private_ui_retired": True,
                "relogin_status": 303,
                "recovered_session_status": 200,
                "recovered_projects_status": 200,
                "recovered_profile_status": 200,
                "recovered_profile_visible": True,
                "recovered_owner": dict(fixed),
            },
            "ui_logout": {
                "clicked": True,
                "sign_out_status": 200,
                "owner": {**fixed, "unexpired": False},
                "issuer_cookies": 0,
                "session_status": 200,
                "authenticated": False,
                "projects_status": 401,
                "old_cookie_status": 401,
            },
            "independent_revocation": {
                "a_owner": dict(deleted),
                "a_session_status": 401,
                "a_projects_status": 401,
                "a_private_ui_retired": True,
                "b_session_status_before_membership": 200,
                "b_owner_before_membership": dict(fixed),
                "b_owner_after_membership": {**fixed, "member": False},
                "b_session_status": 401,
                "b_projects_status": 401,
                "private_ui_retired": True,
            },
        },
        "race": {
            "upstream_profile_status": 200,
            "observation": "cancelled",
            "private_ui_retired": True,
            "cross_tab_focus": True,
        },
    }


def browser_result_validator():
    validator = getattr(smoke, "validate_browser_receipt", None)
    assert callable(validator), "browser receipt must fail closed before final success"
    return validator


@pytest.mark.parametrize("observation", ["cancelled", "delivered_and_retired"])
def test_browser_receipt_accepts_four_journeys_and_observed_race(observation):
    result = complete_browser_result()
    result["race"]["observation"] = observation
    assert browser_result_validator()(result) == result


def test_browser_receipt_rejects_obsolete_tenant_401_without_typed_codes():
    receipt = complete_browser_result()
    journey = receipt["journeys"]["tenant_rejection_recovery"]
    journey["projects_status"] = 401
    journey.pop("session_error_code")
    journey.pop("projects_error_code")
    with pytest.raises(smoke.SmokeError):
        smoke.validate_browser_receipt(receipt)


@pytest.mark.parametrize(
    "field,value",
    [
        ("session_status", 200),
        ("session_status", 403),
        ("projects_status", 200),
        ("projects_status", 401),
        ("session_error_code", "product_tenant_forbidden"),
        ("projects_error_code", "native_session_required"),
        ("session_error_code", "other_error"),
        ("projects_error_code", "other_error"),
        ("session_error_code", None),
        ("projects_error_code", None),
        ("session_error_code", 401),
        ("projects_error_code", 403),
    ],
)
def test_browser_receipt_requires_exact_tenant_status_and_typed_codes(field, value):
    receipt = complete_browser_result()
    journey = receipt["journeys"]["tenant_rejection_recovery"]
    if value is None:
        journey.pop(field)
    else:
        journey[field] = value
    with pytest.raises(smoke.SmokeError):
        smoke.validate_browser_receipt(receipt)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "failed",
        "unknown",
        "secret",
        "race",
        "retired",
        "focus",
        "bool_status",
    ],
)
def test_browser_receipt_rejects_incomplete_failed_or_sensitive_results(mutation):
    result = complete_browser_result()
    if mutation == "missing":
        result["journeys"].pop("ui_logout")
    elif mutation == "failed":
        result["journeys"]["independent_revocation"]["a_session_status"] = 200
    elif mutation == "unknown":
        result["journeys"]["unobserved"] = {"status": "passed"}
    elif mutation == "secret":
        result["journeys"]["cold_login"]["cookie"] = "private-cookie"
    elif mutation == "bool_status":
        result["journeys"]["cold_login"]["initial_issuer_cookies"] = False
    else:
        key = {
            "race": "observation",
            "retired": "private_ui_retired",
            "focus": "cross_tab_focus",
        }[mutation]
        result["race"].pop(key)
    validator = browser_result_validator()
    with pytest.raises(smoke.SmokeError) as caught:
        validator(result)
    assert "private-cookie" not in str(caught.value)


@pytest.mark.parametrize("result", [None, "missing", "failed"])
def test_browser_failure_reaches_main_failure_and_sanitized_receipt(
    tmp_path, monkeypatch, result
):
    if result is None:
        driver = Mock(side_effect=smoke.SmokeError("private-browser-password"))
    else:
        receipt = complete_browser_result()
        if result == "missing":
            receipt["journeys"].pop("ui_logout")
        else:
            receipt["journeys"]["ui_logout"]["old_cookie_status"] = 200
        driver = Mock(return_value=receipt)
    _, resources, _, _, _, _ = simulate_main(
        tmp_path, monkeypatch, browser_driver=driver
    )
    driver.assert_called_once()
    report, path = read_receipt(tmp_path)
    assert report["mode"] == "browser_journeys"
    assert report["status"] == "failed"
    assert report["completed_journeys"] < 4
    assert report["credential_log_check"] in {"passed", "failed"}
    assert "private-browser" not in path.read_text()
    resources.cleanup.assert_called_once()


def test_minimal_mode_receipt_does_not_claim_browser_journeys(tmp_path, monkeypatch):
    simulate_main(tmp_path, monkeypatch)
    report, _ = read_receipt(tmp_path)
    assert report["mode"] == "minimal_http"
    assert report["completed_journeys"] == 0
    assert "not browser" in report["scope"]


@pytest.mark.parametrize("group_remains", [False, True])
def test_browser_group_quiescence_precedes_owner_and_database_cleanup(
    monkeypatch, group_remains
):
    import inspect

    assert (
        "browser_process" in inspect.signature(smoke.close_native_resources).parameters
    ), "browser process group must be a cleanup dependency, including timeout paths"
    events = []
    browser = SimpleNamespace(pid=400, wait=lambda **_: events.append("browser-reap"))
    owner = SimpleNamespace(pid=401, wait=lambda **_: events.append("owner-reap"))
    proxy = SimpleNamespace(close=lambda: events.append("proxy"))
    resources = resources_fixture()
    resources.cleanup.side_effect = lambda: events.append("database")
    monkeypatch.setattr(
        smoke.runtime,
        "stop_owned_process",
        lambda process: events.append(
            "browser-stop" if process is browser else "owner-stop"
        ),
    )

    def group_exists(pid):
        events.append(
            "browser-group-check" if pid == browser.pid else "owner-group-check"
        )
        return group_remains if pid == browser.pid else False

    monkeypatch.setattr(smoke.runtime, "process_group_exists", group_exists)
    monkeypatch.setattr(
        smoke.os, "killpg", lambda *_: events.append("owner-force-stop")
    )
    kwargs = dict(iam_process=owner, browser_process=browser)
    if group_remains:
        with pytest.raises(smoke.NativeCleanupError) as caught:
            smoke.close_native_resources(
                [owner, browser], [proxy], None, resources, **kwargs
            )
        assert caught.value.quiescent is False
        assert "owner-stop" not in events
        resources.cleanup.assert_not_called()
    else:
        smoke.close_native_resources(
            [owner, browser], [proxy], None, resources, **kwargs
        )
        assert (
            events.index("browser-group-check")
            < events.index("owner-stop")
            < events.index("database")
        )
    assert (
        events.index("browser-stop")
        < events.index("browser-group-check")
        < events.index("proxy")
    )


@pytest.mark.parametrize("failure", ["timeout", "malformed", "eof"])
def test_browser_driver_failure_is_tracked_before_protocol_and_has_no_secret_args(
    tmp_path, monkeypatch, failure
):
    import io

    run = getattr(smoke, "run_browser_journeys", None)
    assert callable(run), (
        "browser subprocess must be tracked before a bounded protocol read"
    )
    processes, browsers = [], []
    process = SimpleNamespace(
        pid=420,
        stdin=(tmp_path / "driver-pipe").open("w+b", buffering=0),
        stdout=SimpleNamespace(fileno=lambda: 13),
        wait=Mock(return_value=1),
        poll=lambda: None,
    )
    launches = []

    def popen(command, **kwargs):
        launches.append((command, kwargs))
        assert "private-browser-password" not in repr(command)
        assert "private-browser-cookie" not in repr(command)
        assert kwargs["stdin"] == smoke.subprocess.PIPE
        assert kwargs["stdout"] == smoke.subprocess.PIPE
        assert kwargs["start_new_session"] is True
        return process

    monkeypatch.setattr(smoke.subprocess, "Popen", popen)

    def record(timeout=90):
        assert process in processes and process in browsers
        assert 0 < timeout <= 0.25
        if failure == "malformed":
            return {"kind": "arbitrary", "password": "private-browser-password"}
        raise smoke.session.SmokeError("IAM host protocol " + failure)

    reader = SimpleNamespace(record=record, close=Mock())
    monkeypatch.setattr(smoke.session, "ProtocolReader", lambda _: reader)
    broker = SimpleNamespace(dispatch=Mock())
    with pytest.raises(smoke.SmokeError) as caught:
        run(
            node=tmp_path / "node",
            env={},
            broker=broker,
            web_origin="https://web-native-fixture.example.test",
            proxy_port=1234,
            processes=processes,
            browser_processes=browsers,
            log=io.BytesIO(),
            work_dir=tmp_path,
            timeout=0.25,
        )
    assert launches and processes == [process] and browsers == [process]
    assert "private-browser" not in str(caught.value)
    reader.close.assert_called_once()


@pytest.mark.parametrize("unexpired", [None, "true", True])
def test_browser_broker_requires_exact_owner_expiration_fact(tmp_path, unexpired):
    response = {
        "kind": "browser_session",
        "slot": "primary",
        "exists": True,
        "member": True,
        "active_tenant": "fixed",
    }
    if unexpired is not None:
        response["unexpired"] = unexpired
    broker, _, _, _ = browser_broker(tmp_path, [response])
    if unexpired is True:
        assert (
            broker.dispatch({"command": "inspect_browser_session", "slot": "primary"})
            == response
        )
    else:
        with pytest.raises(smoke.SmokeError):
            broker.dispatch({"command": "inspect_browser_session", "slot": "primary"})


def test_browser_success_keeps_four_journeys_separate_from_credential_scan(
    tmp_path, monkeypatch
):
    driver = Mock(return_value=complete_browser_result())
    simulate_main(tmp_path, monkeypatch, browser_driver=driver, succeeds=True)
    report, _ = read_receipt(tmp_path)
    assert report["status"] == "passed"
    assert report["mode"] == "browser_journeys"
    assert report["completed_journeys"] == 4
    assert report["completed_checks"] == 0
    assert report["credential_log_check"] == "passed"
    assert report["browser"] == complete_browser_result()


def test_browser_driver_reports_only_allowlisted_failure_stage(tmp_path, monkeypatch):
    import io

    process = SimpleNamespace(
        pid=421,
        stdin=(tmp_path / "driver-pipe").open("w+b", buffering=0),
        stdout=SimpleNamespace(fileno=lambda: 13),
        poll=lambda: None,
    )
    monkeypatch.setattr(smoke.subprocess, "Popen", lambda *_args, **_kwargs: process)
    reader = SimpleNamespace(
        record=lambda **_: {
            **browser_failure_record(),
            "stage": "tenant_rejection_recovery",
        },
        close=lambda: None,
    )
    monkeypatch.setattr(smoke.session, "ProtocolReader", lambda _: reader)
    with pytest.raises(smoke.SmokeError, match="tenant_rejection_recovery"):
        smoke.run_browser_journeys(
            node=tmp_path / "node",
            env={},
            broker=None,
            web_origin="https://web-native-fixture.example.test",
            proxy_port=1234,
            processes=[],
            browser_processes=[],
            log=io.BytesIO(),
            work_dir=tmp_path,
        )


def test_browser_login_pacing_respects_owner_window_without_real_sleep(tmp_path):
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const {waitForLoginSlot} = await import(process.argv[1]);
      let now = 1500;
      const waits = [];
      const clock = {now: () => now, sleep: async ms => { waits.push(ms); now += ms; }};
      await waitForLoginSlot([100, 200], 20000, clock);
      assert.deepEqual(waits, []);
      const completed = [100, 200, 1000];
      await waitForLoginSlot(completed, 20000, clock);
      assert.ok(now >= 11000);
      assert.equal(waits.length, 1);
      assert.deepEqual(completed, []);
      await assert.rejects(() => waitForLoginSlot([now, now, now], now + 100, clock));
      assert.equal(waits.length, 1);
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri()],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("remaining", [60_000, 60_001, 60_002, 175_000])
def test_browser_native_admission_window_preserves_overall_deadline(remaining):
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const {waitForNativeAdmissionWindow} = await import(process.argv[1]);
      assert.equal(typeof waitForNativeAdmissionWindow, 'function');
      const remaining = Number(process.argv[2]);
      let now = 1500;
      const deadline = now + remaining;
      const waits = [];
      const clock = {now: () => now, sleep: async ms => { waits.push(ms); now += ms; }};
      if (remaining <= 60001) {
        await assert.rejects(() => waitForNativeAdmissionWindow(deadline, clock), /browser journey failed/);
        assert.deepEqual(waits, []);
        assert.equal(now, 1500);
      } else {
        await waitForNativeAdmissionWindow(deadline, clock);
        assert.deepEqual(waits, [60001]);
        assert.equal(now, 61501);
        assert.ok(now < deadline);
      }
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri(), str(remaining)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "completion", ["rejected", "early", "window_elapsed", "deadline", "late"]
)
def test_browser_native_admission_window_checks_sleep_completion(completion):
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const {waitForNativeAdmissionWindow} = await import(process.argv[1]);
      assert.equal(typeof waitForNativeAdmissionWindow, 'function');
      const completion = process.argv[2];
      let now = 1500;
      const deadline = now + 60002;
      const waits = [];
      const failure = new Error('fixture sleep failure');
      const clock = {now: () => now, sleep: async ms => {
        waits.push(ms);
        if (completion === 'rejected') throw failure;
        now += {early: 59999, window_elapsed: 60000, deadline: 60002, late: 60003}[completion];
      }};
      if (completion === 'window_elapsed') {
        await waitForNativeAdmissionWindow(deadline, clock);
      } else {
        await assert.rejects(
          () => waitForNativeAdmissionWindow(deadline, clock),
          error => completion === 'rejected' ? error === failure : error.message === 'browser journey failed',
        );
      }
      assert.deepEqual(waits, [60001]);
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri(), completion],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


def test_minimal_default_preserves_three_http_checks_plus_log_scan(
    tmp_path, monkeypatch
):
    simulate_main(tmp_path, monkeypatch, native_success=True, succeeds=True)
    report, _ = read_receipt(tmp_path)
    assert report["status"] == "passed"
    assert report["mode"] == "minimal_http"
    assert report["completed_checks"] == 4
    assert report["completed_journeys"] == 0
    assert report["browser"] is None
    assert report["credential_log_check"] == "passed"


@pytest.mark.parametrize(
    "scenario", ["success", "exit_failure", "oversized", "timeout"]
)
def test_browser_process_private_pipe_is_bounded_and_exit_status_matters(
    tmp_path, scenario
):
    import tempfile

    executable = tmp_path / "protocol-child"
    lines = [
        "#!" + sys.executable,
        "import json, sys, time",
        "json.loads(sys.stdin.readline())",
    ]
    if scenario == "timeout":
        lines.append("time.sleep(60)")
    elif scenario == "oversized":
        lines.append("sys.stdout.write('x' * 100000); sys.stdout.flush()")
    else:
        lines.extend(
            [
                "print(json.dumps("
                + repr(complete_browser_result())
                + "), flush=True)",
                "sys.exit(" + ("9" if scenario == "exit_failure" else "0") + ")",
            ]
        )
    executable.write_text("\n".join(lines) + "\n")
    executable.chmod(0o700)
    processes, browsers = [], []
    try:
        with tempfile.TemporaryFile() as log:
            kwargs = dict(
                node=executable,
                env={},
                broker=None,
                web_origin="https://web-native-fixture.example.test",
                proxy_port=1234,
                processes=processes,
                browser_processes=browsers,
                log=log,
                work_dir=tmp_path,
                timeout=0.25 if scenario == "timeout" else 3,
            )
            if scenario == "success":
                assert smoke.run_browser_journeys(**kwargs) == complete_browser_result()
            else:
                with pytest.raises(smoke.SmokeError):
                    smoke.run_browser_journeys(**kwargs)
    finally:
        assert len(browsers) == 1 and processes == browsers
        smoke.close_native_resources(
            processes, [], None, None, browser_process=browsers[0]
        )
        assert not smoke.runtime.process_group_exists(browsers[0].pid)


def test_browser_receipt_rejects_nonscalar_observation_without_reflecting_payload():
    receipt = complete_browser_result()
    receipt["race"]["observation"] = ["private-value"]
    with pytest.raises(smoke.SmokeError) as caught:
        smoke.validate_browser_receipt(receipt)
    assert "private-value" not in str(caught.value)


@pytest.mark.parametrize("visible", [None, False])
def test_browser_tenant_retirement_requires_visible_private_data_before_mutation(
    visible,
):
    receipt = complete_browser_result()
    journey = receipt["journeys"]["tenant_rejection_recovery"]
    if visible is None:
        journey.pop("pre_mutation_profile_visible")
    else:
        journey["pre_mutation_profile_visible"] = visible
    with pytest.raises(smoke.SmokeError):
        smoke.validate_browser_receipt(receipt)


def test_browser_cleanup_reaps_driver_before_quiescence_inventory(monkeypatch):
    events = []
    browser = SimpleNamespace(pid=490, wait=lambda **_: events.append("reaped"))
    monkeypatch.setattr(
        smoke.runtime, "stop_owned_process", lambda _: events.append("stopped")
    )

    def group_exists(_):
        events.append("inventory")
        return "reaped" not in events

    monkeypatch.setattr(smoke.runtime, "process_group_exists", group_exists)
    resources = resources_fixture()
    smoke.close_native_resources(
        [browser], [], None, resources, browser_process=browser
    )
    assert events == ["stopped", "reaped", "inventory"]
    resources.cleanup.assert_called_once()


def test_browser_reap_timeout_preserves_dependencies(monkeypatch):
    browser = SimpleNamespace(
        pid=491, wait=Mock(side_effect=smoke.subprocess.TimeoutExpired("driver", 5))
    )
    monkeypatch.setattr(smoke.runtime, "stop_owned_process", Mock())
    monkeypatch.setattr(smoke.runtime, "process_group_exists", Mock(return_value=False))
    resources = resources_fixture()
    with pytest.raises(smoke.NativeCleanupError) as caught:
        smoke.close_native_resources(
            [browser], [], None, resources, browser_process=browser
        )
    assert caught.value.quiescent is False
    browser.wait.assert_called_once_with(timeout=5)
    resources.cleanup.assert_not_called()


def browser_failure_record():
    return {
        "kind": "browser_failure",
        "stage": "cold_login",
        "error_type": "TimeoutError",
        "driver_line": 123,
        "driver_column": 9,
    }


def browser_failure_validator():
    validator = getattr(smoke, "validate_browser_failure", None)
    assert callable(validator), "browser failures need a fixed diagnostic whitelist"
    return validator


@pytest.mark.parametrize(
    "mutation", ["extra", "stage", "type", "bool", "negative", "large", "half_null"]
)
def test_browser_failure_diagnostics_reject_unknown_or_nonframe_values(mutation):
    record = browser_failure_record()
    if mutation == "extra":
        record["message"] = "private-cookie"
    elif mutation == "stage":
        record["stage"] = "private-email"
    elif mutation == "type":
        record["error_type"] = "private-error"
    elif mutation == "half_null":
        record["driver_line"] = None
    else:
        record["driver_line"] = {"bool": True, "negative": -1, "large": 100001}[
            mutation
        ]
    with pytest.raises(smoke.SmokeError) as caught:
        browser_failure_validator()(record)
    assert "private" not in str(caught.value)


def test_main_retains_only_safe_browser_failure_diagnostics(tmp_path, monkeypatch):
    record = browser_failure_record()
    validator = browser_failure_validator()
    assert validator(record) == record
    driver = Mock(side_effect=smoke.BrowserJourneyError(record))
    simulate_main(tmp_path, monkeypatch, browser_driver=driver)
    report, path = read_receipt(tmp_path)
    assert report["status"] == "failed"
    assert report["stage"] == "browser cold_login"
    assert report["browser_failure"] == record
    assert report["cleanup"]["status"] == "passed"
    assert "private" not in path.read_text()


def test_driver_failure_diagnostic_never_serializes_error_payload():
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const url = process.argv[1];
      const {browserFailure} = await import(url);
      const error = new Error('private-cookie private-email private-url');
      error.name = 'TimeoutError';
      error.stack = `TimeoutError: private-cookie\n at requireFact (${url}:16:33)\n at login (${url}:123:9)\n at external (file:///private-email:1:1)`;
      const result = browserFailure('cold_login', error);
      assert.deepEqual(result, {kind:'browser_failure', stage:'cold_login', error_type:'TimeoutError', driver_line:123, driver_column:9});
      assert.equal(JSON.stringify(result).includes('private'), false);
      error.name = 'private-error';
      error.stack = 'Error: private-cookie\n at external (file:///private-email:1:1)';
      assert.deepEqual(browserFailure('cold_login', error), {kind:'browser_failure', stage:'cold_login', error_type:'Error', driver_line:null, driver_column:null});
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri()],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "case",
    [
        "delivered",
        "cancelled",
        "wrong_origin",
        "wrong_method",
        "wrong_path",
        "query",
        "http_origin",
        "origin_path",
        "origin_credentials",
        "zero_port",
        "large_port",
        "string_port",
        "fractional_port",
        "redirect",
        "unauthorized",
        "missing_subject",
        "transport_failure",
    ],
)
def test_profile_barrier_transport_and_owner_response_boundary(case):
    """Route doubles verify wiring only, not genuine owner/browser acceptance."""
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      import {EventEmitter} from 'node:events';
      const {profileBarrier} = await import(process.argv[1]);
      const scenario = process.argv[2];
      const config = {origin: 'https://web-native-own.example.test', port: 49123};
      const headers = {cookie: 'fixture-cookie', host: 'ignored.invalid', accept: 'application/json'};
      let requestUrl = config.origin + '/api/account/profile';
      let method = 'GET';
      const badConfigs = {
        http_origin: {origin: 'http://web-native-own.example.test'},
        origin_path: {origin: config.origin + '/other'},
        origin_credentials: {origin: 'https://user:fixture@web-native-own.example.test'},
        zero_port: {port: 0}, large_port: {port: 65536},
        string_port: {port: '49123'}, fractional_port: {port: 49123.5},
      };
      if (scenario === 'wrong_origin') requestUrl = 'https://other.example.test/api/account/profile';
      if (scenario === 'wrong_method') method = 'POST';
      if (scenario === 'wrong_path') requestUrl = config.origin + '/api/auth/session';
      if (scenario === 'query') requestUrl += '?redirect=other';
      const invalidRequest = ['wrong_origin', 'wrong_method', 'wrong_path', 'query'].includes(scenario);
      const invalidResponse = ['redirect', 'unauthorized', 'missing_subject', 'transport_failure'].includes(scenario);
      let handler;
      let fetchOptions;
      let headerReads = 0;
      let fulfillment;
      let aborted = false;
      const page = new EventEmitter();
      page.route = async (_pattern, callback) => { handler = callback; };
      page.unroute = async (_pattern, callback) => { assert.equal(callback, handler); handler = undefined; };
      const request = {
        url: () => requestUrl, method: () => method,
        allHeaders: async () => { headerReads++; return headers; },
        failure: () => ({errorText: 'net::ERR_ABORTED'}),
      };
      const response = {
        status: () => scenario === 'redirect' ? 302 : scenario === 'unauthorized' ? 401 : 200,
        json: async () => ({data: scenario === 'missing_subject' ? {} : {subject: 'fixture-subject'}}),
      };
      const route = {
        request: () => request,
        fetch: async options => {
          fetchOptions = options;
          if (scenario === 'transport_failure') throw new Error('fixture transport error');
          return response;
        },
        fulfill: async options => { fulfillment = options; page.emit('requestfinished', request); },
        abort: async () => { aborted = true; },
      };
      if (badConfigs[scenario]) {
        await assert.rejects(() => profileBarrier(page, {...config, ...badConfigs[scenario]}));
        assert.equal(handler, undefined);
        assert.equal(page.eventNames().length, 0);
      } else {
        const barrier = await profileBarrier(page, config);
        const expectedFailure = invalidRequest || invalidResponse;
        const ready = expectedFailure ? assert.rejects(barrier.ready) : barrier.ready;
        const handled = handler(route);
        await ready;
        if (expectedFailure) {
          barrier.cancel();
          await handled;
          assert.equal(fulfillment, undefined);
          if (invalidRequest) {
            assert.equal(fetchOptions, undefined);
            assert.equal(headerReads, 0);
          } else {
            assert.equal(headerReads, 1);
            assert.equal(fetchOptions.maxRedirects, 0);
          }
        } else {
          assert.deepEqual(fetchOptions, {
            url: 'https://127.0.0.1:49123/api/account/profile',
            headers: {...headers, host: 'web-native-own.example.test'},
            timeout: 4500, maxRetries: 0, maxRedirects: 0,
          });
          assert.equal(headerReads, 1);
          assert.equal(headers.host, 'ignored.invalid');
          assert.equal(fulfillment, undefined);
          if (scenario === 'cancelled') page.emit('requestfailed', request);
          const result = await barrier.release();
          await handled;
          assert.deepEqual(result, {
            upstream_profile_status: 200,
            observation: scenario === 'cancelled' ? 'cancelled' : 'delivered_and_retired',
          });
          assert.equal(aborted, scenario === 'cancelled');
          if (scenario === 'delivered') assert.equal(fulfillment.response, response);
          else assert.equal(fulfillment, undefined);
          assert.equal(handler, undefined);
          assert.equal(page.eventNames().length, 0);
        }
      }
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri(), case],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "case",
    [
        "trusted_focus",
        "trusted_visibility",
        "untrusted",
        "hidden",
        "wrong_status",
        "page_cdp_failure",
        "peer_cdp_failure",
    ],
)
def test_focus_probe_disables_both_overrides_and_preserves_trusted_event_oracle(case):
    """Page/CDP doubles exercise driver behavior, not real Chromium focus evidence."""
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const {focusProbe} = await import(process.argv[1]);
      const scenario = process.argv[2];
      const disabled = new Set();
      const sessions = [];
      const events = new Map();
      let peerFront = false;
      let pageFront = false;
      let responseWaitStarted = false;
      const listen = (name, callback, options) => {
        assert.deepEqual(options, {once: true});
        events.set(name, callback);
      };
      globalThis.window = {addEventListener: listen};
      globalThis.document = {addEventListener: listen, visibilityState: 'hidden'};
      const context = {
        newCDPSession: async target => {
          assert.ok(target === page || target === peer);
          assert.ok(!sessions.includes(target));
          sessions.push(target);
          return {
            send: async (command, params) => {
              assert.equal(command, 'Emulation.setFocusEmulationEnabled');
              assert.deepEqual(params, {enabled: false});
              if ((scenario === 'page_cdp_failure' && target === page) ||
                  (scenario === 'peer_cdp_failure' && target === peer)) {
                throw new Error('fixture CDP failure');
              }
              disabled.add(target);
            },
            detach: async () => { throw new Error('early detach restores override'); },
          };
        },
      };
      const peer = {
        context: () => context,
        bringToFront: async () => {
          assert.equal(disabled.has(page) && disabled.has(peer), true, 'both overrides must be disabled');
          peerFront = true;
        },
      };
      const page = {
        context: () => context,
        evaluate: async callback => { assert.equal(peerFront, true); callback(); },
        waitForResponse: (predicate, options) => {
          assert.deepEqual(options, {timeout: 3000});
          assert.equal(predicate({url: () => 'https://fixture.test/api/account/profile'}), false);
          const response = {
            url: () => 'https://fixture.test/api/auth/session',
            status: () => scenario === 'wrong_status' ? 200 : 401,
          };
          assert.equal(predicate(response), true);
          responseWaitStarted = true;
          return Promise.resolve(response);
        },
        bringToFront: async () => {
          assert.equal(responseWaitStarted, true);
          pageFront = true;
          document.visibilityState = scenario === 'hidden' ? 'hidden' : 'visible';
          const event = scenario === 'trusted_visibility' ? 'visibilitychange' : 'focus';
          events.get(event)({isTrusted: scenario !== 'untrusted'});
        },
        waitForFunction: async (predicate, argument, options) => {
          assert.equal(argument, null);
          assert.deepEqual(options, {timeout: 3000});
          if (!predicate()) throw new Error('fixture focus not observed');
        },
      };
      if (scenario.endsWith('_cdp_failure')) {
        await assert.rejects(() => focusProbe(page, peer, 401), /fixture CDP failure/);
        assert.equal(peerFront, false);
        assert.equal(pageFront, false);
      } else if (scenario === 'wrong_status') {
        await assert.rejects(() => focusProbe(page, peer, 401), /browser journey failed/);
      } else if (scenario === 'untrusted' || scenario === 'hidden') {
        await assert.rejects(() => focusProbe(page, peer, 401), /fixture focus not observed/);
        assert.equal(window.__nativeSmokeFocusObserved, false);
      } else {
        assert.equal(await focusProbe(page, peer, 401), true);
        assert.equal(window.__nativeSmokeFocusObserved, true);
        assert.equal(pageFront, true);
        assert.equal(sessions.length, 2);
      }
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri(), case],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr

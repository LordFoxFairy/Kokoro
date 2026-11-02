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


def simulate_main(tmp_path, monkeypatch, *, fail_stop=False, fail_cleanup=False):
    args = prepare_main(tmp_path, monkeypatch)
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
    monkeypatch.setattr(
        smoke.web,
        "Proxy",
        lambda *_: SimpleNamespace(server_port=1234, close=lambda: None),
    )
    monkeypatch.setattr(
        smoke.web,
        "https_browser",
        lambda *_: (_ for _ in ()).throw(RuntimeError("failed-http secret-cookie")),
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
    with pytest.raises(smoke.SmokeError):
        smoke.main([])
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

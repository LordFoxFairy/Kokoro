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
        expected_admin_sha="d" * 40,
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


def purpose_credential_files(tmp_path):
    paths = {}
    for purpose in ("bff_user_context", "account_sessions"):
        path = tmp_path / (purpose + ".json")
        path.write_text(json.dumps({"entries": [{"secret": purpose + "-secret"}]}))
        field = (
            "bff_user_context_credential_file"
            if purpose == "bff_user_context"
            else "account_session_credential_file"
        )
        paths[field] = str(path)
    return paths


def native_record(tmp_path):
    return {
        "kind": "native",
        "cookie": "__Secure-kokoro-issuer.session_token=private-native-cookie",
        **purpose_credential_files(tmp_path),
        "web_origin": "https://web-native-fixture.example.test",
    }


@pytest.mark.parametrize(
    "origin,cookie_name",
    [
        ("http://web-native-fixture.example.test", "kokoro-issuer.session_token"),
        (
            "https://web-native-fixture.example.test",
            "__Secure-kokoro-issuer.session_token",
        ),
    ],
)
def test_native_command_accepts_two_purpose_credentials(tmp_path, origin, cookie_name):
    import io

    record = native_record(tmp_path)
    record["web_origin"] = origin
    record["cookie"] = f"{cookie_name}=private-native-cookie"
    process = SimpleNamespace(stdin=io.BytesIO())
    receipt = smoke.native_command(
        process, SimpleNamespace(record=lambda: record), run_dir=tmp_path
    )
    assert (
        receipt.bff_user_context_credential_file
        == record["bff_user_context_credential_file"]
    )
    assert (
        receipt.account_session_credential_file
        == record["account_session_credential_file"]
    )
    assert receipt.cookie == record["cookie"]
    assert receipt.iam_web_origin == record["web_origin"]
    assert process.stdin.getvalue() == b'{"command":"native"}\n'


@pytest.mark.parametrize(
    "origin,cookie_name",
    [
        (
            "http://web-native-fixture.example.test",
            "__Secure-kokoro-issuer.session_token",
        ),
        ("https://web-native-fixture.example.test", "kokoro-issuer.session_token"),
    ],
)
def test_native_command_rejects_cookie_mode_mismatching_origin(
    tmp_path, origin, cookie_name
):
    import io

    record = native_record(tmp_path)
    record["web_origin"] = origin
    record["cookie"] = f"{cookie_name}=private-native-cookie"
    with pytest.raises(smoke.SmokeError, match="native cookie missing"):
        smoke.native_command(
            SimpleNamespace(stdin=io.BytesIO()),
            SimpleNamespace(record=lambda: record),
            run_dir=tmp_path,
        )


@pytest.mark.parametrize("scheme", ["http", "https"])
@pytest.mark.parametrize("separator", ["; ", ";", ";  ", ";\t"])
def test_native_command_rejects_mixed_cookie_modes(tmp_path, scheme, separator):
    import io

    record = native_record(tmp_path)
    record["web_origin"] = f"{scheme}://web-native-fixture.example.test"
    expected = "__Secure-" if scheme == "https" else ""
    other = "" if expected else "__Secure-"
    record["cookie"] = (
        f"{expected}kokoro-issuer.session_token=expected{separator}"
        f"{other}kokoro-issuer.session_token=other"
    )
    with pytest.raises(smoke.SmokeError, match="native cookie missing"):
        smoke.native_command(
            SimpleNamespace(stdin=io.BytesIO()),
            SimpleNamespace(record=lambda: record),
            run_dir=tmp_path,
        )


@pytest.mark.parametrize("scheme", ["http", "https"])
@pytest.mark.parametrize(
    "pair_template",
    ["{other} =other", "{other}\t=other", "{same} =duplicate", "\u00a0{other}=other"],
)
def test_native_command_rejects_hidden_session_cookie_names(
    tmp_path, scheme, pair_template
):
    import io

    record = native_record(tmp_path)
    record["web_origin"] = f"{scheme}://web-native-fixture.example.test"
    plain = "kokoro-issuer.session_token"
    secure = "__Secure-" + plain
    same, other = (secure, plain) if scheme == "https" else (plain, secure)
    record["cookie"] = f"{same}=expected; " + pair_template.format(
        same=same, other=other
    )
    with pytest.raises(smoke.SmokeError, match="native cookie missing"):
        smoke.native_command(
            SimpleNamespace(stdin=io.BytesIO()),
            SimpleNamespace(record=lambda: record),
            run_dir=tmp_path,
        )


@pytest.mark.parametrize("alias", ["same_path", "symlink", "hardlink"])
def test_native_command_rejects_same_physical_file_for_both_purposes(tmp_path, alias):
    import io

    record = native_record(tmp_path)
    first = Path(record["bff_user_context_credential_file"])
    second = Path(record["account_session_credential_file"])
    second.unlink()
    if alias == "same_path":
        record["account_session_credential_file"] = str(first)
    elif alias == "symlink":
        second.symlink_to(first)
    else:
        second.hardlink_to(first)
    with pytest.raises(smoke.SmokeError, match="distinct"):
        smoke.native_command(
            SimpleNamespace(stdin=io.BytesIO()),
            SimpleNamespace(record=lambda: record),
            run_dir=tmp_path,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "legacy",
        "extra",
        "missing_user_context",
        "missing_account_sessions",
        "not_record",
    ],
)
def test_native_command_rejects_old_or_incomplete_receipt(tmp_path, mutation):
    import io

    record = native_record(tmp_path)
    if mutation == "legacy":
        record["credential_file"] = record.pop("bff_user_context_credential_file")
        record.pop("account_session_credential_file")
    elif mutation == "extra":
        record["credential_file"] = record["bff_user_context_credential_file"]
    elif mutation == "missing_user_context":
        record.pop("bff_user_context_credential_file")
    elif mutation == "missing_account_sessions":
        record.pop("account_session_credential_file")
    else:
        record = None
    with pytest.raises(smoke.SmokeError, match="protocol drift"):
        smoke.native_command(
            SimpleNamespace(stdin=io.BytesIO()),
            SimpleNamespace(record=lambda: record),
            run_dir=tmp_path,
        )


@pytest.mark.parametrize(
    "field",
    ["bff_user_context_credential_file", "account_session_credential_file"],
)
@pytest.mark.parametrize("mutation", ["missing", "not_string", "empty", "escaped"])
def test_native_command_rejects_invalid_purpose_path(tmp_path, field, mutation):
    import io

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    record = native_record(run_dir)
    if mutation == "missing":
        Path(record[field]).unlink()
    elif mutation == "not_string":
        record[field] = []
    elif mutation == "empty":
        record[field] = ""
    else:
        outside = tmp_path / "outside.json"
        outside.write_text("{}")
        Path(record[field]).unlink()
        Path(record[field]).symlink_to(outside)
    with pytest.raises(smoke.SmokeError, match="credential"):
        smoke.native_command(
            SimpleNamespace(stdin=io.BytesIO()),
            SimpleNamespace(record=lambda: record),
            run_dir=run_dir,
        )


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
    native_responses=None,
    credential_log_leak=None,
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
        smoke, "run_native_command", Mock(return_value=None), raising=False
    )
    monkeypatch.setattr(smoke.runtime, "install_schema", lambda *_: None)
    monkeypatch.setattr(smoke.runtime, "run_owned_command", lambda *_, **__: 0)
    monkeypatch.setattr(smoke.web, "iam_owned_inventory", lambda *_: (set(), set()))
    monkeypatch.setattr(smoke.runtime, "wait_ready", lambda *_: None)
    monkeypatch.setattr(smoke.runtime, "free_port", lambda: 1234)
    monkeypatch.setattr(smoke.web, "certificate", lambda *_: None)
    if browser_driver is not None:
        monkeypatch.setattr(
            smoke.web,
            "certificate",
            lambda *_: (tmp_path / "owned.crt", tmp_path / "owned.key"),
        )
        monkeypatch.setattr(
            smoke,
            "admin_runtime_preflight",
            lambda *_: {"pnpm": "12.3.4", "next": "16.2.6", "env_proxy": True},
        )
        monkeypatch.setattr(smoke, "isolated_admin_next", lambda directory: directory)
        monkeypatch.setattr(
            smoke,
            "AdminConnectProxy",
            lambda *_: SimpleNamespace(server_port=1235, close=lambda: None),
        )
        monkeypatch.setattr(smoke, "wait_admin_ready", lambda *_: None)
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
            command=list(_[0]) if _ else [],
            stdin=io.BytesIO(),
            stdout=SimpleNamespace(fileno=lambda: 1, close=lambda: None),
            poll=lambda: None,
        )
        made.append(process)
        environments.append(kwargs["env"])
        if len(made) == 1:
            credential.extend(
                Path(path)
                for path in purpose_credential_files(
                    Path(kwargs["env"]["TMPDIR"])
                ).values()
            )
            if credential_log_leak is not None:
                kwargs["stderr"].write(credential_log_leak.encode())
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
        lambda *_, **__: smoke.NativeReceipt(
            "kokoro-issuer.session_token=cookie-secret",
            str(credential[0]),
            str(credential[1]),
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
                    "data": {
                        "authenticated": True,
                        "subject": "user",
                        "tenant_id": "tenant",
                        "expires_at": "2099-01-01T00:00:00.000Z",
                    }
                },
            ),
            (200, {"projects": []}),
            (200, {"data": {"authenticated": False}}),
        ]
        monkeypatch.setattr(
            smoke.web,
            "https_browser",
            Mock(
                side_effect=[
                    SimpleNamespace(status=status, body=json.dumps(body).encode())
                    for status, body in native_responses or responses
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
    assert all(path.exists() is fail_stop for path in credential)
    assert "secret" not in path.read_text()
    if fail_stop:
        assert processes[0] not in stopped
        resources.cleanup.assert_not_called()
    else:
        assert stopped == processes[::-1]
        resources.cleanup.assert_called_once()


def test_bff_environment_uses_only_purpose_specific_credential_files(
    tmp_path, monkeypatch
):
    _, _, _, environments, credentials, _ = simulate_main(tmp_path, monkeypatch)
    bff_env = environments[1]
    assert bff_env["KOKORO_BFF_IAM_USER_CONTEXT_SERVICE_CREDENTIAL_FILE"] == str(
        credentials[0]
    )
    assert bff_env["KOKORO_BFF_IAM_ACCOUNT_SESSIONS_SERVICE_CREDENTIAL_FILE"] == str(
        credentials[1]
    )
    assert "KOKORO_BFF_IAM_SESSION_ADMISSION_CREDENTIAL_FILE" not in bff_env


@pytest.mark.parametrize("purpose", ["bff_user_context", "account_sessions"])
def test_log_scan_registers_each_purpose_secret(tmp_path, monkeypatch, purpose):
    simulate_main(
        tmp_path,
        monkeypatch,
        native_success=True,
        credential_log_leak=purpose + "-secret",
    )
    receipt, path = read_receipt(tmp_path)
    assert receipt["credential_log_check"] == "failed"
    assert receipt["status"] == "failed"
    assert purpose + "-secret" not in path.read_text()
    assert receipt["cleanup"]["quiescent"] is True
    assert list(path.parent.iterdir()) == [path]


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
        argv.extend(["--browser-journeys", "--expected-admin-sha", "d" * 40])
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
    broker = broker_type(
        process, reader, credentials=credentials, run_dir=tmp_path, timeout=0.25
    )
    return broker, process, reader, credentials


def test_browser_fixture_and_bound_cookie_stay_in_private_protocol(tmp_path, capsys):
    fixture = {
        "kind": "browser_fixture",
        "email": "fixture@example.test",
        "password": "private-browser-password",
        "tenant_id": "fixed-tenant",
        **purpose_credential_files(tmp_path),
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
    "mutation",
    [
        "legacy",
        "extra",
        "missing_user_context",
        "missing_account_sessions",
        "same_path",
        "symlink",
        "hardlink",
        "missing_file",
        "escaped",
    ],
)
def test_browser_fixture_rejects_ambiguous_or_invalid_credentials(tmp_path, mutation):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    fixture = {
        "kind": "browser_fixture",
        "email": "fixture@example.test",
        "password": "private-browser-password",
        "tenant_id": "fixed-tenant",
        **purpose_credential_files(run_dir),
        "web_origin": "https://web-native-fixture.example.test",
    }
    user_context = "bff_user_context_credential_file"
    account_sessions = "account_session_credential_file"
    if mutation == "legacy":
        fixture["credential_file"] = fixture.pop(user_context)
        fixture.pop(account_sessions)
    elif mutation == "extra":
        fixture["credential_file"] = fixture[user_context]
    elif mutation == "missing_user_context":
        fixture.pop(user_context)
    elif mutation == "missing_account_sessions":
        fixture.pop(account_sessions)
    elif mutation == "same_path":
        fixture[account_sessions] = fixture[user_context]
    elif mutation in ("symlink", "hardlink"):
        path = Path(fixture[account_sessions])
        path.unlink()
        if mutation == "symlink":
            path.symlink_to(fixture[user_context])
        else:
            path.hardlink_to(fixture[user_context])
    elif mutation == "missing_file":
        Path(fixture[account_sessions]).unlink()
    else:
        outside = tmp_path / "outside.json"
        outside.write_text("{}")
        Path(fixture[account_sessions]).unlink()
        Path(fixture[account_sessions]).symlink_to(outside)
    broker, _, _, _ = browser_broker(run_dir, [fixture])
    with pytest.raises(smoke.SmokeError):
        broker.dispatch({"command": "browser_fixture"})


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
            "shared_admin": shared_admin_facts(),
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
                "session_status": 403,
                "session_error_code": "product_tenant_forbidden",
                "projects_status": 403,
                "projects_error_code": "product_tenant_forbidden",
                "private_ui_retired": True,
                "relogin_status": 303,
                "recovered_session_status": 200,
                "recovered_authenticated": True,
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
                "projects_error_code": "session_authentication_required",
                "old_cookie_projects_status": 401,
                "old_cookie_projects_error_code": "session_invalid",
            },
            "independent_revocation": {
                "a_owner": dict(deleted),
                "a_session_status": 200,
                "a_authenticated": False,
                "a_projects_status": 401,
                "a_projects_error_code": "session_authentication_required",
                "a_private_ui_retired": True,
                "b_session_status_before_membership": 200,
                "b_authenticated_before_membership": True,
                "b_owner_before_membership": dict(fixed),
                "b_owner_after_membership": {**fixed, "member": False},
                "b_session_status": 403,
                "b_session_error_code": "session_forbidden",
                "b_projects_status": 403,
                "b_projects_error_code": "session_forbidden",
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
        ("session_status", 401),
        ("projects_status", 200),
        ("projects_status", 401),
        ("session_error_code", "native_session_required"),
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
        result["journeys"]["independent_revocation"]["a_authenticated"] = True
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
            receipt["journeys"]["ui_logout"]["old_cookie_projects_status"] = 200
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


def test_browser_success_keeps_native_and_admin_journeys_separate_from_credential_scan(
    tmp_path, monkeypatch
):
    driver = Mock(return_value=complete_browser_result())
    simulate_main(tmp_path, monkeypatch, browser_driver=driver, succeeds=True)
    report, _ = read_receipt(tmp_path)
    assert report["status"] == "passed"
    assert report["mode"] == "browser_journeys"
    assert report["completed_journeys"] == 5
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
    "body",
    [
        {"authenticated": True, "mode": "native", "subject": "user", "expires_at": 123},
        {"data": {"authenticated": False}},
        {"error": {"code": "iam_admission_unavailable"}},
        *[
            {
                "data": {
                    "authenticated": True,
                    "subject": "user",
                    "tenant_id": "tenant",
                    "expires_at": "2099-01-01T00:00:00.000Z",
                    **mutation,
                }
            }
            for mutation in [
                {"authenticated": 1},
                {"subject": "other-user"},
                {"tenant_id": "other-tenant"},
                {"expires_at": 123},
                {"expires_at": "not-a-date"},
                {"expires_at": "2000-01-01T00:00:00Z"},
                {"mode": "native"},
            ]
        ],
    ],
)
def test_minimal_http_rejects_wrong_identity_false_or_obsolete_session_shape(
    tmp_path, monkeypatch, body
):
    simulate_main(
        tmp_path,
        monkeypatch,
        native_success=True,
        native_responses=[
            (200, {}),
            (200, body),
            (200, {"projects": []}),
            (401, {"error": {"code": "native_session_required"}}),
        ],
    )
    report, _ = read_receipt(tmp_path)
    assert report["completed_checks"] == 0
    assert report["cleanup"]["status"] == "passed"


@pytest.mark.parametrize(
    "status,body",
    [
        (401, {"error": {"code": "native_session_required"}}),
        (503, {"error": {"code": "iam_admission_unavailable"}}),
        (200, {"authenticated": False}),
        (200, {"data": {"authenticated": True}}),
        (200, {"data": {"authenticated": False, "subject": "stale-private-user"}}),
        (200, {"data": {"authenticated": 0}}),
    ],
)
def test_minimal_http_requires_explicit_anonymous_after_owner_signout(
    tmp_path, monkeypatch, status, body
):
    simulate_main(
        tmp_path,
        monkeypatch,
        native_success=True,
        native_responses=[
            (200, {}),
            (
                200,
                {
                    "data": {
                        "authenticated": True,
                        "subject": "user",
                        "tenant_id": "tenant",
                        "expires_at": "2099-01-01T00:00:00.000Z",
                    }
                },
            ),
            (200, {"projects": []}),
            (status, body),
        ],
    )
    report, _ = read_receipt(tmp_path)
    assert report["completed_checks"] == 2
    assert report["cleanup"]["status"] == "passed"


@pytest.mark.parametrize(
    "field,value",
    [
        ("a_session_status", 401),
        ("a_authenticated", True),
        ("a_projects_error_code", "native_session_required"),
        ("b_authenticated_before_membership", False),
        ("b_session_status", 401),
        ("b_session_error_code", "session_invalid"),
        ("b_projects_status", 401),
        ("b_projects_error_code", "product_tenant_forbidden"),
    ],
)
def test_browser_receipt_distinguishes_revocation_from_membership_denial(field, value):
    receipt = complete_browser_result()
    receipt["journeys"]["independent_revocation"][field] = value
    with pytest.raises(smoke.SmokeError):
        smoke.validate_browser_receipt(receipt)


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
        "navigation",
        "navigation_cleanup_unavailable",
        "foreign_frame",
        "late_focus",
        "cleanup_slow",
        "cleanup_dispose_hang",
        "cleanup_evaluate_hang",
        "untrusted",
        "hidden",
        "wrong_status",
        "anonymous",
        "false_is_not_active",
        "leaking_anonymous",
        "incomplete_active",
        "valid_active",
        "wrong_active_subject",
        "wrong_active_tenant",
        "expired_active",
        "non_utc_active",
        "flat_body",
        "wrong_code",
        "json_failure",
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
      const anonymous = ['anonymous', 'leaking_anonymous', 'navigation', 'navigation_cleanup_unavailable', 'cleanup_slow', 'cleanup_dispose_hang', 'cleanup_evaluate_hang'].includes(scenario);
      const active = ['false_is_not_active', 'flat_body', 'incomplete_active', 'valid_active',
        'wrong_active_subject', 'wrong_active_tenant', 'expired_active', 'non_utc_active'].includes(scenario);
      const expected = anonymous ? {status: 200, authenticated: false}
        : active ? {status: 200, authenticated: true}
          : {status: 403, error_code: 'product_tenant_forbidden'};
      const identity = {subject: 'observed-profile-subject', tenant_id: 'fixed-fixture-tenant'};
      const disabled = new Set();
      const sessions = [];
      const events = new Map();
      const bindings = new Map();
      const timers = new Map();
      const mainFrame = {};
      let now = 0;
      let nextTimer = 0;
      let bindingCalls = 0;
      let disposed = 0;
      let evaluations = 0;
      let bindingCallback;
      globalThis.setTimeout = (callback, milliseconds) => {
        assert.ok(milliseconds > 0 && milliseconds <= 3000);
        const id = ++nextTimer; timers.set(id, callback); return id;
      };
      globalThis.clearTimeout = id => timers.delete(id);
      const expire = () => {
        now = 3000;
        for (const [id, callback] of [...timers]) { timers.delete(id); callback(); }
      };
      let peerFront = false;
      let pageFront = false;
      let responseWaitStarted = false;
      const listen = (name, callback, options) => {
        assert.deepEqual(options, {once: true});
        events.set(name, callback);
      };
      const remove = (name, callback) => { if (events.get(name) === callback) events.delete(name); };
      const documentState = visibilityState => {
        globalThis.window = {addEventListener: listen, removeEventListener: remove};
        globalThis.document = {addEventListener: listen, removeEventListener: remove, visibilityState};
        for (const [name, callback] of bindings) window[name] = callback;
      };
      documentState('hidden');
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
        mainFrame: () => mainFrame,
        exposeBinding: async (name, callback) => {
          assert.equal(bindings.has(name), false);
          bindingCallback = callback;
          const call = async (...args) => {
            bindingCalls++;
            return callback({page, frame: scenario === 'foreign_frame' ? {} : mainFrame}, ...args);
          };
          bindings.set(name, call); window[name] = call;
          return {dispose: async () => {
            disposed++; bindings.delete(name); delete window[name];
            if (scenario === 'cleanup_slow') now = 4001;
            if (scenario === 'cleanup_dispose_hang') { queueMicrotask(expire); return new Promise(() => {}); }
          }};
        },
        evaluate: async (callback, argument) => {
          assert.equal(peerFront, true);
          if (++evaluations > 1 && ['cleanup_evaluate_hang', 'navigation_cleanup_unavailable'].includes(scenario)) { queueMicrotask(expire); return new Promise(() => {}); }
          callback(argument);
        },
        waitForResponse: (predicate, options) => {
          assert.ok(options.timeout > 0 && options.timeout <= 3000);
          assert.equal(predicate({url: () => 'https://fixture.test/api/account/profile'}), false);
          const response = {
            url: () => 'https://fixture.test/api/auth/session',
            status: () => scenario === 'wrong_status' || anonymous || active ? 200 : 403,
            json: async () => {
              if (scenario === 'json_failure') throw new Error('fixture JSON failure');
              if (scenario === 'anonymous' || scenario.startsWith('navigation') || scenario === 'false_is_not_active' || scenario.startsWith('cleanup_')) return {data: {authenticated: false}};
              if (scenario === 'leaking_anonymous') return {data: {
                authenticated: false, subject: 'stale-private-subject', session_token: 'private-canary',
              }};
              if (scenario === 'incomplete_active') return {data: {authenticated: true}};
              if (['valid_active', 'wrong_active_subject', 'wrong_active_tenant', 'expired_active', 'non_utc_active'].includes(scenario)) return {data: {
                authenticated: true,
                subject: scenario === 'wrong_active_subject' ? 'another-subject' : identity.subject,
                tenant_id: scenario === 'wrong_active_tenant' ? 'another-tenant' : identity.tenant_id,
                expires_at: scenario === 'expired_active' ? '2000-01-01T00:00:00Z'
                  : scenario === 'non_utc_active' ? '2099-01-01T00:00:00+00:00' : '2099-01-01T00:00:00.000Z',
              }};
              if (scenario === 'flat_body') return {authenticated: true};
              return {error: {code: scenario === 'wrong_code' ? 'other_error' : 'product_tenant_forbidden'}};
            },
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
          events.get(event)({isTrusted: scenario !== 'untrusted' && scenario !== 'cleanup_evaluate_hang'});
          if (scenario.startsWith('navigation')) { events.clear(); documentState('visible'); }
          if (scenario === 'late_focus') now = 3001;
          if (['untrusted', 'hidden', 'foreign_frame', 'cleanup_evaluate_hang'].includes(scenario)) queueMicrotask(expire);
        },
        waitForFunction: async (predicate, argument, options) => {
          assert.equal(argument, null);
          assert.deepEqual(options, {timeout: 3000});
          if (!predicate()) throw new Error('fixture focus not observed');
        },
      };
      if (scenario.startsWith('cleanup_')) {
        const pending = focusProbe(page, peer, expected.status, expected.authenticated, identity, {now: () => now});
        const stalled = (async () => {
          for (let i = 0; i < 50; i++) await Promise.resolve();
          throw new Error('fixture cleanup exceeded the original deadline without settling');
        })();
        await assert.rejects(Promise.race([pending, stalled]), /browser journey failed/);
        assert.equal(disposed, 1, 'dispose must be attempted independently of DOM cleanup');
        if (scenario === 'cleanup_evaluate_hang') {
          events.get('focus')?.({isTrusted: true});
          await bindingCallback({page, frame: mainFrame});
          await assert.rejects(pending, /browser journey failed/);
        }
      } else if (scenario.endsWith('_cdp_failure')) {
        await assert.rejects(() => focusProbe(page, peer, expected.status, expected.authenticated ?? expected.error_code, identity, {now: () => now}), /fixture CDP failure/);
        assert.equal(peerFront, false);
        assert.equal(pageFront, false);
      } else if (['wrong_status', 'false_is_not_active', 'leaking_anonymous', 'incomplete_active', 'wrong_active_subject', 'wrong_active_tenant', 'expired_active', 'non_utc_active', 'flat_body', 'wrong_code'].includes(scenario)) {
        await assert.rejects(() => focusProbe(page, peer, expected.status, expected.authenticated ?? expected.error_code, identity, {now: () => now}), /browser journey failed/);
      } else if (scenario === 'json_failure') {
        await assert.rejects(() => focusProbe(page, peer, expected.status, expected.authenticated ?? expected.error_code, identity, {now: () => now}), /fixture JSON failure/);
      } else if (['untrusted', 'hidden', 'foreign_frame', 'late_focus'].includes(scenario)) {
        await assert.rejects(() => focusProbe(page, peer, expected.status, expected.authenticated ?? expected.error_code, identity, {now: () => now}), /browser journey failed/);
        if (scenario === 'untrusted' || scenario === 'hidden') assert.equal(bindingCalls, 0);
      } else {
        const pending = focusProbe(page, peer, expected.status, expected.authenticated ?? expected.error_code, identity, {now: () => now});
        const observed = scenario === 'navigation_cleanup_unavailable' ? Promise.race([pending, (async () => {
          for (let i = 0; i < 50; i++) await Promise.resolve();
          throw new Error('fixture unnecessary document cleanup blocked navigation-safe ACK');
        })()]) : pending;
        assert.equal(await observed, true);
        assert.equal(pageFront, true);
        assert.equal(sessions.length, 2);
      }
      assert.equal(timers.size, 0, 'deadline timer must be cleared');
      if (!scenario.endsWith('_cdp_failure')) {
        assert.equal(disposed, 1);
        assert.equal(bindings.size, 0, 'binding must be disposed');
        if (disposed) assert.equal(events.size, 0, 'browser listeners must retire');
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


def test_old_cookie_replay_uses_protected_resource_and_observed_typed_rejection():
    """In-memory HTTPS double: no listener, browser, or fixture resources are opened."""
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      import https from 'node:https';
      import {EventEmitter} from 'node:events';
      const {replay} = await import(process.argv[1]);
      https.request = (options, callback) => {
        assert.equal(options.hostname, '127.0.0.1');
        assert.equal(options.port, 54321);
        assert.equal(options.servername, 'fixture.example.test');
        assert.equal(options.path, '/api/session/projects');
        assert.equal(options.method, 'GET');
        assert.deepEqual(options.headers, {
          host: 'fixture.example.test', origin: 'https://fixture.example.test',
          cookie: 'kokoro-issuer.session_token=old-private-cookie',
        });
        const request = new EventEmitter();
        request.setTimeout = milliseconds => assert.equal(milliseconds, 5000);
        request.end = () => {
          const response = new EventEmitter();
          response.statusCode = 401;
          callback(response);
          queueMicrotask(() => {
            response.emit('data', Buffer.from('{"error":{"code":"session_invalid"}}'));
            response.emit('end');
          });
        };
        return request;
      };
      assert.deepEqual(await replay({origin: 'https://fixture.example.test', port: 54321},
        'kokoro-issuer.session_token=old-private-cookie'), {
          status: 401, body: {error: {code: 'session_invalid'}},
        });
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri()],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


def test_anonymous_retirement_observes_login_without_old_private_canaries():
    """A Page double checks the oracle only; real navigation remains Root's acceptance."""
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const {retired} = await import(process.argv[1]);
      const profile = {subject: 'old-subject', name: 'Old Fixture Name', email: 'old@example.test'};
      let navigated = false;
      let stale = false;
      let staleName = false;
      let currentUrl = 'https://fixture.test/app';
      let destination = 'https://fixture.test/auth/sign-in?flow=fixture-flow';
      let passwordVisible = true;
      let leaveSignIn = false;
      const checked = new Set();
      const page = {
        url: () => currentUrl,
        waitForURL: async predicate => {
          assert.equal(predicate(new URL('https://fixture.test/auth/sign-in?flow=fixture-flow')), true);
          assert.equal(predicate(new URL('https://fixture.test/login?return_to=%2Fapp')), false);
          assert.equal(predicate(new URL('https://fixture.test/error')), false);
          assert.equal(predicate(new URL('https://other.test/auth/sign-in')), false);
          assert.equal(predicate(new URL('https://fixture.test/app')), false);
          currentUrl = destination;
          if (!predicate(new URL(currentUrl))) throw new Error('fixture canonical sign-in absent');
          navigated = true;
        },
        locator: selector => { assert.equal(selector, 'input[name="password"][type="password"]'); return 'password'; },
        getByRole: (role, options) => {
          assert.equal(role, 'textbox'); assert.deepEqual(options, {name: 'Full name', exact: true});
          return 'private-name';
        },
        getByText: (text, options) => { assert.deepEqual(options, {exact: true}); return text; },
        getByTestId: () => { throw new Error('anonymous is not an unavailable Settings shell'); },
      };
      const expect = locator => ({
        toBeVisible: async () => {
          assert.equal(navigated, true); assert.equal(locator, 'password');
          if (!passwordVisible) throw new Error('fixture password form absent');
        },
        toHaveCount: async count => {
          assert.equal(count, 0); checked.add(locator);
          if (stale && locator === profile.email) throw new Error('old private canary still visible');
          if (staleName && locator === profile.name) throw new Error('old private name still visible');
          if (leaveSignIn && locator === profile.subject) currentUrl = 'https://fixture.test/error';
        },
      });
      assert.equal(await retired(page, profile, expect, true), true);
      assert.deepEqual(checked, new Set(['private-name', profile.name, profile.email, profile.subject]));
      stale = true;
      await assert.rejects(() => retired(page, profile, expect, true), /old private canary still visible/);
      stale = false; staleName = true;
      await assert.rejects(() => retired(page, profile, expect, true), /old private name still visible/);
      staleName = false;
      for (const url of ['https://fixture.test/login', 'https://fixture.test/error', 'https://other.test/auth/sign-in']) {
        currentUrl = 'https://fixture.test/app'; destination = url;
        await assert.rejects(() => retired(page, profile, expect, true), /fixture canonical sign-in absent/);
      }
      currentUrl = 'https://fixture.test/app';
      destination = 'https://fixture.test/auth/sign-in?flow=fixture-flow';
      passwordVisible = false;
      await assert.rejects(() => retired(page, profile, expect, true), /fixture password form absent/);
      passwordVisible = true; leaveSignIn = true; currentUrl = 'https://fixture.test/app';
      await assert.rejects(() => retired(page, profile, expect, true), /browser journey failed/);
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri()],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


def test_anonymous_retirement_shares_original_three_second_navigation_and_canary_budget():
    """Advance an injected clock in Page/expect doubles, never sleep or open a page."""
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const {retired} = await import(process.argv[1]);
      const profile = {subject: 'old-subject', name: 'Old Fixture Name', email: 'old@example.test'};
      for (const late of [false, true]) {
        let now = 100;
        const started = now;
        const calls = [];
        const consume = (options, elapsed, label) => {
          assert.deepEqual(options, {timeout: 3000 - (now - started)}, label + ' must share remaining budget');
          assert.ok(options.timeout > 0 && options.timeout <= 3000);
          calls.push(label);
          now += elapsed;
        };
        const page = {
          url: () => 'https://fixture.test/auth/sign-in',
          waitForURL: async (predicate, options) => {
            assert.equal(predicate(new URL('https://fixture.test/auth/sign-in?flow=fixture-flow')), true);
            consume(options, 1000, 'navigation');
          },
          locator: () => 'password',
          getByRole: () => 'private-name',
          getByText: text => text,
          getByTestId: () => { throw new Error('anonymous is not unavailable'); },
        };
        const expect = locator => ({
          toBeVisible: async options => consume(options, 750, 'login form'),
          toHaveCount: async (count, options) => {
            assert.equal(count, 0);
            consume(options, locator === profile.subject ? (late ? 260 : 250) : locator === 'private-name' ? 500 : 250, locator);
          },
        });
        const observation = () => retired(page, profile, expect, true, {now: () => now});
        if (late) await assert.rejects(observation, /browser journey failed/);
        else assert.equal(await observation(), true);
        assert.deepEqual(calls, ['navigation', 'login form', 'private-name', profile.name, profile.email, profile.subject]);
        assert.equal(now - started, late ? 3010 : 3000);
      }
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
    "scenario",
    [
        "unmounted",
        "disabled_card",
        "removes_card",
        "unretired_card",
        "leaked_email",
        "leaked_subject",
        "login",
        "error_page",
        "missing_shell",
        "late",
        "exhausted",
    ],
)
def test_qualification_retirement_allows_only_private_retirement_in_one_budget(
    scenario,
):
    """Semantic Page doubles; real forbidden DOM/draft evidence belongs to Root."""
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const {retired} = await import(process.argv[1]);
      const scenario = process.argv[2];
      const profile = {subject:'old-subject',email:'old@example.test'};
      const valid = ['unmounted','disabled_card','removes_card'].includes(scenario);
      let now = 100;
      const started = now;
      let cardCount = ['unmounted','error_page','missing_shell'].includes(scenario) ? 0 : 1;
      const nameDisabled = !['unretired_card','removes_card'].includes(scenario);
      const checked = new Set();
      let missingBudget = false;
      const consume = (options, elapsed) => {
        if (!options) missingBudget = true;
        else assert.deepEqual(options,{timeout:3000-(now-started)});
        now += elapsed;
      };
      const name = {
        kind:'name',
        count:async()=>cardCount,
        evaluateAll:async fn=>fn(cardCount ? [{matches:()=>nameDisabled,value:'—'}] : []),
      };
      const card = {
        kind:'card',
        count:async()=>cardCount,
        getByRole:()=>name,
        getByText:text=>({kind:'text',scope:'card',text}),
      };
      const page = {
        url:()=> 'https://fixture.test/'+(scenario==='login'?'login':scenario==='error_page'?'error':scenario==='disabled_card'?'app/project/owned-ref':'app'),
        getByTestId:()=>card,
        getByRole:()=>name,
        getByText:text=>({kind:'text',scope:'global',text}),
        locator:selector=>{
          if(selector==='[data-desktop-web="true"][data-web-skin="kokoro"]')return {kind:'shell'};
          assert.equal(selector,'input[name="password"][type="password"]');
          return {kind:'password'};
        },
      };
      const expect = locator=>({
        toBeVisible:async options=>{
          assert.equal(locator.kind,'shell','only the public shell must stay visible');
          checked.add('shell');
          if(scenario==='missing_shell')throw new Error('public shell is missing');
          consume(options,500);
        },
        toBeDisabled:async()=>{if(!nameDisabled)throw new Error('private state not retired')},
        toHaveValue:async value=>assert.equal(value,'—'),
        toHaveCount:async(count,options)=>{
          assert.equal(count,0);
          if(locator.kind==='password') {
            checked.add('password');
            if(scenario==='login')throw new Error('login form is visible');
            consume(options,scenario==='late'?1001:1000);
          } else {
            checked.add(locator.scope+':'+locator.text);
            if(locator.scope==='global'&&((scenario==='leaked_email'&&locator.text===profile.email)||(scenario==='leaked_subject'&&locator.text===profile.subject)))
              throw new Error('private canary remains globally visible');
            consume(options,500);
          }
        },
      });
      expect.poll = (read,options)=>({toBe:async expected=>{
        let observed=await read();
        if(scenario==='removes_card'&&!observed){cardCount=0;observed=await read()}
        assert.equal(observed,expected,'private state not retired');
        consume(options,scenario==='exhausted'?3000:500);
      }});
      const observe=()=>retired(page,profile,expect,false,{now:()=>now});
      if(valid) {
        assert.equal(await observe(),true);
        assert.equal(missingBudget,false,'every observation shares the original budget');
        assert.equal(now-started,3000);
        assert.deepEqual(checked,new Set(['global:'+profile.email,'global:'+profile.subject,'password','shell']));
      } else await assert.rejects(observe,/browser journey failed|private state not retired|private canary|login form|public shell/);
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri(), scenario],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


def shared_admin_facts():
    return {
        "initial_owner": {"enabled": False, "version": 0, "succeeded_audits": 0},
        "granted_owner": {"enabled": True, "version": 1, "succeeded_audits": 1},
        "shared_issuer_cookie": True,
        "additional_sign_in_requests": 0,
        "admin_me_status": 200,
        "admin_identity_matches": True,
        "admin_shell_visible": True,
        "revoked_owner": {"enabled": False, "version": 2, "succeeded_audits": 2},
        "revoked_admin_me_status": 403,
        "revoked_admin_error_code": "admin_access_denied",
        "private_ui_retired": True,
        "product_session_status": 200,
        "product_authenticated": True,
        "projects_status": 200,
        "product_owner": {
            "exists": True,
            "unexpired": True,
            "member": True,
            "active_tenant": "fixed",
        },
    }


def test_shared_admin_browser_mode_requires_exact_admin_source(tmp_path):
    argv = native_cli_args(tmp_path) + ["--browser-journeys"]
    with pytest.raises(SystemExit):
        smoke.parse_args(argv)
    args = smoke.parse_args(argv + ["--expected-admin-sha", "d" * 40])
    assert args.expected_admin_sha == "d" * 40


def test_browser_rejects_unpublished_iam_option_before_source_or_resource_claim(
    tmp_path, monkeypatch
):
    component_argv = native_cli_args(tmp_path) + ["--allow-unpublished-iam-gitlink"]
    component = smoke.parse_args(component_argv)
    assert component.browser_journeys is False
    assert component.allow_unpublished_iam_gitlink is True
    browser_argv = component_argv + [
        "--browser-journeys",
        "--expected-admin-sha",
        "d" * 40,
    ]
    source = Mock(side_effect=AssertionError("source preflight must not run"))
    resources = Mock(side_effect=AssertionError("resources must not be claimed"))
    monkeypatch.setattr(smoke, "verify_source", source)
    monkeypatch.setattr(smoke.runtime, "OwnedResources", resources)
    monkeypatch.setattr(smoke, "EVIDENCE_ROOT", tmp_path / "evidence")
    for entrypoint in (smoke.parse_args, smoke.main):
        with pytest.raises(SystemExit) as rejected:
            entrypoint(browser_argv)
        assert rejected.value.code == 2
    source.assert_not_called()
    resources.assert_not_called()
    assert not (tmp_path / "evidence").exists()


@pytest.mark.parametrize(
    "command,enabled,version,audits",
    [
        ("inspect_browser_platform_admin", False, 0, 0),
        ("grant_browser_platform_admin", True, 1, 1),
        ("revoke_browser_platform_admin", False, 2, 2),
    ],
)
def test_shared_admin_broker_uses_only_fixed_owner_commands(
    tmp_path, command, enabled, version, audits
):
    reply = {
        "kind": "browser_platform_admin",
        "command": command,
        "enabled": enabled,
        "version": version,
        "succeeded_audits": audits,
    }
    broker, process, reader, _ = browser_broker(tmp_path, [reply])
    assert broker.dispatch({"command": command}) == reply
    assert json.loads(process.stdin.getvalue()) == {"command": command}
    reader.record.assert_called_once()


@pytest.mark.parametrize(
    "mutation",
    ["target", "extra_secret", "bool_version", "wrong_command", "missing_audit"],
)
def test_shared_admin_broker_rejects_target_or_owner_fact_drift(tmp_path, mutation):
    command = "inspect_browser_platform_admin"
    reply = {
        "kind": "browser_platform_admin",
        "command": command,
        "enabled": False,
        "version": 0,
        "succeeded_audits": 0,
    }
    request = {"command": command}
    if mutation == "target":
        request["userId"] = "another-user"
    elif mutation == "extra_secret":
        reply["cookie"] = "private-admin-canary"
    elif mutation == "bool_version":
        reply["version"] = True
    elif mutation == "wrong_command":
        reply["command"] = "grant_browser_platform_admin"
    else:
        reply.pop("succeeded_audits")
    broker, process, reader, _ = browser_broker(tmp_path, [reply])
    with pytest.raises(smoke.SmokeError) as caught:
        broker.dispatch(request)
    assert "private-admin-canary" not in str(caught.value)
    if mutation == "target":
        reader.record.assert_not_called()
        assert process.stdin.getvalue() == b""


def test_shared_admin_receipt_requires_current_eligibility_and_surviving_product():
    result = complete_browser_result()
    result["journeys"]["shared_admin"] = shared_admin_facts()
    assert smoke.validate_browser_receipt(result) == result
    for field, value in [
        ("shared_issuer_cookie", False),
        ("additional_sign_in_requests", 1),
        ("admin_identity_matches", False),
        ("revoked_admin_me_status", 200),
        ("private_ui_retired", False),
        ("product_authenticated", False),
    ]:
        changed = json.loads(json.dumps(result))
        changed["journeys"]["shared_admin"][field] = value
        with pytest.raises(smoke.SmokeError):
            smoke.validate_browser_receipt(changed)


def test_shared_admin_runtime_rejects_wrong_installation_and_missing_proxy_flag(
    tmp_path, monkeypatch
):
    admin = tmp_path / "admin"
    modules = admin / "node_modules"
    (modules / "next").mkdir(parents=True)
    (modules / "next/package.json").write_text('{"version":"16.2.6"}')
    metadata = modules / ".modules.yaml"
    metadata.write_text('{"packageManager":"pnpm@12.3.4"}')
    monkeypatch.setattr(smoke, "ADMIN", admin, raising=False)
    monkeypatch.setattr(
        smoke.subprocess,
        "run",
        lambda *_, **__: SimpleNamespace(stdout='{"env_proxy":true}', returncode=0),
    )
    assert smoke.admin_runtime_preflight(Path("node22"), {}) == {
        "pnpm": "12.3.4",
        "next": "16.2.6",
        "env_proxy": True,
    }
    metadata.write_text('{"packageManager":"pnpm@11.25.0"}')
    with pytest.raises(smoke.SmokeError):
        smoke.admin_runtime_preflight(Path("node22"), {})
    metadata.write_text('{"packageManager":"pnpm@12.3.4"}')
    monkeypatch.setattr(
        smoke.subprocess,
        "run",
        lambda *_, **__: SimpleNamespace(stdout='{"env_proxy":false}', returncode=0),
    )
    with pytest.raises(smoke.SmokeError):
        smoke.admin_runtime_preflight(Path("node22"), {})


def test_shared_admin_isolated_copy_keeps_owner_inputs_and_module_installation(
    tmp_path, monkeypatch
):
    admin = tmp_path / "owner"
    admin.mkdir()
    for directory in ("app", "components", "lib", "patches"):
        (admin / directory).mkdir()
        (admin / directory / "entry.txt").write_text(directory)
    for file in (
        "package.json",
        "tsconfig.json",
        "next-env.d.ts",
        "postcss.config.mjs",
        "pnpm-lock.yaml",
        "pnpm-workspace.yaml",
        "proxy.ts",
    ):
        (admin / file).write_text(file)
    (admin / "next.config.ts").write_text(
        'const nextConfig: NextConfig = {\n  basePath: "/manage",\n};\nexport default nextConfig;\n'
    )
    (admin / "node_modules").mkdir()
    (admin / ".next").mkdir()
    (admin / ".next/owner-build").write_text("do not touch")
    (admin / ".env.local").write_text("private-admin-canary")
    before = {
        str(p.relative_to(admin)): p.read_bytes()
        for p in admin.rglob("*")
        if p.is_file()
    }
    monkeypatch.setattr(smoke, "ADMIN", admin, raising=False)
    work = tmp_path / "work"
    work.mkdir()
    isolated = smoke.isolated_admin_next(work)
    assert isolated.parent == work
    for file in (
        "proxy.ts",
        "app/entry.txt",
        "components/entry.txt",
        "lib/entry.txt",
        "patches/entry.txt",
        "pnpm-lock.yaml",
        "pnpm-workspace.yaml",
    ):
        assert (isolated / file).read_bytes() == (admin / file).read_bytes()
    assert (isolated / "node_modules").is_symlink()
    assert (isolated / "node_modules").resolve() == (admin / "node_modules").resolve()
    assert not (isolated / ".next").exists()
    assert not (isolated / ".env.local").exists()
    assert {
        str(p.relative_to(admin)): p.read_bytes()
        for p in admin.rglob("*")
        if p.is_file()
    } == before


@pytest.mark.parametrize(
    "case",
    [
        "valid",
        "default_port_host",
        "wrong_authority",
        "wrong_port",
        "wrong_host",
        "ambiguous_host",
        "oversized",
        "incomplete",
    ],
)
def test_shared_admin_connect_is_exact_bounded_and_drained(
    tmp_path, monkeypatch, capsys, case
):
    import socket
    import socketserver
    import threading

    calls = []

    class Echo(socketserver.BaseRequestHandler):
        def handle(self):
            calls.append(True)
            self.request.settimeout(1)
            try:
                body = self.request.recv(64)
                if body:
                    self.request.sendall(body)
            except OSError:
                pass

    target = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Echo)
    thread = threading.Thread(
        target=target.serve_forever, kwargs={"poll_interval": 0.01}
    )
    thread.start()
    proxy_type = getattr(smoke, "AdminConnectProxy", None)
    if proxy_type is None:
        target.shutdown()
        target.server_close()
        thread.join(2)
        pytest.fail("shared Admin needs a fixed-authority CONNECT transport")
    monkeypatch.setattr(proxy_type, "HEADER_SECONDS", 0.1)
    proxy = proxy_type("https://owned.example.test", target.server_address[1])
    try:
        with socket.create_connection(
            ("127.0.0.1", proxy.server_port), timeout=1
        ) as client:
            client.settimeout(1)
            authority = "owned.example.test:443"
            if case == "wrong_authority":
                authority = "private-admin-canary.example.test:443"
            if case == "wrong_port":
                authority = "owned.example.test:444"
            header_host = (
                "owned.example.test" if case == "default_port_host" else authority
            )
            if case == "wrong_host":
                header_host = "other.example.test"
            header = f"CONNECT {authority} HTTP/1.1\r\nHost: {header_host}\r\n"
            if case == "ambiguous_host":
                header += "Host: other.example.test:443\r\n"
            if case == "oversized":
                header += "X-Large: " + "x" * 9000 + "\r\n"
            if case != "incomplete":
                header += "\r\n"
            client.sendall(header.encode())
            reply = b""
            while b"\r\n\r\n" not in reply:
                part = client.recv(1024)
                if not part:
                    break
                reply += part
            expected = (
                200
                if case in {"valid", "default_port_host"}
                else 431
                if case == "oversized"
                else 408
                if case == "incomplete"
                else 403
            )
            assert reply.startswith(f"HTTP/1.1 {expected} ".encode())
            if case in {"valid", "default_port_host"}:
                client.sendall(b"actual-tunnel-bytes")
                assert client.recv(64) == b"actual-tunnel-bytes"
            else:
                assert calls == []
    finally:
        proxy.close()
        target.shutdown()
        target.server_close()
        thread.join(2)
    assert not proxy.thread.is_alive()
    assert not thread.is_alive()
    captured = capsys.readouterr()
    assert "private-admin-canary" not in captured.out + captured.err


def test_shared_admin_driver_rejects_unbound_identity_and_private_owner_fields():
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const {requireAdminObservation, requirePlatformAdminObservation} = await import(process.argv[1]);
      const identity = {subject:'current-subject',tenant_id:'fixed-tenant'};
      const good = {status:200,body:{authenticated:true,...identity,platform_admin:true}};
      assert.equal(requireAdminObservation(good,identity),true);
      for(const patch of [{subject:'other'},{tenant_id:'other'},{platform_admin:false},{cookie:'private-admin-canary'}]) {
        assert.throws(()=>requireAdminObservation({status:200,body:{...good.body,...patch}},identity),/browser journey failed/);
      }
      const fact={kind:'browser_platform_admin',command:'grant_browser_platform_admin',enabled:true,version:1,succeeded_audits:1};
      assert.deepEqual(requirePlatformAdminObservation(fact,fact.command,true,1,1),{enabled:true,version:1,succeeded_audits:1});
      for(const patch of [{command:'revoke_browser_platform_admin'},{version:true},{succeeded_audits:0},{cookie:'private-admin-canary'}]) {
        assert.throws(()=>requirePlatformAdminObservation({...fact,...patch},fact.command,true,1,1),/browser journey failed/);
      }
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri()],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


def test_shared_admin_retirement_uses_trusted_focus_and_one_three_second_budget():
    """Page/CDP doubles observe the real driver; this does not claim browser acceptance."""
    import subprocess

    driver = PATH.with_name("web_native_session_chromium.mjs")
    program = r"""
      import assert from 'node:assert/strict';
      const {retireAdminOnFocus} = await import(process.argv[1]);
      const identity={subject:'current-subject',tenant_id:'fixed-tenant'};
      for(const scenario of ['valid','late','wrong_me']) {
        let now=100;
        const started=now;
        const events=new Map();
        const remove=(name,cb)=>{if(events.get(name)===cb)events.delete(name)};
        globalThis.window={addEventListener:(name,cb)=>events.set(name,cb),removeEventListener:remove};
        globalThis.document={visibilityState:'hidden',addEventListener:(name,cb)=>events.set(name,cb),removeEventListener:remove};
        const peer={bringToFront:async()=>{document.visibilityState='hidden'}};
        const frame={};
        const page={
          mainFrame:()=>frame,
          exposeBinding:async(name,cb)=>{window[name]=async()=>cb({page,frame});return {dispose:async()=>{delete window[name]}}},
          context:()=>({newCDPSession:async target=>({send:async(name,value)=>{
            assert.ok(target===page||target===peer);assert.equal(name,'Emulation.setFocusEmulationEnabled');assert.deepEqual(value,{enabled:false});
          }})}),
          evaluate:async fn=>fn(),
          bringToFront:async()=>{now+=1000;document.visibilityState='visible';events.get('focus')({isTrusted:true})},
          waitForFunction:async predicate=>assert.equal(predicate(),true),
          waitForResponse:async(predicate,options)=>{
            const path=predicate({url:()=> 'https://fixture.test/manage/api/v1/me',request:()=>({method:()=> 'GET'})})?'/manage/api/v1/me':'/api/auth/session';
            assert.ok(options.timeout>0&&options.timeout<=3000);
            return {status:()=>path.startsWith('/manage')?403:200,json:async()=>path.startsWith('/manage')?
              {error:{code:scenario==='wrong_me'?'other':'admin_access_denied'}}:
              {data:{authenticated:true,...identity,expires_at:'2099-01-01T00:00:00Z'}}};
          },
          getByText:text=>text,
          getByRole:(_role,options)=>options.name,
        };
        let observations=0;
        const consume=options=>{
          assert.equal(options.timeout,3000-(now-started));
          now+=observations++===2?(scenario==='late'?1001:1000):500;
        };
        const expect=locator=>({
          toHaveCount:async(count,options)=>{assert.equal(count,0);consume(options)},
          toBeVisible:async options=>consume(options),
        });
        peer.context=page.context;
        const pending=retireAdminOnFocus(page,peer,identity,expect,{now:()=>now});
        if(scenario==='valid'){assert.equal(await pending,true);assert.equal(now-started,3000)}
        else await assert.rejects(pending,/browser journey failed/);
      }
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", program, driver.as_uri()],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


def test_shared_admin_startup_is_isolated_and_proxy_environment_is_admin_only(
    tmp_path, monkeypatch
):
    _, resources, made, environments, _, stopped = simulate_main(
        tmp_path,
        monkeypatch,
        browser_driver=Mock(return_value=complete_browser_result()),
        succeeds=True,
    )
    report, _ = read_receipt(tmp_path)
    assert report["sources"]["admin"] == {
        "sha": "d" * 40,
        "clean": True,
        "root_gitlink_matches": True,
    }
    assert report["node_versions"]["admin"] == "22.23.4"
    assert report["required_node_versions"]["admin"] == "22.23.4"
    assert report["admin_runtime"] == {
        "pnpm": "12.3.4",
        "next": "16.2.6",
        "env_proxy": True,
    }
    assert report["admin_verified"] is True
    assert len(made) == 4 and set(map(id, stopped)) == set(map(id, made))
    admin = environments[-1]
    assert admin["HTTPS_PROXY"] == "http://127.0.0.1:1235"
    assert admin["NO_PROXY"] == ""
    assert admin["NODE_EXTRA_CA_CERTS"] == str(tmp_path / "owned.crt")
    assert admin["KOKORO_ADMIN_WEB_ORIGIN"] == environments[0]["IAM_TEST_WEB_ORIGIN"]
    assert admin["KOKORO_TENANT_ID"] == "tenant"
    assert "--use-env-proxy" in made[-1].command
    assert all(
        "HTTPS_PROXY" not in env and "NODE_EXTRA_CA_CERTS" not in env
        for env in environments[:-1]
    )
    assert all(
        key not in admin
        for key in [
            "HTTP_PROXY",
            "ALL_PROXY",
            "https_proxy",
            "NODE_OPTIONS",
            "KOKORO_WEB_REDIS_URL",
            "KOKORO_BFF_IAM_USER_CONTEXT_SERVICE_CREDENTIAL_FILE",
        ]
    )
    assert environments[2]["KOKORO_ADMIN_INTERNAL_ORIGIN"] == "http://127.0.0.1:1234"
    builds = smoke.run_native_command.call_args_list
    admin_build = next(
        call
        for call in builds
        if str(call.args[0][-1]) == "build"
        and "node_modules/next" in str(call.args[0][-2])
    )
    assert "HTTPS_PROXY" not in admin_build.kwargs["env"]
    assert all("install" not in call.args[0] for call in builds)
    resources.cleanup.assert_called_once()


@pytest.mark.parametrize("failure", ["source", "runtime"])
def test_shared_admin_preflight_failure_precedes_any_resource_claim(
    tmp_path, monkeypatch, failure
):
    args = prepare_main(tmp_path, monkeypatch)
    args.browser_journeys = True
    resources = Mock()
    monkeypatch.setattr(smoke.runtime, "OwnedResources", resources)
    if failure == "source":

        def verify(repo, expected, *_):
            if repo == smoke.ADMIN:
                raise smoke.SmokeError("Admin source mismatch")
            return {"sha": expected, "clean": True, "root_gitlink_matches": True}

        monkeypatch.setattr(smoke, "verify_source", verify)
    else:
        monkeypatch.setattr(smoke.session, "node_environment", lambda *_: {})
        monkeypatch.setattr(
            smoke,
            "admin_runtime_preflight",
            Mock(side_effect=smoke.SmokeError("Admin runtime mismatch")),
        )
    with pytest.raises(smoke.SmokeError):
        smoke.main([])
    resources.assert_not_called()
    report, _ = read_receipt(tmp_path)
    assert report["status"] == "failed"
    assert report["admin_verified"] is False
    assert report["stage"] == (
        "source preflight" if failure == "source" else "runtime preflight"
    )


def test_shared_admin_connect_close_drains_an_active_tunnel(monkeypatch):
    import socket
    import socketserver
    import threading

    entered = threading.Event()

    class Waiting(socketserver.BaseRequestHandler):
        def handle(self):
            entered.set()
            self.request.settimeout(2)
            try:
                while self.request.recv(64):
                    pass
            except OSError:
                pass

    target = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Waiting)
    thread = threading.Thread(
        target=target.serve_forever, kwargs={"poll_interval": 0.01}
    )
    thread.start()
    proxy = smoke.AdminConnectProxy(
        "https://owned.example.test", target.server_address[1]
    )
    client = socket.create_connection(("127.0.0.1", proxy.server_port), timeout=1)
    try:
        client.sendall(
            b"CONNECT owned.example.test:443 HTTP/1.1\r\nHost: owned.example.test:443\r\n\r\n"
        )
        assert client.recv(1024).startswith(b"HTTP/1.1 200 ")
        assert entered.wait(1)
        proxy.close()
        assert client.recv(1) == b""
        assert not proxy.thread.is_alive()
    finally:
        client.close()
        if proxy.thread.is_alive():
            proxy.close()
        target.shutdown()
        target.server_close()
        thread.join(2)
    assert not thread.is_alive()

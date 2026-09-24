from __future__ import annotations

import json
from pathlib import Path
from threading import Barrier, Lock
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, build_opener
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts.e2e import run_bff_agent_worker_smoke as smoke


class Recorder:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.redis_sizes = {14: "0", 15: "0"}
        self.redis_keys: dict[int, list[str]] = {14: [], 15: []}
        self.redis_values: dict[tuple[int, str], str] = {}

    def __call__(self, command: list[str], **_kwargs: object) -> str:
        self.commands.append(command)
        if command[0] == "redis-cli":
            url = command[command.index("-u") + 1]
            database = smoke.redis_database_number(url)
            if "EVAL" in command:
                start = command.index("EVAL")
                script = command[start + 1]
                key_count = int(command[start + 2])
                keys = command[start + 3 : start + 3 + key_count]
                arguments = command[start + 3 + key_count :]
                if script == smoke._REDIS_CLAIM_SCRIPT:
                    if self.redis_sizes[database] != "0" or self.redis_keys[database]:
                        return "NOT_EMPTY"
                    marker = keys[0]
                    self.redis_keys[database].append(marker)
                    self.redis_values[(database, marker)] = arguments[0]
                    return "OK"
                if script == smoke._REDIS_CLEANUP_SCRIPT:
                    marker = keys[0]
                    if self.redis_values.get((database, marker), "") != arguments[0]:
                        return "OWNERSHIP_LOST"
                    if any(key not in keys for key in self.redis_keys[database]):
                        return "UNEXPECTED_KEY"
                    for key in list(self.redis_keys[database]):
                        self.redis_keys[database].remove(key)
                        self.redis_values.pop((database, key), None)
                    return "OK"
                raise AssertionError("unknown Redis script")
            if "DBSIZE" in command:
                return self.redis_sizes[database]
            if "SET" in command:
                key = command[command.index("SET") + 1]
                value = command[command.index("SET") + 2]
                self.redis_values[(database, key)] = value
                self.redis_keys[database].append(key)
                return "OK"
            if "GET" in command:
                key = command[command.index("GET") + 1]
                return self.redis_values.get((database, key), "")
            if "--scan" in command:
                return "\n".join(self.redis_keys[database])
            if "UNLINK" in command:
                start = command.index("UNLINK") + 1
                for key in command[start:]:
                    if key in self.redis_keys[database]:
                        self.redis_keys[database].remove(key)
                    self.redis_values.pop((database, key), None)
                return str(len(command[start:]))
        return ""


def resources(recorder: Recorder) -> smoke.OwnedResources:
    return smoke.OwnedResources(
        "postgresql://local/postgres",
        "redis://local/14",
        "redis://local/15",
        "a" * 24,
        command=recorder,
    )


def test_release_inputs_pin_current_bff_and_agent() -> None:
    assert smoke.EXPECTED_RELEASES == {
        "kokoro-bff": "84a560abeac5b7a63f32d7064abdde849ab33cf9",
        "kokoro-agent": "520ec181a101298b4f336aad273ce003b2735955",
    }


def test_release_verification_requires_clean_child_and_published_gitlink(
    monkeypatch,
) -> None:
    def command(command: list[str], **_kwargs: object) -> str:
        repo = command[2] if len(command) > 2 else ""
        if "rev-parse" in command:
            return smoke.EXPECTED_RELEASES[Path(repo).name] + "\n"
        if "status" in command:
            return ""
        if "ls-tree" in command:
            child = command[-1].split("/")[-1]
            return f"160000 commit {smoke.EXPECTED_RELEASES[child]}\t{command[-1]}\n"
        raise AssertionError(command)

    monkeypatch.setattr(smoke, "command_output", command)
    assert set(smoke.verify_release_inputs()) == {"kokoro-bff", "kokoro-agent"}

    def dirty(command: list[str], **kwargs: object) -> str:
        if "status" in command and str(smoke.BFF) in command:
            return " M src/main.ts\n"
        return command_output(command, **kwargs)

    command_output = command
    monkeypatch.setattr(smoke, "command_output", dirty)
    with pytest.raises(smoke.SmokeError, match="source identity"):
        smoke.verify_release_inputs()


def test_redis_databases_must_be_distinct_explicit_and_empty() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    owned.claim_redis()
    assert owned.redis_claimed
    assert smoke.redis_database_number("redis://localhost/15") == 15
    with pytest.raises(smoke.SmokeError, match="distinct"):
        smoke.OwnedResources(
            "postgresql://local/postgres",
            "redis://local/14",
            "redis://local/14",
            "a" * 24,
            command=recorder,
        )
    recorder.redis_sizes[14] = "1"
    with pytest.raises(smoke.SmokeError, match="empty"):
        resources(recorder).claim_redis()
    assert "FLUSH" not in str(recorder.commands)


def test_redis_claim_is_one_atomic_empty_database_operation() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    owned.claim_redis()
    redis_commands = [
        command for command in recorder.commands if command[0] == "redis-cli"
    ]
    assert redis_commands
    assert all("EVAL" in command for command in redis_commands)
    assert all(
        "DBSIZE" not in command and "SET" not in command for command in redis_commands
    )


def test_concurrent_redis_claim_has_exactly_one_winner() -> None:
    class AtomicRecorder(Recorder):
        def __init__(self) -> None:
            super().__init__()
            self.lock = Lock()

        def __call__(self, command: list[str], **kwargs: object) -> str:
            if command[0] != "redis-cli" or "EVAL" not in command:
                return super().__call__(command, **kwargs)
            with self.lock:
                return super().__call__(command, **kwargs)

    recorder = AtomicRecorder()
    first = resources(recorder)
    second = smoke.OwnedResources(
        "postgresql://local/postgres",
        "redis://local/14",
        "redis://local/15",
        "b" * 24,
        command=recorder,
    )
    barrier = Barrier(2)

    def claim(owned: smoke.OwnedResources) -> bool:
        barrier.wait()
        try:
            owned.claim_redis()
        except smoke.SmokeError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim, (first, second)))
    assert sorted(results) == [False, True]


def test_cleanup_unlinks_only_registered_owned_agent_keys_and_marker() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    owned.claim_redis()
    owned.register_agent_keys("conv_abc", "run_abc")
    recorder.redis_keys[15].extend(
        [
            "kokoro:runs:requests",
            "kokoro:run:run_abc:events",
            "kokoro:session:conv_abc:live",
        ]
    )
    owned.cleanup()
    assert recorder.redis_keys == {14: [], 15: []}
    assert any(smoke._REDIS_CLEANUP_SCRIPT in command for command in recorder.commands)
    assert all(
        "FLUSHDB" not in command and "FLUSHALL" not in command
        for command in recorder.commands
    )


def test_cleanup_refuses_unknown_redis_keys_instead_of_deleting_them() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    owned.claim_redis()
    recorder.redis_keys[15].append("someone-elses-key")
    with pytest.raises(smoke.SmokeError, match="unexpected Redis key"):
        owned.cleanup()
    assert "someone-elses-key" in recorder.redis_keys[15]
    unlink_commands = [command for command in recorder.commands if "UNLINK" in command]
    assert all("someone-elses-key" not in command for command in unlink_commands)


def test_cleanup_refuses_foreign_agent_shaped_key_without_deleting_anything() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    owned.claim_redis()
    owned.register_agent_keys("conv_owned", "run_owned")
    owned_key = "kokoro:run:run_owned:events"
    foreign_key = "kokoro:run:run_foreign:events"
    recorder.redis_keys[15].extend([owned_key, foreign_key])
    with pytest.raises(smoke.SmokeError, match="unexpected Redis key"):
        owned.cleanup()
    assert owned_key in recorder.redis_keys[15]
    assert foreign_key in recorder.redis_keys[15]
    assert owned._markers[15] in recorder.redis_keys[15]
    assert not any("UNLINK" in command for command in recorder.commands)


def test_cleanup_lost_marker_never_deletes_registered_run_keys() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    owned.claim_redis()
    owned.register_agent_keys("conv_owned", "run_owned")
    marker = owned._markers[15]
    recorder.redis_keys[15].remove(marker)
    recorder.redis_values.pop((15, marker))
    owned_key = "kokoro:run:run_owned:events"
    recorder.redis_keys[15].append(owned_key)
    with pytest.raises(smoke.SmokeError, match="identity changed"):
        owned.cleanup()
    assert owned_key in recorder.redis_keys[15]


def test_agent_environment_disables_dotenv_without_starting_resources(
    tmp_path: Path,
) -> None:
    assert smoke._agent_environment([tmp_path])["PYTHON_DOTENV_DISABLED"] == "1"


def test_final_sql_evidence_queries_each_owner_separately() -> None:
    bff_evidence = {
        "bff_outbox_status": "succeeded",
        "bff_assistant_status": "completed",
        "bff_agui_frames": 5,
        "bff_source_events": 4,
    }
    agent_evidence = {
        "agent_terminal": True,
        "agent_dispatch_status": "succeeded",
        "agent_chat_events": 4,
        "agent_event_summary": [{"type": "RUN_FINISHED", "payload": {}}],
        "agent_completed_assistants": 1,
    }

    class OwnerSqlRecorder:
        def __init__(self) -> None:
            self.queries: list[str] = []

        def _run(self, command: list[str]) -> str:
            query = command[-1]
            self.queries.append(query)
            owners = {
                owner
                for owner, marker in (
                    ("bff", "kokoro_bff."),
                    ("agent", "kokoro_agent."),
                )
                if marker in query
            }
            if owners == {"bff"}:
                return json.dumps(bff_evidence)
            if owners == {"agent"}:
                return json.dumps(agent_evidence)
            return json.dumps({**bff_evidence, **agent_evidence})

    resources = OwnerSqlRecorder()
    evidence = smoke._final_sql_evidence(
        resources,  # type: ignore[arg-type]
        "postgresql://local/app",
        "conversation-a",
        "run-a",
    )

    assert evidence == {**bff_evidence, **agent_evidence}
    assert len(resources.queries) == 2
    assert all(
        not ("kokoro_bff." in query and "kokoro_agent." in query)
        for query in resources.queries
    )
    assert {
        "bff" if "kokoro_bff." in query else "agent" for query in resources.queries
    } == {"bff", "agent"}


def test_failed_database_create_is_not_registered_for_drop() -> None:
    recorder = Recorder()

    def failed(command: list[str], **kwargs: object) -> str:
        if any("CREATE DATABASE" in value for value in command):
            raise smoke.SmokeError("create failed")
        return recorder(command, **kwargs)

    owned = smoke.OwnedResources(
        "postgresql://local/postgres",
        "redis://local/14",
        "redis://local/15",
        "a" * 24,
        command=failed,
    )
    with pytest.raises(smoke.SmokeError):
        owned.create_database()
    assert owned.created_database is None
    assert "DROP DATABASE" not in str(recorder.commands)


def test_database_cleanup_drops_only_the_successfully_created_random_name() -> None:
    recorder = Recorder()
    owned = resources(recorder)
    database_url = owned.create_database()
    assert "bff_agent_smoke_" + "a" * 24 in database_url
    owned.cleanup()
    drops = [
        value
        for command in recorder.commands
        for value in command
        if value.startswith("DROP DATABASE")
    ]
    assert drops == ['DROP DATABASE "bff_agent_smoke_' + "a" * 24 + '" WITH (FORCE)']


def _json_request(
    url: str, body: dict[str, object], headers: dict[str, str]
) -> tuple[int, dict[str, object]]:
    request = Request(
        url,
        method="POST",
        headers={"content-type": "application/json", **headers},
        data=json.dumps(body).encode(),
    )
    try:
        response = build_opener().open(request, timeout=3)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.loads(response.read())


def test_system_fixture_is_strict_and_returns_generated_route_shape() -> None:
    identity = smoke.FixtureIdentity(
        tenant_id="tenant_a",
        system_secret="system-secret",
        model_secret="model-secret",
        reply="durable reply",
    )
    with smoke.system_model_fixtures(identity) as fixtures:
        status, body = _json_request(
            fixtures.system_url + "/v1/system/model-catalog/resolve",
            {"feature_key": "chat"},
            {
                "authorization": "Bearer system-secret",
                "x-kokoro-service": "kokoro-agent",
                "x-kokoro-tenant-id": "tenant_a",
                "x-request-id": "request-1",
            },
        )
        assert status == 200
        assert body["data"]["transport"] == "litellm"
        assert body["data"]["gateway_model_name"] == "smoke-model"
        denied, denied_body = _json_request(
            fixtures.system_url + "/v1/system/model-catalog/resolve",
            {"feature_key": "chat"},
            {
                "authorization": "Bearer wrong",
                "x-kokoro-service": "kokoro-agent",
                "x-kokoro-tenant-id": "tenant_a",
                "x-request-id": "request-2",
            },
        )
        assert denied == 401
        assert denied_body["error"]["code"] == "service_auth_failed"


def test_model_fixture_is_openai_compatible_but_explicitly_a_fixture() -> None:
    identity = smoke.FixtureIdentity(
        tenant_id="tenant_a",
        system_secret="system-secret",
        model_secret="model-secret",
        reply="durable reply",
    )
    with smoke.system_model_fixtures(identity) as fixtures:
        status, body = _json_request(
            fixtures.model_url + "/v1/chat/completions",
            {
                "model": "smoke-model",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False,
            },
            {"authorization": "Bearer model-secret"},
        )
        assert status == 200
        assert body["choices"][0]["message"]["content"] == "durable reply"
        assert fixtures.observation.model_requests == 1
        assert fixtures.observation.real_provider is False


def test_log_excerpt_redacts_every_registered_secret(tmp_path: Path) -> None:
    log = tmp_path / "process.log"
    log.write_text("x" * 3000 + "\ntoken-a harmless token-b\n")
    excerpt = smoke.safe_log_excerpt(log, {"token-a", "token-b"})
    assert "token-a" not in excerpt
    assert "token-b" not in excerpt
    assert "harmless" in excerpt
    assert len(excerpt) <= smoke.MAX_DIAGNOSTIC_CHARS


def test_finalizer_stops_every_process_before_resource_cleanup() -> None:
    events: list[str] = []
    processes = [SimpleNamespace(pid=1), SimpleNamespace(pid=2)]

    class Resources:
        def cleanup(self) -> None:
            events.append("cleanup")

        def verify_clean(self) -> None:
            events.append("verify")

    smoke.finalize_owned(
        processes,
        Resources(),
        stop=lambda process: events.append(f"stop-{process.pid}"),
    )
    assert events == ["stop-2", "stop-1", "cleanup", "verify"]


def test_process_group_cleanup_runs_after_owned_command_timeout(tmp_path: Path) -> None:
    log = tmp_path / "owned.log"
    with log.open("w+b") as output:
        with pytest.raises(smoke.SmokeError, match="deadline"):
            smoke.run_owned_command(
                ["python3", "-c", "import time; time.sleep(60)"],
                cwd=tmp_path,
                env={},
                log=output,
                timeout=0.1,
            )

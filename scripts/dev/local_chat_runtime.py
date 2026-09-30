"""Explicit System → selected provider and standard Agent processes for Chat.

No infrastructure, model, owner business code, or authorization is emulated.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import time
from urllib.parse import urlsplit

import model_provider

E2E = Path(__file__).resolve().parents[1] / "e2e"
if str(E2E) not in sys.path:
    sys.path.insert(0, str(E2E))
import capability_bff_smoke_runtime as runtime  # noqa: E402
import run_bff_agent_worker_smoke as agent_runtime  # noqa: E402
import run_web_real_model_worker_smoke as real_model  # noqa: E402
import run_web_project_resource_chromium_smoke as owned  # noqa: E402
import run_system_owner_smoke as system  # noqa: E402

ROOT = E2E.parent.parent
AGENT = ROOT / "apps/kokoro-agent"
SYSTEM = ROOT / "apps/kokoro-system"
DRAIN_SECONDS = 60
RENEW = "if redis.call('GET',KEYS[1]) ~= ARGV[1] then return 0 end return redis.call('EXPIRE',KEYS[1],ARGV[2])"
PARENT_GUARD = """import os, signal, threading, time
_parent = os.getppid()
_launcher = int(os.environ['KOKORO_LOCAL_CHAT_PARENT_PID'])
def _watch_parent():
    while os.getppid() == _parent and _parent > 1:
        try:
            os.kill(_launcher, 0)
        except ProcessLookupError:
            break
        time.sleep(0.1)
    os.kill(os.getpid(), signal.SIGTERM)
    time.sleep({grace})
    os.kill(os.getpid(), signal.SIGKILL)
threading.Thread(target=_watch_parent, daemon=True).start()
"""


class ChatError(RuntimeError):
    """Credential-free local lifecycle failure."""


@contextmanager
def registration_guard():
    """Register an owned process before synchronous termination can unwind."""
    pending = []
    watched = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    previous = {sig: signal.getsignal(sig) for sig in watched}

    def defer(signum, _frame):
        pending.append(signum)

    try:
        for sig in watched:
            signal.signal(sig, defer)
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        if pending:
            signal.raise_signal(pending[0])


def validate_options(
    base_redis: str,
    agent_redis: str,
    origin: str,
    model: str,
    external_config: model_provider.ExternalModelConfig | None = None,
) -> None:
    try:
        base, target = urlsplit(base_redis), urlsplit(agent_redis)
        if (
            target.scheme not in {"redis", "rediss"}
            or target.hostname != base.hostname
            or target.port != base.port
            or target.scheme != base.scheme
            or target.username
            or target.password
            or target.query
            or target.fragment
            or not re.fullmatch(r"/[0-9]+", target.path)
            or not 0 <= int(target.path[1:]) <= 15
            or agent_runtime.redis_database_number(base_redis) == int(target.path[1:])
        ):
            raise ValueError
        if external_config is None:
            real_model.RealModelConfig(origin, model, "0" * 40)
        elif not isinstance(external_config, model_provider.ExternalModelConfig):
            raise ValueError
    except (ValueError, runtime.SmokeError, agent_runtime.SmokeError, owned.SmokeError):
        raise ChatError(
            "explicit distinct Agent Redis DB and a valid selected provider required"
        ) from None


def agent_command(uv: Path, entry: str) -> list[str]:
    if entry not in {"http", "worker", "db-apply-schema"}:
        raise ChatError("Agent entry point invalid")
    return [str(uv), "run", "--frozen", "--no-sync", f"kokoro-agent-{entry}"]


def install_python_parent_guard(
    directory: Path, env: dict[str, str], *, grace: float = 70
) -> None:
    guard = directory / "python-parent-guard"
    guard.mkdir(mode=0o700, exist_ok=True)
    (guard / "sitecustomize.py").write_text(PARENT_GUARD.format(grace=grace))
    # Startup hook only; never expose an owner source tree or inherit PYTHONPATH.
    env["PYTHONPATH"] = str(guard)
    env["KOKORO_LOCAL_CHAT_PARENT_PID"] = str(os.getpid())


def provider_preflight(config) -> None:
    if isinstance(config, model_provider.ExternalModelConfig):
        try:
            model_provider.provider_preflight(config)
        except model_provider.ProviderObservationError:
            raise
        except model_provider.ProviderError:
            raise ChatError("external model inventory unavailable") from None
    else:
        real_model.provider_preflight(config)


def preflight(
    uv: Path,
    origin: str,
    model: str,
    log,
    external_config: model_provider.ExternalModelConfig | None = None,
) -> real_model.RealModelConfig | model_provider.ExternalModelConfig:
    sha = runtime.command_output(
        ["git", "rev-parse", "HEAD:apps/kokoro-system"], cwd=ROOT
    ).strip()
    owned._verify_source(SYSTEM, sha, "apps/kokoro-system")
    for owner in ("kokoro-agent", "kokoro-bff"):
        pinned = runtime.command_output(
            ["git", "rev-parse", f"HEAD:apps/{owner}"], cwd=ROOT
        ).strip()
        owned._verify_source(ROOT / "apps" / owner, pinned, f"apps/{owner}")
    config = external_config or real_model.RealModelConfig(origin, model, sha)
    provider_preflight(config)
    environment = agent_runtime._agent_environment([uv.parent])
    if (
        runtime.run_owned_command(
            [
                str(uv),
                "run",
                "--frozen",
                "--no-sync",
                "python",
                "-c",
                "import kokoro_agent.worker.main; import kokoro_agent.interfaces.http.main",
            ],
            cwd=AGENT,
            env=environment,
            log=log,
            timeout=30,
        )
        != 0
    ):
        raise ChatError("installed frozen Agent runtime unavailable")
    return config


def register_owned_runs(resources, database_url: str, ownership) -> None:
    # Read-only inventory of this invocation's own Agent schema, after processes
    # stop. It does not grant execution or reach another owner's business facts.
    raw = resources.command(
        [
            "psql",
            database_url,
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-Atc",
            "SELECT coalesce(json_agg(r),'[]'::json) FROM (SELECT run_id AS run, request_json::jsonb->>'session_id' AS session FROM kokoro_agent.kokoro_agent_run ORDER BY run_id LIMIT 10001) r",
        ]
    )
    try:
        rows = json.loads(raw)
    except (ValueError, TypeError):
        raise ChatError("owned Agent Run inventory invalid") from None
    if not isinstance(rows, list) or len(rows) > 10000:
        raise ChatError("owned Agent Run inventory exceeded cleanup budget")
    for row in rows:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(k), str)
            or re.fullmatch(r"[A-Za-z0-9_.:-]+", row[k]) is None
            for k in ("session", "run")
        ):
            raise ChatError("owned Agent Run inventory invalid")
        ownership.register_run(row["session"], row["run"])


def stop_chat_process(process, grace: float) -> None:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            runtime.stop_owned_process(process)
            raise ChatError("Chat process exceeded graceful shutdown budget") from None
    runtime.stop_owned_process(process)


class LocalChatRuntime:
    """One invocation owns System, Agent HTTP/worker and exclusive Agent Redis."""

    def __init__(
        self,
        *,
        config,
        uv: Path,
        node: Path,
        node_env: dict[str, str],
        directory: Path,
        resources,
        credentials,
        log,
        tenant: str,
        agent_redis_url: str,
    ):
        self.config, self.uv, self.node = config, uv, node
        self.node_env = dict(node_env)
        self.directory, self.resources, self.credentials, self.log = (
            directory,
            resources,
            credentials,
            log,
        )
        self.tenant = tenant
        self.ownership = owned.AgentRedisOwnership(agent_redis_url, resources.run_id)
        self.ownership.url = (
            agent_redis_url  # explicit validated DB, not helper's DB10 default
        )
        self.processes: list[tuple[str, subprocess.Popen]] = []
        self.agent_installed = False
        self.quiescent = True
        self.database_url = ""
        self._token = secrets.token_urlsafe(32)
        self._model_key = (
            config.api_key
            if isinstance(config, model_provider.ExternalModelConfig)
            else secrets.token_urlsafe(32)
        )
        credentials.add(self._token, self._model_key)
        self.route: dict[str, str] = {}
        self.health_generation = (
            "1"  # sole successful create in owner seed_control_plane
        )
        self.next_refresh = 0.0

    def _start(self, label: str, command: list[str], cwd: Path, env: dict[str, str]):
        with registration_guard():
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=self.log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            self.processes.append((label, process))
            self.quiescent = False
        return process

    def _command(
        self,
        label: str,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout: float,
    ) -> None:
        """Own short-lived installers exactly like long-lived services.

        Only Popen + registration defers signals. Waiting remains interruptible;
        an interrupted _start has already retained its process for close().
        """
        process = None
        try:
            process = self._start(label, command, cwd, env)
            if process.wait(timeout=timeout) != 0:
                raise ChatError(f"{label} failed")
        except subprocess.TimeoutExpired:
            raise ChatError(f"{label} deadline exceeded") from None
        finally:
            if process is not None:
                # Do not discard the handle if stopping fails. close() must keep
                # dependencies alive until this same registry is quiescent.
                stop_chat_process(process, 15)
                self.processes.remove((label, process))
                self.quiescent = not self.processes

    def start(self, database_url: str) -> dict[str, str]:
        self.database_url = database_url
        with registration_guard():
            try:
                self.ownership.claim()
            except BaseException:
                if (
                    self.ownership._call("GET", self.ownership.marker)
                    == self.resources.run_id
                ):
                    self.ownership.claimed = True
                raise
        self.resources.claim_redis_prefix()
        system_root = owned._isolated_owner(SYSTEM, self.directory, "system")
        port = runtime.free_port()
        self.system_base = f"http://127.0.0.1:{port}"
        env = {
            **self.node_env,
            "DATABASE_URL": database_url,
            "REDIS_URL": self.resources.redis_url,
            "KOKORO_SYSTEM_REDIS_NAMESPACE": self.resources.redis_prefix + "system",
            "KOKORO_SYSTEM_HOST": "127.0.0.1",
            "KOKORO_SYSTEM_PORT": str(port),
            "KOKORO_SYSTEM_BFF_SERVICE_TOKEN": self._token,
            "KOKORO_SYSTEM_AGENT_SERVICE_TOKEN": self._token,
            "KOKORO_SYSTEM_ADMIN_SERVICE_TOKEN": self._token,
            "KOKORO_SYSTEM_MODEL_HEALTH_MAX_AGE_MS": "300000",
            "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC",
        }
        for command in (
            [
                str(self.node),
                str(system_root / "node_modules/tsx/dist/cli.mjs"),
                "scripts/apply-schema.ts",
            ],
            [
                str(self.node),
                str(system_root / "node_modules/typescript/bin/tsc"),
                "-p",
                "tsconfig.build.json",
            ],
        ):
            self._command(
                "System setup", command, cwd=system_root, env=env, timeout=120
            )
        process = self._start(
            "system",
            [str(self.node), str(system_root / "dist/main.js")],
            system_root,
            env,
        )
        system.wait_ready(self.system_base, process)
        provider_preflight(self.config)
        self.route = system.seed_control_plane(
            self.system_base,
            self.tenant,
            self._token,
            self.resources.run_id,
            feature_key="chat",
            provider=(
                "openai-compatible"
                if isinstance(self.config, model_provider.ExternalModelConfig)
                else "ollama"
            ),
            model_name=self.config.model,
        )
        agent_env = {
            **agent_runtime._agent_environment([self.uv.parent]),
            "KOKORO_AGENT_DATABASE_URL": database_url,
            "KOKORO_AGENT_DATABASE_SCHEMA": "kokoro_agent",
            "KOKORO_REDIS_URL": self.ownership.url,
            "KOKORO_INTERNAL_SECRET_AGENT": self._token,
            "KOKORO_SYSTEM_BASE_URL": self.system_base,
            "KOKORO_LITELLM_ENABLED": "1",
            "KOKORO_LITELLM_BASE_URL": (
                self.config.base_url
                if isinstance(self.config, model_provider.ExternalModelConfig)
                else self.config.endpoint + "/v1"
            ),
            "KOKORO_LITELLM_API_KEY": self._model_key,
            "KOKORO_DISABLE_STREAMING": "0",
            "KOKORO_MCP_EGRESS_MODE": "deny",
            "KOKORO_DRAIN_TIMEOUT_S": str(DRAIN_SECONDS),
            "KOKORO_AGENT_LOCAL_SHELL_ROOT": str(self.directory / "workspace"),
        }
        (self.directory / "workspace").mkdir(mode=0o700)
        install_python_parent_guard(self.directory, agent_env)
        self._command(
            "Agent schema",
            agent_command(self.uv, "db-apply-schema"),
            cwd=AGENT,
            env=agent_env,
            timeout=90,
        )
        self.agent_installed = True
        agent_port = runtime.free_port()
        agent_base = f"http://127.0.0.1:{agent_port}"
        http_env = {
            **agent_env,
            "KOKORO_AGENT_HTTP_HOST": "127.0.0.1",
            "KOKORO_AGENT_HTTP_PORT": str(agent_port),
        }
        process = self._start("http", agent_command(self.uv, "http"), AGENT, http_env)
        agent_runtime._wait_ready(agent_base, process, path="/healthz")
        worker = self._start(
            "worker", agent_command(self.uv, "worker"), AGENT, agent_env
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if worker.poll() is not None:
                raise ChatError("Agent worker exited during startup")
            if self.ownership._call("EXISTS", "kokoro:runs:requests") == "1":
                break
            time.sleep(0.1)
        else:
            raise ChatError("Agent worker startup deadline")
        self.next_refresh = time.monotonic() + 60
        return {
            "KOKORO_AGENT_ENABLED": "true",
            "KOKORO_AGENT_BASE_URL": agent_base,
            "KOKORO_INTERNAL_SECRET_BFF": self._token,
            "KOKORO_SYSTEM_BASE_URL": self.system_base,
        }

    def tick(self) -> None:
        stage = "process"
        try:
            if any(process.poll() is not None for _, process in self.processes):
                raise ChatError("owned Chat service exited")
            if time.monotonic() < self.next_refresh:
                return
            # Foreground, bounded, no timer threads/queued retries. An expected
            # external inventory failure blocks new routing, not auth/Web lifetime.
            stage = "provider"
            health_status = "healthy"
            try:
                provider_preflight(self.config)
            except model_provider.ProviderObservationError:
                health_status = "unknown"
                try:
                    log = getattr(self, "log", None)
                    if log is not None:
                        log.write(
                            b"Local Chat provider observation unavailable; health=unknown\n"
                        )
                        log.flush()
                except Exception:
                    pass
            for stage, url, marker, ttl in (
                ("agent_ownership", self.ownership.url, self.ownership.marker, "7200"),
                (
                    "application_ownership",
                    self.resources.redis_url,
                    self.resources.redis_prefix + "ownership",
                    "600",
                ),
            ):
                if (
                    self.resources.command(
                        [
                            "redis-cli",
                            "-e",
                            "-u",
                            url,
                            "EVAL",
                            RENEW,
                            "1",
                            marker,
                            self.resources.run_id,
                            ttl,
                        ]
                    ).strip()
                    != "1"
                ):
                    raise ChatError("Chat resource ownership lost")
            stage = "health_request"
            observed_at = (
                datetime.now(timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
            response = system.http_json(
                self.system_base,
                f"/v1/system/model-catalog/providers/{self.route['provider_id']}/health",
                method="PUT",
                headers={
                    "authorization": f"Bearer {self._token}",
                    "x-kokoro-service": "system-admin",
                    "x-kokoro-actor-id": "local-chat-operator",
                    "x-kokoro-iam-permissions": "system:write",
                    "idempotency-key": secrets.token_hex(16),
                    "x-request-id": secrets.token_hex(16),
                    "if-match": f'"{self.health_generation}"',
                },
                body={
                    "status": health_status,
                    "observed_at": observed_at,
                },
            )
            stage = "health_receipt"
            result = system.data_of(response)
            generation = result.get("generation")
            if (
                result.get("provider_id") != self.route["provider_id"]
                or result.get("status") != health_status
                # System serializes Date with UTC Z and millisecond precision.
                # Require the receipt to confirm this exact sent observation.
                or result.get("observed_at") != observed_at
                or not isinstance(generation, str)
                or not re.fullmatch(r"[1-9][0-9]*", generation)
            ):
                raise ChatError("System health receipt invalid")
            self.health_generation = generation
            self.next_refresh = time.monotonic() + 60
        except Exception:
            # Diagnostics are fixed labels only and must never mask the failure.
            try:
                log = getattr(self, "log", None)
                if log is not None:
                    log.write(
                        f"Local Chat tick failed: stage={stage}\n".encode("ascii")
                    )
                    log.flush()
            except Exception:
                pass
            raise

    def close(self) -> list[str]:
        for label, process in reversed(self.processes):
            try:
                stop_chat_process(process, 70 if label == "worker" else 15)
            except Exception:
                self.quiescent = False
                return [f"Chat {label} shutdown"]
        self.processes.clear()
        self.quiescent = True
        try:
            if self.agent_installed:
                register_owned_runs(self.resources, self.database_url, self.ownership)
            self.ownership.cleanup()
        except Exception:
            return ["Chat Redis cleanup; preserve database evidence"]
        return []

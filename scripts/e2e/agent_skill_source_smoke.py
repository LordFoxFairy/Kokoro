"""Opt-in, owned Agent Source composition; imports alone require only stdlib.

This is a Root test driver, not an execution service or an Agent implementation.
The production package supplies HTTP, persistence, signing, authorization and reads.
"""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack, contextmanager
from functools import partial
import base64
import hashlib
import http.client
import importlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import threading
from typing import Callable, Iterator
from urllib.parse import parse_qsl, urlsplit, urlunsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "apps/kokoro-agent"
SCHEMA = "kokoro_agent_source"
ISSUER = "https://agent.example.test"
RESOURCE = "https://kokoro.dev/resources/platform-internal"
SCOPE = "platform:execution.invoke"
TASK_DRAIN_SECONDS = 5
# The longest submitted callback is IAM record(timeout=30); HTTP launch uses 10s.
THREAD_DRAIN_SECONDS = 35
SKILL_NAME = "source-smoke"
SKILL_DESCRIPTION = "Read this owned source smoke capability."
SKILL_BYTES = (
    f"---\nname: {SKILL_NAME}\ndescription: {SKILL_DESCRIPTION}\n---\n# Sandbox\n\nOwned signed PUT smoke.\n"
).encode()
# The same atomic ownership semantics as the existing BFF/Agent smoke, but one DB.
CLAIM = """if redis.call('DBSIZE') ~= 0 then return 'NOT_EMPTY' end
return redis.call('SET',KEYS[1],ARGV[1],'NX','EX',7200) or 'CLAIM_FAILED'"""
CLEAN = """if redis.call('GET',KEYS[1]) ~= ARGV[1] then return 'OWNERSHIP_LOST' end
local allowed = {}; for _,k in ipairs(KEYS) do allowed[k]=true end
local present=redis.call('KEYS','*'); for _,k in ipairs(present) do
if not allowed[k] then return 'UNEXPECTED_KEY' end end
if #present>0 then redis.call('UNLINK',unpack(present)) end; return 'OK'"""


class SourceError(RuntimeError):
    """Bounded, secret-free Source diagnostic."""


@contextmanager
def _registering_activity() -> Iterator[None]:
    """Defer the installed raising SIGTERM handler only until ownership is saved.

    A main-thread pthread mask alone is insufficient when an existing HTTP thread
    can receive a process-directed signal and schedule Python's main-thread handler.
    Restore and forward instead; default/ignored handlers are left untouched.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.getsignal(signal.SIGTERM)
    if not callable(previous):
        yield
        return
    pending: tuple[int, object] | None = None

    def defer(signum: int, frame: object) -> None:
        nonlocal pending
        pending = (signum, frame)

    signal.signal(signal.SIGTERM, defer)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)
        if pending is not None:
            previous(*pending)


def preflight(enabled: bool, agent_redis: str | None, shared_redis: str) -> None:
    if type(enabled) is not bool or (not enabled and agent_redis is not None):
        raise SourceError("Agent source mode must be explicit")
    if not enabled:
        return
    try:
        source, shared = urlsplit(agent_redis or ""), urlsplit(shared_redis)
        if (
            source.scheme not in {"redis", "rediss"}
            or source.hostname not in {"127.0.0.1", "localhost", "::1"}
            or source.port == 3310
            or source.query
            or source.fragment
            or not re.fullmatch(r"/[0-9]+", source.path)
            or not 0 <= int(source.path[1:]) <= 15
            or (source.scheme, source.hostname, source.port or 6379)
            != (shared.scheme, shared.hostname, shared.port or 6379)
            or int(source.path[1:]) == int(shared.path.removeprefix("/") or "0")
        ):
            raise ValueError
    except (ValueError, TypeError):
        raise SourceError(
            "Agent source needs a distinct explicit local Redis database"
        ) from None
    require_agent_environment()


def require_agent_environment() -> None:
    """Reject missing/wrong installation before creating any external resource."""
    try:
        if Path(sys.prefix).resolve() != (AGENT / ".venv").resolve():
            raise ValueError
        package = importlib.import_module("kokoro_agent")
        if (
            Path(package.__file__).resolve().parent
            != (AGENT / "src/kokoro_agent").resolve()
        ):
            raise ValueError
        for module in (
            "kokoro_agent.worker.platform",
            "kokoro_agent.skills.backend",
            "kokoro_agent.skills.middleware",
            "kokoro_agent.interfaces.http.main",
            "kokoro_agent.infrastructure.schema",
            "kokoro_agent.generated.kokoro.platform.v1.platform_runtime_connect",
            "cryptography.hazmat.primitives.asymmetric.ed25519",
            "redis.asyncio",
        ):
            importlib.import_module(module)

        def git(*args: str) -> str:
            return subprocess.run(
                ["git", *args], check=True, capture_output=True, text=True, timeout=10
            ).stdout.strip()

        if git("-C", str(AGENT), "status", "--porcelain"):
            raise ValueError
        sha = git("-C", str(AGENT), "rev-parse", "HEAD")
        if not git("-C", str(ROOT), "ls-tree", "HEAD", "apps/kokoro-agent").startswith(
            f"160000 commit {sha}\t"
        ):
            raise ValueError
    except Exception:
        raise SourceError(
            "Agent source requires the clean Root-pinned Agent .venv installation"
        ) from None


def database_url(admin: str, name: str) -> str:
    parsed = urlsplit(admin)
    if (
        not re.fullmatch(r"iam_web_oidc_[a-z0-9]+", name)
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.scheme not in {"postgres", "postgresql"}
        or parsed.fragment
        or any(
            key.lower() in {"schema", "options", "search_path"}
            for key, _ in parse_qsl(parsed.query)
        )
    ):
        raise SourceError("Agent source database target invalid")
    return urlunsplit((parsed.scheme, parsed.netloc, "/" + name, parsed.query, ""))


def command_document(
    tenant: str, method: str, fields: dict[str, object]
) -> dict[str, object]:
    expected = {
        "InstallSkill": {"source_ref", "target_owner_scope"},
        "SetSkillInstallationEnabled": {"installation_id", "enabled"},
    }
    if method not in expected or set(fields) != expected[method]:
        raise SourceError("Agent source setup command invalid")
    return {
        "command_digest_version": "3.0.0",
        "fq_method": "kokoro.platform.v1.SkillInstallationService/" + method,
        "tenant_ref": tenant,
        "command": fields,
    }


def command_digest(document: dict[str, object]) -> str:
    """JCS-equivalent for this fixture's ASCII strings, objects and booleans only.

    Reject all numbers/non-ASCII rather than pretend json.dumps is a general JCS
    implementation. Production bindings still use the owner's generated projector.
    """

    def validate(value: object) -> None:
        if type(value) is str:
            if not value.isascii() or any(ord(char) < 32 for char in value):
                raise SourceError("Agent source command scalar invalid")
        elif type(value) is dict:
            for key, item in value.items():
                if type(key) is not str:
                    raise SourceError("Agent source command key invalid")
                validate(key)
                validate(item)
        elif type(value) is not bool:
            raise SourceError("Agent source command scalar invalid")

    validate(document)
    return hashlib.sha256(
        json.dumps(
            document, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()


def require_revoke_result(record: object) -> None:
    if record != {
        "kind": "result",
        "command": "revoke-agent-execution",
        "status": "ok",
    }:
        raise SourceError("IAM Agent execution revoke protocol invalid")


def require_inventory(before: tuple[int, ...], after: tuple[int, ...]) -> None:
    if before != (2, 31, 2, 1) or after != (2, 34, 2, 1):
        raise SourceError("Agent source setup receipt inventory mismatch")


def close_steps(steps: list[tuple[str, Callable[[], object]]]) -> list[str]:
    failures = []
    for name, close in steps:
        try:
            close()
        except BaseException:
            failures.append(f"Agent source {name} cleanup failed")
    return failures


def _secret_file(path: Path, content: bytes) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)


async def verify_native_metadata(backend: object, encoded_skill_id: str) -> None:
    """Exercise the same native parser and public lifecycle hook as the Factory."""
    from deepagents.backends.composite import CompositeBackend
    from deepagents.backends.state import StateBackend
    from langgraph.runtime import Runtime
    from kokoro_agent.skills.middleware import RunSkillsMiddleware

    route = CompositeBackend(default=StateBackend(), routes={"/.skills/": backend})
    middleware = RunSkillsMiddleware(backend=route, sources=["/.skills/"])
    result = await middleware.abefore_agent({"messages": []}, Runtime(), {})
    metadata = result["skills_metadata"]
    if (
        len(metadata) != 1
        or metadata[0]["name"] != SKILL_NAME
        or metadata[0]["description"] != SKILL_DESCRIPTION
        or metadata[0]["path"] != f"/.skills/{encoded_skill_id}/SKILL.md"
        or result.get("skills_load_errors")
    ):
        raise SourceError("Agent source native Skill discovery mismatch")


class AgentSourceDriver:
    """One owned HTTP thread and one event loop; no model/worker loop."""

    def __init__(
        self, directory: Path, database: str, redis_url: str, run_id: str
    ) -> None:
        self.directory, self.database, self.redis_url, self.run_id = (
            directory.resolve(),
            database,
            redis_url,
            run_id,
        )
        self.secret = secrets.token_hex(32)
        self.marker = f"kokoro:root:agent-source:{run_id}:ownership"
        self.claimed = False
        self.claim_attempted = False
        self.server = self.thread = self.runner = self.stack = self.redis = None
        self.closed = False
        self._closing = False
        self.dependencies_quiescent = False
        self._http_quiescent = False
        self._activity_failures: list[str] = []
        self._exercise_task: asyncio.Task[dict[str, object]] | None = None
        self._exercise_observed = False
        self._blocking_futures: dict[asyncio.Future[object], str] = {}
        self.phase = "not-started"
        self.close_failures: list[str] = []
        self._files: list[Path] = []

    @property
    def jwks_url(self) -> str:
        if self.server is None:
            raise SourceError("Agent source HTTP is not started")
        return (
            f"http://127.0.0.1:{self.server.server_address[1]}/v1/execution-proof/jwks"
        )

    def start_http(self) -> None:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from kokoro_agent.interfaces.http.main import build_http_composition
        from kokoro_agent.interfaces.http.server import create_http_server

        key = Ed25519PrivateKey.generate()
        x = (
            base64.urlsafe_b64encode(
                key.public_key().public_bytes(
                    serialization.Encoding.Raw, serialization.PublicFormat.Raw
                )
            )
            .rstrip(b"=")
            .decode()
        )
        core = {"crv": "Ed25519", "kty": "OKP", "x": x}
        self.thumbprint = (
            base64.urlsafe_b64encode(
                hashlib.sha256(
                    json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
                ).digest()
            )
            .rstrip(b"=")
            .decode()
        )
        self.kid = "source-" + self.run_id
        private, public = (
            self.directory / "agent-private.pem",
            self.directory / "agent-public.json",
        )
        for path, value in (
            (
                private,
                key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                ),
            ),
            (
                public,
                json.dumps(
                    {"keys": [{**core, "kid": self.kid, "use": "sig", "alg": "EdDSA"}]}
                ).encode(),
            ),
        ):
            _secret_file(path, value)
            self._files.append(path)
        self.private = private
        self.env = {
            "KOKORO_AGENT_DATABASE_URL": self.database,
            "KOKORO_AGENT_DATABASE_SCHEMA": SCHEMA,
            "KOKORO_REDIS_URL": self.redis_url,
            "KOKORO_INTERNAL_SECRET_AGENT": self.secret,
            "KOKORO_AGENT_EXECUTION_PROOF_PUBLIC_JWKS_FILE": str(public),
            "KOKORO_AGENT_EXECUTION_PROOF_HTTP_ACTIVE_KID": self.kid,
            "KOKORO_AGENT_EXECUTION_PROOF_HTTP_ACTIVE_JWK_THUMBPRINT_SHA256": self.thumbprint,
        }
        composition = build_http_composition(self.env)
        if not composition.jwks.available:
            raise SourceError("Agent source JWKS unavailable")
        self.server = create_http_server(
            composition.config, "127.0.0.1", 0, execution_proof_jwks=composition.jwks
        )
        if self.server.server_address[1] == 3310:
            raise SourceError("Agent source reserved port")
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True
        )
        self.thread.start()
        self.runner = asyncio.Runner()

    def exercise(
        self,
        ready: object,
        platform_base: str,
        object_origin: str,
        skill_id: str,
        revision: int,
        expected: bytes,
        revoke: Callable[[], object],
    ) -> dict[str, object]:
        if self.runner is None or self._closing or self._exercise_task is not None:
            raise SourceError("Agent source runtime unavailable")
        # Runner.run does not cancel its Task when a synchronous signal handler
        # raises. Retain it before running the loop so close can cancel first.
        with _registering_activity():
            self._exercise_task = self.runner.get_loop().create_task(
                self._exercise(
                    ready,
                    platform_base,
                    object_origin,
                    skill_id,
                    revision,
                    expected,
                    revoke,
                )
            )

        async def wait_for_exercise() -> None:
            # The wrapper never owns the result/exception; the retained Task does.
            await asyncio.wait({self._exercise_task})

        try:
            self.runner.run(wait_for_exercise())
            result = self._exercise_task.result()
            self._exercise_observed = True
            return result
        except BaseException as error:
            if not self._exercise_task.done():
                # External interruption belongs to the enclosing runner.
                raise
            self._exercise_observed = True
            if isinstance(error, SourceError) or not isinstance(error, Exception):
                raise
            raise SourceError(
                f"Agent source {self.phase} failed ({type(error).__name__})"
            ) from None

    async def _blocking_call(
        self, label: str, callback: Callable[..., object], *args: object
    ) -> object:
        if self._closing:
            raise SourceError("Agent source is closing")
        with _registering_activity():
            future = asyncio.get_running_loop().run_in_executor(
                None, partial(callback, *args)
            )
            self._blocking_futures[future] = label
        try:
            # Canceling the business Task must not cancel/hide the executor Future.
            result = await asyncio.shield(future)
        except asyncio.CancelledError:
            raise
        except BaseException:
            if future.done():
                self._blocking_futures.pop(future)
            raise
        else:
            self._blocking_futures.pop(future)
            return result

    async def _drain(self) -> tuple[bool, list[str]]:
        failures = self._activity_failures
        task = self._exercise_task
        if task is not None:
            _, pending = await asyncio.wait({task}, timeout=TASK_DRAIN_SECONDS)
            if pending:
                return False, [*failures, "Agent source business task drain timed out"]
            if not task.cancelled():
                error = task.exception()
                if error is not None and not self._exercise_observed:
                    failures.append("Agent source business task failed during drain")
                self._exercise_observed = True
        if self._blocking_futures:
            done, pending = await asyncio.wait(
                self._blocking_futures, timeout=THREAD_DRAIN_SECONDS
            )
            for future in done:
                label = self._blocking_futures.pop(future)
                if future.cancelled() or future.exception() is not None:
                    failures.append(f"Agent source {label} thread failed during drain")
            if pending:
                return False, [
                    *failures,
                    "Agent source executor thread drain timed out",
                ]
        return True, list(failures)

    async def _prepare(
        self, ready: object, platform_base: str, object_origin: str
    ) -> None:
        from redis.asyncio import Redis
        from kokoro_agent.config import AppConfig
        from kokoro_agent.infrastructure.postgres import connect_pg
        from kokoro_agent.infrastructure.schema import (
            apply_agent_schema,
            verify_agent_schema,
        )
        from kokoro_agent.infrastructure.postgres_run_repository import (
            make_run_repository,
            RunRepositorySettings,
        )
        from kokoro_agent.worker.platform import worker_platform_runtime

        self.phase = "Redis ownership"
        self.redis = Redis.from_url(
            self.redis_url,
            socket_connect_timeout=3,
            socket_timeout=5,
            decode_responses=True,
        )
        self.claim_attempted = True
        if await self.redis.eval(CLAIM, 1, self.marker, self.run_id) != "OK":
            raise SourceError("Agent source Redis database is not exclusively empty")
        self.claimed = True
        self.phase = "schema installation"
        async with connect_pg(self.database) as connection:
            await apply_agent_schema(connection, SCHEMA, require_blank=True)
            await verify_agent_schema(connection, SCHEMA)
        credential = ready.tenant_execution
        if credential is None:
            raise SourceError("IAM Agent execution credential absent")
        path = self.directory / "agent-execution.json"
        _secret_file(
            path,
            json.dumps(
                [
                    {
                        "tenant_id": ready.tenant_id,
                        "generation": 1,
                        "credential_ref_version": "source-v1",
                        "client_id": credential.client_id,
                        "client_secret": credential.client_secret,
                        "resource": RESOURCE,
                        "scope": SCOPE,
                    }
                ]
            ).encode(),
        )
        self._files.append(path)
        config = AppConfig.from_env(
            {
                **self.env,
                "KOKORO_AGENT_IAM_BASE_URL": ready.base_url,
                "KOKORO_PLATFORM_BASE_URL": platform_base,
                "KOKORO_AGENT_PLATFORM_CLIENT_CREDENTIALS_FILE": str(path),
                "KOKORO_AGENT_EXECUTION_PROOF_ISSUER": ISSUER,
                "KOKORO_AGENT_EXECUTION_PROOF_PRIVATE_KEY_FILE": str(self.private),
                "KOKORO_AGENT_EXECUTION_PROOF_WORKER_ACTIVE_KID": self.kid,
                "KOKORO_AGENT_EXECUTION_PROOF_WORKER_ACTIVE_JWK_THUMBPRINT_SHA256": self.thumbprint,
                "KOKORO_STORAGE_OBJECT_ORIGIN": object_origin,
            }
        )
        self.phase = "runtime composition"
        self.stack = AsyncExitStack()
        self.runtime = await self.stack.enter_async_context(
            worker_platform_runtime(config)
        )
        self.repository = await self.stack.enter_async_context(
            make_run_repository(
                RunRepositorySettings(
                    database_url=self.database, schema_name=SCHEMA, lease_ttl_ms=120_000
                )
            )
        )
        from pyqwest import Client, HTTPTransport
        from kokoro_agent.clients.platform_transport import BoundedConnectTransport
        from kokoro_agent.generated.kokoro.platform.v1.platform_runtime_connect import (
            SkillInstallationServiceClient,
        )

        pool = HTTPTransport(
            follow_redirects=False,
            connect_timeout=3,
            read_timeout=10,
            enable_otel=False,
        )
        self.stack.push_async_callback(pool.aclose)
        self.installer = SkillInstallationServiceClient(
            platform_base,
            http_client=Client(BoundedConnectTransport(pool)),
            read_max_bytes=1_048_576,
            timeout_ms=10_000,
            send_compression=None,
        )
        self.stack.push_async_callback(self.installer.close)

    def _launch(self, ready: object, source_ref: str) -> None:
        body = {
            "request_id": "source-" + self.run_id,
            "run_id": "source-" + self.run_id,
            "session_id": "source-session-" + self.run_id,
            "feature_key": "chat",
            "selected_skill_source_refs": [source_ref],
            "message_id": "source-message-" + self.run_id,
            "content": "Read selected Skill source.",
        }
        connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_address[1], timeout=10
        )
        try:
            connection.request(
                "POST",
                "/v1/runs",
                json.dumps(body),
                headers={
                    "authorization": "Bearer " + self.secret,
                    "content-type": "application/json",
                    "x-kokoro-tenant-ref": ready.tenant_id,
                    "x-kokoro-actor-ref": ready.subject_id,
                    "x-kokoro-subject-ref": ready.subject_id,
                    "x-kokoro-actor-kind": "user",
                    "x-kokoro-subject-kind": "user",
                    "x-kokoro-identity-assertion-ref": "source-fixture-" + self.run_id,
                },
            )
            response = connection.getresponse()
            raw = response.read(1_048_577)
            if response.status != 202 or len(raw) > 1_048_576:
                raise SourceError("Agent source HTTP admission failed")
            if json.loads(raw).get("data", {}).get("run_id") != body["run_id"]:
                raise SourceError("Agent source admission identity mismatch")
        finally:
            connection.close()

    async def _command(
        self,
        ready: object,
        leased: object,
        method: str,
        fields: dict[str, object],
        request: object,
    ) -> object:
        from kokoro_agent.generated.kokoro.common.v1 import common_pb
        from kokoro_agent.execution.platform_request_binding import (
            project_request_binding,
        )
        from kokoro_agent.execution.execution_proof_supplier import (
            create_execution_proof_supplier,
        )

        request.request_id = str(uuid4())
        request.command = common_pb.CommandIdentity(
            command_id=str(uuid4()),
            request_digest=command_digest(
                command_document(ready.tenant_id, method, fields)
            ),
        )
        token = await self.runtime.tokens.token(ready.tenant_id)
        binding = project_request_binding(tenant_ref=ready.tenant_id, request=request)
        supplier = create_execution_proof_supplier(
            leased_run=leased,
            lease_reader=self.runtime.lease_reader,
            signer=self.runtime.signer,
        )
        request.execution_proof = await supplier.issue(
            binding.operation, binding.sha256
        )
        call = (
            self.installer.install_skill
            if method == "InstallSkill"
            else self.installer.set_skill_installation_enabled
        )
        return await call(
            request, headers={"authorization": "Bearer " + token}, timeout_ms=10_000
        )

    async def _exercise(
        self,
        ready: object,
        platform_base: str,
        object_origin: str,
        skill_id: str,
        revision: int,
        expected: bytes,
        revoke: Callable[[], object],
    ) -> dict[str, object]:
        from kokoro_agent.generated.kokoro.platform.v1 import platform_runtime_pb as pb
        from kokoro_agent.domain.run.models import LeasedRun
        from kokoro_agent.skills.backend import TypedSkillBackend
        from kokoro_agent.clients.skills import SkillClientError
        from kokoro_agent.clients.platform_transport import PlatformCallError
        from kokoro_agent.execution.execution_proof_supplier import (
            ExecutionProofUnavailableError,
        )

        await self._prepare(ready, platform_base, object_origin)
        source_ref = "skill:" + skill_id
        self.phase = "HTTP admission and claim"
        await self._blocking_call("launch", self._launch, ready, source_ref)
        run_id = "source-" + self.run_id
        request = await self.repository.get_pending_dispatch(run_id)
        if request is None or request.selected_skill_source_refs != (source_ref,):
            raise SourceError("Agent source persisted selection mismatch")
        lease = await self.repository.claim_dispatch(request, consumer="source-smoke")
        if lease is None:
            raise SourceError("Agent source lease claim failed")
        leased = LeasedRun(request=request, lease=lease)
        self.phase = "installation"
        installed = await self._command(
            ready,
            leased,
            "InstallSkill",
            {
                "source_ref": {"present": True, "value": source_ref},
                "target_owner_scope": {
                    "present": True,
                    "value": {"kind": "user", "id": ready.subject_id},
                },
            },
            pb.InstallSkillRequest(
                source_ref=pb.SkillSourceRef(value=source_ref),
                target_owner_scope=pb.OwnerScope(kind="user", id=ready.subject_id),
            ),
        )
        item = installed.installation
        if (
            item is None
            or item.installation_id is None
            or item.source_ref is None
            or item.source_ref.value != source_ref
            or item.revision != revision
            or not item.installed
            or not item.enabled
            or installed.replayed
        ):
            raise SourceError("Agent source installed identity mismatch")
        self.phase = "typed resolution and bytes"
        reader = self.runtime.skills_for_run(leased)
        resolved = await reader.resolve(request.selected_skill_source_refs)
        if (
            len(resolved) != 1
            or resolved[0].revision != revision
            or resolved[0].asset_ref != item.package_asset_ref
            or resolved[0].content_digest != item.content_digest
        ):
            raise SourceError("Agent source resolved identity mismatch")
        backend = TypedSkillBackend(resolved, reader)
        path = f"/{resolved[0].path_segment}/SKILL.md"

        async def read(current: object) -> None:
            result = (await current.adownload_files([path]))[0]
            if result.error is not None or result.content != expected:
                raise SourceError("Agent source original bytes mismatch")

        async def denied(current: object) -> None:
            try:
                await current.adownload_files([path])
            except SkillClientError as error:
                if str(error) != "SKILL_AUTHORIZATION_UNAVAILABLE":
                    raise SourceError(
                        "Agent source failed outside authorization"
                    ) from None
            else:
                raise SourceError("Agent source denied read succeeded")

        async def owner_denied(current_lease: object, expected_code: str) -> None:
            try:
                await self.runtime.for_run(current_lease).send(
                    pb.GetApprovedSkillPackageReferenceRequest(
                        request_id=str(uuid4()),
                        source_ref=pb.SkillSourceRef(value=source_ref),
                    )
                )
            except PlatformCallError as error:
                if error.code != expected_code:
                    raise SourceError(
                        "Agent source denial was not the expected owner decision"
                    ) from None
            else:
                raise SourceError(
                    "Agent source owner unexpectedly approved denied read"
                )

        await read(backend)
        from deepagents.backends.protocol import PERMISSION_DENIED

        if (
            await backend.awrite(path, "forbidden overwrite")
        ).error != PERMISSION_DENIED:
            raise SourceError("Agent source write was not denied")
        self.phase = "native discovery"
        await verify_native_metadata(backend, resolved[0].path_segment)
        await read(backend)
        self.phase = "installation enablement"
        for enabled in (False, True):
            result = await self._command(
                ready,
                leased,
                "SetSkillInstallationEnabled",
                {
                    "installation_id": {
                        "present": True,
                        "value": item.installation_id.value,
                    },
                    "enabled": enabled,
                },
                pb.SetSkillInstallationEnabledRequest(
                    installation_id=item.installation_id, enabled=enabled
                ),
            )
            if (
                result.installation is None
                or result.installation.enabled is not enabled
                or result.replayed
            ):
                raise SourceError("Agent source installation change mismatch")
            if enabled:
                await read(backend)
            else:
                await denied(backend)
                await owner_denied(leased, "PLATFORM_NOT_FOUND")
        self.phase = "lease takeover"
        if not await self.repository.pause(run_id, lease):
            raise SourceError("Agent source lease pause failed")
        next_lease = await self.repository.adopt(run_id, owner="source-smoke-next")
        if next_lease is None or next_lease.generation <= lease.generation:
            raise SourceError("Agent source lease takeover failed")
        try:
            await backend.adownload_files([path])
        except ExecutionProofUnavailableError:
            pass
        else:
            raise SourceError("Agent source old lease read succeeded")
        current = LeasedRun(request=request, lease=next_lease)
        current_reader = self.runtime.skills_for_run(current)
        current_resolved = await current_reader.resolve(
            request.selected_skill_source_refs
        )
        current_backend = TypedSkillBackend(current_resolved, current_reader)
        await read(current_backend)
        self.phase = "IAM execution revocation"
        require_revoke_result(await self._blocking_call("revoke", revoke))
        await denied(current_backend)
        await owner_denied(current, "PLATFORM_PERMISSION_DENIED")
        await self.repository.try_mark_terminal(run_id, next_lease)
        return {
            "original_bytes": "PASS",
            "read_only": "PASS",
            "native_metadata": "PASS",
            "installation_disabled": "PASS",
            "old_lease": "PASS",
            "iam_execution_revoked": "PASS",
            "setup_receipts": 3,
        }

    def _close_http(self) -> None:
        if self.server is None:
            self._http_quiescent = True
            return
        self.server.start_draining()
        if self.thread is not None and self.thread.is_alive():
            self.server.shutdown()
        drained = self.server.wait_for_active_handlers(2)
        if self.thread is not None:
            self.thread.join(2)
        self._http_quiescent = drained and (
            self.thread is None or not self.thread.is_alive()
        )
        self.server.server_close()
        if not self._http_quiescent:
            raise SourceError("Agent source HTTP activity remained")

    async def _close_async(self) -> None:
        failures = []
        if self.stack is not None:
            try:
                async with asyncio.timeout(10):
                    await self.stack.aclose()
            except BaseException:
                failures.append("runtime")
        if self.redis is not None:
            try:
                # An interrupted SET may have committed before its reply was lost.
                owns_marker = self.claimed
                if self.claim_attempted and not self.claimed:
                    owns_marker = await self.redis.get(self.marker) == self.run_id
                if owns_marker:
                    if (
                        await self.redis.eval(
                            CLEAN, 2, self.marker, "kokoro:runs:requests", self.run_id
                        )
                        != "OK"
                    ):
                        raise SourceError("Agent source Redis ownership changed")
                    self.claimed = False
            except BaseException:
                failures.append("Redis ownership")
            finally:
                async with asyncio.timeout(5):
                    await self.redis.aclose()
        if failures:
            raise SourceError("Agent source cleanup failed: " + ", ".join(failures))

    def close(self) -> list[str]:
        if self.closed:
            return list(self.close_failures)
        self._closing = True
        # Cancel synchronously BEFORE any Runner.run can restart pending business.
        if self._exercise_task is not None and not self._exercise_task.done():
            self._exercise_task.cancel()
        failures = []
        if self.runner is not None:
            try:
                drained, failures = self.runner.run(self._drain())
            except BaseException:
                drained = False
                failures = ["Agent source activity drain interrupted"]
            if not drained:
                # Python cannot kill a running executor thread. Do not close its
                # resources or the loop (Runner.close would wait without a bound).
                # A caller may retry close after the actual work has finished.
                self.close_failures = failures
                return list(failures)
        http_failures = close_steps([("HTTP", self._close_http)])
        self.dependencies_quiescent = not http_failures or self._http_quiescent
        if not self.dependencies_quiescent:
            self.close_failures = failures + http_failures
            self.closed = True
            return list(self.close_failures)
        failures.extend(http_failures)
        self.closed = True
        steps = []
        if self.runner is not None:
            steps.extend(
                [
                    ("runtime/Redis", lambda: self.runner.run(self._close_async())),
                    ("event loop", self.runner.close),
                ]
            )
        failures.extend(close_steps(steps))
        if not failures:
            failures.extend(
                close_steps(
                    [
                        ("secret file", lambda path=path: path.unlink())
                        for path in self._files
                    ]
                )
            )
        self.close_failures = failures
        return list(failures)

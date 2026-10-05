"""Owned Platform lifecycle for the local capability composition."""

from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
import secrets
import subprocess

import capability_bff_smoke_runtime as runtime
import local_chat_runtime
import run_bff_skill_draft_sandbox_smoke as sandbox

PLATFORM = Path(__file__).resolve().parents[2] / "apps/kokoro-capability"


class PlatformRuntimeError(RuntimeError):
    """Sanitized composition failure; never includes credentials or endpoints."""


class LocalPlatformRuntime:
    def __init__(
        self,
        *,
        node: Path,
        node_environment: dict[str, str],
        directory: Path,
        credentials,
        log,
    ) -> None:
        self.node = node
        self.node_environment = node_environment
        self.directory = directory
        self.credentials = credentials
        self.log = log
        self.process: subprocess.Popen[bytes] | None = None
        self.quiescent = True
        self.storage_service_credential = secrets.token_hex(32)
        self.credentials.add(self.storage_service_credential)
        self._files = ExitStack()

    def start(
        self,
        application_database_url: str,
        redis_url: str,
        ready: sandbox.SandboxReady,
        storage_base_url: str,
    ) -> dict[str, str]:
        if self.process is not None:
            raise PlatformRuntimeError("Platform runtime was already started")
        database_url = sandbox.owner_database_url(
            application_database_url,
            ready.database_name,
            "kokoro_platform",
        )
        files = self._files.enter_context(
            sandbox.credential_files(self.directory, ready)
        )
        port = runtime.free_port()
        environment = {
            **self.node_environment,
            "NODE_ENV": "development",
            "KOKORO_POSTGRES_URL": database_url,
            "KOKORO_REDIS_URL": redis_url,
            "KOKORO_STORAGE_URL": storage_base_url,
            "KOKORO_PLATFORM_STORAGE_SERVICE_CREDENTIAL": self.storage_service_credential,
            "KOKORO_IAM_BASE_URL": ready.base_url,
            "KOKORO_PLATFORM_HOST": "127.0.0.1",
            "KOKORO_PLATFORM_PORT": str(port),
            "KOKORO_PLATFORM_SURFACES": "skill-catalog,skill-source,skill-installation-product",
            "KOKORO_PLATFORM_IAM_RESOURCE_SERVER_CREDENTIAL_FILE": str(
                files["resource-server.json"]
            ),
            "KOKORO_PLATFORM_IAM_TENANT_CREDENTIALS_FILE": str(
                files["tenant-execution.json"]
            ),
        }
        for command, timeout in (
            ([str(self.node.parent / "corepack"), "pnpm", "build"], 120),
            (
                [
                    str(self.node.parent / "corepack"),
                    "pnpm",
                    "db:apply-schema",
                ],
                180,
            ),
        ):
            if (
                runtime.run_owned_command(
                    command,
                    cwd=PLATFORM,
                    env=environment,
                    log=self.log,
                    timeout=timeout,
                )
                != 0
            ):
                raise PlatformRuntimeError(
                    "Platform build or owner schema installation failed"
                )
        with local_chat_runtime.registration_guard():
            self.process = runtime.start_process(
                self.node, PLATFORM, environment, self.log
            )
            self.quiescent = False
        base = f"http://127.0.0.1:{port}"
        sandbox._wait_ready(base, self.process)
        return {
            "KOKORO_PLATFORM_BASE_URL": base,
            "KOKORO_BFF_PLATFORM_CATALOG_CREDENTIALS_FILE": str(
                files["bff-catalog.json"]
            ),
            "KOKORO_PLATFORM_PROJECTION_CREDENTIAL_FILE": str(
                files["bff-projection.json"]
            ),
            "KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED": "true",
        }

    def require_alive(self) -> None:
        if self.process is None or self.process.poll() is not None:
            raise PlatformRuntimeError("Owned Platform process exited")

    def close(self) -> list[str]:
        failures: list[str] = []
        if self.process is not None:
            try:
                runtime.stop_owned_process(self.process)
                self.quiescent = self.process.poll() is not None
            except Exception:
                self.quiescent = False
                failures.append("Platform process cleanup")
        if self.quiescent:
            try:
                self._files.close()
            except Exception:
                failures.append("Platform credential file cleanup")
        else:
            failures.append("Platform credentials preserved for active process")
        return failures

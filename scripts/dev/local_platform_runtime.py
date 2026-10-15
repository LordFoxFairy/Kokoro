"""Owned Platform lifecycle for the local capability composition."""

from __future__ import annotations

import base64
from contextlib import ExitStack
import json
import os
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

    def _write_private_json(self, name: str, value: object) -> Path:
        """Create a run-owned 0600 JSON input and remove it with this run."""
        path = self.directory / name
        try:
            descriptor = os.open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except OSError as error:
            raise PlatformRuntimeError("local Platform credential setup failed") from error
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(value, stream, separators=(",", ":"), sort_keys=True)
                stream.write("\n")
        except Exception:
            path.unlink(missing_ok=True)
            raise
        self._files.callback(path.unlink, missing_ok=True)
        return path

    def _keyring(self, name: str) -> Path:
        """Generate a one-run keyring; plaintext material never leaves it."""
        key = base64.b64encode(secrets.token_bytes(32)).decode("ascii")
        self.credentials.add(key)
        return self._write_private_json(
            name,
            {
                "activeKeyVersion": "local-v1",
                "keys": [{"version": "local-v1", "keyBase64": key}],
            },
        )

    def _service_credentials(
        self, tenant_id: str
    ) -> tuple[Path, dict[str, Path]]:
        """Create exact per-surface BFF credentials for the local owner run."""
        surfaces = {
            "projection": "projection",
            "mcp-personal": "mcp_personal",
            "custom-api": "custom_api_personal",
            "mcp-admin": "mcp_admin",
        }
        entries: list[dict[str, object]] = []
        bff_files: dict[str, Path] = {}
        for label, surface in surfaces.items():
            secret = secrets.token_urlsafe(48)
            self.credentials.add(secret)
            entry = {
                "credential_id": f"local-bff-{label}",
                "secret": secret,
                "caller": "kokoro-bff",
                "surfaces": [surface],
                "tenant_id": tenant_id,
            }
            entries.append(entry)
            bff_files[label] = self._write_private_json(
                f"bff-{label}-credential.json",
                {"version": 1, "entries": [entry]},
            )
        return (
            self._write_private_json(
                "platform-service-credentials.json",
                {"version": 1, "entries": entries},
            ),
            bff_files,
        )

    def start(
        self,
        application_database_url: str,
        redis_url: str,
        ready: sandbox.SandboxReady,
        storage_base_url: str | None,
        web_origin: str,
        *,
        include_skills: bool = True,
    ) -> dict[str, str]:
        if self.process is not None:
            raise PlatformRuntimeError("Platform runtime was already started")
        if include_skills != (storage_base_url is not None):
            raise PlatformRuntimeError(
                "Platform Skills composition requires an owned Storage endpoint"
            )
        database_url = sandbox.owner_database_url(
            application_database_url,
            ready.database_name,
            "kokoro_platform",
        )
        files = self._files.enter_context(
            sandbox.credential_files(self.directory, ready)
        )
        service_credentials, bff_credentials = self._service_credentials(
            ready.tenant_id
        )
        private_secret_keyring = self._keyring("mcp-private-secrets.json")
        private_fingerprint_keyring = self._keyring(
            "mcp-private-fingerprints.json"
        )
        oauth_keyring = self._keyring("mcp-oauth-secrets.json")
        custom_api_secret_keyring = self._keyring("custom-api-secrets.json")
        custom_api_fingerprint_keyring = self._keyring(
            "custom-api-fingerprints.json"
        )
        port = runtime.free_port()
        environment = {
            **self.node_environment,
            "NODE_ENV": "development",
            "KOKORO_POSTGRES_URL": database_url,
            "KOKORO_REDIS_URL": redis_url,
            "KOKORO_IAM_BASE_URL": ready.base_url,
            "KOKORO_PLATFORM_HOST": "127.0.0.1",
            "KOKORO_PLATFORM_PORT": str(port),
            "KOKORO_PLATFORM_SURFACES": (
                "skill-catalog,skill-source,skill-installation-product,"
                "mcp-personal,custom-api-personal,mcp-provider-admin"
                if include_skills
                else "mcp-personal,custom-api-personal,mcp-provider-admin"
            ),
            "KOKORO_PLATFORM_IAM_RESOURCE_SERVER_CREDENTIAL_FILE": str(
                files["resource-server.json"]
            ),
            "KOKORO_PLATFORM_IAM_TENANT_CREDENTIALS_FILE": str(
                files["tenant-execution.json"]
            ),
            "KOKORO_PLATFORM_SERVICE_CREDENTIALS_FILE": str(service_credentials),
            "KOKORO_MCP_DECLARATION_DRIVER": "http",
            "KOKORO_MCP_OAUTH_REDIRECT_URI": web_origin
            + "/mcp/oauth/callback",
            "KOKORO_MCP_CREDENTIAL_KEYRING_FILE": str(oauth_keyring),
            "KOKORO_MCP_PRIVATE_SECRET_KEYRING_FILE": str(
                private_secret_keyring
            ),
            "KOKORO_MCP_PRIVATE_FINGERPRINT_KEYRING_FILE": str(
                private_fingerprint_keyring
            ),
            "KOKORO_CUSTOM_API_SECRET_KEYRING_FILE": str(
                custom_api_secret_keyring
            ),
            "KOKORO_CUSTOM_API_FINGERPRINT_KEYRING_FILE": str(
                custom_api_fingerprint_keyring
            ),
        }
        if include_skills:
            if storage_base_url is None:
                raise PlatformRuntimeError(
                    "Platform Skills composition requires an owned Storage endpoint"
                )
            environment.update(
                {
                    "KOKORO_STORAGE_URL": storage_base_url,
                    "KOKORO_PLATFORM_STORAGE_SERVICE_CREDENTIAL": self.storage_service_credential,
                }
            )
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
        result = {
            "KOKORO_PLATFORM_BASE_URL": base,
            "KOKORO_BFF_PLATFORM_CATALOG_CREDENTIALS_FILE": str(
                files["bff-catalog.json"]
            ),
            "KOKORO_PLATFORM_PROJECTION_CREDENTIAL_FILE": str(
                bff_credentials["projection"]
            ),
            "KOKORO_BFF_PLATFORM_MCP_PERSONAL_CREDENTIALS_FILE": str(
                bff_credentials["mcp-personal"]
            ),
            "KOKORO_BFF_PLATFORM_CUSTOM_API_CREDENTIALS_FILE": str(
                bff_credentials["custom-api"]
            ),
            "KOKORO_BFF_PLATFORM_MCP_ADMIN_CREDENTIALS_FILE": str(
                bff_credentials["mcp-admin"]
            ),
        }
        if include_skills:
            result["KOKORO_SKILL_DRAFT_CANDIDATE_ENABLED"] = "true"
        return result

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

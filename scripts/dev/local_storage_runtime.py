"""Owned Storage lifecycle for the existing local login composition.

Reuse real PostgreSQL, Redis, S3 and ClamAV. Only the newly created bucket and
Storage process belong to this object; the caller owns the application database.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import secrets
import subprocess
from urllib.parse import urlsplit

import capability_bff_smoke_runtime as runtime
import local_chat_runtime
import run_agent_storage_artifact_smoke as storage_helper
import run_bff_skill_draft_sandbox_smoke as sandbox

STORAGE = Path(__file__).resolve().parents[2] / "apps/kokoro-storage"
INPUTS = (
    "KOKORO_OBJECT_STORE_ENDPOINT",
    "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT",
    "KOKORO_OBJECT_STORE_REGION",
    "KOKORO_OBJECT_STORE_ACCESS_KEY_ID",
    "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY",
    "KOKORO_SCANNER_HOST",
    "KOKORO_SCANNER_PORT",
    "KOKORO_OBJECT_STORE_PROFILE",
    "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE",
)


class StorageRuntimeError(RuntimeError):
    """Sanitized composition failure; never includes credentials or endpoints."""


def validate_environment(environment: dict[str, str]) -> dict[str, str]:
    """Admit only explicit loopback infrastructure inputs; no emulated providers."""
    values = {key: environment.get(key, "") for key in INPUTS}
    if any(not value.strip() for value in values.values()):
        raise StorageRuntimeError("Storage infrastructure inputs are incomplete")
    try:
        for key in INPUTS[:2]:
            values[key] = storage_helper._local_origin(values[key], "ObjectStore")
        port = int(values["KOKORO_SCANNER_PORT"])
        if (
            values["KOKORO_SCANNER_HOST"] not in sandbox.LOCAL_HOSTS
            or port == 3310
            or not 1 <= port <= 65535
            or values["KOKORO_OBJECT_STORE_PROFILE"] != "custom"
            or values["KOKORO_OBJECT_STORE_FORCE_PATH_STYLE"] != "true"
        ):
            raise ValueError
    except (ValueError, storage_helper.SmokeError):
        raise StorageRuntimeError(
            "Storage requires explicit local S3 and ClamAV"
        ) from None
    return values


class LocalStorageRuntime:
    def __init__(
        self,
        *,
        node: Path,
        environment: dict[str, str],
        node_environment: dict[str, str],
        directory: Path,
        credentials,
        log,
    ) -> None:
        self.node = node
        self.environment = validate_environment(environment)
        self.node_environment = node_environment
        self.directory = directory
        self.credentials = credentials
        self.log = log
        self.process: subprocess.Popen[bytes] | None = None
        self.bucket = "kokoro-local-" + secrets.token_hex(12)
        self.bucket_created = False
        self.bucket_attempted = False
        self.s3 = None
        self.quiescent = True

    def start(
        self,
        application_database_url: str,
        redis_url: str,
        *,
        platform_service_credential: str | None = None,
    ) -> dict[str, str]:
        if self.process is not None or self.s3 is not None:
            raise StorageRuntimeError("Storage runtime was already started")
        if importlib.util.find_spec("boto3") is None:
            raise StorageRuntimeError(
                "Storage profile requires the approved Agent Python runtime"
            )
        database = urlsplit(application_database_url).path.removeprefix("/")
        if not database or urlsplit(application_database_url).scheme not in {
            "postgres",
            "postgresql",
        }:
            raise StorageRuntimeError("Storage application database identity invalid")
        port = runtime.free_port()
        bff_secret, agent_secret = secrets.token_hex(32), secrets.token_hex(32)
        self.credentials.add(
            bff_secret,
            agent_secret,
            self.environment["KOKORO_OBJECT_STORE_ACCESS_KEY_ID"],
            self.environment["KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY"],
        )
        inputs = {
            **self.node_environment,
            **self.environment,
            "KOKORO_W2_STORAGE_NODE_BIN": str(self.node),
            "KOKORO_W2_POSTGRES_ADMIN_URL": application_database_url,
            "KOKORO_W2_REDIS_URL": redis_url,
            "KOKORO_W2_TEST_BUCKET": self.bucket,
        }
        self.s3 = storage_helper._s3(inputs)
        self.bucket_attempted = True

        def claim_bucket() -> None:
            self.bucket_created = True

        sandbox.create_owned_bucket(
            self.s3,
            self.bucket,
            self.environment["KOKORO_OBJECT_STORE_REGION"],
            claim_bucket,
        )
        storage_helper.preflight_bucket(self.s3, self.bucket, "")
        environment = storage_helper._storage_env(
            inputs, database, agent_secret, bff_secret, port
        )
        if platform_service_credential is not None:
            if not platform_service_credential:
                raise StorageRuntimeError("Platform service credential invalid")
            self.credentials.add(platform_service_credential)
            environment["KOKORO_STORAGE_SERVICE_CREDENTIALS"] += (
                f",kokoro-platform={platform_service_credential}"
            )
        environment.update(
            {
                key: value
                for key, value in self.node_environment.items()
                if key in {"NODE_OPTIONS", "TMPDIR"}
            }
        )
        fixture = storage_helper._storage_schema_fixture(self.directory)
        for command, cwd, timeout in (
            ([str(self.node.parent / "corepack"), "pnpm", "build"], STORAGE, 120),
            (
                [
                    str(self.node),
                    str(STORAGE / "node_modules/tsx/dist/cli.mjs"),
                    "scripts/apply-schema.ts",
                ],
                fixture,
                180,
            ),
        ):
            if (
                runtime.run_owned_command(
                    command, cwd=cwd, env=environment, log=self.log, timeout=timeout
                )
                != 0
            ):
                raise StorageRuntimeError(
                    "Storage build or owner schema installation failed"
                )
        with local_chat_runtime.registration_guard():
            self.process = runtime.start_process(
                self.node, STORAGE, environment, self.log
            )
            self.quiescent = False
        base = f"http://127.0.0.1:{port}"
        storage_helper._wait_storage(base, self.process)
        return {
            "KOKORO_STORAGE_RPC_BASE_URL": base,
            "KOKORO_STORAGE_OBJECT_ORIGIN": self.environment[
                "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"
            ],
            "KOKORO_BFF_STORAGE_SECRET": bff_secret,
        }

    def require_alive(self) -> None:
        if self.process is None or self.process.poll() is not None:
            raise StorageRuntimeError("Owned Storage process exited")

    def close(self) -> list[str]:
        failures: list[str] = []
        if self.process is not None:
            try:
                runtime.stop_owned_process(self.process)
                self.quiescent = self.process.poll() is not None
            except Exception:
                self.quiescent = self.process.poll() is not None
                failures.append("Storage process cleanup")
        if not self.quiescent:
            return [*failures, "Storage objects preserved for active process"]
        if self.bucket_attempted and not self.bucket_created:
            return [
                *failures,
                "Storage bucket creation outcome requires reconciliation",
            ]
        if self.bucket_created:
            try:
                sandbox.delete_owned_bucket(self.s3, self.bucket, storage_helper)
                sandbox.require_bucket_absent(self.s3, self.bucket)
                self.bucket_created = False
                self.bucket_attempted = False
            except Exception:
                failures.append("Storage owned bucket cleanup")
        return failures

"""Process, PostgreSQL and Redis lifecycle for the Scheduler/BFF smoke."""

from __future__ import annotations

from collections.abc import Callable
import getpass
import hashlib
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from typing import BinaryIO, Protocol
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
BFF = ROOT / "apps" / "kokoro-bff"
SCHEDULER = ROOT / "apps" / "kokoro-scheduler"


class SmokeError(RuntimeError):
    """Controlled failure whose message is safe to summarize."""


class ProcessLike(Protocol):
    pid: int

    def poll(self) -> int | None: ...


Command = Callable[..., str]


def process_group_exists(pgid: int) -> bool:
    try:
        result = subprocess.run(
            ["ps", "-axo", "pgid="],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        raise SmokeError("Owned process inventory failed") from None
    return str(pgid) in result.stdout.split()


def stop_owned_process(process: ProcessLike) -> None:
    for sig, seconds in ((signal.SIGTERM, 15.0), (signal.SIGKILL, 5.0)):
        process.poll()
        if not process_group_exists(process.pid):
            return
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        except PermissionError:
            if process_group_exists(process.pid):
                raise SmokeError("Owned process group termination was denied") from None
            return
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            process.poll()
            if not process_group_exists(process.pid):
                return
            time.sleep(0.05)
    raise SmokeError("Owned process group still exists after forced cleanup")


def run_owned_command(
    command: list[str], *, cwd: Path, env: dict[str, str], log: BinaryIO, timeout: float
) -> int:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SmokeError("Owned command exceeded its deadline") from None
    finally:
        stop_owned_process(process)


def command_output(
    command: list[str],
    *,
    timeout: float = 30,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> str:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        stop_owned_process(process)
        process.communicate()
        raise SmokeError("Owned command exceeded its deadline") from None
    finally:
        if process.poll() is None:
            stop_owned_process(process)
    if process.returncode != 0:
        raise SmokeError(
            f"{Path(command[0]).name} command failed (exit {process.returncode})"
        )
    return output


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _database_url(admin_url: str, name: str) -> str:
    parts = urlsplit(admin_url)
    netloc = parts.netloc
    if parts.username is None and parts.hostname is not None:
        host = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
        netloc = f"{quote(getpass.getuser(), safe='')}@{host}{'' if parts.port is None else f':{parts.port}'}"
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["options"] = "-csearch_path=public,pg_catalog -ctimezone=UTC"
    return urlunsplit((parts.scheme, netloc, f"/{name}", urlencode(query), ""))


def _redis_db_url(raw_url: str, database: int) -> str:
    parts = urlsplit(raw_url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{database}", parts.query, ""))


def native_dispatch_key(tenant_id: str, occurrence_id: str) -> str:
    digest = hashlib.sha256((tenant_id + "\0" + occurrence_id).encode()).hexdigest()
    return "kokoro:scheduler:dispatch:" + digest


class OwnedResources:
    """Own only two random databases, one harness prefix and registered native keys."""

    def __init__(
        self,
        postgres_admin_url: str,
        redis_url: str,
        run_id: str,
        *,
        command: Command = command_output,
    ) -> None:
        postgres = urlsplit(postgres_admin_url)
        redis = urlsplit(redis_url)
        if postgres.scheme not in {"postgres", "postgresql"} or redis.scheme not in {
            "redis",
            "rediss",
        }:
            raise SmokeError("Explicit PostgreSQL and Redis endpoints required")
        if redis.path != "/7":
            raise SmokeError("Scheduler Redis endpoint must select DB 7")
        if re.fullmatch(r"[a-f0-9]{24}", run_id) is None:
            raise SmokeError("Invalid smoke run identity")
        self.postgres_admin_url = postgres_admin_url
        self.scheduler_redis_url = redis_url
        self.bff_redis_url = _redis_db_url(redis_url, 8)
        self.run_id = run_id
        self.redis_prefix = f"kokoro:w0b:scheduler:{run_id}:"
        self.command = command
        self.created_databases: list[str] = []
        self.database_names: list[str] = []
        self.database_reconciliation: set[str] = set()
        self.preexisting_databases: set[str] = set()
        self.harness_claimed = False
        self.harness_was_claimed = False
        self.harness_reconciliation = False
        self.harness_preexisting = False
        self.native_redis_keys: set[str] = set()

    def _run(self, command: list[str]) -> str:
        return self.command(command)

    def _database_exists(self, name: str) -> bool:
        found = self._run(
            [
                "psql",
                self.postgres_admin_url,
                "-X",
                "-v",
                "ON_ERROR_STOP=1",
                "-Atc",
                "SELECT datname FROM pg_database WHERE datname = " + _sql_literal(name),
            ]
        ).strip()
        if found not in {"", name}:
            raise SmokeError("PostgreSQL inventory returned an unexpected identity")
        return found == name

    def create_database(self, owner: str) -> str:
        if owner not in {"scheduler", "bff"}:
            raise SmokeError("Invalid smoke database owner")
        name = f"w0b_sched_{self.run_id}_{owner}"
        if name in self.database_names:
            raise SmokeError("Database already requested by this run")
        self.database_names.append(name)
        if self._database_exists(name):
            self.preexisting_databases.add(name)
            raise SmokeError("Smoke database already exists")
        try:
            self._run(
                [
                    "psql",
                    self.postgres_admin_url,
                    "-X",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-Atc",
                    f'CREATE DATABASE "{name}"',
                ]
            )
        except BaseException:
            try:
                if self._database_exists(name):
                    self.created_databases.append(name)
            except (SmokeError, subprocess.SubprocessError, OSError):
                self.database_reconciliation.add(name)
            raise
        self.created_databases.append(name)
        return _database_url(self.postgres_admin_url, name)

    def claim_harness_prefix(self) -> None:
        key = self.redis_prefix + "ownership"
        if self._harness_keys():
            self.harness_preexisting = True
            raise SmokeError("Owned Redis prefix already exists")
        if self._harness_owner():
            self.harness_preexisting = True
            raise SmokeError("Owned Redis prefix already exists")
        try:
            result = self._run(
                [
                    "redis-cli",
                    "-e",
                    "-u",
                    self.scheduler_redis_url,
                    "SET",
                    key,
                    self.run_id,
                    "NX",
                    "EX",
                    "600",
                ]
            ).strip()
        except BaseException:
            try:
                owner = self._harness_owner()
                if owner == self.run_id:
                    self.harness_claimed = self.harness_was_claimed = True
                elif owner:
                    self.harness_preexisting = True
            except (SmokeError, subprocess.SubprocessError, OSError):
                self.harness_reconciliation = True
            raise
        if result != "OK":
            raise SmokeError("Owned Redis prefix could not be claimed")
        self.harness_claimed = self.harness_was_claimed = True

    def _harness_owner(self) -> str:
        return self._run(
            [
                "redis-cli",
                "-e",
                "-u",
                self.scheduler_redis_url,
                "GET",
                self.redis_prefix + "ownership",
            ]
        ).strip()

    def _harness_keys(self) -> list[str]:
        keys = self._run(
            [
                "redis-cli",
                "-e",
                "-u",
                self.scheduler_redis_url,
                "--scan",
                "--pattern",
                self.redis_prefix + "*",
            ]
        ).splitlines()
        if any(not key.startswith(self.redis_prefix) for key in keys):
            raise SmokeError("Redis scan returned a key outside this run")
        return keys

    def register_native_keys(self, scheduler_database_url: str, tenant_id: str) -> None:
        query = (
            "SELECT occurrence_id::text FROM scheduler_dispatch_outbox WHERE tenant_id = "
            + _sql_literal(tenant_id)
            + " ORDER BY occurrence_id"
        )
        rows = self._run(
            [
                "psql",
                scheduler_database_url,
                "-X",
                "-v",
                "ON_ERROR_STOP=1",
                "-Atc",
                query,
            ]
        ).splitlines()
        for occurrence_id in rows:
            if re.fullmatch(r"[0-9a-f-]{36}", occurrence_id) is None:
                raise SmokeError("Private Scheduler occurrence identity was invalid")
            self.native_redis_keys.add(native_dispatch_key(tenant_id, occurrence_id))

    def cleanup(self) -> None:
        failures: list[str] = []
        for name in self.database_reconciliation.copy():
            try:
                if self._database_exists(name):
                    self.created_databases.append(name)
                self.database_reconciliation.remove(name)
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("owned PostgreSQL reconciliation failed")
        if self.harness_reconciliation:
            try:
                owner = self._harness_owner()
                if owner == self.run_id:
                    self.harness_claimed = self.harness_was_claimed = True
                elif owner:
                    self.harness_preexisting = True
                self.harness_reconciliation = False
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("owned Redis reconciliation failed")
        if self.harness_claimed:
            try:
                owner = self._harness_owner()
                if owner == self.run_id:
                    keys = self._harness_keys()
                    if keys:
                        self._run(
                            [
                                "redis-cli",
                                "-e",
                                "-u",
                                self.scheduler_redis_url,
                                "UNLINK",
                                *keys,
                            ]
                        )
                    self.harness_claimed = False
                elif not owner:
                    self.harness_claimed = False
                else:
                    failures.append("owned harness Redis ownership changed")
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("owned harness Redis cleanup failed")
        if self.native_redis_keys:
            try:
                self._run(
                    [
                        "redis-cli",
                        "-e",
                        "-u",
                        self.scheduler_redis_url,
                        "UNLINK",
                        *sorted(self.native_redis_keys),
                    ]
                )
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("registered native Redis cleanup failed")
        for name in reversed(self.created_databases.copy()):
            try:
                self._run(
                    [
                        "psql",
                        self.postgres_admin_url,
                        "-X",
                        "-v",
                        "ON_ERROR_STOP=1",
                        "-Atc",
                        f'DROP DATABASE "{name}" WITH (FORCE)',
                    ]
                )
                self.created_databases.remove(name)
            except (SmokeError, subprocess.SubprocessError, OSError):
                failures.append("owned PostgreSQL cleanup failed")
        if failures:
            raise SmokeError("; ".join(failures))

    def verify_clean(self) -> None:
        if self.database_reconciliation:
            raise SmokeError("Owned PostgreSQL reconciliation was incomplete")
        if self.harness_reconciliation:
            raise SmokeError("Owned Redis reconciliation was incomplete")
        if self.created_databases:
            raise SmokeError("Owned PostgreSQL cleanup was incomplete")
        if self.harness_was_claimed and self._harness_keys():
            raise SmokeError("Owned harness Redis cleanup was incomplete")
        if self.native_redis_keys:
            exists = self._run(
                [
                    "redis-cli",
                    "-e",
                    "-u",
                    self.scheduler_redis_url,
                    "EXISTS",
                    *sorted(self.native_redis_keys),
                ]
            ).strip()
            if exists != "0":
                raise SmokeError("Registered native Redis cleanup was incomplete")
        for name in self.database_names:
            if name not in self.preexisting_databases and self._database_exists(name):
                raise SmokeError("Owned PostgreSQL cleanup was incomplete")

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path
from typing import TypeAlias

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.slice_a.guardian import identity_matches
from scripts.slice_a.native import (
    BACKEND_PROCESSES,
    _grpc_health_probe,
    _http2_probe,
    _http_probe,
    _redis_probe,
)


JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)


def assert_ready_inventory(state: dict[str, JsonValue]) -> None:
    public, processes = state.get("public"), state.get("processes")
    if not isinstance(public, dict) or public.get("status") != "ready":
        raise RuntimeError("native Slice A is not ready")
    if not isinstance(processes, dict) or set(processes) != BACKEND_PROCESSES:
        raise RuntimeError("native Slice A process inventory mismatch")


def _tcp(port: int) -> None:
    with socket.create_connection(("127.0.0.1", port), timeout=1):
        pass


def _probe(name: str, record: dict[str, JsonValue]) -> None:
    pid, identity, port, readiness = (
        record.get("pid"),
        record.get("start_identity"),
        record.get("port"),
        record.get("readiness"),
    )
    if (
        not isinstance(pid, int)
        or not isinstance(identity, str)
        or not identity_matches(pid, identity)
    ):
        raise RuntimeError(f"owned process identity mismatch: {name}")
    if not isinstance(port, int) or not isinstance(readiness, str):
        raise RuntimeError(f"invalid process record: {name}")
    if name == "redis":
        _redis_probe(port)
    elif name == "model-fixture" or name == "litellm":
        _http_probe(readiness)
    elif name in {"iam", "model", "capability", "chat"}:
        _http2_probe(readiness)
    elif name == "agent":
        _grpc_health_probe(port, "kokoro.agent.v1.AgentRuntimeService")
    else:
        _tcp(port)


def wait_ready(state_dir: Path, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error = "runtime state is absent"
    while time.monotonic() < deadline:
        try:
            raw = json.loads((state_dir / "runtime.json").read_text())
            if not isinstance(raw, dict):
                raise RuntimeError("invalid runtime state")
            assert_ready_inventory(raw)
            processes = raw["processes"]
            assert isinstance(processes, dict)
            for name, value in processes.items():
                if not isinstance(value, dict):
                    raise RuntimeError(f"invalid process record: {name}")
                _probe(name, value)
            return
        except (OSError, RuntimeError, json.JSONDecodeError) as error:
            last_error = str(error)
            time.sleep(0.2)
    raise RuntimeError(f"native Slice A readiness timed out: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe the native Slice A runtime")
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    wait_ready(args.state_dir.absolute(), args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

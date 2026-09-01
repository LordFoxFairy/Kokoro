from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
import re
import signal
import socket
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProcessFacts:
    pid: int
    pgid: int
    session_id: int
    state: str
    started: str


EXPECTED_PORT_NAMES = frozenset(
    {
        "postgres",
        "redis",
        "model-fixture",
        "litellm",
        "iam",
        "model",
        "capability",
        "agent",
        "chat",
    }
)
IDENTITY_PATTERN = re.compile(r"[0-9a-f]{64}")


def _darwin_process_facts(pid: int) -> ProcessFacts | None:
    class ProcBsdInfo(ctypes.Structure):
        _fields_ = [
            ("pbi_flags", ctypes.c_uint32),
            ("pbi_status", ctypes.c_uint32),
            ("pbi_xstatus", ctypes.c_uint32),
            ("pbi_pid", ctypes.c_uint32),
            ("pbi_ppid", ctypes.c_uint32),
            ("pbi_uid", ctypes.c_uint32),
            ("pbi_gid", ctypes.c_uint32),
            ("pbi_ruid", ctypes.c_uint32),
            ("pbi_rgid", ctypes.c_uint32),
            ("pbi_svuid", ctypes.c_uint32),
            ("pbi_svgid", ctypes.c_uint32),
            ("pbi_rfu_1", ctypes.c_uint32),
            ("pbi_comm", ctypes.c_char * 16),
            ("pbi_name", ctypes.c_char * 32),
            ("pbi_nfiles", ctypes.c_uint32),
            ("pbi_pgid", ctypes.c_uint32),
            ("pbi_pjobc", ctypes.c_uint32),
            ("e_tdev", ctypes.c_uint32),
            ("e_tpgid", ctypes.c_uint32),
            ("pbi_nice", ctypes.c_int32),
            ("pbi_start_tvsec", ctypes.c_uint64),
            ("pbi_start_tvusec", ctypes.c_uint64),
        ]

    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    proc_pidinfo = library.proc_pidinfo
    proc_pidinfo.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint64,
        ctypes.c_void_p,
        ctypes.c_int,
    ]
    proc_pidinfo.restype = ctypes.c_int
    info = ProcBsdInfo()
    size = ctypes.sizeof(info)
    result = proc_pidinfo(pid, 3, 0, ctypes.byref(info), size)
    if result == 0:
        error = ctypes.get_errno()
        if error in (0, 3):
            return None
        raise RuntimeError(f"cannot read high-precision process facts for pid {pid}")
    if result != size or info.pbi_pid != pid:
        raise RuntimeError(f"incomplete high-precision process facts for pid {pid}")
    try:
        session_id = os.getsid(pid)
    except ProcessLookupError:
        return None
    return ProcessFacts(
        pid=pid,
        pgid=int(info.pbi_pgid),
        session_id=session_id,
        state="zombie" if info.pbi_status == 5 else "live",
        started=f"{info.pbi_start_tvsec}.{info.pbi_start_tvusec:06d}",
    )


def _linux_process_facts(pid: int) -> ProcessFacts | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise RuntimeError(
            f"cannot read high-precision process facts for pid {pid}"
        ) from error
    closing = raw.rfind(")")
    fields = raw[closing + 2 :].split() if closing >= 0 else []
    if len(fields) < 20:
        raise RuntimeError(f"incomplete process facts for pid {pid}")
    return ProcessFacts(
        pid=pid,
        state="zombie" if fields[0] == "Z" else "live",
        pgid=int(fields[2]),
        session_id=int(fields[3]),
        started=fields[19],
    )


def _process_facts(pid: int) -> ProcessFacts | None:
    if sys.platform == "darwin":
        return _darwin_process_facts(pid)
    if sys.platform.startswith("linux"):
        return _linux_process_facts(pid)
    raise RuntimeError(
        f"high-precision process identity is unsupported on {sys.platform}"
    )


def _identity(facts: ProcessFacts) -> str:
    return hashlib.sha256(
        f"v2:{facts.pid}:{facts.pgid}:{facts.session_id}:{facts.started}".encode()
    ).hexdigest()


def process_identity(pid: int) -> str:
    facts = _process_facts(pid)
    if facts is None:
        raise ProcessLookupError(pid)
    return _identity(facts)


def identity_matches(pid: int, expected: str) -> bool:
    facts = _process_facts(pid)
    return (
        facts is not None and facts.state != "zombie" and _identity(facts) == expected
    )


def _darwin_group_facts(pgid: int) -> tuple[ProcessFacts, ...]:
    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    proc_listpids = library.proc_listpids
    proc_listpids.argtypes = [
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_int,
    ]
    proc_listpids.restype = ctypes.c_int
    required = proc_listpids(2, pgid, None, 0)
    if required <= 0:
        raise RuntimeError(f"cannot enumerate owned process group {pgid}")
    capacity = required // ctypes.sizeof(ctypes.c_int) + 32
    pids = (ctypes.c_int * capacity)()
    written = proc_listpids(2, pgid, pids, ctypes.sizeof(pids))
    if written < 0:
        raise RuntimeError(f"cannot enumerate owned process group {pgid}")
    facts: list[ProcessFacts] = []
    for pid in pids[: written // ctypes.sizeof(ctypes.c_int)]:
        if pid <= 0:
            continue
        current = _darwin_process_facts(pid)
        if current is not None and current.pgid == pgid:
            facts.append(current)
    return tuple(facts)


def _linux_group_facts(pgid: int) -> tuple[ProcessFacts, ...]:
    facts: list[ProcessFacts] = []
    try:
        entries = tuple(Path("/proc").iterdir())
    except OSError as error:
        raise RuntimeError(f"cannot enumerate owned process group {pgid}") from error
    for entry in entries:
        if not entry.name.isdecimal():
            continue
        current = _linux_process_facts(int(entry.name))
        if current is not None and current.pgid == pgid:
            facts.append(current)
    return tuple(facts)


def _group_facts(pgid: int) -> tuple[ProcessFacts, ...]:
    if sys.platform == "darwin":
        return _darwin_group_facts(pgid)
    if sys.platform.startswith("linux"):
        return _linux_group_facts(pgid)
    raise RuntimeError(f"process-group enumeration is unsupported on {sys.platform}")


def group_alive(pgid: int) -> bool:
    return any(facts.state != "zombie" for facts in _group_facts(pgid))


def stop_owned_group(
    *, pid: int, pgid: int, session_id: int, identity: str, timeout: float = 8.0
) -> None:
    if pid <= 1 or pgid != pid or session_id != pid:
        raise RuntimeError("owned process record is not a dedicated session/group")
    facts = _process_facts(pid)
    if facts is not None and (
        _identity(facts) != identity
        or facts.pgid != pgid
        or facts.session_id != session_id
    ):
        raise RuntimeError(f"owned process identity mismatch for pid {pid}")
    members = _group_facts(pgid)
    if any(member.session_id != session_id for member in members):
        raise RuntimeError(f"owned process session mismatch for group {pgid}")
    if not group_alive(pgid):
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + timeout
    while group_alive(pgid) and time.monotonic() < deadline:
        time.sleep(0.05)
    if group_alive(pgid):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + 5
        while group_alive(pgid) and time.monotonic() < deadline:
            time.sleep(0.05)
    if group_alive(pgid):
        raise RuntimeError(f"owned process group survived cleanup: {pgid}")


def _port_is_free(port: int) -> bool:
    if not 1 <= port <= 65535:
        raise RuntimeError(f"invalid owned port: {port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as error:
            if error.errno == errno.EADDRINUSE:
                return False
            raise RuntimeError("cannot verify owned port") from None
        return True


def _safe_process_record(record: object) -> dict[str, int | str] | None:
    if not isinstance(record, dict):
        return None
    try:
        pid = record["pid"]
        pgid = record["pgid"]
        session_id = record["session_id"]
        identity = record["start_identity"]
        port = record["port"]
    except KeyError:
        return None
    if (
        type(pid) is not int
        or type(pgid) is not int
        or type(session_id) is not int
        or type(port) is not int
        or not isinstance(identity, str)
        or IDENTITY_PATTERN.fullmatch(identity) is None
    ):
        return None
    return {
        "pid": pid,
        "pgid": pgid,
        "session_id": session_id,
        "start_identity": identity,
        "port": port,
    }


def reap_orphans(
    state_dir: Path, *, supervisor_pid: int, supervisor_identity: str
) -> None:
    if identity_matches(supervisor_pid, supervisor_identity):
        return
    state_path = state_dir / "runtime.json"
    if not state_path.is_file() or state_path.is_symlink():
        raise RuntimeError("invalid owned runtime state path")
    raw = json.loads(state_path.read_text())
    if not isinstance(raw, dict):
        raise RuntimeError("invalid owned runtime state document")
    processes, public = raw.get("processes"), raw.get("public")
    if not isinstance(public, dict):
        raise RuntimeError("invalid owned runtime state public facts")
    errors: list[str] = []

    def record_error(scope: str, error: BaseException) -> None:
        # Guardian state is a public artifact. Preserve only structural context;
        # exception messages may contain tokens or command output.
        errors.append(f"{scope}: {type(error).__name__}")

    try:
        if not isinstance(processes, dict):
            raw["processes"] = {}
            record_error(
                "processes.inventory",
                RuntimeError("invalid owned runtime state process inventory"),
            )
            processes = {}
        ports = public.get("ports")
        valid_records: list[tuple[int, int]] = []
        safe_processes: dict[str, dict[str, int | str]] = {}
        indexed_records = tuple(enumerate(processes.items()))
        structurally_safe: list[tuple[int, object, dict[str, int | str]]] = []
        for index, (name, record) in indexed_records:
            safe_record = _safe_process_record(record)
            if safe_record is None:
                record_error(f"process[{index}].shape", RuntimeError("invalid record"))
                continue
            structurally_safe.append((index, name, safe_record))
            if isinstance(name, str) and name in EXPECTED_PORT_NAMES:
                safe_processes[name] = safe_record
        raw["processes"] = safe_processes
        for index, _name, safe_record in reversed(structurally_safe):
            try:
                pid = int(safe_record["pid"])
                pgid = int(safe_record["pgid"])
                stop_owned_group(
                    pid=pid,
                    pgid=pgid,
                    session_id=int(safe_record["session_id"]),
                    identity=str(safe_record["start_identity"]),
                )
                valid_records.append((index, pgid))
            except BaseException as error:
                record_error(f"process[{index}]", error)
                valid_records.append((index, int(safe_record["pgid"])))
        for index, name, safe_record in structurally_safe:
            if (
                not isinstance(name, str)
                or name not in EXPECTED_PORT_NAMES
                or not isinstance(ports, dict)
                or ports.get(name) != safe_record["port"]
            ):
                record_error(
                    f"process[{index}].port-parity",
                    RuntimeError("owned process port parity mismatch"),
                )
        for index, pgid in valid_records:
            try:
                if group_alive(pgid):
                    raise RuntimeError("owned process group survived cleanup")
            except BaseException as error:
                record_error(f"process[{index}].group-proof", error)
        if not isinstance(ports, dict):
            record_error("ports.inventory", RuntimeError("invalid port inventory"))
            public["ports"] = {}
        else:
            safe_ports = {
                name: port
                for name, port in ports.items()
                if name in EXPECTED_PORT_NAMES and type(port) is int
            }
            public["ports"] = safe_ports
            if set(ports) != EXPECTED_PORT_NAMES or len(
                set(safe_ports.values())
            ) != len(EXPECTED_PORT_NAMES):
                record_error("ports.inventory", RuntimeError("invalid port inventory"))
            for index, (name, port) in enumerate(ports.items()):
                try:
                    if (
                        not isinstance(name, str)
                        or name not in EXPECTED_PORT_NAMES
                        or type(port) is not int
                    ):
                        raise RuntimeError("invalid owned port record")
                    if not _port_is_free(port):
                        raise RuntimeError("owned port survived cleanup")
                except BaseException as error:
                    record_error(f"port[{index}]", error)
        if errors:
            raise RuntimeError("guardian cleanup failed")
        public["status"] = "guardian_stopped"
    except BaseException as error:
        public["status"] = "guardian_failed"
        if not errors:
            record_error("guardian", error)
        public["guardian_errors"] = errors
        raise RuntimeError("guardian cleanup failed") from None
    finally:
        public["guardian_at_unix_ms"] = int(time.time() * 1000)
        temporary = state_path.with_suffix(".json.guardian.tmp")
        temporary.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, state_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Crash guardian for native Slice A")
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--supervisor-pid", required=True, type=int)
    parser.add_argument("--supervisor-identity", required=True)
    args = parser.parse_args()
    while sys.stdin.buffer.read(4096):
        pass
    reap_orphans(
        args.state_dir,
        supervisor_pid=args.supervisor_pid,
        supervisor_identity=args.supervisor_identity,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

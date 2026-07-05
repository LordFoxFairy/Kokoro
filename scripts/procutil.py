"""验证脚本共享进程管理：进程组级 spawn/停止 + 端口预检，杜绝 tsx/worker 僵尸泄漏。"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import time
from pathlib import Path


def ensure_port_free(port: int) -> None:
    """端口被占即 fail-loud：僵尸残留会让脚本测到旧进程，假绿比失败更糟。"""
    with socket.socket() as s:
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            raise SystemExit(
                f"port {port} already in use — stale process from a previous run? "
                f"kill it first (lsof -ti:{port} | xargs kill)"
            )


def spawn(cmd: list[str], *, cwd: Path, env: dict[str, str], log: Path) -> subprocess.Popen:
    """新会话（进程组长）启动：npm/uv 的子进程随组一起可杀。"""
    return subprocess.Popen(
        cmd, cwd=cwd, env=env,
        stdout=log.open("w"), stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def stop(proc: subprocess.Popen, sig: int = signal.SIGTERM, timeout: float = 10.0) -> None:
    """杀整个进程组（npm 包装层 + tsx/worker 子进程），SIGTERM 超时升级 SIGKILL。"""
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), sig)
    except (ProcessLookupError, PermissionError):
        return
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.2)
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    proc.wait(timeout=5)

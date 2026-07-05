#!/usr/bin/env python3
"""一键全量验证：按前置条件可用性依次跑四套验证，汇总一张表。

deterministic（LocalFake，只要 redis+mongo）：e2e-v21-gate / chaos-verify / trace-verify*
real-model（要 kokoro-agent/.env 真凭据，走钱）：--real 才跑 real-model-verify。
*trace-verify 需自托管 langfuse（:3310）可达，否则 SKIP。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def reachable(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def run(script: str, env: dict[str, str] | None = None) -> str:
    import os

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        env=None if env is None else {**os.environ, **env},
    )
    return "PASS" if proc.returncode == 0 else "FAIL"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="附带真模型五场景（走钱）")
    args = parser.parse_args()

    results: dict[str, str] = {}
    results["e2e-v21-gate"] = run("e2e-v21-gate.py")
    # S3 workspace 档（ADR-009）：同一 gate、minio 底座；独立端口/redis db 防串扰。
    results["e2e-v21-gate(s3)"] = (
        run("e2e-v21-gate.py", env={
            "E2E_WORKSPACE_BACKEND": "s3",
            "E2E_SESSION_PORT": "3907",
            "E2E_REDIS_URL": "redis://127.0.0.1:6379/12",
        })
        if reachable("http://127.0.0.1:9100/minio/health/live")
        else "SKIP (minio :9100 不可达，启动见 docs/test-cases.md L2 前置)"
    )
    results["chaos-verify"] = run("chaos-verify.py")
    results["trace-verify"] = (
        run("trace-verify.py")
        if reachable("http://127.0.0.1:3310/api/public/health")
        else "SKIP (langfuse :3310 不可达，见 ops/README.md)"
    )
    if args.real:
        results["real-model-verify"] = run("real-model-verify.py")

    print("\n==== verify-all 汇总 ====")
    for name, status in results.items():
        print(f"  {name:20s} {status}")
    return 1 if any(status == "FAIL" for status in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())

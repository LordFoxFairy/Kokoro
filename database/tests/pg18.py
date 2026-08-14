from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/database/run_in_fresh_pg18.py"


def apply_sql(database_url: str, sql: bytes) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(sql.decode("utf-8"))


def segment_prefix(*segments: str) -> bytes:
    chunks: list[bytes] = []
    for segment in segments:
        path = ROOT / "database/schema" / f"{segment}.sql"
        if path.exists():
            chunks.append(path.read_bytes().replace(b"\r\n", b"\n").rstrip(b"\n"))
    return b"\n\n".join(chunks) + b"\n"


def run_pg18_case(case_file: Path, case: str) -> None:
    prefix = segment_prefix("00-foundation")
    with tempfile.TemporaryDirectory(prefix=f"kokoro-{case}-") as directory:
        baseline = Path(directory) / "site-iam-prefix.sql"
        baseline.write_bytes(prefix)
        result = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--label",
                f"site-iam-{case}",
                "--cwd",
                str(ROOT),
                "--baseline",
                str(baseline),
                "--",
                sys.executable,
                str(case_file),
                "--case",
                case,
            ],
            cwd=ROOT,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            timeout=90,
        )
    assert result.returncode == 0, result.stderr

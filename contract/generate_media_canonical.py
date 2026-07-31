#!/usr/bin/env python3
"""Thin launcher for the descriptor-backed canonical runtime generator."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    generator = Path(__file__).with_name("generate-media-canonical.mjs")
    command = ["node", str(generator), "--language", "python", *sys.argv[1:]]
    completed = subprocess.run(command, check=False)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()

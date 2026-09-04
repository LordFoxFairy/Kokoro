"""Extract executable handbook examples without copying their source of truth.

Run: python3 -m scripts.governance.handbook_examples --output /tmp/new-directory
This only writes to a new empty output directory; it does not install or run tools.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STANDARDS = ROOT / "docs/kokoro-handbook/standards"


def code_blocks(text: str, language: str) -> list[str]:
    return re.findall(rf"^```{language}\n(.*?)^```", text, re.MULTILINE | re.DOTALL)


def extract_examples(output: Path) -> tuple[Path, ...]:
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("example output directory must be empty")
    written: list[Path] = []

    def write(relative: str, content: str) -> None:
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(path)

    ts = (STANDARDS / "08-typescript-backend-engineering.md").read_text()
    for block in code_blocks(ts, "ts"):
        first = block.splitlines()[0]
        if re.fullmatch(r"// src/[a-z/-]+(?:\.[a-z]+)*\.ts", first):
            write("typescript/" + first[3:], block)
        elif "export function loadConfig" in block:
            write("typescript/src/config/env.ts", block)
    for block in code_blocks(ts, "json"):
        config = json.loads(block)
        if "compilerOptions" in config:
            config["include"] = ["src/**/*.ts"]
            config["compilerOptions"].update({"rootDir": "src", "outDir": "dist"})
            write("typescript/tsconfig.json", json.dumps(config, indent=2))
    write(
        "typescript/package.json",
        json.dumps({"private": True, "type": "module"}, indent=2),
    )
    py = (STANDARDS / "09-python-backend-engineering.md").read_text()
    destinations = {
        "class RunRow(": "runs/rows.py",
        "class CreateRunRequest(": "runs/schemas.py",
        "class Run:": "runs/models.py",
        "class RunRecords(": "runs/service.py",
        "class Settings(": "settings.py",
    }
    for block in code_blocks(py, "python"):
        for marker, relative in destinations.items():
            if marker in block:
                write("python/src/kokoro_agent/" + relative, block)
                break
    for relative in ("__init__.py", "runs/__init__.py"):
        write("python/src/kokoro_agent/" + relative, "")
    config = code_blocks(py, "toml")[0]
    write("python/pyproject.toml", config)
    sql = (STANDARDS / "03-sql-and-postgresql.md").read_text()
    write("schema.sql", code_blocks(sql, "sql")[0])
    return tuple(written)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    for path in extract_examples(args.output.resolve()):
        print(path)


if __name__ == "__main__":
    main()

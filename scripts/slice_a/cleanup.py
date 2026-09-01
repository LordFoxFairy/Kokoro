from __future__ import annotations

import argparse
import shutil
from pathlib import Path


MARKERS = {
    "kokoro-slice-a:secrets:v1\n",
    "kokoro-slice-a:fixtures:v1\n",
    "kokoro-slice-a:state:v1\n",
}


def remove_marked_directory(target: Path) -> None:
    if not str(target) or target == Path("/"):
        raise RuntimeError("refusing unsafe cleanup path")
    target = target.absolute()
    if target == Path("/") or target.is_symlink() or not target.is_dir():
        raise RuntimeError("cleanup target must be a real marked directory")
    marker = target / ".kokoro-slice-a-owner"
    if marker.is_symlink() or not marker.is_file() or marker.read_text() not in MARKERS:
        raise RuntimeError("cleanup target is not owned by Slice A")
    shutil.rmtree(target)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove one Root-owned Slice A directory"
    )
    parser.add_argument("--dir", required=True, type=Path)
    args = parser.parse_args()
    remove_marked_directory(args.dir)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import os
import stat
from pathlib import Path


MARKER = ".kokoro-slice-a-owner"
MARKER_CONTENT = "kokoro-slice-a:fixtures:v1\n"


def create_fixture_directory(target: Path) -> None:
    target = target.absolute()
    if target.exists() or target.is_symlink():
        raise RuntimeError("fixture directory must not already exist")
    target.mkdir(mode=0o700, parents=False)
    os.chmod(target, 0o700)
    try:
        marker = target / MARKER
        descriptor = os.open(
            marker,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            os.write(descriptor, MARKER_CONTENT.encode())
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        magic_links = target / "magic-links"
        magic_links.mkdir(mode=0o700)
        os.chmod(magic_links, 0o700)
    except BaseException:
        for child in target.iterdir():
            if child.is_dir():
                child.rmdir()
            else:
                child.unlink(missing_ok=True)
        target.rmdir()
        raise


def validate_fixture_directory(target: Path, *, require_empty: bool) -> None:
    target = target.absolute()
    metadata = os.lstat(target)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise RuntimeError("fixture directory must be a real mode-0700 directory")
    marker = target / MARKER
    if marker.is_symlink() or marker.read_text() != MARKER_CONTENT:
        raise RuntimeError("fixture directory marker mismatch")
    expected = {MARKER, "magic-links"}
    if {path.name for path in target.iterdir()} != expected:
        raise RuntimeError("fixture directory manifest mismatch")
    magic_links = target / "magic-links"
    item = os.lstat(magic_links)
    if not stat.S_ISDIR(item.st_mode) or stat.S_IMODE(item.st_mode) != 0o700:
        raise RuntimeError("magic-links must be a real mode-0700 directory")
    if require_empty and any(magic_links.iterdir()):
        raise RuntimeError("magic-links must be empty before native start")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the native Slice A fixture directory"
    )
    parser.add_argument("--dir", required=True, type=Path)
    args = parser.parse_args()
    create_fixture_directory(args.dir)


if __name__ == "__main__":
    main()

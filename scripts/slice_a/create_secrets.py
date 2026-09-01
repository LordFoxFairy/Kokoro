from __future__ import annotations

import argparse
import os
import secrets
import stat
import subprocess
from pathlib import Path


MARKER = ".kokoro-slice-a-owner"
MARKER_CONTENT = "kokoro-slice-a:secrets:v1\n"
SECRET_FILES = (
    "web.workload-token",
    "chat.workload-token",
    "agent.workload-token",
    "iam.refresh-derivation-key",
    "web.session-key",
    "litellm.api-key",
    "iam.jwt-private.pem",
    "iam.jwt-public.pem",
)
HEX_SECRET_FILES = SECRET_FILES[:6]


def _write_exclusive(path: Path, content: bytes, mode: int) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        mode,
    )
    try:
        written = 0
        while written < len(content):
            count = os.write(descriptor, content[written:])
            if count <= 0:
                raise RuntimeError(f"secret write made no progress: {path.name}")
            written += count
        os.fsync(descriptor)
        os.fchmod(descriptor, mode)
    finally:
        os.close(descriptor)


def create_secret_directory(target: Path) -> None:
    target = target.absolute()
    if target.exists() or target.is_symlink():
        raise RuntimeError("secret directory must not already exist")
    target.mkdir(mode=0o700, parents=False)
    os.chmod(target, 0o700)
    try:
        _write_exclusive(target / MARKER, MARKER_CONTENT.encode(), 0o600)
        for name in HEX_SECRET_FILES:
            _write_exclusive(target / name, secrets.token_hex(32).encode(), 0o600)

        private_path = target / "iam.jwt-private.pem"
        subprocess.run(
            [
                "openssl",
                "genpkey",
                "-algorithm",
                "RSA",
                "-pkeyopt",
                "rsa_keygen_bits:2048",
                "-out",
                str(private_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.chmod(private_path, 0o600)
        public = subprocess.run(
            ["openssl", "pkey", "-in", str(private_path), "-pubout"],
            check=True,
            capture_output=True,
        ).stdout
        _write_exclusive(target / "iam.jwt-public.pem", public, 0o644)
        descriptor = os.open(target, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except BaseException:
        for child in target.iterdir():
            child.unlink(missing_ok=True)
        target.rmdir()
        raise


def validate_secret_directory(target: Path) -> None:
    target = target.absolute()
    metadata = os.lstat(target)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise RuntimeError("secret directory must be a real mode-0700 directory")
    actual = {path.name for path in target.iterdir()}
    expected = set(SECRET_FILES) | {MARKER}
    if actual != expected:
        raise RuntimeError("secret directory manifest mismatch")
    if (target / MARKER).read_text() != MARKER_CONTENT:
        raise RuntimeError("secret directory marker mismatch")
    values: set[str] = set()
    for name in HEX_SECRET_FILES:
        path = target / name
        item = os.lstat(path)
        if not stat.S_ISREG(item.st_mode) or stat.S_IMODE(item.st_mode) != 0o600:
            raise RuntimeError(f"secret must be a regular mode-0600 file: {name}")
        value = path.read_text()
        if len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise RuntimeError(
                f"secret must be exactly 64 lowercase hexadecimal bytes: {name}"
            )
        if value in values:
            raise RuntimeError("secret files must be independently generated")
        values.add(value)
    private = target / "iam.jwt-private.pem"
    public = target / "iam.jwt-public.pem"
    for path, mode in ((private, 0o600), (public, 0o644)):
        item = os.lstat(path)
        if not stat.S_ISREG(item.st_mode) or stat.S_IMODE(item.st_mode) != mode:
            raise RuntimeError(f"JWT key mode mismatch: {path.name}")
    derived = subprocess.run(
        ["openssl", "pkey", "-in", str(private), "-pubout"],
        check=True,
        capture_output=True,
    ).stdout
    if derived != public.read_bytes():
        raise RuntimeError("JWT public key does not match private key")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the native Slice A secret manifest"
    )
    parser.add_argument("--dir", required=True, type=Path)
    args = parser.parse_args()
    create_secret_directory(args.dir)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


SITE_ID = "11111111-1111-4111-8111-111111111111"
DOMAIN_ID = "11111111-1111-4111-8111-111111111112"
SITE_HOST = "slice-a.localhost"


def build_site_contexts() -> dict[str, dict[str, str]]:
    return {
        SITE_HOST: {
            "site_id": SITE_ID,
            "brand_key": "kokoro",
            "locale": "en-US",
            "skin": "default",
        }
    }


def select_site_context(
    host: str, contexts: dict[str, dict[str, str]]
) -> dict[str, str]:
    normalized = host.strip().lower().rstrip(".")
    selected = contexts.get(normalized)
    if selected is None:
        raise RuntimeError(f"unknown Site Host: {normalized}")
    return dict(selected)


def build_model_manifest() -> dict[str, str | int]:
    return {
        "version": "slice-a-v1",
        "siteId": SITE_ID,
        "providerKey": "slice-a-fixture",
        "providerDisplayName": "Slice A Fixture",
        "modelKey": "slice-a-fixture",
        "modelDisplayName": "Slice A Fixture",
        "providerModelName": "slice-a-fixture",
        "revision": 1,
        "label": "default",
        "priority": 0,
    }


def write_seed_artifacts(fixture_directory: Path) -> tuple[Path, Path]:
    site_context_path = fixture_directory / "site-contexts.json"
    model_manifest_path = fixture_directory / "model-bootstrap.json"
    for path, value in (
        (site_context_path, build_site_contexts()),
        (model_manifest_path, build_model_manifest()),
    ):
        path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        os.chmod(path, 0o600)
    return site_context_path, model_manifest_path


def seed_site(admin_url: str) -> None:
    sql = f"""
    INSERT INTO kokoro.site_site(site_id,key,name,status,default_locale,timezone)
    VALUES ('{SITE_ID}','slice-a','Slice A','active','en-US','UTC');
    INSERT INTO kokoro.site_domain(
      domain_id,site_id,normalized_host,status,is_primary,verified_at
    ) VALUES (
      '{DOMAIN_ID}','{SITE_ID}','{SITE_HOST}','active',true,now()
    );
    """
    subprocess.run(
        ["psql", admin_url, "-v", "ON_ERROR_STOP=1", "-c", sql],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def bootstrap_model(
    model_root: Path, app_url: str, manifest_path: Path
) -> dict[str, str | bool]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "DATABASE_URL_KOKORO_APP": app_url,
    }
    command = ["pnpm", "bootstrap:model", "--manifest", str(manifest_path)]
    first = subprocess.run(
        command,
        cwd=model_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    replay = subprocess.run(
        command,
        cwd=model_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    if first.stdout != replay.stdout:
        raise RuntimeError("Model bootstrap exact replay changed its result")
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, dict):
        raise RuntimeError("Model bootstrap manifest must be an object")
    drift = dict(manifest)
    drift["providerDisplayName"] = f"{drift.get('providerDisplayName', '')} drift"
    descriptor, drift_name = tempfile.mkstemp(
        prefix="model-drift-", suffix=".json", dir=manifest_path.parent
    )
    drift_path = Path(drift_name)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(
                json.dumps(drift, sort_keys=True, separators=(",", ":")) + "\n"
            )
        os.chmod(drift_path, 0o600)
        rejected = subprocess.run(
            ["pnpm", "bootstrap:model", "--manifest", str(drift_path)],
            cwd=model_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if rejected.returncode == 0 or "MODEL_BOOTSTRAP_DRIFT" not in (
            rejected.stdout + rejected.stderr
        ):
            raise RuntimeError("Model bootstrap manifest drift was not rejected")
    finally:
        drift_path.unlink(missing_ok=True)
    return {
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "result_sha256": hashlib.sha256(first.stdout.encode()).hexdigest(),
        "exact_replay": True,
        "drift_rejected": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision Root-owned Slice A fixtures"
    )
    parser.add_argument("--admin-url", required=True)
    parser.add_argument("--app-url", required=True)
    parser.add_argument("--fixture-dir", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    args = parser.parse_args()
    _, model_manifest = write_seed_artifacts(args.fixture_dir)
    seed_site(args.admin_url)
    bootstrap_model(args.model, args.app_url, model_manifest)


if __name__ == "__main__":
    main()

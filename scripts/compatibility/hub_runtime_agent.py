"""Compatibility driver for Agent's public Hub execution-assembly client."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from kokoro_agent.contract import SkillGrant
from kokoro_agent.hub import (
    ExecutionAssemblyError,
    HubExecutionAssemblyClient,
    HubRuntimeSettings,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--rpc-url", required=True)
    parser.add_argument("--server-name", required=True)
    parser.add_argument("--ca", required=True)
    parser.add_argument("--cert", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--expect-rejected", action="store_true")
    return parser.parse_args()


def _fixture(path: str) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file() or source.stat().st_size > 16 * 1024:
        raise RuntimeError("hub_runtime_fixture_invalid")
    value: Any = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {
        "agentCatalogRef",
        "expectedBodySha256",
        "namespace",
        "projectionState",
        "skill",
    }:
        raise RuntimeError("hub_runtime_fixture_invalid")
    if value["projectionState"] != "committed" or not isinstance(value["skill"], dict):
        raise RuntimeError("hub_runtime_fixture_invalid")
    return value


async def _run(args: argparse.Namespace) -> dict[str, object]:
    fixture = _fixture(args.fixture)
    skill = SkillGrant.model_validate(fixture["skill"])
    client = HubExecutionAssemblyClient(
        HubRuntimeSettings(
            rpc_url=args.rpc_url,
            server_name=args.server_name,
            ca_file=args.ca,
            cert_file=args.cert,
            key_file=args.key,
            artifact_cache_dir=args.cache,
            timeout_ms=5_000,
        )
    )
    if os.environ.get("KOKORO_COMPAT_DEBUG") == "1":
        inner = getattr(client, "_client")

        class DebugClient:
            async def resolve_execution_assembly(self, request: Any, **kwargs: Any) -> Any:
                try:
                    return await inner.resolve_execution_assembly(request, **kwargs)
                except Exception as error:
                    print(
                        f"agent_hub_connect_error:{type(error).__name__}:"
                        f"{getattr(error, 'code', 'unknown')}:{error}",
                        file=sys.stderr,
                    )
                    raise

            def fetch_skill_artifact(self, request: Any, **kwargs: Any) -> Any:
                return inner.fetch_skill_artifact(request, **kwargs)

        setattr(client, "_client", DebugClient())
    try:
        assembly = await client.resolve(
            fixture["namespace"],
            fixture["agentCatalogRef"],
            [skill],
            [],
        )
    except ExecutionAssemblyError:
        if args.expect_rejected:
            return {"schemaVersion": 1, "rejected": True}
        raise
    if args.expect_rejected:
        raise RuntimeError("hub_runtime_non_agent_not_rejected")
    body = await assembly.skills.read_body(skill.scope, skill.name, skill.content_hash)
    body_digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if body_digest != fixture["expectedBodySha256"]:
        raise RuntimeError("hub_runtime_skill_body_mismatch")
    return {
        "schemaVersion": 1,
        "resolvedSkills": 1,
        "fetchedArtifacts": 1,
        "bodySha256": body_digest,
        "assemblyDigest": assembly.assembly_digest,
    }


def main() -> None:
    print(json.dumps(asyncio.run(_run(_arguments())), separators=(",", ":")))


if __name__ == "__main__":
    main()

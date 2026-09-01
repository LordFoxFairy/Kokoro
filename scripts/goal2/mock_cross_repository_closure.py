"""Deterministic Goal 2 cross-repository contract fixture.

This is deliberately a contract/mock gate: it does not import application code
or connect to another repository's database. It verifies the Goal 2 root
contract registry, owner documents, and boundary markers before a BFF v1
deployment composition is attempted.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "contract/goal2-repository-contract-manifest.json"

REPOSITORIES = {
    "kokoro-iam": ROOT / "kokoro-iam",
    "kokoro-system": ROOT / "kokoro-system",
    "kokoro-model": ROOT / "kokoro-model",
    "kokoro-billing": ROOT / "kokoro-billing",
    "kokoro-capability": ROOT / "kokoro-capability",
    "kokoro-storage": ROOT / "kokoro-storage",
    "kokoro-scheduler": ROOT / "kokoro-scheduler",
}

REQUIRED_MARKERS = ("request_id", "Idempotency", "cursor")


class GateError(RuntimeError):
    """A deterministic fixture assertion that should produce a machine failure."""


def main() -> int:
    evidence: dict[str, object] = {"status": "PASS", "mode": "mock-fixture", "repositories": {}}
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if manifest.get("artifact") != "goal2-repository-contract-manifest":
            raise GateError("invalid Goal 2 contract manifest artifact")
        if set(manifest.get("repositories", {})) != set(REPOSITORIES):
            raise GateError("Goal 2 contract manifest repository set does not match the seven owners")

        for name, repository in REPOSITORIES.items():
            if not repository.is_dir():
                raise GateError(f"missing repository: {name}: {repository}")
            if repository.resolve().parent != ROOT.resolve():
                raise GateError(f"repository path is not a direct Root child: {name}: {repository}")
            entry = manifest["repositories"][name]
            expected_path = name
            if entry["path"] != expected_path:
                raise GateError(f"manifest path mismatch for {name}: {entry['path']}")
            documents = (
                entry["api_contract"],
                entry["technical_design"],
                entry["bff_integration"],
                entry["acceptance"],
                entry["risk_register"],
            )
            contents = []
            for relative in documents:
                path = repository / relative
                if not path.is_file():
                    raise GateError(f"missing owner document: {name}: {path}")
                contents.append(path.read_text(encoding="utf-8"))
            combined = "\n".join(contents)
            lowered = combined.lower()
            missing = []
            if "request_id" not in lowered:
                missing.append("request_id")
            if "idempotency" not in lowered and "command_id" not in lowered:
                missing.append("Idempotency/command_id")
            if "cursor" not in lowered and "no list" not in lowered:
                missing.append("cursor")
            if missing:
                raise GateError(f"missing contract markers for {name}: {', '.join(missing)}")
            root_wire = entry.get("root_wire", [])
            for relative in root_wire:
                if "*" in relative:
                    parent = ROOT / relative.split("*", 1)[0]
                    if not list(parent.parent.glob(parent.name + "*")):
                        raise GateError(f"missing root wire glob for {name}: {relative}")
                elif not (ROOT / relative).is_file():
                    raise GateError(f"missing root wire file for {name}: {relative}")
            evidence["repositories"][name] = {"docs": list(documents), "root_wire": root_wire, "contract_markers": list(REQUIRED_MARKERS)}  # type: ignore[index]

        flows = {
            "bff_to_owner": ["iam", "system", "model", "billing", "capability", "storage"],
            "capability_to_storage": ["opaque artifact_ref", "Storage API", "no database sharing"],
            "billing_to_scheduler": ["business task definition", "generic trigger", "receipt owned by Billing"],
            "scheduler_boundary": ["Go", "Redis coordination", "no Billing/Credit database access"],
        }
        evidence["flows"] = flows
    except (GateError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        evidence["status"] = "FAIL"
        evidence["errors"] = [str(exc)]
        print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
        return 1

    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

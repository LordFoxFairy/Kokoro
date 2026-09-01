from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from contract.validate_slice_a_manifest import load_manifest, validate


MANIFEST = load_manifest(ROOT / "contract/slice-a-contract-manifest.yaml")


def test_renderer_input_has_exact_slice_a_inventory() -> None:
    validate(MANIFEST)
    assert MANIFEST["authority"] == "machine"
    assert len(MANIFEST["protobuf"]["files"]) == 10
    assert len(MANIFEST["protobuf"]["services"]) == 15
    assert sum(len(service["methods"]) for service in MANIFEST["protobuf"]["services"]) == 54
    stream = next(
        method
        for service in MANIFEST["protobuf"]["services"]
        for method in service["methods"]
        if method["name"] == "StreamConversationEvents"
    )
    assert stream["serverStreaming"] is True
    assert len(MANIFEST["agentEvents"]["variants"]) == 20
    assert len(MANIFEST["http"]["operations"]) == 10
    assert len(MANIFEST["sse"]["browserEvents"]) == 21

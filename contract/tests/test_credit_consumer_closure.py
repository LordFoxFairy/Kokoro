from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_credit_contract_has_explicit_root_owned_consumer_closure() -> None:
    manifest = json.loads((ROOT / "credit-v1-consumers.json").read_text(encoding="utf-8"))
    assert manifest["owner"] == "kokoro-billing"
    assert manifest["consumers"]["kokoro-billing"]["protoFiles"] == [
        "kokoro/credit/v1/credit.proto"
    ]
    assert not any(".." in Path(path).parts for path in manifest["consumers"]["kokoro-billing"]["protoFiles"])

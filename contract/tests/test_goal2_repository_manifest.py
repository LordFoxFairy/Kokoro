import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_goal2_manifest_has_exact_owner_set_and_contract_surfaces() -> None:
    manifest = json.loads(
        (ROOT / "contract/goal2-repository-contract-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["artifact"] == "goal2-repository-contract-manifest"
    assert set(manifest["repositories"]) == {
        "kokoro-iam",
        "kokoro-system",
        "kokoro-model",
        "kokoro-billing",
        "kokoro-capability",
        "kokoro-storage",
        "kokoro-scheduler",
    }
    for entry in manifest["repositories"].values():
        for key in ("path", "api_contract", "technical_design", "bff_integration", "acceptance", "risk_register"):
            assert entry[key]
        assert "owner" in entry
        assert "root_wire" in entry


def test_goal2_manifest_declares_postgres_redis_and_object_store_rules() -> None:
    manifest = json.loads(
        (ROOT / "contract/goal2-repository-contract-manifest.json").read_text(encoding="utf-8")
    )
    rules = manifest["rules"]
    assert "PostgreSQL" in rules["database"]
    assert "Redis" in rules["database"]
    assert "S3-compatible" in rules["objectStore"]

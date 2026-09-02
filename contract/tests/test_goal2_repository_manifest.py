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


def test_goal2_cross_repository_contract_is_root_machine_readable() -> None:
    contract = json.loads(
        (ROOT / "contract/goal2-cross-repository-contract-v1.json").read_text(encoding="utf-8")
    )
    assert contract["artifact"] == "goal2-cross-repository-contract-v1"
    assert contract["version"] == 1
    assert set(contract["owner_contracts"]) == {
        "kokoro-iam",
        "kokoro-system",
        "kokoro-model",
        "kokoro-billing",
        "kokoro-capability",
        "kokoro-storage",
        "kokoro-agent",
        "kokoro-scheduler",
    }
    assert contract["bff_surface_ownership"]["/v1/projects"]["fact_owner"] == "kokoro-bff"
    assert "KOKORO_HUB_BASE_URL" in contract["forbidden_legacy_paths"]
    system = contract["owner_contracts"]["kokoro-system"]
    assert system["bff_http"]["path"] == "/v1/system/runtime-manifest"
    assert "product_id" in system["bff_http"]["success_data"]
    scheduler = contract["owner_contracts"]["kokoro-scheduler"]
    assert scheduler["dispatch_http"]["path"] == "/internal/bff/scheduled-tasks/dispatch"
    assert "Idempotency-Key" in scheduler["dispatch_http"]["required_headers"]
    billing = contract["owner_contracts"]["kokoro-billing"]
    assert billing["bff_service_auth"]["credential"] == "BILLING_OPERATOR_PROXY_SECRET"

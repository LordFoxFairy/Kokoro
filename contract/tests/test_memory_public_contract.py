"""Public Product Memory M0.1 contract owned by the Root repository."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_OPENAPI = ROOT / "contract/openapi/platform-public-v1.yaml"
BOUNDARY_REGISTRY = ROOT / "contract/registry/boundaries.yaml"

MEMORY_OPERATIONS = {
    "getMemorySettings": ("get", "/v1/memory/settings"),
    "updateMemorySettings": ("patch", "/v1/memory/settings"),
    "listMemoryEntries": ("get", "/v1/memory/entries"),
    "getMemoryEntry": ("get", "/v1/memory/entries/{entryRef}"),
    "listMemoryEntryHistory": (
        "get",
        "/v1/memory/entries/{entryRef}/history",
    ),
    "rememberMemoryEntry": ("post", "/v1/memory/entries"),
    "correctMemoryEntry": ("post", "/v1/memory/entries/{entryRef}:correct"),
    "restoreMemoryEntryRevision": (
        "post",
        "/v1/memory/entries/{entryRef}/history/{revisionRef}:restore",
    ),
    "prioritizeMemoryEntry": (
        "post",
        "/v1/memory/entries/{entryRef}:prioritize",
    ),
    "deprioritizeMemoryEntry": (
        "post",
        "/v1/memory/entries/{entryRef}:deprioritize",
    ),
    "forgetMemoryEntry": ("post", "/v1/memory/entries/{entryRef}:forget"),
    "resetMemorySpace": ("post", "/v1/memory:reset"),
    "requestMemoryExport": ("post", "/v1/memory/exports"),
    "getMemoryExport": ("get", "/v1/memory/exports/{exportRef}"),
    "requestMemoryImport": ("post", "/v1/memory/imports"),
    "getMemoryImport": ("get", "/v1/memory/imports/{importRef}"),
    "recoverMemoryCommand": ("get", "/v1/memory/commands/{commandId}"),
}

MUTATIONS = {
    "updateMemorySettings",
    "rememberMemoryEntry",
    "correctMemoryEntry",
    "restoreMemoryEntryRevision",
    "prioritizeMemoryEntry",
    "deprioritizeMemoryEntry",
    "forgetMemoryEntry",
    "resetMemorySpace",
    "requestMemoryExport",
    "requestMemoryImport",
}

REQUEST_SCHEMAS = {
    "MemorySettingsUpdateInput",
    "MemoryRememberInput",
    "MemoryCorrectInput",
    "MemoryRestoreInput",
    "MemoryPriorityInput",
    "MemoryForgetInput",
    "MemoryResetInput",
    "MemoryExportInput",
    "MemoryImportInput",
}

MEMORY_OBJECT_SCHEMAS = {
    "MemorySettingsAxis",
    "MemorySettings",
    "MemorySettingsUpdateInput",
    "MemoryRememberInput",
    "MemoryCorrectInput",
    "MemoryRestoreInput",
    "MemoryPriorityInput",
    "MemoryForgetInput",
    "MemoryResetInput",
    "MemoryExportInput",
    "MemoryImportInput",
    "MemorySourceSummary",
    "MemoryOwnerSnapshot",
    "MemoryEntryActiveView",
    "MemoryEntryRevokedView",
    "MemoryEntryPurgedView",
    "MemoryEntryPage",
    "MemoryEntryResponse",
    "MemoryRevisionAvailableView",
    "MemoryRevisionPurgedView",
    "MemoryEntryHistoryPage",
    "MemoryArtifactDownloadRequest",
    "MemoryExportStatus",
    "MemoryExportResponse",
    "MemoryImportStatus",
    "MemoryImportResponse",
    "MemoryCommandCursor",
    "MemoryEntryCommandResult",
    "MemoryRestoreCommandResult",
    "MemoryPurgeCommandResult",
    "MemorySettingsCommandResult",
    "MemoryExportCommandResult",
    "MemoryImportCommandResult",
    "MemoryCommandPendingResponse",
    "MemoryCommandSucceededResponse",
    "MemoryCommandRejectedResponse",
    "MemoryCommandRejection",
}


def _openapi() -> dict:
    return yaml.safe_load(PUBLIC_OPENAPI.read_text())


def _operations(document: dict) -> dict[str, tuple[str, str, dict]]:
    return {
        operation["operationId"]: (method, path, operation)
        for path, item in document["paths"].items()
        for method, operation in item.items()
        if isinstance(operation, dict) and "operationId" in operation
    }


def _parameter_refs(operation: dict) -> set[str]:
    return {
        parameter["$ref"].rsplit("/", 1)[-1]
        for parameter in operation.get("parameters", [])
        if "$ref" in parameter
    }


def _walk_schema(
    schema: dict,
    schemas: dict[str, dict],
    seen: frozenset[str] = frozenset(),
) -> Iterator[dict]:
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        if name in seen:
            return
        yield from _walk_schema(schemas[name], schemas, seen | {name})
        return
    yield schema
    for key in ("oneOf", "anyOf", "allOf"):
        for child in schema.get(key, []):
            yield from _walk_schema(child, schemas, seen)
    for child in schema.get("properties", {}).values():
        yield from _walk_schema(child, schemas, seen)
    items = schema.get("items")
    if isinstance(items, dict):
        yield from _walk_schema(items, schemas, seen)


def _property_names(schema: dict, schemas: dict[str, dict]) -> set[str]:
    return {
        property_name
        for node in _walk_schema(schema, schemas)
        for property_name in node.get("properties", {})
    }


def test_memory_public_surface_is_closed_site_bound_and_recoverable() -> None:
    document = _openapi()
    operations = _operations(document)
    actual_memory_operations = {
        operation_id
        for operation_id in operations
        if "Memory" in operation_id
    }
    assert actual_memory_operations == set(MEMORY_OPERATIONS)

    for operation_id, (expected_method, expected_path) in MEMORY_OPERATIONS.items():
        method, path, operation = operations[operation_id]
        assert (method, path) == (expected_method, expected_path)
        assert operation.get("security", document["security"]) == [
            {"ProductWorkload": [], "UserSession": []}
        ]
        assert "ContractVersion" in _parameter_refs(operation)

    for operation_id in MUTATIONS:
        refs = _parameter_refs(operations[operation_id][2])
        assert {"CommandIdentity", "IdempotencyKey", "CsrfToken"}.issubset(refs)

    for operation_id in MEMORY_OPERATIONS.keys() - MUTATIONS:
        refs = _parameter_refs(operations[operation_id][2])
        assert "CommandIdentity" not in refs
        assert "IdempotencyKey" not in refs
        assert "CsrfToken" not in refs

    assert _parameter_refs(operations["listMemoryEntries"][2]) == {
        "MemoryCategoryFilter",
        "MemorySourceFilter",
        "PageCursor",
        "PageLimit",
        "ContractVersion",
    }


def test_memory_requests_are_closed_bounded_and_have_no_caller_scope() -> None:
    document = _openapi()
    schemas = document["components"]["schemas"]
    forbidden_properties = {
        "siteid",
        "siteref",
        "subjectref",
        "subjectgeneration",
        "projectref",
        "spaceref",
        "namespace",
        "keybytes",
        "encryptionkey",
        "sourcecredential",
        "sourceaccessgrant",
        "sourceaccesstoken",
        "digest",
        "contentdigest",
        "requestdigest",
        "sha256",
    }

    for name in REQUEST_SCHEMAS:
        schema = schemas[name]
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["x-kokoro-max-json-utf8-bytes"] == 65536
        exposed = {value.lower() for value in _property_names(schema, schemas)}
        assert exposed.isdisjoint(forbidden_properties), (name, exposed & forbidden_properties)

    for name in MEMORY_OBJECT_SCHEMAS:
        schema = schemas[name]
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False

    for name, schema in schemas.items():
        if not name.startswith("Memory"):
            continue
        for node in _walk_schema(schema, schemas):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False, name

    for name in ("MemoryRememberInput", "MemoryCorrectInput"):
        content = schemas[name]["properties"]["content"]
        assert content["x-kokoro-max-utf8-bytes"] == 16384
        assert content["maxLength"] == 16384

    # M0.1 exposes only the caller's server-derived personal space. Category describes
    # content semantics; it must never be reused as an implicit scope selector.
    assert schemas["MemoryCategory"]["enum"] == ["profile", "preference", "fact"]
    assert schemas["MemoryEntryActiveView"]["properties"]["scopeKind"] == {
        "type": "string",
        "const": "user",
    }

    owner_snapshot = schemas["MemoryOwnerSnapshot"]
    assert owner_snapshot["additionalProperties"] is False
    assert owner_snapshot["required"] == ["snapshotRef", "spaceVersion"]
    assert schemas["MemoryEntryPage"]["required"] == ["items", "pageInfo", "ownerSnapshot"]
    assert schemas["MemoryEntryPage"]["properties"]["ownerSnapshot"] == {
        "$ref": "#/components/schemas/MemoryOwnerSnapshot"
    }
    assert schemas["MemoryEntryPage"][
        "x-kokoro-continuation-requires-same-owner-snapshot"
    ] is True
    assert schemas["MemoryEntryPage"]["x-kokoro-stale-owner-snapshot-rejected"] is True
    assert schemas["MemoryEntryResponse"]["required"] == ["entry", "observedSpaceVersion"]
    succeeded = schemas["MemoryCommandSucceededResponse"]
    assert succeeded["required"] == ["state", "command", "result", "committedSpaceVersion"]
    assert "committedSpaceVersion" not in schemas["MemoryCommandPendingResponse"]["properties"]
    assert "committedSpaceVersion" not in schemas["MemoryCommandRejectedResponse"]["properties"]

    import_input = schemas["MemoryImportInput"]
    assert import_input["x-kokoro-referenced-manifest-max-utf8-bytes"] == 65536
    assert set(import_input["properties"]) == {
        "assetRef",
        "assetVersionRef",
        "format",
        "conflictPolicy",
    }
    assert schemas["MemoryEntryPage"]["properties"]["items"]["maxItems"] == 100
    assert schemas["MemoryEntryPage"]["properties"]["items"]["items"] == {
        "$ref": "#/components/schemas/MemoryEntryActiveView"
    }
    assert schemas["MemoryEntryHistoryPage"]["properties"]["items"]["maxItems"] == 100
    assert document["components"]["parameters"]["PageCursor"]["schema"]["maxLength"] == 2048
    assert document["components"]["parameters"]["PageLimit"]["schema"]["minimum"] == 1
    assert document["components"]["parameters"]["PageLimit"]["schema"]["maximum"] == 100


def test_memory_history_restore_purge_and_async_jobs_are_explicit() -> None:
    document = _openapi()
    schemas = document["components"]["schemas"]

    history = schemas["MemoryEntryHistoryPage"]
    assert history["x-kokoro-immutable-history"] is True
    restore = schemas["MemoryRestoreCommandResult"]
    assert restore["properties"]["resultKind"]["const"] == "restored"
    assert {
        "restoredFromRevisionRef",
        "newRevisionRef",
        "newRevision",
    }.issubset(restore["required"])
    assert restore["properties"]["newRevision"]["minimum"] == 2

    assert schemas["MemoryPurgeState"]["enum"] == [
        "revoked_purge_pending",
        "purged",
    ]
    assert schemas["MemoryPurgeCommandResult"]["properties"]["purgeState"] == {
        "$ref": "#/components/schemas/MemoryPurgeState"
    }

    assert schemas["MemoryExportState"]["enum"] == [
        "queued",
        "running",
        "ready",
        "failed",
        "expired",
        "purged",
    ]
    assert schemas["MemoryImportState"]["enum"] == [
        "queued",
        "validating",
        "quarantined",
        "applying",
        "completed",
        "rejected",
        "failed",
    ]
    export_wire = yaml.safe_dump(schemas["MemoryExportStatus"]).lower()
    assert "artifactdownloadrequest" in export_wire
    assert set(schemas["MemoryArtifactDownloadRequest"]["properties"]) == {
        "artifactRef",
        "artifactVersionRef",
        "deliveryRequestRef",
        "purpose",
    }
    for forbidden in (
        "capability",
        "ciphertext",
        "deliveryhandle",
        "permanenturl",
        "presignedurl",
        "storagekey",
    ):
        assert forbidden not in export_wire

    response = schemas["MemoryCommandResponse"]
    assert response["discriminator"]["propertyName"] == "state"
    assert len(response["oneOf"]) == 3
    command_kind = schemas["MemoryCommandKind"]["enum"]
    assert set(command_kind) == MUTATIONS


def test_memory_m01_does_not_advertise_successor_phase_runtime() -> None:
    document = _openapi()
    schemas = document["components"]["schemas"]

    settings = schemas["MemorySettings"]
    assert set(settings["properties"]) == {
        "revision",
        "savedMemoryUse",
        "pastChatReference",
        "automaticLearning",
        "observedAt",
    }
    assert (
        settings["properties"]["pastChatReference"]["properties"]["availability"]["const"]
        == "unavailable_until_session_m1a"
    )
    assert (
        settings["properties"]["automaticLearning"]["properties"]["availability"]["const"]
        == "unavailable_until_memory_m3"
    )
    memory_wire = yaml.safe_dump(
        {
            "paths": {
                path: item
                for path, item in document["paths"].items()
                if path.startswith("/v1/memory")
            },
            "schemas": {
                name: schema
                for name, schema in schemas.items()
                if name.startswith("Memory")
            },
        }
    ).lower()
    for forbidden in (
        "temporarychat",
        "memoryselectionsnapshot",
        "contextusereceipt",
        "memoryport",
        "searchmemory",
        "conversationsearch",
        "proposal",
        "embedding",
        "namespace",
    ):
        assert forbidden not in memory_wire


def test_platform_public_registry_keeps_memory_contract_only() -> None:
    registry = json.loads(BOUNDARY_REGISTRY.read_text())
    boundary = next(item for item in registry["boundaries"] if item["id"] == "platform-public")
    assert boundary["lifecycle"] == "contract-only"
    by_id = {operation["id"]: operation for operation in boundary["operations"]}
    assert set(MEMORY_OPERATIONS).issubset(by_id)

    for operation_id in MUTATIONS:
        operation = by_id[operation_id]
        assert operation["effect"] is True
        assert operation["retryClass"] == "reconcile_receipt"
        assert operation["receipt"]["recoveryOperation"] == "recoverMemoryCommand"
    for operation_id in set(MEMORY_OPERATIONS) - MUTATIONS:
        assert by_id[operation_id]["effect"] is False
        assert by_id[operation_id]["receipt"] is None

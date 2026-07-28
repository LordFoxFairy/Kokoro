from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from check_admin_browser_schemas import BrowserSchemaError, parse_browser_schemas, run

CONTRACT = {
    "openapi": "3.1.0",
    "components": {
        "schemas": {
            "Me": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "roleKey": {"type": "string"},
                },
            },
            "ResourceRow": {"type": "object", "additionalProperties": True},
            "ModuleOnline": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "manifest": {"type": "object"},
                },
            },
            "ModuleOffline": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "error": {"type": "string"}},
            },
            "ModuleStatus": {
                "oneOf": [
                    {"$ref": "#/components/schemas/ModuleOnline"},
                    {"$ref": "#/components/schemas/ModuleOffline"},
                ]
            },
        }
    },
}


def write(
    tmp_path: Path, reader: str, contract: dict | None = None
) -> tuple[Path, Path]:
    openapi = tmp_path / "admin-web-v1.yaml"
    openapi.write_text(yaml.safe_dump(contract if contract is not None else CONTRACT))
    schemas = tmp_path / "schemas.ts"
    schemas.write_text(textwrap.dedent(reader))
    return openapi, schemas


def patch_map(
    monkeypatch,
    mapping: dict[str, str],
    uncontracted: dict[str, str] | None = None,
    transitional: dict[str, str] | None = None,
):
    import check_admin_browser_schemas as module

    monkeypatch.setattr(module, "SCHEMA_MAP", mapping)
    monkeypatch.setattr(module, "UNCONTRACTED", uncontracted or {})
    monkeypatch.setattr(
        module, "TRANSITIONAL_SCHEMA_MAP", transitional or {}, raising=False
    )


def test_passes_when_every_field_is_declared(tmp_path, monkeypatch):
    patch_map(monkeypatch, {"meSchema": "Me"})
    openapi, schemas = write(
        tmp_path,
        """
        export const meSchema = z.object({
          email: z.string(),
          roleKey: z.string(),
        });
        """,
    )
    message = run(openapi, schemas)
    assert "2 fields proven against the contract" in message
    assert "0 mapped to a schema with no field contract" in message


# The drift this exists to catch: the contract drops a field, the browser keeps reading it.
def test_rejects_a_field_the_contract_does_not_declare(tmp_path, monkeypatch):
    patch_map(monkeypatch, {"meSchema": "Me"})
    openapi, schemas = write(
        tmp_path,
        """
        export const meSchema = z.object({
          email: z.string(),
          removedUpstream: z.string(),
        });
        """,
    )
    with pytest.raises(BrowserSchemaError) as excinfo:
        run(openapi, schemas)
    assert excinfo.value.code == "admin_browser_field_undeclared"
    assert "meSchema.removedUpstream" in str(excinfo.value)
    # The code is printed once, not doubled by re-prefixing a message that already carries it.
    assert str(excinfo.value).count("admin_browser_field_undeclared") == 1


def test_new_reader_must_be_mapped(tmp_path, monkeypatch):
    patch_map(monkeypatch, {}, transitional={"orderSchema": "ResourceRow"})
    openapi, schemas = write(
        tmp_path, "export const meSchema = z.object({\n  email: z.string(),\n});"
    )
    with pytest.raises(BrowserSchemaError) as excinfo:
        run(openapi, schemas)
    assert excinfo.value.code == "admin_browser_schema_unmapped"


def test_removed_reader_makes_its_mapping_fail(tmp_path, monkeypatch):
    patch_map(monkeypatch, {"meSchema": "Me", "goneSchema": "Me"})
    openapi, schemas = write(
        tmp_path, "export const meSchema = z.object({\n  email: z.string(),\n});"
    )
    with pytest.raises(BrowserSchemaError) as excinfo:
        run(openapi, schemas)
    assert excinfo.value.code == "admin_browser_mapping_stale"


def test_transitional_reader_is_checked_while_the_old_pin_still_exports_it(
    tmp_path, monkeypatch
):
    patch_map(monkeypatch, {}, transitional={"orderSchema": "ResourceRow"})
    contract = {
        **CONTRACT,
        "components": {
            "schemas": {
                **CONTRACT["components"]["schemas"],
                "ResourceRow": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "amountMinor": {"type": "string"},
                    },
                },
            }
        },
    }
    openapi, schemas = write(
        tmp_path,
        """
        export const orderSchema = z.object({
          id: z.string(),
          amountMinor: z.string(),
        });
        """,
        contract=contract,
    )

    message = run(openapi, schemas)

    assert "2 fields proven against the contract" in message
    assert "1 transitional reader present (orderSchema)" in message


def test_transitional_reader_still_rejects_a_field_missing_from_the_contract(
    tmp_path, monkeypatch
):
    patch_map(monkeypatch, {}, transitional={"orderSchema": "Me"})
    openapi, schemas = write(
        tmp_path,
        """
        export const orderSchema = z.object({
          removedUpstream: z.string(),
        });
        """,
    )

    with pytest.raises(BrowserSchemaError) as excinfo:
        run(openapi, schemas)

    assert excinfo.value.code == "admin_browser_field_undeclared"
    assert "orderSchema.removedUpstream" in str(excinfo.value)


def test_transitional_reader_may_be_absent_after_the_new_pin_lands(
    tmp_path, monkeypatch
):
    patch_map(
        monkeypatch,
        {"meSchema": "Me"},
        transitional={"orderSchema": "ResourceRow"},
    )
    openapi, schemas = write(
        tmp_path,
        """
        export const meSchema = z.object({
          email: z.string(),
          roleKey: z.string(),
        });
        """,
    )

    message = run(openapi, schemas)

    assert "2 fields proven against the contract" in message
    assert "0 transitional readers present" in message


# A contract entry with no field contract cannot verify anything; it must be counted, not passed off.
def test_counts_schemas_with_no_field_contract(tmp_path, monkeypatch):
    patch_map(monkeypatch, {"orderSchema": "ResourceRow"})
    openapi, schemas = write(
        tmp_path,
        """
        export const orderSchema = z.object({
          amountMinor: z.string(),
        });
        """,
    )
    message = run(openapi, schemas)
    assert "0 fields proven against the contract" in message
    assert (
        "1 mapped to a schema with no field contract (orderSchema->ResourceRow)"
        in message
    )


def test_resolves_a_oneof_union_across_both_branches(tmp_path, monkeypatch):
    patch_map(monkeypatch, {"moduleSchema": "ModuleStatus"})
    openapi, schemas = write(
        tmp_path,
        """
        export const moduleSchema = z.object({
          id: z.string(),
          manifest: z.string(),
          error: z.string(),
        });
        """,
    )
    assert "3 fields proven" in run(openapi, schemas)


def test_rejects_a_field_in_neither_union_branch(tmp_path, monkeypatch):
    patch_map(monkeypatch, {"moduleSchema": "ModuleStatus"})
    openapi, schemas = write(
        tmp_path,
        "export const moduleSchema = z.object({\n  id: z.string(),\n  nope: z.string(),\n});",
    )
    with pytest.raises(BrowserSchemaError) as excinfo:
        run(openapi, schemas)
    assert excinfo.value.code == "admin_browser_field_undeclared"


def test_uncontracted_readers_are_skipped_but_still_tracked(tmp_path, monkeypatch):
    patch_map(monkeypatch, {}, {"hubSchema": "hub payload"})
    openapi, schemas = write(
        tmp_path, "export const hubSchema = z.object({\n  anything: z.string(),\n});"
    )
    assert "1 uncontracted by design" in run(openapi, schemas)


def test_missing_contract_schema_fails(tmp_path, monkeypatch):
    patch_map(monkeypatch, {"meSchema": "NoSuchSchema"})
    openapi, schemas = write(
        tmp_path, "export const meSchema = z.object({\n  email: z.string(),\n});"
    )
    with pytest.raises(BrowserSchemaError) as excinfo:
        run(openapi, schemas)
    assert excinfo.value.code == "admin_browser_contract_schema_missing"


# Reading clean because the parser stopped matching would be worse than failing.
def test_fails_closed_when_no_reader_is_parsed(tmp_path, monkeypatch):
    patch_map(monkeypatch, {})
    openapi, schemas = write(tmp_path, "export type Foo = string;\n")
    with pytest.raises(BrowserSchemaError) as excinfo:
        run(openapi, schemas)
    assert excinfo.value.code == "admin_browser_no_schemas"


def test_fails_closed_on_an_empty_contract(tmp_path, monkeypatch):
    patch_map(monkeypatch, {"meSchema": "Me"})
    openapi, schemas = write(
        tmp_path,
        "export const meSchema = z.object({\n  email: z.string(),\n});",
        contract={"openapi": "3.1.0", "components": {"schemas": {}}},
    )
    with pytest.raises(BrowserSchemaError) as excinfo:
        run(openapi, schemas)
    assert excinfo.value.code == "admin_browser_contract_empty"


# Only depth-one fields belong to the schema; a nested object's keys belong to its own field.
def test_reads_only_top_level_fields():
    parsed = parse_browser_schemas(
        textwrap.dedent(
            """
            export const outer = z.object({
              top: z.object({
                buried: z.string(),
              }),
              sibling: z.string(),
            });
            """
        )
    )
    assert parsed == {"outer": ["top", "sibling"]}


def test_real_repository_passes():
    root = Path(__file__).resolve().parents[2]
    message = run(
        root / "contract" / "openapi" / "admin-web-v1.yaml",
        root / "kokoro-web" / "apps" / "admin" / "lib" / "schemas.ts",
    )
    assert message.startswith("admin_browser_schemas_ok:")
    # D4 is still open, so the three non-acquisition row readers cannot be verified. If
    # this drops, the contract gained a row shape and generation becomes the better answer.
    assert "3 mapped to a schema with no field contract" in message


def test_admin_resource_manifest_requires_an_explicit_site_scope_field():
    root = Path(__file__).resolve().parents[2]
    document = yaml.safe_load(
        (root / "contract" / "openapi" / "admin-web-v1.yaml").read_text(
            encoding="utf-8"
        )
    )
    schema = document["components"]["schemas"]["AdminResourceManifest"]

    assert "siteScopeField" in schema["required"]
    assert schema["properties"]["siteScopeField"] == {
        "description": "返回行中承载 Site scope 的字段；null 表示真正的平台级资源。",
        "type": ["string", "null"],
        "enum": ["siteId", "id", None],
    }


def test_sites_and_billing_contract_publish_the_resolved_permissions_and_scope():
    root = Path(__file__).resolve().parents[2]
    source = (root / "contract" / "openapi" / "admin-web-v1.yaml").read_text(
        encoding="utf-8"
    )
    document = yaml.safe_load(source)
    sites = document["paths"]["/api/sites"]["get"]
    billing = document["paths"]["/api/billing-overview"]["get"]

    assert sites["x-kokoro-required-permission"] == "site.read"
    assert billing["x-kokoro-required-permission"] == "billing.read"
    assert billing["parameters"] == [
        {
            "name": "siteId",
            "in": "query",
            "required": True,
            "description": "计费聚合所属 Site；超出 operator 作用域时 403。",
            "schema": {"type": "string", "minLength": 1},
        }
    ]
    assert "400" in billing["responses"]
    assert "403" in billing["responses"]
    assert "待裁决 D9" not in source
    assert "# D9" not in source

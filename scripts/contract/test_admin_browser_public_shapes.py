"""Live invariants for the filtered Admin browser surface.

The Platform gateway may return a wider upstream object than the Web BFF publishes.
This test deliberately compares the browser contract, the BFF positive schema, and
the browser reader so acquisition fields cannot survive in only one of the three.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from yaml.nodes import MappingNode, Node, SequenceNode

from check_admin_browser_schemas import parse_browser_schemas

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = ROOT / "contract" / "openapi" / "admin-web-v1.yaml"
BFF = ROOT / "kokoro-web" / "apps" / "admin" / "lib" / "admin-gateway.ts"
BROWSER = ROOT / "kokoro-web" / "apps" / "admin" / "lib" / "schemas.ts"


def _duplicate_mapping_keys(node: Node, path: str = "$") -> list[str]:
    duplicates: list[str] = []
    if isinstance(node, MappingNode):
        seen: set[str] = set()
        for key, value in node.value:
            rendered = str(key.value)
            if rendered in seen:
                duplicates.append(f"{path}.{rendered}")
            seen.add(rendered)
            duplicates.extend(_duplicate_mapping_keys(value, f"{path}.{rendered}"))
    elif isinstance(node, SequenceNode):
        for index, value in enumerate(node.value):
            duplicates.extend(_duplicate_mapping_keys(value, f"{path}[{index}]"))
    return duplicates


def test_admin_browser_contract_has_no_silently_overwritten_yaml_keys() -> None:
    node = yaml.compose(OPENAPI.read_text(encoding="utf-8"))
    assert node is not None
    assert _duplicate_mapping_keys(node) == []


def _nested_zod_object_fields(source: str, schema: str, field: str) -> set[str]:
    """Read one named inline z.object without pretending to parse all TypeScript."""
    lines = source.splitlines()
    declaration = re.compile(rf"^const {re.escape(schema)} = z\.object\(\{{\s*$")
    nested = re.compile(rf"^  {re.escape(field)}: z\.object\(\{{\s*$")
    property_line = re.compile(r"^    (?P<field>[A-Za-z_]\w*):")

    start = next(
        (index for index, line in enumerate(lines) if declaration.match(line)), None
    )
    if start is None:
        raise AssertionError(f"missing zod schema: {schema}")

    depth = 1
    nested_start: int | None = None
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if depth == 1 and nested.match(line):
            nested_start = index
            break
        depth += line.count("{") + line.count("(") - line.count("}") - line.count(")")
        if depth <= 0:
            break
    if nested_start is None:
        raise AssertionError(f"missing inline zod object: {schema}.{field}")

    fields: set[str] = set()
    depth = 1
    for line in lines[nested_start + 1 :]:
        if depth == 1:
            match = property_line.match(line)
            if match is not None:
                fields.add(match.group("field"))
        depth += line.count("{") + line.count("(") - line.count("}") - line.count(")")
        if depth <= 0:
            return fields
    raise AssertionError(f"unterminated inline zod object: {schema}.{field}")


def test_user360_public_shape_is_exact_across_contract_bff_and_browser() -> None:
    document = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    contract = document["components"]["schemas"]["User360"]
    contract_fields = set(contract["properties"])
    required = set(contract["required"])
    bff_fields = _nested_zod_object_fields(
        BFF.read_text(encoding="utf-8"), "user360EnvelopeSchema", "data"
    )
    browser_fields = set(
        parse_browser_schemas(BROWSER.read_text(encoding="utf-8"))["user360Schema"]
    )

    expected = {"creditAccount", "identity"}
    assert contract["additionalProperties"] is False
    assert contract_fields == required == bff_fields == browser_fields == expected


def test_module_openapi_operation_publishes_the_filtered_browser_boundary() -> None:
    document = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    operation = document["paths"]["/api/openapi/{moduleId}"]["get"]

    assert operation["operationId"] == "getModuleOpenApi"
    assert operation["x-kokoro-required-permission"] == "docs.read"
    assert operation["parameters"] == [
        {
            "name": "moduleId",
            "in": "path",
            "required": True,
            "description": "浏览器可查看的固定非支付 Platform 模块。",
            "schema": {
                "type": "string",
                "enum": ["site", "user", "model", "credit", "hub"],
            },
        }
    ]
    assert set(operation["responses"]) == {
        "200",
        "400",
        "401",
        "403",
        "404",
        "502",
        "503",
        "504",
    }
    assert {
        status: response["$ref"]
        for status, response in operation["responses"].items()
        if status != "200"
    } == {
        "400": "#/components/responses/OpenApiBadRequest",
        "401": "#/components/responses/OpenApiUnauthorized",
        "403": "#/components/responses/OperatorForbidden",
        "404": "#/components/responses/OpenApiAcquisitionDisabled",
        "502": "#/components/responses/OpenApiBadGateway",
        "503": "#/components/responses/OpenApiBoundaryUnavailable",
        "504": "#/components/responses/OpenApiTimeout",
    }
    success = operation["responses"]["200"]
    assert success["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/OpenApiDocument"
    }
    assert success["headers"]["Content-Disposition"]["schema"]["pattern"] == (
        '^inline; filename="(?:site|user|model|credit|hub)-openapi\\.json"$'
    )

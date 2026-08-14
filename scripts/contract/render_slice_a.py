#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from contract.validate_slice_a_manifest import (
    ManifestError,
    load_manifest,
    validate as validate_manifest,
)


HEADER = "// GENERATED SOURCE — authority: contract/slice-a-contract-manifest.yaml"


def _proto_type(value: str) -> str:
    return value.removeprefix(".")


def _render_enum(enum: dict[str, Any]) -> list[str]:
    lines = [f"enum {enum['name']} {{"]
    lines.extend(f"  {value['name']} = {value['number']};" for value in enum["values"])
    lines.append("}")
    return lines


def _render_field(field: dict[str, Any], indent: str = "  ") -> str:
    label = field["label"]
    prefix = "" if label == "required" else f"{label} "
    return f"{indent}{prefix}{_proto_type(field['type'])} {field['name']} = {field['number']};"


def _render_message(message: dict[str, Any]) -> list[str]:
    if not message["fields"]:
        return [f"message {message['name']} {{}}"]
    lines = [f"message {message['name']} {{"]
    fields = message["fields"]
    emitted_oneofs: set[str] = set()
    for field in fields:
        oneof = field.get("oneof")
        if oneof is None:
            lines.append(_render_field(field))
            continue
        if oneof in emitted_oneofs:
            continue
        emitted_oneofs.add(oneof)
        lines.append(f"  oneof {oneof} {{")
        lines.extend(_render_field(item, "    ") for item in fields if item.get("oneof") == oneof)
        lines.append("  }")
    lines.append("}")
    return lines


def _render_service(service: dict[str, Any]) -> list[str]:
    lines = [f"service {service['name']} {{"]
    for method in service["methods"]:
        stream = "stream " if method.get("serverStreaming", False) else ""
        lines.append(
            f"  rpc {method['name']}({_proto_type(method['input'])}) "
            f"returns ({stream}{_proto_type(method['output'])});"
        )
    lines.append("}")
    return lines


def _render_file(
    file: dict[str, Any],
    declarations: dict[tuple[str, str, str], dict[str, Any]],
) -> str:
    lines = [HEADER, 'syntax = "proto3";', "", f"package {file['package']};"]
    imports = sorted(file["imports"])
    if imports:
        lines.append("")
        lines.extend(f'import "{item}";' for item in imports)
    for assignment in file["declarations"]:
        declaration = declarations[(assignment["kind"], file["package"], assignment["name"])]
        lines.append("")
        if assignment["kind"] == "enum":
            lines.extend(_render_enum(declaration))
        elif assignment["kind"] == "message":
            lines.extend(_render_message(declaration))
        elif assignment["kind"] == "service":
            lines.extend(_render_service(declaration))
        else:
            raise ManifestError(f"unknown declaration kind {assignment['kind']}")
    return "\n".join(lines) + "\n"


def render_proto(manifest: dict[str, Any], output_root: Path) -> list[Path]:
    validate_manifest(manifest)
    proto = manifest["protobuf"]
    declarations = {
        (kind, item["package"], item["name"]): item
        for kind, items in (
            ("enum", proto["enums"]),
            ("message", proto["messages"]),
            ("service", proto["services"]),
        )
        for item in items
    }
    output_root = output_root.absolute()
    if output_root.is_symlink():
        raise ManifestError(f"Proto output must not be a symlink: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{output_root.name}.", dir=output_root.parent) as temporary:
        temporary_root = Path(temporary)
        staged_root = temporary_root / "tree"
        for file in proto["files"]:
            relative = Path(file["path"])
            staged_path = staged_root / relative
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            staged_path.write_text(_render_file(file, declarations))
        backup = temporary_root / "previous"
        if output_root.exists():
            if not output_root.is_dir() or output_root.is_symlink():
                raise ManifestError(f"Proto output must be a real directory: {output_root}")
            os.replace(output_root, backup)
        try:
            os.replace(staged_root, output_root)
        except BaseException:
            if backup.exists():
                os.replace(backup, output_root)
            raise
    return [output_root / file["path"] for file in proto["files"]]


def _enum_json_values(enum: dict[str, Any]) -> list[str]:
    prefix = enum["name"]
    prefix = "".join(f"_{character}" if character.isupper() else character for character in prefix).lstrip("_").upper() + "_"
    return [value["name"].removeprefix(prefix).lower() for value in enum["values"]]


def _protobuf_schema(type_name: str, declarations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if type_name == ".google.protobuf.Timestamp":
        return {"type": "string", "format": "date-time"}
    if type_name.startswith("."):
        return {"$ref": f"#/components/schemas/{type_name.removeprefix('.')}"}
    if type_name in {"double", "float"}:
        return {"type": "number", "format": type_name}
    if type_name in {"int32", "sint32", "sfixed32"}:
        return {"type": "integer", "format": "int32"}
    if type_name in {"uint32", "fixed32"}:
        return {"type": "integer", "minimum": 0, "maximum": 4294967295}
    if type_name in {"int64", "sint64", "sfixed64"}:
        return {"type": "integer", "minimum": -9007199254740991, "maximum": 9007199254740991}
    if type_name in {"uint64", "fixed64"}:
        return {"type": "integer", "minimum": 0, "maximum": 9007199254740991}
    if type_name == "bool":
        return {"type": "boolean"}
    if type_name == "string":
        return {"type": "string"}
    if type_name == "bytes":
        return {"type": "object", "additionalProperties": True, "x-kokoro-source": "canonical-json-bytes"}
    raise ManifestError(f"unsupported OpenAPI protobuf type {type_name}")


def _http_property_schema(source: dict[str, Any], error_codes: list[str]) -> dict[str, Any]:
    kind = source["type"]
    if kind == "array":
        items = source["items"]
        item_schema = {"$ref": f"#/components/schemas/{items}"} if isinstance(items, str) else _http_property_schema(items, error_codes)
        schema: dict[str, Any] = {"type": "array", "items": item_schema}
    elif kind == "json-object":
        schema = {"type": "object", "additionalProperties": True}
    elif kind == "object":
        schema = {"type": "object", "additionalProperties": source.get("additionalProperties", False)}
        if "properties" in source:
            schema["properties"] = {
                property_["name"]: _http_property_schema(property_, error_codes)
                for property_ in source["properties"]
            }
            schema["required"] = source.get("required", [])
    else:
        schema = {"type": kind}
    for key in ("format", "pattern", "minLength", "maxLength", "minimum", "maximum", "minItems", "maxItems", "enum"):
        if key in source:
            schema[key] = source[key]
    if "enumSource" in source:
        schema["enum"] = error_codes
    if "uniqueBy" in source:
        schema["x-kokoro-unique-by"] = source["uniqueBy"]
    if "maxBytes" in source:
        schema["x-kokoro-max-bytes"] = source["maxBytes"]
    return schema


def _control_decision_schema(manifest: dict[str, Any]) -> dict[str, Any]:
    arms = []
    for kind, payload in manifest["rules"]["controlDecisionPayloadSchemasByKind"].items():
        payload_schema = _http_property_schema({"type": "object", **payload}, [])
        arms.append(
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "target_id", "payload"],
                "properties": {
                    "kind": {"type": "string", "const": kind},
                    "target_id": {"type": "string", "minLength": 1},
                    "payload": payload_schema,
                },
            }
        )
    return {"oneOf": arms, "discriminator": {"propertyName": "kind"}}


def _response_headers(headers: dict[str, Any]) -> dict[str, Any]:
    return {
        name: {
            "description": " | ".join(value) if isinstance(value, list) else value,
            "schema": {"type": "string"},
        }
        for name, value in headers.items()
    }


def _openapi_document(manifest: dict[str, Any]) -> dict[str, Any]:
    http = manifest["http"]
    proto = manifest["protobuf"]
    files = {file["path"]: file for file in proto["files"]}
    declarations = {
        f"{kind}:{item['package']}.{item['name']}": item
        for kind, items in (("enum", proto["enums"]), ("message", proto["messages"]))
        for item in items
    }
    web_files = set(manifest["consumerFileClosure"]["kokoro-web"])
    web_declarations = {
        f"{assignment['kind']}:{files[path]['package']}.{assignment['name']}"
        for path in web_files
        for assignment in files[path]["declarations"]
        if assignment["kind"] in {"enum", "message"}
    }
    selected: set[str] = set()
    pending = [
        source["responseSchema"]
        for source in http["operations"]
        if isinstance(source["responseSchema"], str) and source["responseSchema"].startswith("kokoro.")
    ]
    while pending:
        full_name = pending.pop()
        matching = [key for key in web_declarations if key.endswith(f":{full_name}")]
        if len(matching) != 1:
            raise ManifestError(f"browser response references non-Web protobuf declaration: {full_name}")
        key = matching[0]
        if key in selected:
            continue
        selected.add(key)
        if key.startswith("message:"):
            for field in declarations[key]["fields"]:
                if field["type"].startswith(".") and field["type"] != ".google.protobuf.Timestamp":
                    pending.append(field["type"].removeprefix("."))
    schemas: dict[str, Any] = {}
    for key in sorted(selected):
        kind, full_name = key.split(":", 1)
        declaration = declarations[key]
        if kind == "enum":
            schemas[full_name] = {"type": "string", "enum": _enum_json_values(declaration)}
            continue
        properties: dict[str, Any] = {}
        required: list[str] = []
        for field in declaration["fields"]:
            property_schema = _protobuf_schema(field["type"], declarations)
            if field["label"] == "repeated":
                property_schema = {"type": "array", "items": property_schema}
            properties[field["name"]] = property_schema
            if field["label"] != "optional":
                required.append(field["name"])
        schemas[full_name] = {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": required,
        }
    error_codes = list(http["errorStatusByCode"])
    custom_by_name = {source["name"]: source for source in http["schemas"]}
    custom_selected = {
        name
        for operation in http["operations"]
        for name in (operation["requestBodySchema"], operation["responseSchema"])
        if name in custom_by_name and name != "Empty"
    }
    pending_custom = list(custom_selected)
    while pending_custom:
        name = pending_custom.pop()
        source = custom_by_name[name]
        for property_ in source.get("properties", []):
            referenced = property_.get("items")
            if isinstance(referenced, str) and referenced in custom_by_name and referenced not in custom_selected:
                custom_selected.add(referenced)
                pending_custom.append(referenced)
    for name in sorted(custom_selected):
        source = custom_by_name[name]
        if source["name"] == "ControlDecisionHttp":
            schemas[source["name"]] = _control_decision_schema(manifest)
        else:
            schemas[source["name"]] = _http_property_schema(source, error_codes)
    schemas["KokoroError"] = _http_property_schema(http["errorBody"], error_codes)

    paths: dict[str, Any] = {}
    for source in http["operations"]:
        responses: dict[str, Any] = {}
        success: dict[str, Any] = {"description": "Success"}
        if source["successHeaders"]:
            success["headers"] = _response_headers(source["successHeaders"])
        if source["responseSchema"] == "text/event-stream":
            success["content"] = {"text/event-stream": {"schema": {"type": "string"}}}
        elif source["responseSchema"] != "Empty" and source["successStatus"] not in {204, 303}:
            success["content"] = {
                "application/json": {"schema": {"$ref": f"#/components/schemas/{source['responseSchema']}"}}
            }
        if source["alternateResponses"]:
            success["x-kokoro-alternate-responses"] = source["alternateResponses"]
        responses[str(source["successStatus"])] = success
        for status in source["errorStatuses"]:
            responses[str(status)] = {
                "description": "Kokoro error",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/KokoroError"}}},
            }
        operation: dict[str, Any] = {
            "operationId": source["operationId"],
            "summary": " ".join(re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", source["operationId"])).capitalize(),
            "parameters": [
                {"name": item["name"], "in": item["in"], "required": item["required"], "schema": item["schema"]}
                for item in source["parameters"]
            ],
            "responses": responses,
            "security": (
                [{"cookieAuth": []}]
                if any(item["name"] == "kokoro_session" and item["required"] for item in source["parameters"])
                else []
            ),
        }
        if source["requestBodySchema"] is not None:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{source['requestBodySchema']}"}
                    }
                },
            }
        paths.setdefault(source["path"], {})[source["method"]] = operation
    return {
        "openapi": http["openapiVersion"],
        "info": {"title": "Kokoro Slice A Web API", "version": "1.0.0", "license": {"name": "Proprietary"}},
        "servers": [{"url": "/"}],
        "paths": paths,
        "components": {
            "schemas": schemas,
            "securitySchemes": {"cookieAuth": {"type": "apiKey", "in": "cookie", "name": "kokoro_session"}},
        },
    }


def render_openapi(manifest: dict[str, Any], output_path: Path) -> Path:
    validate_manifest(manifest)
    document = _openapi_document(manifest)
    output_path = output_path.absolute()
    if output_path.is_symlink():
        raise ManifestError(f"OpenAPI output must not be a symlink: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", prefix=f".{output_path.name}.", dir=output_path.parent, delete=False) as temporary:
        temporary.write("# GENERATED SOURCE — authority: contract/slice-a-contract-manifest.yaml\n")
        yaml.safe_dump(document, temporary, sort_keys=False, allow_unicode=True, width=120)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, output_path)
    return output_path


def check_tree(manifest_path: Path, expected_root: Path, expected_openapi: Path) -> None:
    manifest = load_manifest(manifest_path)
    expected_paths = {item["path"] for item in manifest["protobuf"]["files"]}
    actual_paths = {
        path.relative_to(expected_root).as_posix()
        for path in expected_root.rglob("*.proto")
        if path.is_file()
    } if expected_root.is_dir() else set()
    if actual_paths != expected_paths:
        raise ManifestError(f"rendered Proto file inventory drift: {sorted(actual_paths ^ expected_paths)}")
    with tempfile.TemporaryDirectory(prefix="slice-a-contract-check-") as temporary:
        rendered_root = Path(temporary).resolve()
        rendered = render_proto(manifest, rendered_root)
        for rendered_path in rendered:
            relative = rendered_path.relative_to(rendered_root)
            expected = expected_root / relative
            if not expected.is_file() or expected.read_bytes() != rendered_path.read_bytes():
                raise ManifestError(f"rendered contract drift: {relative.as_posix()}")
        rendered_openapi = render_openapi(manifest, rendered_root / "slice-a-web-v1.yaml")
        if not expected_openapi.is_file() or expected_openapi.read_bytes() != rendered_openapi.read_bytes():
            raise ManifestError("rendered contract drift: slice-a-web-v1.yaml")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--proto-root", type=Path, default=Path("contract/proto"))
    parser.add_argument("--openapi", type=Path, default=Path("contract/openapi/slice-a-web-v1.yaml"))
    args = parser.parse_args()
    if args.write:
        paths = render_proto(load_manifest(args.manifest), args.proto_root)
        render_openapi(load_manifest(args.manifest), args.openapi)
        print(f"slice_a_contract_rendered:proto={len(paths)}:openapi=1")
    else:
        check_tree(args.manifest, args.proto_root, args.openapi)
        print("slice_a_contract_tree_verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

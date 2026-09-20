"""Canonical SQL naming and OpenAPI governance checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .ten_repository_standard import (
    REPOSITORY_PATHS,
    ROOT,
    Failure,
    add,
    read_text,
    yaml_document_body,
)

REQUIRED_OPENAPI_OPERATION_EXTENSIONS = (
    "x-kokoro-owner",
    "x-kokoro-visibility",
    "x-kokoro-stability",
    "x-kokoro-idempotency",
    "x-kokoro-permission",
)
HTTP_OPERATION_METHODS = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
)


def missing_openapi_operation_extensions(
    text: str,
    suffix: str,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    return _missing_operation_extensions(read_openapi_document(text, suffix))


def _missing_operation_extensions(
    document: dict[str, object] | None,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    operations: list[tuple[str, str, set[str]]] = []
    paths = document.get("paths", {}) if document else {}
    if document is not None and isinstance(paths, dict):
        for path in _document_paths(document):
            path_item = paths[path]
            for method, operation in path_item.items():
                if method in HTTP_OPERATION_METHODS:
                    operations.append((path, method, set(operation)))

    missing: list[tuple[str, str, tuple[str, ...]]] = []
    for path, method, fields in operations:
        if path in {"/healthz", "/livez", "/readyz", "/metrics"}:
            continue
        absent = tuple(
            extension
            for extension in REQUIRED_OPENAPI_OPERATION_EXTENSIONS
            if extension not in fields
        )
        if absent:
            missing.append((path, method, absent))
    return tuple(missing)


def check_schema_naming(
    repository_name: str, canonical: Path, failures: list[Failure]
) -> None:
    """Require explicit, stable names for database diagnostics."""
    pending_constraint_name: str | None = None
    for line_number, line in enumerate(read_text(canonical).splitlines(), start=1):
        named_constraint = re.search(
            r"\bCONSTRAINT\s+([a-z0-9_]+)", line, re.IGNORECASE
        )
        if named_constraint:
            pending_constraint_name = named_constraint.group(1).lower()

        if re.search(r"\bCHECK\s*\(", line, re.IGNORECASE) and not (
            re.search(r"\bCONSTRAINT\s+ck_[a-z0-9_]+\b", line, re.IGNORECASE)
            or (pending_constraint_name or "").startswith("ck_")
        ):
            add(
                failures,
                repository_name,
                "sql-naming",
                f"database/schema.sql:{line_number} CHECK must have a ck_ constraint name",
            )
        if (
            re.search(r"\bUNIQUE(?:\s*\(|\s*[,)]?$)", line, re.IGNORECASE)
            and not re.search(r"\bCREATE\s+UNIQUE\s+INDEX\b", line, re.IGNORECASE)
            and not re.search(r"\bCONSTRAINT\s+uq_[a-z0-9_]+\b", line, re.IGNORECASE)
            and not (pending_constraint_name or "").startswith("uq_")
        ):
            add(
                failures,
                repository_name,
                "sql-naming",
                f"database/schema.sql:{line_number} UNIQUE must have a uq_ constraint name",
            )

        index_match = re.search(
            r"CREATE\s+(UNIQUE\s+)?INDEX(?:\s+IF\s+NOT\s+EXISTS)?\s+([a-z0-9_]+)",
            line,
            re.IGNORECASE,
        )
        if index_match:
            expected_prefix = "uq_" if index_match.group(1) else "ix_"
            if not index_match.group(2).lower().startswith(expected_prefix):
                add(
                    failures,
                    repository_name,
                    "sql-naming",
                    f"database/schema.sql:{line_number} index must start with {expected_prefix}",
                )

        constraint_match = re.search(
            r"\bCONSTRAINT\s+([a-z0-9_]+)", line, re.IGNORECASE
        )
        if constraint_match and not constraint_match.group(1).lower().startswith(
            ("ck_", "uq_", "pk_", "ex_")
        ):
            add(
                failures,
                repository_name,
                "sql-naming",
                f"database/schema.sql:{line_number} has a non-standard constraint name",
            )
        if re.search(
            r"\b(?:CHECK|UNIQUE|PRIMARY\s+KEY|EXCLUDE)\b", line, re.IGNORECASE
        ):
            pending_constraint_name = None


class OpenApiPathParseError(ValueError):
    """A path map cannot be interpreted by the dependency-free preflight."""


def _yaml_mapping_entries(text: str) -> dict[str, tuple[str, str]]:
    """Read one explicit block mapping, keeping child bodies opaque.

    This is a deliberately bounded preflight, not a general YAML parser. Node
    properties, complex keys, merges, multiline inline values and multiple
    documents are rejected wherever they could hide the mapping being read.
    """
    entries: dict[str, tuple[str, str]] = {}
    root_indent: int | None = None
    key: str | None = None
    is_block_scalar = False
    block_scalar_indent: int | None = None
    block_scalar_closed = False
    for line in text.splitlines():
        stripped = line.lstrip(" ")
        if not stripped:
            continue
        indent = len(line) - len(stripped)
        if stripped.startswith("#"):
            if key is None or root_indent is None:
                continue
            value, body = entries[key]
            if is_block_scalar:
                if indent <= root_indent or (
                    block_scalar_indent is not None and indent < block_scalar_indent
                ):
                    block_scalar_closed = True
                if block_scalar_closed:
                    continue
            else:
                if not value or value.startswith("#"):
                    # Retain even dedented comments so nested scalar readers
                    # can observe the point at which their content ended.
                    entries[key] = (value, body + line + "\n")
                continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise OpenApiPathParseError("YAML tabs in indentation are unsupported")
        if root_indent is None:
            root_indent = indent
        if indent < root_indent:
            raise OpenApiPathParseError("inconsistent YAML mapping indentation")
        if indent > root_indent and key is not None:
            value, body = entries[key]
            if value and not value.startswith("#"):
                if not is_block_scalar:
                    raise OpenApiPathParseError(
                        "indented YAML content after an inline value is unsupported"
                    )
                if block_scalar_closed:
                    raise OpenApiPathParseError(
                        "indented YAML content after a closed block scalar"
                    )
                if block_scalar_indent is None:
                    block_scalar_indent = indent
                elif indent < block_scalar_indent:
                    raise OpenApiPathParseError(
                        "inconsistent YAML block scalar indentation"
                    )
            entries[key] = (value, body + line + "\n")
            continue
        match = re.fullmatch(
            r"(?:\"([^\"\\]+)\"|'([^']+)'|([A-Za-z0-9_/$~.{}-]+))\s*:\s*(.*)",
            stripped,
        )
        if not match:
            raise OpenApiPathParseError(
                "unsupported YAML mapping key, root node or document boundary"
            )
        key = next(value for value in match.groups()[:3] if value is not None)
        if key in entries:
            raise OpenApiPathParseError(f"duplicate YAML mapping key {key!r}")
        value = match.group(4).rstrip()
        block_scalar = re.fullmatch(r"[|>][+-]?(?:\s+#.*)?", value)
        is_block_scalar = block_scalar is not None
        block_scalar_indent = None
        block_scalar_closed = False
        if value.startswith(("|", ">")) and not is_block_scalar:
            raise OpenApiPathParseError("unsupported YAML block scalar header")
        if value.startswith(("&", "*", "!")):
            raise OpenApiPathParseError(
                "YAML anchors, aliases and tags are unsupported"
            )
        if value.startswith(('"', "'")):
            if not re.fullmatch(
                r'(?:"(?:[^"\\]|\\.)*"|\'(?:[^\']|\'\')*\')(?:\s+#.*)?', value
            ):
                raise OpenApiPathParseError(
                    "multiline YAML quoted values are unsupported"
                )
        elif value.startswith(("{", "[")):
            # Opaque inline leaves are allowed; multiline flow can cross the
            # indentation boundary and must never masquerade as root entries.
            closing = "}" if value[0] == "{" else "]"
            if not re.search(re.escape(closing) + r"(?:\s+#.*)?$", value):
                raise OpenApiPathParseError(
                    "multiline YAML flow values are unsupported"
                )
        entries[key] = (value, "")
    return entries


def _yaml_block_mapping(entry: tuple[str, str]) -> dict[str, tuple[str, str]]:
    value, body = entry
    value = value.split("#", 1)[0].strip()
    has_content = any(
        line.strip() and not line.lstrip().startswith("#") for line in body.splitlines()
    )
    if value == "{}" and not has_content:
        return {}
    if value or not has_content:
        raise OpenApiPathParseError(
            "expected explicit YAML block mapping or {}; flow, scalar and indirect maps are unsupported"
        )
    return _yaml_mapping_entries(body)


def _json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document: dict[str, object] = {}
    for key, value in pairs:
        if key in document:
            raise OpenApiPathParseError(f"duplicate JSON mapping key {key!r}")
        document[key] = value
    return document


def read_openapi_document(text: str, suffix: str) -> dict[str, object] | None:
    """Return a confirmed OpenAPI view, known non-OpenAPI, or raise a diagnostic.

    JSON is parsed structurally regardless of extension. Explicit block YAML
    is projected only at root/paths/path-item/operation mapping boundaries;
    unsupported syntax fails closed before ownership or governance succeeds.
    """
    if suffix.lower() in {".yaml", ".yml"}:
        try:
            text = yaml_document_body(text)
        except ValueError as error:
            raise OpenApiPathParseError(str(error)) from error
    if not text.strip():
        raise OpenApiPathParseError("empty or unreadable OpenAPI candidate")
    try:
        document = json.loads(text, object_pairs_hook=_json_object)
    except json.JSONDecodeError as error:
        if suffix.lower() == ".json" or text.lstrip().startswith(("{", "[")):
            raise OpenApiPathParseError(
                "invalid JSON or unsupported YAML flow document"
            ) from error
    else:
        if not isinstance(document, dict) or "openapi" not in document:
            return None
        if not isinstance(document["openapi"], str):
            raise OpenApiPathParseError("OpenAPI version must be a string")
        return document

    root = _yaml_mapping_entries(text)
    if "openapi" not in root:
        return None
    version, version_body = root["openapi"]
    if version_body or not re.fullmatch(
        r"(?:3\.\d+\.\d+|'3\.\d+\.\d+'|\"3\.\d+\.\d+\")(?:\s+#.*)?", version
    ):
        raise OpenApiPathParseError("unsupported YAML OpenAPI version declaration")
    paths: dict[str, object] = {}
    for route, item in _yaml_block_mapping(root.get("paths", ("{}", ""))).items():
        if route.startswith("x-"):
            continue
        path_item = _yaml_block_mapping(item)
        if "$ref" in path_item:
            raise OpenApiPathParseError("indirect YAML path items are unsupported")
        operations: dict[str, object] = {}
        for method, operation in path_item.items():
            if method in HTTP_OPERATION_METHODS:
                fields = _yaml_block_mapping(operation)
                operations[method] = {
                    field: value for field, (value, _) in fields.items()
                }
            elif method not in {
                "summary",
                "description",
                "servers",
                "parameters",
            } and not method.startswith("x-"):
                raise OpenApiPathParseError(
                    f"unsupported YAML path-item field {method!r}"
                )
        paths[route] = operations
    return {"openapi": version, "paths": paths}


def _document_paths(document: dict[str, object]) -> tuple[str, ...]:
    paths = document.get("paths", {})
    if not isinstance(paths, dict):
        raise OpenApiPathParseError("OpenAPI paths must be a mapping")
    routes: list[str] = []
    for key, path_item in paths.items():
        if isinstance(key, str) and key.startswith("x-"):
            continue
        if not isinstance(key, str) or not key.startswith("/"):
            raise OpenApiPathParseError(
                "OpenAPI paths entries must be routes or x-* extensions"
            )
        if not isinstance(path_item, dict):
            raise OpenApiPathParseError("OpenAPI path items must be mappings")
        for method, operation in path_item.items():
            if method in HTTP_OPERATION_METHODS:
                if not isinstance(operation, dict):
                    raise OpenApiPathParseError("OpenAPI operations must be mappings")
            elif method not in {
                "summary",
                "description",
                "servers",
                "parameters",
            } and not method.startswith("x-"):
                raise OpenApiPathParseError(
                    f"unsupported OpenAPI path-item field {method!r}"
                )
        routes.append(key)
    return tuple(routes)


def openapi_paths(text: str, suffix: str) -> tuple[str, ...]:
    document = read_openapi_document(text, suffix)
    return _document_paths(document) if document is not None else ()


def is_v1_http_path(route: str) -> bool:
    return route.startswith(("/v1/", "/internal/v1/", "/.well-known/")) or route in {
        "/v1",
        "/internal/v1",
        "/healthz",
        "/livez",
        "/readyz",
        "/metrics",
    }


def check_openapi_contract(
    repository_name: str, specification: Path, failures: list[Failure]
) -> bool:
    specification_text = read_text(specification)
    try:
        document = read_openapi_document(specification_text, specification.suffix)
        if document is None:
            return False
        paths = _document_paths(document)
    except OpenApiPathParseError as error:
        add(
            failures,
            repository_name,
            "openapi-parsing",
            f"{specification.relative_to(ROOT / REPOSITORY_PATHS[repository_name])}: {error}",
        )
        return False
    for route in paths:
        if not is_v1_http_path(route):
            add(
                failures,
                repository_name,
                "http-versioning",
                f"{specification.relative_to(ROOT / REPOSITORY_PATHS[repository_name])} path {route!r} violates the first-release v1 baseline",
            )
    lines = specification_text.splitlines()
    properties_indents: list[int] = []
    for line_number, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        while properties_indents and indent <= properties_indents[-1]:
            properties_indents.pop()
        if re.match(r"properties\s*:\s*$", stripped):
            properties_indents.append(indent)
            continue
        if properties_indents and indent == properties_indents[-1] + 2:
            property_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*):", stripped)
            if property_match and re.search(r"[A-Z]", property_match.group(1)):
                add(
                    failures,
                    repository_name,
                    "wire-naming",
                    f"{specification.relative_to(ROOT / REPOSITORY_PATHS[repository_name])}:{line_number} property {property_match.group(1)!r} is not snake_case",
                )

    for route, method, missing_extensions in _missing_operation_extensions(document):
        add(
            failures,
            repository_name,
            "openapi-governance",
            f"{specification.relative_to(ROOT / REPOSITORY_PATHS[repository_name])} {method.upper()} {route} lacks "
            + ", ".join(missing_extensions),
        )

    return True

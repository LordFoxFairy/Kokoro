"""Canonical SQL naming and OpenAPI governance checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .ten_repository_standard import ROOT, Failure, add, read_text

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
    operations: list[tuple[str, str, set[str]]] = []
    if suffix.lower() == ".json":
        try:
            document = json.loads(text)
        except json.JSONDecodeError:
            return ()
        paths = document.get("paths", {}) if isinstance(document, dict) else {}
        if isinstance(paths, dict):
            for path, path_item in paths.items():
                if not isinstance(path, str) or not isinstance(path_item, dict):
                    continue
                for method, operation in path_item.items():
                    if method.lower() not in HTTP_OPERATION_METHODS or not isinstance(
                        operation, dict
                    ):
                        continue
                    operations.append((path, method.lower(), set(operation)))
    else:
        lines = text.splitlines()
        current_path: str | None = None
        current_path_indent = -1
        for index, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(stripped)
            path_match = re.match(r"[\"']?(/[^:\"']*)[\"']?\s*:\s*$", stripped)
            if path_match:
                current_path = path_match.group(1)
                current_path_indent = indent
                continue
            method_match = re.match(r"([a-z]+)\s*:\s*$", stripped, re.IGNORECASE)
            if (
                current_path is None
                or method_match is None
                or indent <= current_path_indent
                or method_match.group(1).lower() not in HTTP_OPERATION_METHODS
            ):
                continue
            method = method_match.group(1).lower()
            fields: set[str] = set()
            for nested_line in lines[index + 1 :]:
                nested_stripped = nested_line.lstrip()
                if not nested_stripped or nested_stripped.startswith("#"):
                    continue
                nested_indent = len(nested_line) - len(nested_stripped)
                if nested_indent <= indent:
                    break
                field_match = re.match(r"([a-zA-Z0-9_-]+)\s*:", nested_stripped)
                if field_match:
                    fields.add(field_match.group(1))
            operations.append((current_path, method, fields))

    missing: list[tuple[str, str, tuple[str, ...]]] = []
    for path, method, fields in operations:
        if path in {"/healthz", "/readyz", "/metrics"}:
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


def check_openapi_contract(
    repository_name: str, specification: Path, failures: list[Failure]
) -> None:
    specification_text = read_text(specification)
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
        path_match = re.match(r"(/[^:]*):\s*$", stripped)
        if path_match and indent <= 4:
            route = path_match.group(1)
            internal_versioned = re.match(
                r"^/internal(?:/[a-z0-9._{}-]+)*/v[0-9]+(?:/|$)", route
            )
            if not (
                route.startswith(("/v1/", "/.well-known/"))
                or route in {"/v1", "/healthz", "/readyz", "/metrics"}
                or internal_versioned
            ):
                add(
                    failures,
                    repository_name,
                    "http-versioning",
                    f"{specification.relative_to(ROOT / repository_name)}:{line_number} has non-versioned path {route!r}",
                )
        if properties_indents and indent == properties_indents[-1] + 2:
            property_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*):", stripped)
            if property_match and re.search(r"[A-Z]", property_match.group(1)):
                add(
                    failures,
                    repository_name,
                    "wire-naming",
                    f"{specification.relative_to(ROOT / repository_name)}:{line_number} property {property_match.group(1)!r} is not snake_case",
                )

    for route, method, missing_extensions in missing_openapi_operation_extensions(
        specification_text,
        specification.suffix,
    ):
        add(
            failures,
            repository_name,
            "openapi-governance",
            f"{specification.relative_to(ROOT / repository_name)} {method.upper()} {route} lacks "
            + ", ".join(missing_extensions),
        )

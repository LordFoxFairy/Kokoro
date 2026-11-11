"""Canonical SQL naming and OpenAPI governance checks."""

from __future__ import annotations

import json
from hashlib import sha256
import re
from pathlib import Path

from .contract_inventory import git_blob, safe_relative_path
from .ten_repository_standard import (
    REPOSITORY_PATHS,
    REPOSITORY_PROFILES,
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


class OpenApiUnsupportedError(OpenApiPathParseError):
    """Syntax outside this bounded preflight, not proof of an invalid contract."""


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
            raise OpenApiPathParseError("YAML tabs in indentation are invalid")
        if root_indent is None:
            root_indent = indent
        if indent < root_indent:
            raise OpenApiPathParseError("inconsistent YAML mapping indentation")
        if indent > root_indent and key is not None:
            value, body = entries[key]
            if value and not value.startswith("#"):
                if not is_block_scalar:
                    raise OpenApiUnsupportedError(
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
            raise OpenApiUnsupportedError(
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
            error = (
                OpenApiUnsupportedError
                if re.fullmatch(r"[|>](?:[1-9][+-]?|[+-][1-9])(?:\s+#.*)?", value)
                else OpenApiPathParseError
            )
            raise error("unsupported or invalid YAML block scalar header")
        if value.startswith(("&", "*", "!")):
            raise OpenApiUnsupportedError(
                "YAML anchors, aliases and tags are unsupported"
            )
        if value.startswith(('"', "'")):
            if not re.fullmatch(
                r'(?:"(?:[^"\\]|\\.)*"|\'(?:[^\']|\'\')*\')(?:\s+#.*)?', value
            ):
                raise OpenApiUnsupportedError(
                    "multiline YAML quoted values are unsupported"
                )
        elif value.startswith(("{", "[")):
            # Opaque inline leaves are allowed; multiline flow can cross the
            # indentation boundary and must never masquerade as root entries.
            closing = "}" if value[0] == "{" else "]"
            if not re.search(re.escape(closing) + r"(?:\s+#.*)?$", value):
                raise OpenApiUnsupportedError(
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
        error = (
            OpenApiUnsupportedError
            if value.startswith(("{", "&", "*", "!"))
            else OpenApiPathParseError
        )
        raise error(
            "expected explicit YAML block mapping or {}; flow and indirect maps are unsupported"
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
            # A valid non-JSON inline document exceeds the bounded projection;
            # malformed/repeated directives remain recognized violations.
            error_type = (
                OpenApiUnsupportedError
                if str(error) == "inline YAML document markers support JSON values only"
                else OpenApiPathParseError
            )
            raise error_type(str(error)) from error
    if not text.strip():
        raise OpenApiPathParseError("empty or unreadable OpenAPI candidate")
    try:
        document = json.loads(text, object_pairs_hook=_json_object)
    except json.JSONDecodeError as error:
        if suffix.lower() == ".json":
            raise OpenApiPathParseError("invalid JSON document") from error
        if text.lstrip().startswith(("{", "[")):
            raise OpenApiUnsupportedError(
                "YAML flow documents are unsupported"
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
    # Recognized non-string scalars/collections are invalid, not tool limits.
    # Quoted strings and indirect YAML nodes retain the bounded-reader behavior.
    version_value = version.split("#", 1)[0].strip()
    if (
        not version_value
        or version_value.lower() in {"null", "~", "true", "false"}
        or version_value.startswith(("[", "{"))
        or re.fullmatch(
            r"[+-]?(?:0x[0-9a-f_]+|0o[0-7_]+|[0-9][0-9_]*(?:\.[0-9_]*)?(?:e[+-]?[0-9_]+)?|\.[0-9_]+|\.inf|\.nan)",
            version_value,
            re.IGNORECASE,
        )
    ):
        raise OpenApiPathParseError("OpenAPI version must be a string")
    if version_body or not re.fullmatch(
        r"(?:3\.\d+\.\d+|'3\.\d+\.\d+'|\"3\.\d+\.\d+\")(?:\s+#.*)?", version
    ):
        raise OpenApiUnsupportedError("unsupported YAML OpenAPI version declaration")
    paths: dict[str, object] = {}
    for route, item in _yaml_block_mapping(root.get("paths", ("{}", ""))).items():
        if route.startswith("x-"):
            continue
        path_item = _yaml_block_mapping(item)
        if "$ref" in path_item:
            raise OpenApiUnsupportedError("indirect YAML path items are unsupported")
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


def check_imported_openapi_snapshot(
    repository_name: str,
    specification: Path,
    failures: list[Failure],
    unverified: list[Failure] | None,
) -> None:
    """Prove imported bytes from existing pins and immutable publisher objects.

    This establishes attribution, not current runtime consumption or approval of
    upstream API rules. Unproven vendor content remains blocking and never proves
    that the consumer owns a published contract.
    """
    repository = ROOT / REPOSITORY_PATHS[repository_name]
    relative = specification.relative_to(repository)
    parts = relative.parts
    if (
        len(parts) != 5
        or parts[2] == repository_name
        or parts[2] not in REPOSITORY_PROFILES
        or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", parts[3])
    ):
        add(
            failures,
            repository_name,
            "snapshot-provenance",
            f"{relative}: invalid imported snapshot identity",
        )
        return
    owner_name, commit = parts[2:4]
    profile = REPOSITORY_PROFILES[repository_name]
    records: list[tuple[object, object, object, object]] = []
    for publisher, manifest_path in profile.imported_openapi_manifests:
        if publisher != owner_name:
            continue
        try:
            manifest = json.loads(
                read_text(repository / manifest_path), object_pairs_hook=_json_object
            )
        except ValueError:
            continue
        if not isinstance(manifest, dict):
            continue
        owner = manifest.get("owner")
        if isinstance(owner, dict):
            records.append(
                (
                    owner.get("repository_path"),
                    owner.get("repository_commit"),
                    owner.get("contract_path"),
                    owner.get("contract_sha256"),
                )
            )
        elif isinstance(owner, str) and owner in REPOSITORY_PATHS:
            records.append(
                (
                    REPOSITORY_PATHS[owner].as_posix(),
                    manifest.get("owner_commit"),
                    manifest.get("source_path"),
                    manifest.get("source_sha256"),
                )
            )
        if manifest_path == "contract/iam-relay-policy.json":
            records.append(
                (
                    "apps/kokoro-iam",
                    manifest.get("iamOwnerCommit"),
                    manifest.get("iamOpenapiPath"),
                    manifest.get("iamOpenapiSha256"),
                )
            )
    owner_repository = REPOSITORY_PATHS[owner_name].as_posix()
    references: set[tuple[str, str]] = set()
    for owner_path, pinned_commit, source, digest in records:
        if (
            owner_path != owner_repository
            or pinned_commit != commit
            or not isinstance(source, str)
            or not isinstance(digest, str)
        ):
            continue
        try:
            safe_source = safe_relative_path(source).as_posix()
        except ValueError:
            continue
        if (
            safe_source != source
            or Path(source).name != specification.name
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            continue
        if (
            not source.startswith("contract/openapi/")
            and source not in REPOSITORY_PROFILES[owner_name].upstream_openapi_snapshots
        ):
            continue
        references.add((source, digest))
    historical_source = dict(profile.historical_openapi_snapshots).get(
        relative.as_posix()
    )
    if len(references) > 1 or (not references and historical_source is None):
        add(
            failures,
            repository_name,
            "snapshot-provenance",
            f"{relative}: no unique approved source pin/digest",
        )
        return
    source, expected_digest = (
        next(iter(references)) if references else (historical_source, None)
    )
    try:
        content = specification.read_bytes()
        actual_digest = sha256(content).hexdigest()
        if expected_digest is not None and expected_digest != actual_digest:
            add(
                failures,
                repository_name,
                "snapshot-provenance",
                f"{relative}: imported bytes differ from the source pin",
            )
            return
        source_blob = git_blob(ROOT, owner_repository, commit, source)
    except (OSError, ValueError) as error:
        add(
            unverified if unverified is not None else failures,
            repository_name,
            "snapshot-provenance",
            f"{relative}: unverified publisher bytes: {error}",
        )
        return
    if sha256(source_blob).hexdigest() != actual_digest:
        add(
            failures,
            repository_name,
            "snapshot-provenance",
            f"{relative}: imported bytes differ from the source pin or immutable publisher blob",
        )


def check_openapi_contract(
    repository_name: str,
    specification: Path,
    failures: list[Failure],
    unverified: list[Failure] | None = None,
) -> bool | None:
    repository = ROOT / REPOSITORY_PATHS[repository_name]
    relative = specification.relative_to(repository)
    profile = REPOSITORY_PROFILES[repository_name]
    if (
        len(relative.parts) >= 3
        and relative.parts[:2] == ("contract", "vendor")
        and relative.parts[2]
        in {publisher for publisher, _ in profile.imported_openapi_manifests}
    ):
        check_imported_openapi_snapshot(
            repository_name, specification, failures, unverified
        )
        return False
    specification_text = read_text(specification)
    try:
        document = read_openapi_document(specification_text, specification.suffix)
        if document is None:
            return False
        paths = _document_paths(document)
    except OpenApiUnsupportedError as error:
        # Callers without a separate channel still fail closed.
        add(
            unverified if unverified is not None else failures,
            repository_name,
            "openapi-parsing",
            f"{specification.relative_to(ROOT / REPOSITORY_PATHS[repository_name])}: unverified: {error}",
        )
        return None
    except OpenApiPathParseError as error:
        add(
            failures,
            repository_name,
            "openapi-parsing",
            f"{specification.relative_to(ROOT / REPOSITORY_PATHS[repository_name])}: {error}",
        )
        return False
    for route in paths:
        operations = document["paths"][route]
        private_path = route in REPOSITORY_PROFILES[repository_name].private_http_paths
        private_operations = [
            value
            for method, value in operations.items()
            if method in HTTP_OPERATION_METHODS
        ]
        approved_private = (
            private_path
            and bool(private_operations)
            and all(
                operation.get("x-kokoro-visibility") == "browser-private"
                and operation.get("x-kokoro-owner") == repository_name
                for operation in private_operations
            )
        )
        profile = REPOSITORY_PROFILES[repository_name]
        approved_internal = (
            route in profile.internal_http_paths
            and bool(private_operations)
            and all(
                operation.get("x-kokoro-owner") == repository_name
                and operation.get("x-kokoro-visibility") == "internal-owner"
                for operation in private_operations
            )
        )
        # Same-origin adapters have an explicit /api/v1 namespace. This is a
        # versioning rule, not synthesized ownership/visibility metadata; the
        # independent operation-governance check below retains missing fields.
        approved_adapter = (
            profile.kind == "web"
            and relative.parts[:2] == ("contract", "openapi")
            and route.startswith(profile.web_adapter_http_prefixes)
        )
        if not is_v1_http_path(route) and not (
            approved_private or approved_internal or approved_adapter
        ):
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

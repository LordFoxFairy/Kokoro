"""Strict OpenAPI YAML reader used by the Node contract gates.

PyYAML is pinned by the root lock. Keeping YAML parsing here avoids maintaining a second,
partial YAML grammar in JavaScript while still making duplicate keys a hard error.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from typing import Any

import yaml


HTTP_METHODS = frozenset(
    {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
)
OPERATION_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")


class StrictSafeLoader(yaml.SafeLoader):
    """SafeLoader variant that rejects duplicate mapping keys."""


def _construct_mapping(
    loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as error:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "unhashable YAML mapping key",
                key_node.start_mark,
            ) from error
        if duplicate:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be a string-keyed mapping")
    return value


def read_document(source: str) -> dict[str, Any]:
    loaded = yaml.load(source, Loader=StrictSafeLoader)
    document = dict(_require_mapping(loaded, "OpenAPI document"))
    if document.get("openapi") != "3.1.0":
        raise ValueError("OpenAPI version must equal 3.1.0")
    paths = _require_mapping(document.get("paths"), "OpenAPI paths")
    seen: set[str] = set()
    operation_count = 0
    for path, raw_item in paths.items():
        if not path.startswith("/"):
            raise ValueError(f"invalid OpenAPI path: {path}")
        item = _require_mapping(raw_item, f"OpenAPI path item {path}")
        for raw_method, raw_operation in item.items():
            method = raw_method.lower()
            if method not in HTTP_METHODS:
                continue
            operation = _require_mapping(
                raw_operation, f"OpenAPI operation {raw_method} {path}"
            )
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not OPERATION_ID.fullmatch(
                operation_id
            ):
                raise ValueError(f"missing operationId: {method} {path}")
            if operation_id in seen:
                raise ValueError(f"duplicate operationId: {operation_id}")
            seen.add(operation_id)
            operation_count += 1
    if operation_count == 0:
        raise ValueError("OpenAPI has no operations")
    return document


def main() -> int:
    try:
        document = read_document(sys.stdin.read())
        json.dump(document, sys.stdout, separators=(",", ":"), sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (
        Exception
    ) as error:  # The caller translates this into its gate-specific error code.
        sys.stderr.write(f"{error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
